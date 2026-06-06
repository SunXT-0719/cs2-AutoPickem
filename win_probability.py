"""
Win Probability Model — Elo / Ratio Hybrid
==========================================
Two-component model:
  p_vrs  = 1 / (1 + 10^((vrs_B - vrs_A) / _M["sigma_vrs"]))     [Elo formula]
  p_hltv = 1 / (1 + (hltv_B / hltv_A) ^ _M["hltv_exp"])          [ratio formula]

  p_total = _M["w_hltv"] * p_hltv + _M["w_vrs"] * p_vrs

rank_bias: user-defined per-team adjustment in config.py.
  +1 = team is 1 rank better than data suggests
  -1 = team is 1 rank worse than data suggests
  Applied by shifting effective VRS and HLTV ratings proportionally.
"""

import math
import argparse
from config import MODEL as _M

# ── Rating estimation from ranks ─────────────────────────────────
# Maps rank → typical absolute rating for Elo calculations.
# Derived from CS2 competitive rating distributions.

def _vrs_from_rank(rank):
    """Estimate VRS absolute rating from rank (1=best, 74=worst)."""
    rank = max(1, int(rank))
    # Typical VRS range: ~1900 (rank 1) to ~1100 (rank 74)
    return 1880 - (rank - 1) * 10.5

def _hltv_rating_from_pts(pts):
    """Estimate HLTV absolute rating from HLTV points."""
    pts = max(1, pts)
    # Scale: 1000 pts → ~180 rating, 1 pt → ~1 rating
    return 3 + pts * 0.177


def _effective_ratings(team):
    """
    Apply rank_bias to get effective VRS rank and HLTV rating.
    Positive bias → team is better → effectively lower VRS rank, higher HLTV rating.
    """
    bias = team.get("rank_bias", 0)
    if bias == 0:
        return team.get("rating_vrs", _vrs_from_rank(team["vrs"])), \
               team.get("rating_hltv", _hltv_rating_from_pts(team["hltv_pts"]))

    # With bias: shift effective rank, then recompute rating
    eff_vrs_rank = max(1, team["vrs"] - bias)
    # For HLTV: shift rank proportionally, recompute pts from curve
    eff_hltv_rank = max(1, team["hltv_rank"] - bias)
    from config import TEAMS
    # Simple proportional HLT pts estimation from rank
    if eff_hltv_rank <= 5:
        eff_pts = 500 - (eff_hltv_rank - 1) * 80
    elif eff_hltv_rank <= 10:
        eff_pts = 200 - (eff_hltv_rank - 5) * 20
    elif eff_hltv_rank <= 20:
        eff_pts = 100 - (eff_hltv_rank - 10) * 7
    elif eff_hltv_rank <= 30:
        eff_pts = 30 - (eff_hltv_rank - 20) * 2.5
    else:
        eff_pts = max(1, 5 - (eff_hltv_rank - 30) * 0.15)
    eff_pts = max(1, eff_pts)

    eff_vrs_rating = _vrs_from_rank(eff_vrs_rank)
    eff_hltv_rating = _hltv_rating_from_pts(eff_pts)
    return eff_vrs_rating, eff_hltv_rating


def composite_strength(team):
    """
    Composite strength score [0,1] for display/comparison.
    Combines normalized Elo expectations.
    """
    v, h = _effective_ratings(team)
    # Normalize against baseline
    v_norm = (v - 1050) / 850       # ~0 to ~1
    h_norm = math.log(1 + h) / math.log(1 + 185)  # ~0 to ~1
    return _M["w_hltv"] * h_norm + _M["w_vrs"] * v_norm


def _base_map_prob(team_a, team_b):
    """Raw single-map win probability from Elo/Ratio model (before upset adjustment)."""
    va, ha = _effective_ratings(team_a)
    vb, hb = _effective_ratings(team_b)

    p_vrs = 1.0 / (1.0 + 10.0 ** ((vb - va) / _M["sigma_vrs"]))
    if hb > 0 and ha > 0:
        p_hltv = 1.0 / (1.0 + (hb / ha) ** _M["hltv_exp"])
    else:
        p_hltv = 0.5

    return (_M["w_hltv"] * p_hltv + _M["w_vrs"] * p_vrs) / (_M["w_hltv"] + _M["w_vrs"])


def _apply_upset(p, upset):
    """Pull a probability toward 50% by the given factor."""
    return 0.5 + (p - 0.5) * (1.0 - upset)


def win_probability(team_a, team_b, head_to_head=None):
    """
    Probability of team_a beating team_b in a BO1.
    Applies BO1 upset factor (high variance, pulled toward 50%).
    """
    p = _base_map_prob(team_a, team_b)
    p = _apply_upset(p, _M["upset_bo1"])

    if head_to_head:
        key = (team_a["code"], team_b["code"])
        if key in head_to_head:
            adj = (head_to_head[key] - 0.5) * 0.12
            p = max(0.02, min(0.98, p + adj))

    return p


def bo3_win_probability(team_a, team_b, head_to_head=None):
    """
    Probability of team_a beating team_b in a BO3.
    Applies BO3 upset factor per-map, then computes BO3 binomial.
    """
    p_map = _base_map_prob(team_a, team_b)
    p_map = _apply_upset(p_map, _M["upset_bo3"])

    if head_to_head:
        key = (team_a["code"], team_b["code"])
        if key in head_to_head:
            adj = (head_to_head[key] - 0.5) * 0.12
            p_map = max(0.02, min(0.98, p_map + adj))

    return p_map * p_map + 2 * p_map * p_map * (1 - p_map)


def match_win_probability(team_a, team_b, is_bo3=False, head_to_head=None):
    """Convenience: call win_probability or bo3_win_probability based on is_bo3."""
    if is_bo3:
        return bo3_win_probability(team_a, team_b, head_to_head)
    return win_probability(team_a, team_b, head_to_head)


def print_ranking(teams):
    ranked = [(c, t["name"], t["hltv_rank"], t["vrs"],
               t.get("rank_bias", 0), composite_strength(t))
              for c, t in teams.items()]
    ranked.sort(key=lambda x: x[5], reverse=True)
    print(f"\n{'Rk':<4} {'Team':<22} {'HLTV':>5} {'VRS':>4} {'bias':>5} {'Str':>8}")
    print("-" * 55)
    for i, (code, name, hr, vr, bias, s) in enumerate(ranked, 1):
        bias_str = f"+{bias}" if bias > 0 else str(bias) if bias < 0 else "0"
        print(f"{i:<4} {name:<22} {hr:>5} {vr:>4} {bias_str:>5} {s:>8.4f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    from config import TEAMS
    print_ranking(TEAMS)
