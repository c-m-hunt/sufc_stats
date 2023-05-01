from wyscout.viz.consts import SPONSOR_LOGO, SPONSOR_TEXT, COLOUR_1, COLOUR_2, APP_FONT
from mplsoccer import add_image
from collections import defaultdict
from typing import List, Dict
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from imageio import imread
from matplotlib.offsetbox import (OffsetImage, AnnotationBbox)
from wyscout.match import get_match_events_for_season, get_match_details_and_events
from wyscout.team import get_team_details


def plot_xg_charts(team_id: int, match_id: int, colours: List[str] = ["blue", "green"]):
    match, match_details, squad, team_details = get_match_details_and_events(
        team_id, match_id, all_events=True)

    xg_events = [e for e in match["events"] if "shot" in e]
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(20, 10))

    plot_xg_line_chart(team_id, xg_events, colours=colours,
                       match_details=match_details, team_details=team_details, ax=ax1)


def plot_xg_line_chart(team_id: int, evnts: List[Dict[str, any]], colours: List[str], match_details, team_details, ax):
    xg_by_time = defaultdict(lambda: defaultdict(int))
    xg_by_team = defaultdict(int)
    for e in evnts:
        if "shot" not in e or e["shot"] is None:
            continue
        team = e["team"]["id"]
        time = e["minute"] + (e["second"] / 60)
        period = e["matchPeriod"]
        if period == "1H" and time > 45:
            time = 45
        elif period == "2H" and time > 90:
            time = 90
        xg_by_team[team] += e["shot"]["xg"]
        if team not in xg_by_time:
            xg_by_time[team][0] = 0
        xg_by_time[team][time] = xg_by_team[team]

    colour_idx = 0
    for team in match_details["teamsData"]:
        team = int(team)
        colour = colours[colour_idx]
        prev_xg = 0
        prev_time = 0
        for t in xg_by_time[team]:
            curr_xg = xg_by_time[team][t]
            if curr_xg == prev_xg:
                continue
            ax.plot([prev_time, t], [prev_xg, prev_xg], color=colour)
            ax.plot([t, t], [prev_xg, curr_xg], color=colour)
            prev_xg = curr_xg
            prev_time = t
        colour_idx += 1
        ax.plot([prev_time, 90], [prev_xg, prev_xg], color=colour)
        ax.yaxis.grid(True)

    custom_lines = [Line2D([0], [0], color=colours[0], lw=2),
                    Line2D([0], [0], color=colours[1], lw=2)]

    ax.legend(custom_lines, [
        team_details[int(t)]["name"] for t in match_details["teamsData"]
    ])


def plot_attacking_stats(team_id: int, season_id: int, colors: List[str] = ["royalblue", "yellow"], edgecolors: list[str] = ["royalblue", "royalblue"]):
    sorted_players, team_details = _get_attacking_stats_data(
        team_id, season_id)
    fig, axs = plt.subplots(4, 1, figsize=(10, 10))

    (ax1, ax2, ax3, ax4) = axs

    # Chart 1
    ax1.bar([p[0] for p in sorted_players], [p[1]["xgDiff"]
            for p in sorted_players], color=colors[0], label="Post-shot xG minus xG", zorder=3)
    ax1.xaxis.set_tick_params(labeltop=True)
    ax1.xaxis.set_tick_params(labelbottom=False)

    for tick in ax1.get_xticklabels():
        tick.set_rotation(90)
    ax1.legend(loc="lower left")

    # Chart 2
    x = np.arange(len(list(sorted_players)))
    width = 0.35
    ax2.bar(x - width/2, [p[1]["xg"] for p in sorted_players],
            width=width, label="xG", color=colors[0], edgecolor=edgecolors[0], zorder=3)
    ax2.bar(x + width/2, [p[1]["goals"] for p in sorted_players],
            width=width, label="Goals", color=colors[1], edgecolor=edgecolors[1], zorder=3)
    ax2.xaxis.set_tick_params(labelbottom=False)
    ax2.set_xticks(x, [p[0] for p in sorted_players])
    ax2.legend()

    # Chart 3
    ax3.bar(x - width/2, [p[1]["attempts"] for p in sorted_players],
            width=width, label="Attempts", color=colors[0], edgecolor=edgecolors[0], zorder=3)
    ax3.bar(x + width/2, [p[1]["onTarget"] for p in sorted_players],
            width=width, label="On target", color=colors[1], edgecolor=edgecolors[1], zorder=3)
    ax3.set_xticks(x, [p[0] for p in sorted_players])
    ax3.legend()

    ax4.bar([p[0] for p in sorted_players], [p[1]["avexg"]
            for p in sorted_players], color=colors[0], label="Average xG per attempt", zorder=3)
    for tick in ax4.get_xticklabels():
        tick.set_rotation(90)
    ax4.legend()

    plt.subplots_adjust(wspace=0, hspace=0.05)

    for ax in axs:
        ax.set_anchor('W')
        ax.grid(True, zorder=0)

    # Add club badge
    img = Image.fromarray(imread(team_details["imageDataURL"]))
    imagebox = OffsetImage(img, zoom=0.8)
    x_min_max = ax2.get_xlim()
    y_min_max = ax2.get_ylim()
    x = x_min_max[1] / 2
    y = y_min_max[1] / 2
    ab = AnnotationBbox(imagebox, (x, y), frameon=False, zorder=2)
    ax2.add_artist(ab)

    plt.show()


def _get_attacking_stats_data(team_id: int, season_id: int):
    matches = get_match_events_for_season(team_id, season_id, all_events=False)
    team_details = get_team_details(team_id)
    players = defaultdict(lambda: {
        "xg": 0,
        "postShotXg": 0,
        "attempts": 0,
        "onTarget": 0,
        "goals": 0
    })

    for m in matches:
        for e in m["events"]:
            if e["type"]["primary"] == "shot":
                players[e["player"]["name"]]["xg"] += e["shot"]["xg"]
                players[e["player"]["name"]
                        ]["postShotXg"] += e["shot"]["postShotXg"] if e["shot"]["postShotXg"] is not None else 0
                players[e["player"]["name"]]["attempts"] += 1
                players[e["player"]["name"]
                        ]["onTarget"] += 1 if e["shot"]["postShotXg"] is not None else 0
                players[e["player"]["name"]
                        ]["goals"] += 1 if e["shot"]["isGoal"] == True else 0

    for p in players:
        players[p]["xgDiff"] = players[p]["postShotXg"] - players[p]["xg"]
        players[p]["onTargetPct"] = players[p]["onTarget"] / \
            players[p]["attempts"]
        players[p]["avexg"] = players[p]["xg"] / players[p]["attempts"]

    sorted_players = sorted(
        players.items(), key=lambda x: x[1]["xgDiff"], reverse=True)

    return sorted_players, team_details
