#!/usr/bin/env python3
"""
IEM Cologne Major 2026 — Pick'em Simulator
==========================================
Unified CLI for simulating any Swiss stage of the Major.

Usage:
  python3 main.py --stage 1                 # Stage 1 (Opening)
  python3 main.py --stage 2                 # Stage 2 (Elimination)
  python3 main.py --stage 3                 # Stage 3 (Legends)
  python3 main.py --stage 2 --sims 10000    # More simulations
  python3 main.py --stage 1 --no-advancers  # Simulate from scratch (no preset S1 results)

Config:
  Edit config.py to change team data, stage assignments, or set rank_bias
  for individual teams. rank_bias = +2 means the team is 2 ranks better
  than their HLTV/VRS data suggests.

Algorithm:
  Data-driven win probability using HLTV points, VRS rank, and recent form.
  Swiss pairing follows the CS Major rulebook (inverted seed + DFS matching).
"""

import argparse
import itertools
import random
import sys
from collections import defaultdict

# Ensure the project directory is on the path
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import TEAMS, HEAD_TO_HEAD, STAGE1, STAGE2, STAGE3, STAGE1_ADVANCERS, SIM as _SIM
from swiss_simulator import (
    TeamState, simulate_swiss_stage, monte_carlo_simulate
)
from win_probability import composite_strength, win_probability


# ── Simulation defaults ───────────────────────────────────────────
DEFAULT_TEAM_SIMS = _SIM["team_sims"]
DEFAULT_PICK_SIMS = _SIM["pick_sims"]
DEFAULT_CANDIDATES = _SIM["candidates"]


def _build_pool(codes, start_seed=1):
    """Convert a list of team codes into a {code: team_data_with_seed} dict."""
    pool = {}
    for i, code in enumerate(codes):
        if code is None:
            continue
        t = dict(TEAMS[code])
        t["code"] = code
        t["seed"] = start_seed + i
        pool[code] = t
    return pool


def _simulate_prior_stage_and_sort(stage_num, use_actual):
    """Simulate a prior stage and return advancer codes sorted by VRS."""
    pool = get_teams_for_stage(stage_num, use_actual_s1=use_actual)
    states = {c: TeamState(t) for c, t in pool.items()}
    result = simulate_swiss_stage(states, stage_num=stage_num)
    advancers = result["advancers"]
    advancers.sort(key=lambda c: TEAMS[c]["vrs"])
    return advancers


def get_teams_for_stage(stage, use_actual_s1=True):
    """
    Build the team pool for the requested stage from STAGE1/2/3 config lists.
    Each list entry's position = seed (index 0 = seed 1).

    Stage 1: read directly from STAGE1 list.
    Stage 2: seeds 1-8 from STAGE2[0:8]; seeds 9-16 from STAGE2[8:16]
             (or simulated from Stage 1 if --no-advancers).
    Stage 3: seeds 1-8 from STAGE3[0:8]; seeds 9-16 simulated from Stage 2.
    """
    if stage == 1:
        return _build_pool(STAGE1)

    elif stage == 2:
        direct = [c for c in STAGE2[:8] if c is not None]
        from_s1 = [c for c in STAGE2[8:16] if c is not None]

        if not use_actual_s1 or not from_s1:
            # Simulate Stage 1 to get advancers
            from_s1 = _simulate_prior_stage_and_sort(1, use_actual_s1)

        pool = _build_pool(direct, start_seed=1)
        pool.update(_build_pool(from_s1, start_seed=9))
        return pool

    elif stage == 3:
        direct = [c for c in STAGE3[:8] if c is not None]
        from_s2 = [c for c in STAGE3[8:16] if c is not None]

        if not from_s2:
            # Simulate Stage 1 + Stage 2 to get S2 advancers
            from_s2 = _simulate_prior_stage_and_sort(2, use_actual_s1)

        pool = _build_pool(direct, start_seed=1)
        pool.update(_build_pool(from_s2, start_seed=9))
        return pool

    else:
        raise ValueError(f"Unknown stage: {stage}")


