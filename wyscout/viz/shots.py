"""Attempts on goal drawn as circles sized by xG."""

from collections.abc import Sequence
from typing import Any

import matplotlib.pyplot as plt
from mplsoccer import VerticalPitch

from wyscout.viz.consts import APP_FONT, COLOUR_1, COLOUR_3, TEAM_COLOURS
from wyscout.viz.pitch import make_pitch, pitch_grid
from wyscout.viz.utils import add_footer

Event = dict[str, Any]
Colours = str | tuple[str, str]


def plot_shots(
    shots: Sequence[Event],
    colors: Colours,
    pitch: VerticalPitch,
    ax: plt.Axes,
    reverse: bool = False,
    base_size: float = 1000,
    line_width: float = 1.5,
    goal_edge: str = "red",
    edge: str = "black",
    colour_by: str = "on_target",
) -> None:
    """One circle per attempt, area proportional to xG, ringed in goal_edge for goals.

    colors is (on target, off target) - or with colour_by="goal", (goal, no goal).
    A single colour is used for everything. reverse=True flips the attempts to
    the other end, for plotting the opposition's shots on the same pitch.
    """
    if not isinstance(colors, tuple):
        colors = (colors, colors)

    for shot in shots:
        x, y = shot["location"]["x"], shot["location"]["y"]
        if reverse:
            x, y = 100 - x, 100 - y
        is_goal = shot["shot"]["isGoal"] is True
        hit = shot["shot"]["onTarget"] is True if colour_by == "on_target" else is_goal
        pitch.scatter(
            x,
            y,
            s=shot["shot"]["xg"] * base_size,
            label=shot["player"]["name"],
            color=colors[0] if hit else colors[1],
            edgecolors=[goal_edge if is_goal else edge],
            linewidth=line_width,
            marker="o",
            ax=ax,
        )


def plot_shot_map(
    shots: Sequence[Event],
    title: str,
    colors: tuple[str, str] | None = None,
    fig_height: float = 8,
    base_size: float = 1000,
    show: bool = True,
):
    """A single striped half pitch of attempts, coloured (on target, off target)."""
    return plot_shot_maps([shots], title, colors, fig_height, base_size, show)


def plot_shot_maps(
    shot_groups: Sequence[Sequence[Event]],
    title: str,
    colors: tuple[str, str] | None = None,
    fig_height: float = 8,
    base_size: float = 1000,
    show: bool = True,
    panel_titles: Sequence[str] | None = None,
):
    """Side-by-side striped half pitches, one per group of attempts."""
    colors = colors or (COLOUR_3, COLOUR_1)
    pitch = make_pitch(half=True, grass=True, goal_type="box", pad_bottom=-20, pad_top=8)
    fig, axs = pitch_grid(
        pitch,
        ncols=len(shot_groups),
        fig_height=fig_height,
        title_height=0.1,
        title_space=0.02,
        endnote_height=0.06,
        grid_height=0.78,
    )
    axs["title"].text(
        0.5,
        0.5,
        title,
        va="center",
        ha="center",
        color="black",
        fontproperties=APP_FONT.prop,
        fontsize=fig_height * 3,
    )

    pitches = [axs["pitch"]] if len(shot_groups) == 1 else list(axs["pitch"])
    for i, (shots, ax) in enumerate(zip(shot_groups, pitches)):
        plot_shots(shots, colors, pitch, ax, base_size=base_size)
        if panel_titles:
            ax.text(50, 103, panel_titles[i], ha="center", va="center", fontsize=fig_height * 1.6,
                    fontproperties=APP_FONT.prop)

    add_footer(fig, axs["endnote"], font_size=fig_height * 1.5, scale_img=1)

    if show:
        plt.show()
    return fig, axs, pitch


DEFAULT_TEAM_COLOURS = TEAM_COLOURS
