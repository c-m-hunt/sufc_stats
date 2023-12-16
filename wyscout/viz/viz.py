from collections import defaultdict
from datetime import datetime
from typing import List
from urllib.request import urlopen

import matplotlib.pyplot as plt
import numpy as np
from mplsoccer import VerticalPitch, add_image
from PIL import Image

from wyscout.match import (
    get_match_details_and_events,
    get_match_events,
    get_match_events_for_season,
)
from wyscout.team import get_team_details, get_team_squad
from wyscout.viz.arrow import ArrowOptions, is_first_half, pass_event_to_arrow
from wyscout.viz.consts import (
    APP_FONT,
    COLOUR_1,
    COLOUR_2,
    COLOUR_3,
    SPONSOR_LOGO,
    SPONSOR_TEXT,
)
from wyscout.viz.data import get_key_passes, get_shots
from wyscout.viz.heat_map import add_heat_map, plot_pass_map, plot_player_action_map
from wyscout.viz.key_passes import plot_arrows, plot_key_passes
from wyscout.viz.shots import (
    plot_chances,
    plot_match_chances,
    plot_shots,
    plot_shots_compare,
)
from wyscout.viz.utils import add_footer, add_header, format_match_details


def pass_heat_map_for_matches(team_id: int, match_ids: List[int]):
    players = []
    pass_recipients = defaultdict(lambda: defaultdict(int))
    for match_id in match_ids:
        match, match_details, squad, team_details = get_match_details_and_events(
            team_id, match_id
        )

        passes = [e for e in match["events"] if e["type"]["primary"] == "pass"]

        INCOMPLETE = "Incomplete"
        OPPOSITION = "Opposition"
        for p in passes:
            recipient = p["pass"]["recipient"]["name"]
            recipient = INCOMPLETE if recipient is None else recipient
            if recipient != INCOMPLETE and p["pass"]["recipient"]["id"] not in squad:
                recipient = OPPOSITION
            pass_recipients[p["player"]["name"]][recipient] += 1
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
    fig, ax = plt.subplots(figsize=(300, 10))

    im = ax.imshow(count, cmap=plt.cm.Blues)

    ax.set_yticks(np.arange(len(from_players)), labels=from_players)
    ax.set_xticks(np.arange(len(to_players)), labels=to_players)
    ax.grid(False)

    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

    for i in range(len(from_players)):
        for j in range(len(to_players)):
            text = ax.text(j, i, count[i, j], ha="center", va="center", color="black")

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
        team_id, match_id
    )

    touches = []
    passes = []
    passes_received = []
    crosses = []

    for t in match["events"]:
        if period and t["matchPeriod"] != period:
            continue

        def highlight(x):
            return False

        if highlight_by_half:
            highlight = is_first_half

        if t["player"]["id"] == player_id:
            touches.append([t["location"]["x"], t["location"]["y"]])

            if show_crosses and "cross" in t["type"]["secondary"]:
                crosses.append(
                    pass_event_to_arrow(
                        t, [], ArrowOptions(width=2, highlight=highlight)
                    )
                )

        if (
            show_passes_received
            and t["type"]["primary"] == "pass"
            and t["pass"]["recipient"]["id"] == player_id
        ):
            passes_received.append(
                pass_event_to_arrow(t, [], ArrowOptions(width=2, highlight=highlight))
            )

        if show_passes and t["type"]["primary"] == "pass":
            passes.append(
                pass_event_to_arrow(t, [], ArrowOptions(width=2, highlight=highlight))
            )

    plot_player_action_map(
        squad[player_id],
        format_match_details(match_details, team_id),
        subtitle,
        touches,
        passes or passes_received,
        crosses,
    )