def evaluate_pick(picks, teams_pool, stage_num, num_trials):
    states = {c: TeamState(t) for c, t in teams_pool.items()}
    return monte_carlo_simulate(states, stage_num, picks, num_simulations=num_trials)


def find_best_pickem(teams_pool, stage_num, num_team_sims, num_pick_sims, num_candidates):
    codes = list(teams_pool.keys())

    print(f"  Running team probability simulation ({num_team_sims} trials)...")
    states = {c: TeamState(t) for c, t in teams_pool.items()}
    quick = monte_carlo_simulate(states, stage_num, {
        "exact30": [], "advancers": [], "exact03": []
    }, num_simulations=num_team_sims)
    probs = quick["team_probabilities"]

    e30_scores = [(c, probs[c]["exact30_rate"]) for c in codes]
    adv_scores = [(c, probs[c]["advance_rate"] - probs[c]["exact30_rate"]) for c in codes]
    e03_scores = [(c, probs[c]["exact03_rate"]) for c in codes]

    e30_scores.sort(key=lambda x: x[1], reverse=True)
    adv_scores.sort(key=lambda x: x[1], reverse=True)
    e03_scores.sort(key=lambda x: x[1], reverse=True)

    top_e30 = [c for c, _ in e30_scores[:5]]
    top_adv = [c for c, _ in adv_scores[:10]]
    top_e03 = [c for c, _ in e03_scores[:5]]

    # Collect top combinations (score -> picks+result), keep top 3 unique
    scored = []  # list of (score, picks_dict, result)

    print(f"  Testing up to {num_candidates} Pick'em combinations ({num_pick_sims} trials each)...")
    tested = 0
    for e30_combo in itertools.combinations(top_e30, 2):
        if tested >= num_candidates:
            break

        adv_combo = tuple(c for c in top_adv if c not in e30_combo)[:6]
        if len(adv_combo) < 6:
            extra = [c for c in codes if c not in set(e30_combo) and c not in set(adv_combo)]
            adv_combo = tuple(list(adv_combo) + extra[:6 - len(adv_combo)])

        for e03_combo in itertools.combinations(top_e03, 2):
            all_picked = set(e30_combo + adv_combo + e03_combo)
            if len(all_picked) < 10:
                continue
            tested += 1
            if tested > num_candidates:
                break

            result = evaluate_pick(
                {"exact30": list(e30_combo), "advancers": list(adv_combo[:6]),
                 "exact03": list(e03_combo)},
                teams_pool, stage_num, num_pick_sims
            )
            picks_dict = {"exact30": list(e30_combo),
                          "advancers": list(adv_combo[:6]),
                          "exact03": list(e03_combo),
                          "_strategy": "optimized"}
            scored.append((result["success_rate"], picks_dict, result))

    # Strategy-based picks
    s_adv = sorted(probs.items(), key=lambda x: x[1]["advance_rate"], reverse=True)
    s_e30 = sorted(probs.items(), key=lambda x: x[1]["exact30_rate"], reverse=True)
    s_e03 = sorted(probs.items(), key=lambda x: x[1]["exact03_rate"], reverse=True)
    top8 = [c for c, _ in s_adv[:8]]

    strategies = {
        "safe": {
            "exact30": top8[:2], "advancers": top8[2:8],
            "exact03": [c for c, _ in s_adv[-2:]],
        },
        "balanced": {
            "exact30": [c for c, _ in s_e30[:2]],
            "advancers": [c for c, _ in s_adv if c not in [c2 for c2, _ in s_e30[:2]]
                          and c not in [c2 for c2, _ in s_e03[:2]]][:6],
            "exact03": [c for c, _ in s_e03[:2]],
        },
    }
    for sname, picks in strategies.items():
        result = evaluate_pick(picks, teams_pool, stage_num, num_pick_sims)
        picks["_strategy"] = sname
        scored.append((result["success_rate"], picks.copy(), result))

    # Keep top 3 unique (by combination fingerprint)
    def _fingerprint(p):
        return (tuple(sorted(p["exact30"])), tuple(sorted(p["advancers"])), tuple(sorted(p["exact03"])))

    seen = set()
    unique = []
    for score, picks, result in sorted(scored, key=lambda x: x[0], reverse=True):
        fp = _fingerprint(picks)
        if fp not in seen:
            seen.add(fp)
            unique.append((score, picks, result))
        if len(unique) >= 3:
            break

    return unique, probs


