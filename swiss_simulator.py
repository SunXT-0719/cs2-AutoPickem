"""
CS2 Major Swiss Stage Simulator

Simulates the IEM Cologne Major 2026 Swiss system using the win probability
model from win_probability.py. Runs Monte Carlo simulations to find the
optimal Pick'em selections.

Swiss format (16 teams, Stage 1 & 2 & 3):
- 3 wins to advance, 3 losses to eliminate
- BO1 for non-elimination/advancement matches
- BO3 for elimination matches (0-2, 1-2, 2-1, 2-2 records)
- Buchholz seeding for tiebreakers
- Matchmaking: teams face others with same W-L record, avoid rematches

Pick'em scoring (5 points max):
- 2 slots: Pick teams going 3-0 (exact30)  - 1pt each
- 6 slots: Pick teams advancing (advancers) - 1pt each (must go 3-1 or 3-2)
- 2 slots: Pick teams going 0-3 (exact03)  - 1pt each
"""

import math
import random
import itertools
from collections import defaultdict
from win_probability import win_probability, bo3_win_probability
from config import TEAMS, HEAD_TO_HEAD

# Swiss rules for 2026 Cologne Major
WINS_TO_ADVANCE = 3
LOSSES_TO_ELIMINATE = 3
TOTAL_ROUNDS = 5  # 0-1-2-3-4 (max 5 rounds for swiss)


class TeamState:
    """Tracks a team's state during a Swiss tournament simulation."""
    def __init__(self, team_data):
        self.code = team_data["code"]
        self.name = team_data["name"]
        self.data = team_data
        self.wins = 0
        self.losses = 0
        self.opponents = []  # list of opponent codes played
        self.buchholtz = 0  # opponent record score
        self.eliminated = False
        self.advanced = False


def get_pools(teams):
    """Group teams by W-L record, return sorted pools."""
    pools = defaultdict(list)
    for t in teams:
        if t.eliminated or t.advanced:
            continue
        key = f"{t.wins}-{t.losses}"
        pools[key].append(t)

    # Sort pools: most wins first
    sorted_keys = sorted(pools.keys(), key=lambda k: (-int(k.split('-')[0]), int(k.split('-')[1])))
    return [(k, pools[k]) for k in sorted_keys]


def calculate_buchholtz(teams):
    """Calculate Buchholtz score for each team."""
    record_score = {}
    for t in teams:
        record_score[t.code] = t.wins - t.losses

    for t in teams:
        t.buchholtz = sum(record_score.get(op, 0) for op in t.opponents)


def compare_teams(a, b, stage):
    """Sort comparison for Swiss seeding."""
    # 1. Fewer losses first
    if a.losses != b.losses:
        return -1 if a.losses < b.losses else 1
    # 2. More wins first
    if a.wins != b.wins:
        return -1 if a.wins > b.wins else 1
    # 3. Buchholtz (after round 0)
    if stage > 0:
        if a.buchholtz != b.buchholtz:
            return -1 if a.buchholtz > b.buchholtz else 1
    # 4. Seed
    return -1 if a.data["seed"] < b.data["seed"] else 1


def sort_teams(teams, stage):
    """
    Sort teams within a pool for Swiss pairing.

    Round 0 (stage=0): CS Major "inverted seed" for bottom-half teams.
    Seeds 1-8 rank normally (1 is best). Seeds 9-16 are REVERSED so
    16 becomes the best among bottom seeds. This produces the classic
    folded pairing (1v16, 2v15, ... 8v9) when paired top-vs-bottom-half.

    Later rounds (stage>0): standard ordering by losses, wins, Buchholtz, seed.
    """
    all_seeds = [t.data["seed"] for t in teams]
    min_seed = min(all_seeds) if all_seeds else 1

    def sort_key(t):
        seed = t.data["seed"]
        if stage == 0:
            # Inverted seed for bottom half (seed >= min_seed + 8)
            use_seed = 1000 - seed if seed >= min_seed + 8 else seed
            return (t.losses, -t.wins, 0, use_seed)
        else:
            return (t.losses, -t.wins, -(t.buchholtz), seed)

    return sorted(teams, key=sort_key)


def has_played(a, b):
    """Check if two teams have already played each other."""
    return b.code in a.opponents or a.code in b.opponents


