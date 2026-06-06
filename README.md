# Cologne Major 2026 — Pick'em Simulator

[中文版](README_zh.md)

CS2 Major Swiss stage simulator for finding optimal Pick'em selections.
Uses an Elo/ratio hybrid win-probability model with Monte Carlo simulation.

## Quick Start

```bash
cd /Users/sunxt/projects/cologne-pickem
python3 main.py --stage 1
python3 main.py --stage 2
python3 main.py --stage 3
```

## CLI Options

```
--stage {1,2,3}        Which Swiss stage to simulate (required)
--sims N               Monte Carlo trials for team probabilities
--pick-sims N          Trials per Pick'em candidate
--candidates N         Max Pick'em combinations to test
--no-advancers         Ignore preset S1 results; simulate prior stages from scratch
--seed N               Random seed for reproducibility (default: 42)
```

Examples:
```bash
python3 main.py --stage 2 --sims 10000 --pick-sims 5000
python3 main.py --stage 3 --no-advancers
```

## File Structure

```
cologne-pickem/
├── config.py              # All configurable data and parameters
├── win_probability.py     # Elo/ratio win probability model
├── swiss_simulator.py     # Swiss tournament simulation engine
├── main.py                # CLI entry point + Pick'em optimizer
└── README.md
```

## Configuration

All tunable parameters are in `config.py`.

### Team data (`TEAMS`)

```python
"vita": {
    "name": "Team Vitality",
    "vrs": 1,              # VRS rank (Valve Regional Standings)
    "hltv_rank": 1,        # HLTV world ranking position
    "hltv_pts": 1000,      # HLTV ranking points
    "form": 0.95,          # recent form [0-1] (unused in Elo model)
    "rank_bias": 0,        # optional strength adjustment
},
```

### Stage seedings (`STAGE1`, `STAGE2`, `STAGE3`)

Each stage is a list of 16 team codes in seed order. Reorder codes to change seeding.

```python
STAGE2 = [
    "fut", "spir", "astr", "g2", "lega", "pain", "monte", "9z",   # seeds 1-8
    "b8", "betb", "gl", "m80", "mibr", "tylo", "big", "fly",      # seeds 9-16
]
```

### rank_bias

Adjust a team's perceived strength relative to their HLTV/VRS ranking.
Shifts effective rank, then recalculates Elo ratings from the adjusted rank.

```python
"tylo": {..., "rank_bias": 5},     # treated as 5 ranks better
"astr": {..., "rank_bias": -3},    # treated as 3 ranks worse
```

- `+N`: effective rank = actual rank - N (team is stronger than data shows)
- `-N`: effective rank = actual rank + N (team is weaker than data shows)
- Default `0`: no adjustment

### Model parameters (`MODEL`)

```python
MODEL = {
    # Elo / Ratio weights
    "sigma_vrs": 89.0,       # Elo sigma for VRS component
    "hltv_exp": 0.432,       # exponent for HLTV ratio component
    "w_hltv": 0.837,         # HLTV weight (dominant)
    "w_vrs": 0.163,          # VRS weight

    # Upset factors
    #   upset > 0  -> pulls toward 50% (more randomness)
    #   upset = 0  -> no change
    #   upset < 0  -> pushes away from 50% (amplifies favorite)
    "upset_bo1": 0.20,       # BO1: high variance, single-map randomness
    "upset_bo3": -0.10,      # BO3: multi-map amplifies skill gap

    # H2H adjustment
    "h2h_weight": 0.12,      # max ±6% for extreme head-to-head records
}
```

### Simulation defaults (`SIM`)

```python
SIM = {
    "team_sims": 5000,       # trials for team probability estimation
    "pick_sims": 3000,       # trials per Pick'em candidate evaluation
    "candidates": 4000,      # max Pick'em combinations to test
}
```

## Win Probability Model

Two-component Elo/ratio hybrid:

```
VRS ratings estimated from rank:  1880 - (rank - 1) * 10.5
HLTV ratings estimated from points:  3 + pts * 0.177

p_vrs  = 1 / (1 + 10^((vrs_B - vrs_A) / sigma_vrs))
p_hltv = 1 / (1 + (hltv_B / hltv_A) ^ hltv_exp)
p_base = w_hltv * p_hltv + w_vrs * p_vrs

Upset adjustment:
p_map  = 0.5 + (p_base - 0.5) * (1 - upset_factor)

BO1:  uses upset_bo1 (e.g. 0.20 -> 80% becomes 74%)
BO3:  applies upset_bo3 per-map (e.g. -0.10 -> 80% becomes 83%),
      then computes binomial: P(2-0) + P(2-1)
```

## Swiss Pairing Algorithm

Follows the CS Major 2026 official rulebook (verified against [majors.im](https://majors.im/2026/cologne) source code):

1. **Inverted seed sort** (Round 0): seeds 1-8 rank normally; seeds 9-16 are inverted so the strongest bottom-half team pairs with the strongest top-half team
2. **DFS from end**: within each W-L pool, the first team pairs with the last eligible team from the end of the sorted list, avoiding rematches
3. **Buchholz tiebreaker**: after Round 0, teams are sorted by losses (asc), wins (desc), Buchholz (desc), then seed
4. **BO3 for elimination/advancement matches**: when a team is at 2 wins or 2 losses

## Pick'em Scoring

10 picks per stage, max 10 points:

| Category | Slots | Scores if |
|----------|:-----:|-----------|
| exact30  | 2 | team goes exactly 3-0 |
| advancers | 6 | team goes 3-1 or 3-2 |
| exact03  | 2 | team goes exactly 0-3 |

Pass threshold: >= 5 correct picks (>=5 pts).

## Output

The simulation prints:
- Team pool with strength scores and rank_bias indicators
- Round 0 matchups for pairing verification
- **Top 3** Pick'em combinations, each with:
  - Pass rates (>=5pts, >=4pts) and expected points
  - Exact 3-0 / Advancers / Exact 0-3 picks with per-team probabilities
- Point distribution chart from the best combination
- Full team projections (advance / 3-0 / 0-3 rates)

## Data Sources

- HLTV rankings from [5EPlay](https://csgo.5eplay.com) weekly reports (June 2, 2026)
- VRS rankings from official Major seeding
- Tournament results from HLTV / Liquipedia / esports news