def show_round1(teams_pool):
    """Display Round 0 matchups for verification."""
    from swiss_simulator import generate_round_matches
    states = list(TeamState(t).__dict__ for _, t in teams_pool.items())
    # Rebuild proper TeamState objects
    state_objs = {c: TeamState(t) for c, t in teams_pool.items()}
    matches, stage = generate_round_matches(list(state_objs.values()))
    print(f"\n  Round 0 Matchups (Swiss Round 1):")
    print(f"  {'-' * 50}")
    for t1, t2 in matches:
        s1 = composite_strength(t1.data)
        s2 = composite_strength(t2.data)
        prob = win_probability(t1.data, t2.data, HEAD_TO_HEAD)
        print(f"  {t1.data['name']:<22} (S{t1.data['seed']}, {s1:.3f})")
        print(f"    vs {t2.data['name']:<22} (S{t2.data['seed']}, {s2:.3f})"
              f"  -> {t1.data['name']} {prob:.1%}")
        print()


def print_results(top_results, probs, teams_pool):
    """
    Print the top Pick'em combinations (up to 3).
    top_results is a list of (score, picks_dict, result).
    """
    for rank, (score, picks, result) in enumerate(top_results, 1):
        strategy = picks.pop("_strategy", "optimized")
        labels = {1: "1st", 2: "2nd", 3: "3rd"}
        label = labels.get(rank, f"{rank}th")

        print(f"\n{'=' * 70}")
        print(f"{label} PICK'EM  (strategy: {strategy})")
        print(f"{'=' * 70}")

        print(f"\n  Pass Rate (>=5pts):   {score:.1%}")
        print(f"  Pass Rate (>=4pts):   {result['success_rate_4plus']:.1%}")
        print(f"  Expected Points:      {result.get('expected_points', 0):.2f} / 10")

        print(f"\n  Exact 3-0 Picks (2 slots):")
        for code in picks["exact30"]:
            p = probs[code]
            print(f"    {TEAMS[code]['name']:<22} advance={p['advance_rate']:.1%}  3-0={p['exact30_rate']:.1%}")

        print(f"\n  Advancers Picks (6 slots):")
        for code in picks["advancers"]:
            p = probs[code]
            a_3x = p['advance_rate'] - p['exact30_rate']
            print(f"    {TEAMS[code]['name']:<22} advance={p['advance_rate']:.1%}  3-0={p['exact30_rate']:.1%}"
                  f"  3-1/3-2={a_3x:.1%}")

        print(f"\n  Exact 0-3 Picks (2 slots):")
        for code in picks["exact03"]:
            p = probs[code]
            print(f"    {TEAMS[code]['name']:<22} 0-3={p['exact03_rate']:.1%}")

    # Point distribution from the best result
    best_result = top_results[0][2]
    print(f"\n  Point Distribution (best):")
    for pts in range(11):
        prob = best_result["point_distribution"].get(pts, 0)
        if prob > 0.001:
            bar = "=" * int(prob * 100)
            marker = " <-- pass" if pts == 5 else ""
            print(f"    {pts:2d} pts: {prob:6.1%} {bar}{marker}")

    print(f"\n{'=' * 70}")
    print(f"ALL TEAM PROJECTIONS (sorted by advance rate)")
    print(f"{'=' * 70}")
    print(f"{'Team':<22} {'Advance':>8} {'3-0':>8} {'0-3':>8} {'Str':>6} {'Seed':>4}")
    print("-" * 56)
    for code, p in sorted(probs.items(), key=lambda x: x[1]["advance_rate"], reverse=True):
        t = teams_pool[code]
        s = composite_strength(t)
        print(f"{t['name']:<22} {p['advance_rate']:>7.1%} {p['exact30_rate']:>7.1%}"
              f" {p['exact03_rate']:>7.1%} {s:>6.4f} {t['seed']:>4}")