def pair_pool(pool_teams, stage):
    """
    Pair teams within the same W-L pool.

    Matches the algorithm in majors.im: uses DFS-like pairing where
    the first team (best in sorted order) pairs with the last available
    candidate from the end of the list (reverse search). For stage <= 2,
    returns the first valid match found (no exhaustive optimization).

    This produces: pool[i] vs pool[n-1-i] for stage 0 (folded pairing),
    and similar reversed-bottom-half pairing for later stages.

    Handles rematches by trying earlier candidates in the reverse search.
    """
    n = len(pool_teams)
    if n == 0:
        return []
    if n % 2 != 0:
        return []

    sorted_teams = sort_teams(pool_teams, stage)
    matches = []
    used = [False] * n

    for i in range(n):
        if used[i]:
            continue

        t1 = sorted_teams[i]
        # Search from the END of the list for a valid partner
        # (mirrors the DFS `for (let c = remaining.length - 1; c >= 1; c -= 1)` loop)
        found = False
        for j in range(n - 1, i, -1):
            if used[j]:
                continue
            t2 = sorted_teams[j]
            if not has_played(t1, t2):
                matches.append((t1, t2))
                used[i] = True
                used[j] = True
                found = True
                break

        if not found:
            # Fallback: force-pair with first available (should be rare)
            for j in range(i + 1, n):
                if not used[j]:
                    matches.append((t1, sorted_teams[j]))
                    used[i] = True
                    used[j] = True
                    found = True
                    break

    return matches


def generate_round_matches(teams):
    """Generate all matches for the current Swiss round."""
    pools = get_pools(teams)

    # Calculate stage (current round number based on min wins+losses)
    active = [t for t in teams if not t.eliminated and not t.advanced]
    if not active:
        return [], 0

    stage = min(t.wins + t.losses for t in active)

    all_matches = []
    pool_teams_list = []

    for pool_key, pool_teams in pools:
        # Sort within pool
        sorted_pool = sort_teams(pool_teams, stage)
        pool_teams_list.append(sorted_pool)

        if len(sorted_pool) % 2 != 0:
            # Odd pool: promote one team to next pool
            # Promote the best team from this pool to the next pool (higher difficulty)
            # Actually: promote to next pool for pairing
            pass

    # Handle odd pools by moving teams up
    for i in range(len(pool_teams_list) - 1):
        if len(pool_teams_list[i]) % 2 != 0:
            # Move the lowest seed team from pool i to pool i+1
            moved = pool_teams_list[i].pop()
            pool_teams_list[i + 1].append(moved)
            # Re-sort pool i+1
            pool_teams_list[i + 1] = sort_teams(pool_teams_list[i + 1], stage)

    for pool_teams in pool_teams_list:
        matches = pair_pool(pool_teams, stage)
        all_matches.extend(matches)

    return all_matches, stage


def is_bo3(match_record):
    """
    Determine if a match should be BO3.
    In 2026 Cologne Major:
    - BO3 for elimination/advancement matches (where one team is at 2-x or x-2)
    - Actually: ALL elimination and advancement matches are BO3
    """
    # In the 2026 major, Stage 3 is all BO3
    # Stage 1 & 2: elimination and advancement matches are BO3
    # 0-2, 1-2, 2-1, 2-2 matches are BO3
    w1, l1 = match_record
    # If either team is at 2 wins or 2 losses, it's a bo3
    return w1 >= 2 or l1 >= 2


def simulate_match(team_a, team_b, stage_info, is_stage3=False):
    """
    Simulate a single match outcome based on win probability model.

    Args:
        team_a, team_b: TeamState objects
        stage_info: dict with match context
        is_stage3: if True, ALL matches are BO3 (Stage 3 rule)

    Returns:
        winner, loser: TeamState objects
    """
    # Determine BO1 vs BO3
    use_bo3 = is_stage3 or is_bo3((team_a.wins, team_a.losses))

    if use_bo3:
        prob = bo3_win_probability(team_a.data, team_b.data, HEAD_TO_HEAD)
    else:
        prob = win_probability(team_a.data, team_b.data, HEAD_TO_HEAD)

    # Simulate
    if random.random() < prob:
        return team_a, team_b
    else:
        return team_b, team_a


def apply_result(winner, loser):
    """Update team records after a match."""
    winner.wins += 1
    loser.losses += 1
    winner.opponents.append(loser.code)
    loser.opponents.append(winner.code)

    # Check for advance/elimination
    if winner.wins >= WINS_TO_ADVANCE:
        winner.advanced = True
    if loser.losses >= LOSSES_TO_ELIMINATE:
        loser.eliminated = True