def player_pass_map_for_season(
    player_id_from: int,
    player_id_to: int,
    team_id: int,
    season_id: int,
    subtitle="",
):
    matches = get_match_events_for_season(team_id, season_id)

    evnt = [e for m in matches for e in m["events"] if e["id"] == 1463391358][0]

    all_events = [e for m in matches for e in m["events"]]
    evnts = [
        e
        for e in all_events
        if e["type"]["primary"] == "pass"
        and e["player"]["id"] == player_id_from
        and e["pass"]["recipient"]["id"] == player_id_to
    ]

    evnts.append(evnt)

    squad = get_team_squad(team_id, season_id)
    squad = {p["wyId"]: p for p in squad["squad"]}
    team = get_team_details(team_id)

    passes = []
    for evnt in evnts:

        def isHighPass(x):
            return x["pass"]["height"] == "high"

        width = (
            3
            if evnt["possession"]["attack"] and evnt["possession"]["attack"]["withShot"]
            else 2
        )

        passes.append(
            pass_event_to_arrow(
                evnt,
                [],
                ArrowOptions(
                    width=width,
                    color=COLOUR_2 if isHighPass(evnt) else COLOUR_1,
                    edgecolor=COLOUR_3,
                ),
            )
        )

    plot_pass_map(
        squad[player_id_from], squad[player_id_to], team, passes, subtitle=subtitle
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


def shot_map_for_matches(
    matches: any,
    team_id: int,
    title: str,
    include_pens: bool = False,
    forAgainst: str = "for",
):
    shots = []
    event_types = ["shot"]
    if include_pens:
        event_types.append("penalty")
    for m in matches:
        events = get_match_events(m["matchId"])
        for e in events["events"]:
            if (
                e["type"]["primary"] in event_types
                and e["team" if forAgainst == "for" else "opponentTeam"]["id"]
                == team_id
            ):
                shots.append(e)

    plot_chances(shots, title, True, colors=[COLOUR_1, COLOUR_2])


def plot_dual_pitch(
    header_text: str,
    pitch_headers: List[str],
    touches: List[any],
    shots: List[any],
    passes: List[any],
    oppo_shots: List[any],
    logo_url: str,
    fig_height=30,
    cmap="Blues",
    shot_colors=("blue", "cornflowerblue"),
    oppo_shot_colors=("whitesmoke", "darkgrey"),
    subtitle=[],
):
    cols = len(shots)
    split = cols > 1
    if len(pitch_headers) != 0 and len(pitch_headers) != cols:
        raise ValueError(
            f"pitch_headers must be empty or have the same number of elements"
        )

    pitch = VerticalPitch(
        pitch_type="wyscout", line_zorder=2, linewidth=1, line_color="black", pad_top=20
    )

    GRID_HEIGHT = 0.8
    CBAR_WIDTH = 0.03

    match_font_size = 55
    title_font_size = fig_height * 3 if split else fig_height * 2
    subtitle_font_size = fig_height * 2 if split else fig_height * 1.6
    footer_font_size = fig_height * 1.3
    scale_badge_img = 5 if split else 7
    badge_pos = (0.11, 0.03) if split else (0.17, 0.07)
    title_height = 0.025 if split else 0.015
    title_space = 0.0 if split else 0
    subtitle_start_pos = -0.5 if split else -4
    title_start_height = 1.3 if split else 0

    fig, axs = pitch.grid(
        nrows=1,
        ncols=cols,
        figheight=fig_height,
        # leaves some space on the right hand side for the colorbar
        grid_width=0.88,
        left=0.025,
        endnote_height=0.05,
        endnote_space=0,
        # Turn off the endnote/title axis. I usually do this after
        # I am happy with the chart layout and text placement
        axis=False,
        title_space=title_space,
        title_height=title_height,
        grid_height=GRID_HEIGHT,
    )

    for col in range(cols):
        ax = axs["pitch"][col] if cols > 1 else axs["pitch"]
        ax.text(
            50,
            103,
            pitch_headers[col],
            ha="center",
            va="center",
            fontsize=match_font_size,
        )
        add_heat_map(touches[col], pitch, ax, levels=50, cmap=cmap)
        plot_shots(shots[col], shot_colors, pitch, ax, False, 5000)
        plot_shots(oppo_shots[col], oppo_shot_colors, pitch, ax, True, 5000)
        plot_arrows(passes[col], pitch, ax)

    logo_img = Image.open(urlopen(logo_url))
    add_header(
        fig,
        axs["title"],
        header_text,
        subtitle=subtitle,
        subtitle_font_size=subtitle_font_size,
        subtitle_start_pos=subtitle_start_pos,
        scale_img=scale_badge_img,
        font_size=title_font_size,
        title_va="center",
        title_pos=(0, title_start_height),
        imgs=[logo_img],
        img_rel_x_pos=badge_pos[0],
        img_rel_y_pos=badge_pos[1],
    )

    add_footer(fig, axs["endnote"], scale_img=1.3, font_size=footer_font_size)

    plt.show()