def main():
    parser = argparse.ArgumentParser(
        description="IEM Cologne Major 2026 Pick'em Simulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 main.py --stage 1
  python3 main.py --stage 2 --sims 10000
  python3 main.py --stage 3 --no-advancers

Customize team strength: edit config.py, set rank_bias per team.
  rank_bias = +2  → team treated as 2 ranks better
  rank_bias = -1  → team treated as 1 rank worse
        """)
    parser.add_argument("--stage", type=int, required=True, choices=[1, 2, 3],
                        help="Which Swiss stage to simulate (1/2/3)")
    parser.add_argument("--sims", type=int, default=DEFAULT_TEAM_SIMS,
                        help=f"Number of Monte Carlo trials (default: {DEFAULT_TEAM_SIMS})")
    parser.add_argument("--pick-sims", type=int, default=DEFAULT_PICK_SIMS,
                        help=f"Trials per Pick'em candidate (default: {DEFAULT_PICK_SIMS})")
    parser.add_argument("--candidates", type=int, default=DEFAULT_CANDIDATES,
                        help=f"Max Pick'em combinations to test (default: {DEFAULT_CANDIDATES})")
    parser.add_argument("--no-advancers", action="store_true",
                        help="For stage 2/3: simulate prior stages from scratch "
                             "(ignore config.STAGE1_ADVANCERS)")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for reproducibility (default: 42)")
    args = parser.parse_args()

    random.seed(args.seed)
    use_actual = not args.no_advancers

    # ── Stage info ──────────────────────────────────────────────
    stage_names = {
        1: "OPENING STAGE (Stage 1)",
        2: "ELIMINATION STAGE (Stage 2)",
        3: "LEGENDS STAGE (Stage 3)",
    }
    print("=" * 70)
    print(f"IEM COLOGNE MAJOR 2026 — {stage_names[args.stage]}")
    print("=" * 70)

    # ── Build team pool ─────────────────────────────────────────
    print(f"\n  Building team pool...")
    teams_pool = get_teams_for_stage(args.stage, use_actual_s1=use_actual)

    # Count rank_bias overrides
    bias_count = sum(1 for t in teams_pool.values() if t.get("rank_bias", 0) != 0)
    if bias_count > 0:
        print(f"  ({bias_count} team(s) with custom rank_bias)")

    print(f"\n  Stage {args.stage} — {len(teams_pool)} teams:")
    for code in sorted(teams_pool.keys(), key=lambda c: teams_pool[c]["seed"]):
        t = teams_pool[code]
        s = composite_strength(t)
        bias = t.get("rank_bias", 0)
        bias_str = f" bias={'+' if bias > 0 else ''}{bias}" if bias != 0 else ""
        print(f"    Seed{t['seed']:>2}: {t['name']:<22} VRS#{t['vrs']}"
              f" HLTV#{t['hltv_rank']} s={s:.4f}{bias_str}")

    # ── Verify Round 1 pairings ─────────────────────────────────
    show_round1(teams_pool)

    # ── Find optimal Pick'em ────────────────────────────────────
    top_results, probs = find_best_pickem(
        teams_pool, args.stage, args.sims, args.pick_sims, args.candidates
    )

    # ── Print results ───────────────────────────────────────────
    print_results(top_results, probs, teams_pool)

    # ── Show next-stage context ─────────────────────────────────
    if args.stage == 1:
        print(f"\n  Top 8 advance to Stage 2 and join:")
        print(f"  Spirit, Astralis, FUT, G2, Legacy, paiN, Monte, 9z")
    elif args.stage == 2:
        print(f"\n  Top 8 advance to Stage 3 (Legends) and join:")
        print(f"  Vitality, NAVI, Falcons, FURIA, Aurora, MOUZ, MongolZ, PARIVISION")
    elif args.stage == 3:
        print(f"\n  Top 8 advance to Playoffs (single-elimination bracket).")


if __name__ == "__main__":
    main()