def simulate_swiss_stage(teams_dict, stage_num, random_seed=None):
    """
    Simulate a single Swiss stage tournament.

    Args:
        teams_dict: dict of code -> TeamState for the 16 teams in this stage
        stage_num: 1, 2, or 3 (determines BO3 rules for stage 3)
        random_seed: optional seed for reproducibility

    Returns:
        results: {
            'exact30': [code, code],  # Teams that went 3-0
            'advancers': [code, ...],  # All teams that advanced (3-1, 3-2)
            'exact03': [code, code],   # Teams that went 0-3
            'eliminated': [code, ...], # All eliminated teams
            'all_results': {code: '3-0'|'3-1'|'3-2'|'2-3'|'1-3'|'0-3'}
        }
    """
    if random_seed is not None:
        random.seed(random_seed)

    teams = list(teams_dict.values())

    # Reset state
    for t in teams:
        t.wins = 0
        t.losses = 0
        t.opponents = []
        t.buchholtz = 0
        t.eliminated = False
        t.advanced = False

    is_stage3 = (stage_num == 3)

    # Simulate up to 5 rounds
    max_rounds = 5
    for round_num in range(max_rounds):
        active = [t for t in teams if not t.eliminated and not t.advanced]
        if not active:
            break

        calculate_buchholtz(teams)
        matches, stage_round = generate_round_matches(teams)

        for team_a, team_b in matches:
            winner, loser = simulate_match(team_a, team_b, {}, is_stage3)
            apply_result(winner, loser)

    # Collect results
    exact30 = []
    advancers_3x = []  # 3-1 or 3-2
    exact03 = []
    eliminated = []
    all_results = {}

    for t in teams:
        record = f"{t.wins}-{t.losses}"
        all_results[t.code] = record

        if t.wins == 3 and t.losses == 0:
            exact30.append(t.code)
        if t.wins == 3 and t.losses > 0:
            advancers_3x.append(t.code)
        if t.wins == 0 and t.losses == 3:
            exact03.append(t.code)
        if t.losses >= 3 and t.wins < 3:
            eliminated.append(t.code)

    return {
        "exact30": exact30,
        "advancers": exact30 + advancers_3x,  # All advancing teams
        "advancers_3x": advancers_3x,
        "exact03": exact03,
        "eliminated": eliminated,
        "all_results": all_results,
    }


def score_pickem(picks, results):
    """
    Score a Pick'em selection against tournament results.

    Args:
        picks: {
            'exact30': [code, code],     # 2 picks
            'advancers': [code, ...],    # 6 picks
            'exact03': [code, code],     # 2 picks
        }
        results: output from simulate_swiss_stage()

    Returns:
        int: points scored (0-5)
    """
    points = 0

    # Exact 3-0: 1 point each if team goes exactly 3-0
    for code in picks.get("exact30", []):
        if code in results["exact30"]:
            points += 1

    # Advancers: 1 point each if team advances (3-1 or 3-2, NOT 3-0)
    for code in picks.get("advancers", []):
        if code in results["advancers_3x"]:
            points += 1

    # Exact 0-3: 1 point each if team goes exactly 0-3
    for code in picks.get("exact03", []):
        if code in results["exact03"]:
            points += 1

    return points


def monte_carlo_simulate(teams_dict, stage_num, picks, num_simulations=10000):
    """
    Run Monte Carlo simulation of the Swiss stage and score a Pick'em.

    Returns:
        dict with success_rate, point_distribution, advance_rates, etc.
    """
    point_counts = defaultdict(int)
    exact30_counts = defaultdict(int)
    exact03_counts = defaultdict(int)
    advance_counts = defaultdict(int)
    result_30_counts = defaultdict(int)
    result_03_counts = defaultdict(int)
    result_advance_counts = defaultdict(int)

    for sim in range(num_simulations):
        results = simulate_swiss_stage(teams_dict, stage_num, random_seed=sim)
        points = score_pickem(picks, results)
        point_counts[points] += 1

        # Track per-team results
        for code in results["exact30"]:
            result_30_counts[code] += 1
        for code in results["exact03"]:
            result_03_counts[code] += 1
        for code in results["advancers"]:
            result_advance_counts[code] += 1

        # Track pick accuracy
        for code in picks.get("exact30", []):
            if code in results["exact30"]:
                exact30_counts[code] += 1
        for code in picks.get("exact03", []):
            if code in results["exact03"]:
                exact03_counts[code] += 1
        for code in picks.get("advancers", []):
            if code in results["advancers"]:
                advance_counts[code] += 1

    # Calculate success rate (>=5 points = pass this stage)
    success_5 = sum(point_counts[p] for p in range(5, 11)) / num_simulations
    success_4 = sum(point_counts[p] for p in range(4, 11)) / num_simulations

    # Team probabilities
    team_probs = {}
    for code, team in teams_dict.items():
        team_probs[code] = {
            "name": team.name,
            "advance_rate": result_advance_counts[code] / num_simulations,
            "exact30_rate": result_30_counts[code] / num_simulations,
            "exact03_rate": result_03_counts[code] / num_simulations,
        }

    # Expected value
    expected_points = sum(p * count for p, count in point_counts.items()) / num_simulations

    return {
        "success_rate": success_5,
        "success_rate_4plus": success_4,
        "expected_points": expected_points,
        "point_distribution": {
            p: point_counts[p] / num_simulations for p in range(11)
        },
        "team_probabilities": team_probs,
        "pick_accuracy": {
            "exact30": {k: v / num_simulations for k, v in exact30_counts.items()},
            "advancers": {k: v / num_simulations for k, v in advance_counts.items()},
            "exact03": {k: v / num_simulations for k, v in exact03_counts.items()},
        },
    }
