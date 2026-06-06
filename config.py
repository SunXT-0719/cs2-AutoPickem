"""
IEM Cologne Major 2026 — Configuration
======================================
Three sections:
  1. TEAMS       — base data shared across all stages
  2. STAGE1/2/3  — team codes in seed order (list index = seed - 1)
  3. STAGE1_ADVANCERS / HEAD_TO_HEAD — tournament results & history

To customize a team's perceived strength, add rank_bias:
  +2 = team is 2 ranks better than HLTV/VRS suggests
  -1 = team is 1 rank worse than data shows
"""

# ═══════════════════════════════════════════════════════════════════
# 1. TEAM BASE DATA  (shared across stages)
# ═══════════════════════════════════════════════════════════════════
TEAMS = {
    # ── Stage 3 direct (Legends) ──────────────────────────────────
    "vita": {"name": "Team Vitality",     "vrs": 1,  "hltv_rank": 1,  "hltv_pts": 1000, "form": 0.95},
    "navi": {"name": "Natus Vincere",     "vrs": 2,  "hltv_rank": 2,  "hltv_pts": 711,  "form": 0.85},
    "falc": {"name": "Team Falcons",      "vrs": 3,  "hltv_rank": 4,  "hltv_pts": 509,  "form": 0.78},
    "furi": {"name": "FURIA",             "vrs": 10, "hltv_rank": 5,  "hltv_pts": 400,  "form": 0.74},
    "auro": {"name": "Aurora Gaming",     "vrs": 9,  "hltv_rank": 6,  "hltv_pts": 350,  "form": 0.70},
    "mouz": {"name": "MOUZ",              "vrs": 11, "hltv_rank": 8,  "hltv_pts": 300,  "form": 0.68},
    "mong": {"name": "The MongolZ",       "vrs": 7,  "hltv_rank": 9,  "hltv_pts": 280,  "form": 0.72},
    "pv":   {"name": "PARIVISION",        "vrs": 8,  "hltv_rank": 11, "hltv_pts": 250,  "form": 0.66},

    # ── Stage 2 direct (Elimination) ──────────────────────────────
    "spir": {"name": "Team Spirit",       "vrs": 5,  "hltv_rank": 3,  "hltv_pts": 517,  "form": 0.80},
    "astr": {"name": "Astralis",          "vrs": 6,  "hltv_rank": 12, "hltv_pts": 240,  "form": 0.73, "rank_bias": -3},
    "fut":  {"name": "FUT Esports",       "vrs": 4,  "hltv_rank": 13, "hltv_pts": 225,  "form": 0.74},
    "g2":   {"name": "G2 Esports",        "vrs": 12, "hltv_rank": 14, "hltv_pts": 210,  "form": 0.68},
    "lega": {"name": "Legacy",            "vrs": 14, "hltv_rank": 7,  "hltv_pts": 340,  "form": 0.82},
    "pain": {"name": "paiN Gaming",       "vrs": 17, "hltv_rank": 18, "hltv_pts": 150,  "form": 0.62},
    "monte":{"name": "Monte",             "vrs": 18, "hltv_rank": 24, "hltv_pts": 95,   "form": 0.58},
    "9z":   {"name": "9z Team",           "vrs": 19, "hltv_rank": 20, "hltv_pts": 130,  "form": 0.56},

    # ── Stage 1 (Opening) ─────────────────────────────────────────
    "gl":   {"name": "GamerLegion",       "vrs": 13, "hltv_rank": 10, "hltv_pts": 265,  "form": 0.76},
    "b8":   {"name": "B8",                "vrs": 16, "hltv_rank": 16, "hltv_pts": 170,  "form": 0.60},
    "hero": {"name": "HEROIC",            "vrs": 20, "hltv_rank": 27, "hltv_pts": 80,   "form": 0.55},
    "betb": {"name": "BetBoom Team",      "vrs": 21, "hltv_rank": 21, "hltv_pts": 120,  "form": 0.60},
    "big":  {"name": "BIG",               "vrs": 23, "hltv_rank": 32, "hltv_pts": 65,   "form": 0.52},
    "m80":  {"name": "M80",               "vrs": 24, "hltv_rank": 28, "hltv_pts": 72,   "form": 0.55},
    "mibr": {"name": "MIBR",              "vrs": 27, "hltv_rank": 19, "hltv_pts": 140,  "form": 0.58},
    "sinn": {"name": "SINNERS Esports",   "vrs": 30, "hltv_rank": 30, "hltv_pts": 55,   "form": 0.40},
    "nrg":  {"name": "NRG",               "vrs": 31, "hltv_rank": 33, "hltv_pts": 40,   "form": 0.42},
    "tylo": {"name": "TYLOO",             "vrs": 34, "hltv_rank": 29, "hltv_pts": 65,   "form": 0.45, "rank_bias": 5},
    "shks": {"name": "Sharks Esports",    "vrs": 37, "hltv_rank": 40, "hltv_pts": 18,   "form": 0.30},
    "gg":   {"name": "Gaimin Gladiators", "vrs": 40, "hltv_rank": 45, "hltv_pts": 14,   "form": 0.28, "rank_bias": -20},
    "liqu": {"name": "Team Liquid",       "vrs": 47, "hltv_rank": 25, "hltv_pts": 90,   "form": 0.50, "rank_bias": 5},
    "lvg":  {"name": "Lynn Vision Gaming","vrs": 49, "hltv_rank": 31, "hltv_pts": 50,   "form": 0.40, "rank_bias": 5},
    "tdu":  {"name": "THUNDERdOWNUNDER",  "vrs": 56, "hltv_rank": 60, "hltv_pts": 5,    "form": 0.20},
    "fly":  {"name": "FlyQuest",          "vrs": 74, "hltv_rank": 70, "hltv_pts": 3,    "form": 0.22, "rank_bias": 10},
}

