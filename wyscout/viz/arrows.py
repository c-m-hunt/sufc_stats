"""Passes and crosses as arrows."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any

import matplotlib.pyplot as plt
from mplsoccer import Pitch, VerticalPitch

from wyscout.viz.consts import APP_FONT, COLOUR_1

Event = dict[str, Any]


@dataclass
class Arrow:
    start: tuple[float, float]
    end: tuple[float, float]
    color: str
    edgecolor: str
    width: float
    zorder: float | None = 100


@dataclass
class ArrowOptions:
    """How to draw a pass, and which passes to pick out.

    highlight is a predicate on the event; a pass it accepts is drawn in
    highlighted_color and highlighted_width, on top of the rest.
    """

    color: str = COLOUR_1
    width: float = 2
    edgecolor: str | None = None
    highlighted_width: float = 4
    highlighted_color: str = "red"
    highlight: Callable[[Event], bool] = field(default=lambda event: False)
    zorder: float | None = 100


def pass_event_to_arrow(event: Event, options: ArrowOptions | None = None) -> Arrow:
    options = options or ArrowOptions()
    color, width, zorder = options.color, options.width, options.zorder
    if options.highlight(event):
        color, width, zorder = options.highlighted_color, options.highlighted_width, options.zorder + 1
    return Arrow(
        start=(event["location"]["x"], event["location"]["y"]),
        end=(event["pass"]["endLocation"]["x"], event["pass"]["endLocation"]["y"]),
        color=color,
        width=width,
        edgecolor=options.edgecolor or options.color,
        zorder=zorder,
    )


def passes_to_arrows(events: Sequence[Event], options: ArrowOptions | None = None) -> list[Arrow]:
    return [pass_event_to_arrow(e, options) for e in events if e.get("pass")]


def plot_arrows(
    arrows: Sequence[Arrow], pitch: Pitch | VerticalPitch, ax: plt.Axes
) -> list[Any]:
    drawn = []
    for arrow in arrows:
        end = arrow.start if arrow.end == (0, 0) else arrow.end
        drawn.append(
            pitch.arrows(
                arrow.start[0],
                arrow.start[1],
                end[0],
                end[1],
                color=arrow.color,
                width=arrow.width,
                headwidth=20,
                headlength=20,
                ax=ax,
                alpha=1,
                zorder=arrow.zorder,
            )
        )
    return drawn


def plot_key_passes(
    arrows: Sequence[Arrow], title: str, fig_height: float = 8, show: bool = True
):
    """Key passes on a striped half pitch."""
    from wyscout.viz.pitch import make_pitch, pitch_grid

    pitch = make_pitch(half=True, grass=True, goal_type="box", pad_bottom=-20, pad_top=8)
    fig, axs = pitch_grid(pitch, fig_height=fig_height, title_height=0.1, title_space=0.02,
                          endnote_height=0, grid_height=0.83)
    axs["title"].text(0.5, 0.5, title, va="center", ha="center", color="black",
                      fontproperties=APP_FONT.prop, fontsize=fig_height * 3)
    plot_arrows(arrows, pitch, axs["pitch"])
    if show:
        plt.show()
    return fig, axs, pitch
