from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Union

import matplotlib.pyplot as plt
from mplsoccer import FontManager, Pitch, VerticalPitch

from wyscout.viz.arrow import Arrow, pass_event_to_arrow


def plot_key_passes(
    matches: List[Dict[str, Any]],
    last_x_games: int = 5,
    highlight_players: List[int] = [],
) -> None:
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
        endnote_height=0,  # no endnote
        title_height=0.1,
        title_space=0.02,
        # Turn off the endnote/title axis. I usually do this after
        # I am happy with the chart layout and text placement
        axis=False,
        grid_height=0.83,
    )

    plt.style.use("ggplot")

    robotto_regular = FontManager()

    axs["title"].text(
        0.5,
        0.5,
        f"Key Passess - Last {last_x_games} games",
        va="center",
        ha="center",
        color="black",
        fontproperties=robotto_regular.prop,
        fontsize=25,
    )

    arrows = []
    for j, match in enumerate(matches[:last_x_games]):
        for i, event in enumerate(match["events"]):
            arrows.append(pass_event_to_arrow(event, highlight_players))

    plot_arrows(arrows, pitch, axs["pitch"])
    plt.show()


def plot_arrows(
    arrows: List[Arrow], pitch: Union[Pitch, VerticalPitch], ax: plt.Axes
) -> List[plt.Arrow]:
    for_legend = []
    for arrow in arrows:
        if arrow.end == (0, 0):
            arrow.end = arrow.start
        for_legend.append(pitch.arrows(
            arrow.start[0],
            arrow.start[1],
            arrow.end[0],
            arrow.end[1],
            color=arrow.color,
            width=arrow.width,
            headwidth=20, headlength=20,
            ax=ax,
            alpha=1,
            zorder=arrow.zorder,
        ))
    return for_legend