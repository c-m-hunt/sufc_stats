"""Wyscout ids used across the notebooks.

Teams and competitions are stable. Seasons are added each summer - find the
new one with wyscout.competitions.get_competition_seasons(NATIONAL_LEAGUE).
Players move, so look them up by name with wyscout.data.player.find_player
rather than adding to the list here unless they are used in several places.
"""

# ── competitions ────────────────────────────────────────────────────────────
NATIONAL_LEAGUE = 351
NATIONAL_LEAGUE_NORTH = 352
PREMIER_LEAGUE = 364
ENGLAND = "XEN"  # area code for competitions lookups

# ── National League seasons, named by the year they start ───────────────────
SEASON_2021 = 187596  # 2021/22
SEASON_2022 = 188172  # 2022/23
SEASON_2023 = 189051  # 2023/24
SEASON_2024 = 190045  # 2024/25
SEASON_2025 = 191757  # 2025/26
SEASON_2026 = 192798  # 2026/27

SEASONS = {
    "2021/22": SEASON_2021,
    "2022/23": SEASON_2022,
    "2023/24": SEASON_2023,
    "2024/25": SEASON_2024,
    "2025/26": SEASON_2025,
    "2026/27": SEASON_2026,
}

# National League North seasons
SEASON_2022_NORTH = 188337
SEASON_2023_NORTH = 189070

# ── teams ────────────────────────────────────────────────────────────────────
SOUTHEND = 1687
ALTRINCHAM = 1745
BARNET = 1701
BOREHAM_WOOD = 1917
EASTLEIGH = 1772
KINGS_LYNN = 2412
NOTTS_COUNTY = 1677
OXFORD_CITY = 1847
RUSHALL = 1905
WEALDSTONE = 1833
WESTON_SUPER_MARE = 1764
WREXHAM = 10530
YORK = 1699

# ── players ──────────────────────────────────────────────────────────────────
# Southend
H_CARDWELL = 330285
L_CHAMBERS_PARILLON = 702447
J_BRIDGE = 289901
S_HOBSON = 489434
C_POWELL = 444130
M_DAKERS = 601997
K_LOPATA = 592169
G_SCOTT_MORRISS = 486095
C_MILEY = 516768
D_MOONEY = 547377
J_MORTON_SUFC = 546341
D_WALDRON = 526333

# players at other clubs, used for scouting comparisons
C_HAIGH = 393954  # Oxford City goalkeeper, 2023/24
A_CROWTHER = 846357  # King's Lynn, 2022/23 (National League North)
P_MCCALLUM = 10126  # Eastleigh, 2023/24
J_MORTON_WSM = 546341  # Weston-super-Mare, 2023/24 (National League North)