# ═══════════════════════════════════════════════════════════════════
# 2. STAGE SEEDINGS  (list index = seed - 1)
# ═══════════════════════════════════════════════════════════════════
# Reorder or replace codes to change seeding within each stage.

STAGE1 = [
    # seed  1-8
    "gl", "b8", "hero", "betb", "big", "m80", "mibr", "sinn",
    # seed  9-16
    "nrg", "tylo", "shks", "gg", "liqu", "lvg", "tdu", "fly",
]

STAGE2 = [
    # seed  1-8  (direct — sorted by VRS)
    "fut", "spir", "astr", "g2", "lega", "pain", "monte", "9z",
    # seed  9-16 (from Stage 1 — by record then VRS)
    #   3-0: B8, BetBoom
    #   3-1: GL, M80, MIBR
    #   3-2: TYLOO, BIG, FlyQuest  (TYLOO ahead of BIG by HLTV rank tiebreaker)
    "b8", "betb", "gl", "m80", "mibr", "tylo", "big", "fly",
]

STAGE3 = [
    # seed  1-8  (direct — sorted by VRS)
    "vita", "navi", "falc", "mong", "pv", "auro", "furi", "mouz",
    # seed  9-16 (from Stage 2 — TBD, fill in after Stage 2 completes)
    None, None, None, None, None, None, None, None,
]

# ═══════════════════════════════════════════════════════════════════
# 3. WIN PROBABILITY MODEL PARAMETERS
# ═══════════════════════════════════════════════════════════════════

MODEL = {
    # --- Elo / Ratio weights ---
    "sigma_vrs": 89.0,       # Elo sigma for VRS component
    "hltv_exp": 0.432,       # exponent for HLTV ratio component
    "w_hltv": 0.837,         # HLTV weight (dominant)
    "w_vrs": 0.163,          # VRS weight

    # --- Upset factors ---
    # Formula: adj = 0.5 + (p - 0.5) * (1 - upset)
    #   upset > 0  -> pulls toward 50% (more randomness)
    #   upset = 0  -> no change
    #   upset < 0  -> pushes away from 50% (amplifies favorite)
    #   upset = 2  -> exchange
    "upset_bo1": 0.20,       # BO1: high variance, single-map randomness
    "upset_bo3": -0.10,      # BO3: multi-map amplifies skill gap

    # --- H2H adjustment ---
    "h2h_weight": 0.12,      # max H2H adjustment (±6% for extreme records)
}

# ═══════════════════════════════════════════════════════════════════
# 4. SIMULATION DEFAULTS
# ═══════════════════════════════════════════════════════════════════

SIM = {
    "team_sims": 5000,       # Monte Carlo trials for team probabilities
    "pick_sims": 3000,       # trials per Pick'em candidate
    "candidates": 4000,      # max Pick'em combinations to test
}

# ═══════════════════════════════════════════════════════════════════
# 5. TOURNAMENT RESULTS & HISTORY
# ═══════════════════════════════════════════════════════════════════

# Actual Stage 1 advancer codes (for seeding Stage 2)
STAGE1_ADVANCERS = ["b8", "betb", "gl", "m80", "mibr", "tylo", "big", "fly"]

HEAD_TO_HEAD = {
    ("navi", "vita"): 0.60,  ("vita", "navi"): 0.55,
    ("vita", "spir"): 0.70,  ("vita", "falc"): 0.65,
    ("navi", "spir"): 0.60,  ("navi", "falc"): 0.55,
    ("spir", "falc"): 0.52,
    ("gl", "lega"):  0.48,   ("lega", "gl"):   0.52,
    ("hero", "lvg"): 0.55,   ("lvg", "hero"):  0.45,
    ("mouz", "g2"):  0.48,   ("g2", "mouz"):   0.52,
}

# ═══════════════════════════════════════════════════════════════════
# 6. PICK'EM FILTER (user-customizable)
# ═══════════════════════════════════════════════════════════════════
# Define rules to reject invalid Pick'em combinations before evaluation.
# Receives picks dict and TEAMS dict; return True to keep, False to skip.
#
# picks = {
#     "exact30": ["code1", "code2"],       # 2 team codes
#     "advancers": ["c1","c2",...,"c6"],   # 6 team codes
#     "exact03": ["code1", "code2"],       # 2 team codes
# }

def pickem_filter_default(picks, teams):
    """
    User-customizable Pick'em validation.
    Return True if the combination is acceptable, False to skip it.
    """
    return True  # default: accept all

# --- Example rules (uncomment and edit) ---
def pickem_filter_custom(picks, teams):
    # Don't put TYLOO or FlyQuest in 0-3
    if "tylo" in picks["exact03"]:
        return False

    # Don't put Brazilian teams in 3-0
    br_teams = {"furi", "mibr", "pain", "lega", "9z"}
    for code in picks["exact30"]:
        if code in br_teams:
            return False

    return True

pickem_filter = pickem_filter_custom