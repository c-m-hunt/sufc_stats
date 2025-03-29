import math
from typing import List

import matplotlib.pyplot as plt
from mplsoccer import VerticalPitch

from wyscout.viz.consts import APP_FONT, COLOUR_1, COLOUR_3
from wyscout.viz.utils import add_footer


def plot_shots_compare(
    match_events: any,
    last_x_games: int = None,
    first_x_games: int = None,
    include_pens: bool = False,
    colors: list = ["red", "blue"],
    style: str = "fivethirtyeight",
):
    if last_x_games and not first_x_games:
        first_x_games = len(match_events) - last_x_games

    if first_x_games and not last_x_games:
        last_x_games = len(match_events) - first_x_games

    if not first_x_games and not last_x_games:
        first_x_games = math.floor(len(match_events) / 2)
        last_x_games = len(match_events) - first_x_games

    title = (
        f"Attempts on goal - first {first_x_games} games vs last {last_x_games} games"
    )
    event_types = ["shot"]
    if include_pens:
        event_types.append("penalty")

    def get_events(match_events):
        all_events = []
        for j, match in enumerate(match_events[:8]):
            all_events.extend(
                [e for e in match["events"] if e["type"]["primary"] in event_types]
            )
        return all_events

    events = [
        get_events(match_events[-1 * first_x_games :]),
        get_events(match_events[:last_x_games]),
    ]

    plot_dual_shot_map(events, title, colors, style)


def plot_dual_shot_map(
    shots: List[any],
    title: str,
    colors: list = ["red", "blue"],
    style: str = "fivethirtyeight",
):
    pitch = VerticalPitch(
        pitch_type="wyscout",
        half=True,
        goal_type="box",
        pad_bottom=-20,
        pitch_color="grass",
        line_color="white",
        stripe=True,
    )
    fig, axs = pitch.grid(
        figheight=15,
        ncols=2,
        title_height=0.1,
        title_space=0.02,
        axis=False,
    )

    plt.style.use(style)

    font = APP_FONT

    if len(shots) != 2:
        raise ValueError("Must have two sets of shots to plot")

    axs["title"].text(
        0.5,
        0.5,
        title,
        va="center",
        ha="center",
        color="black",
        fontproperties=font.prop,
        fontsize=50,
    )

    for i, shot_coll in enumerate(shots):
        for event in shot_coll:
            size = event["shot"]["xg"] * 2000
            color = colors[0] if event["shot"]["isGoal"] is True else colors[1]
            pitch.scatter(
                event["location"]["x"],
                event["location"]["y"],
                s=size,
                label=event["player"]["name"],
                color=color,
                edgecolors=["black"],
                marker="o",
                ax=axs["pitch"][i],
            )

    add_footer(fig, axs["endnote"], font_size=24, scale_img=1)

    plt.show()


def plot_shots(shots, color, pitch, ax, reverse=False, base_size=1000, line_width=1.5):
    if type(color) is not tuple:
        color = (color, color)

    for shot in shots:
        if reverse:
            shot["location"]["x"] = 100 - shot["location"]["x"]
            shot["location"]["y"] = 100 - shot["location"]["y"]

        size = shot["shot"]["xg"] * base_size
        edge_color = "red" if shot["shot"]["isGoal"] is True else "black"
        pitch.scatter(
            shot["location"]["x"],
            shot["location"]["y"],
            s=size,
            label=shot["player"]["name"],
            color=color[0] if shot["shot"]["onTarget"] is True else color[1],
            edgecolors=[edge_color],
            linewidth=line_width,
            marker="o",
            ax=ax,
        )


def plot_chances(
    chances: any,
    title: str,
    include_pens: bool = False,
    colors: List[str] = None,
    style: str = "fivethirtyeight",
):
    if not colors:
        colors = [COLOUR_3, COLOUR_1]

    pitch = VerticalPitch(
        pitch_type="wyscout",
        half=True,
        goal_type="box",
        pad_bottom=-20,
        pitch_color="grass",
        line_color="white",
        stripe=True,
    )

    fig, axs = pitch.grid(
        figheight=8,
        endnote_height=0.08,
        title_height=0.1,
        title_space=0.02,
        axis=False,
        grid_height=0.78,
    )

    plt.style.use(style)

    robotto_regular = APP_FONT

    axs["title"].text(
        0.5,
        0.5,
        title,
        va="center",
        ha="center",
        color="black",
        fontproperties=robotto_regular.prop,
        fontsize=30,
    )

    event_types = ["shot"]
    if include_pens:
        event_types.append("penalty")

    shots = [e for e in chances if e["type"]["primary"] in event_types]

    plot_shots(shots, tuple(colors), pitch, axs["pitch"])

    add_footer(fig, axs["endnote"], font_size=14, scale_img=1)

    plt.show()
