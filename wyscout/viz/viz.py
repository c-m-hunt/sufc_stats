from collections import defaultdict
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
from urllib.request import urlopen
from mplsoccer import add_image

from wyscout.match import get_match_events_for_season, get_match_details_and_events
from wyscout.viz.arrow import is_first_half, pass_event_to_arrow, ArrowOptions
from wyscout.viz.consts import COLOUR_1, COLOUR_2, COLOUR_3
from wyscout.viz.heat_map import plot_player_action_map, plot_pass_map
from wyscout.viz.key_passes import plot_key_passes
from wyscout.team import get_team_squad, get_team_details
from wyscout.viz.shots import plot_shots_compare, plot_match_chances
from wyscout.viz.consts import SPONSOR_LOGO, SPONSOR_TEXT, COLOUR_1, COLOUR_2, APP_FONT
from PIL import Image
from wyscout.viz.utils import format_match_details
from wyscout.viz.data import get_shots, get_key_passes


def pass_heat_map_for_match(
    team_id: int,
    match_id: int
):
    match, match_details, squad, team_details = get_match_details_and_events(
        team_id, match_id)

    passes = [e for e in match["events"] if e["type"]
              ["primary"] == "pass"]
    pass_recipients = defaultdict(lambda: defaultdict(int))
    players = []
    INCOMPLETE = "Incomplete"
    OPPOSITION = "Opposition"
    for p in passes:
        recipient = p["pass"]["recipient"]["name"]
        recipient = INCOMPLETE if recipient is None else recipient
        if recipient != INCOMPLETE and p["pass"]["recipient"]["id"] not in squad:
            recipient = OPPOSITION
        pass_recipients[p["player"]["name"]
                        ][recipient] += 1
        players.append(p["player"]["name"])
        players.append(recipient)

    sorted_players = sorted(list(set(players)))
    from_players = sorted_players.copy()
    from_players.remove(INCOMPLETE)
    from_players.remove(OPPOSITION)
    to_players = from_players.copy()
    to_players.append(INCOMPLETE)
    to_players.append(OPPOSITION)

    count = []
    for p in from_players:
        row = []
        for r in to_players:
            row.append(pass_recipients[p][r] or 0)
        count.append(row)
    count = np.array(count)
    fig, ax = plt.subplots()
    im = ax.imshow(count, cmap=plt.cm.Blues)

    ax.set_yticks(np.arange(len(from_players)), labels=from_players)
    ax.set_xticks(np.arange(len(to_players)), labels=to_players)
    ax.grid(False)

    plt.setp(ax.get_xticklabels(), rotation=45, ha="right",
             rotation_mode="anchor")

    for i in range(len(from_players)):
        for j in range(len(to_players)):
            text = ax.text(j, i, count[i, j],
                           ha="center", va="center", color="black")

    fig.tight_layout()
    plt.show()
    return pass_recipients, sorted_players


def player_heat_map_for_match(
    player_id: int,
    team_id: int,
    match_id: int,
    show_passes=False,
    show_crosses=False,
    show_passes_received=False,
    highlight_by_half=False,
    period=None,
    subtitle="",
):
    match, match_details, squad, team_details = get_match_details_and_events(
        team_id, match_id)

    touches = []
    passes = []
    passes_received = []
    crosses = []

    for t in match["events"]:
        if period and t["matchPeriod"] != period:
            continue

        def highlight(x): return False
        if highlight_by_half:
            highlight = is_first_half

        if t["player"]["id"] == player_id:

            touches.append([t["location"]["x"], t["location"]["y"]])

            if show_crosses and "cross" in t["type"]["secondary"]:
                crosses.append(pass_event_to_arrow(t, [], ArrowOptions(
                    width=2,
                    highlight=highlight
                )))

        if show_passes_received and t["type"]["primary"] == "pass" and t["pass"]["recipient"]["id"] == player_id:
            passes_received.append(pass_event_to_arrow(t, [], ArrowOptions(
                width=2,
                highlight=highlight
            )))

        if show_passes and t["type"]["primary"] == "pass":
            passes.append(pass_event_to_arrow(t, [], ArrowOptions(
                width=2,
                highlight=highlight
            )))

    plot_player_action_map(
        squad[player_id],
        format_match_details(match_details, team_id),
        subtitle,
        touches,
        passes or passes_received,
        crosses
    )


def player_pass_map_for_season(
    player_id_from: int,
    player_id_to: int,
    team_id: int,
    season_id: int,
    subtitle="",
):
    matches = get_match_events_for_season(team_id, season_id)

    evnt = [e for m in matches for e in m["events"]
            if e["id"] == 1463391358][0]

    all_events = [e for m in matches for e in m["events"]]
    evnts = [e for e in all_events if e["type"]["primary"] == "pass" and e["player"]
             ["id"] == player_id_from and e["pass"]["recipient"]["id"] == player_id_to]

    evnts.append(evnt)

    squad = get_team_squad(team_id, season_id)
    squad = {p["wyId"]: p for p in squad["squad"]}
    team = get_team_details(team_id)

    passes = []
    for evnt in evnts:
        def isHighPass(x): return x["pass"]["height"] == "high"
        width = 3 if evnt["possession"]["attack"] and evnt["possession"]["attack"]["withShot"] else 2

        passes.append(pass_event_to_arrow(evnt, [], ArrowOptions(
            width=width,
            color=COLOUR_2 if isHighPass(evnt) else COLOUR_1,
            edgecolor=COLOUR_3
        )))

    plot_pass_map(
        squad[player_id_from],
        squad[player_id_to],
        team,
        passes,
        subtitle=subtitle
    )


def key_pass_map(season_id: int, player_id: int, team_id: int):
    kp = get_key_passes(team_id, season_id)
    plot_key_passes(kp, 10, [player_id])


def shot_compare_map(team_id: int, season_id: int, compare_last_n: int = 1):
    match_events = get_shots(team_id, season_id)
    plot_shots_compare(match_events, compare_last_n)


def shot_map(team_id: int, season_id: int):
    match_events = get_shots(team_id, season_id)
    plot_match_chances(match_events[0], True, [COLOUR_1, COLOUR_3])
