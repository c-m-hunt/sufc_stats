"""Shared pitch and figure construction, so every chart lays out the same way."""

from dataclasses import dataclass
from typing import Any

import numpy as np
from matplotlib.figure import Figure
from mplsoccer import VerticalPitch


def make_pitch(
    half: bool = False,
    grass: bool = False,
    linewidth: float = 1,
    line_color: str = "black",
    pad_top: float = 20,
    pad_bottom: float | None = None,
    **kwargs,
) -> VerticalPitch:
    """A Wyscout-coordinates vertical pitch. grass=True gives the striped green look."""
    style = (
        {"pitch_color": "#aabb97", "stripe_color": "#c2d59d", "stripe": True, "line_color": "white"}
        if grass
        else {"line_color": line_color}
    )
    if pad_bottom is None:
        pad_bottom = -10 if half else 0
    return VerticalPitch(
        pitch_type="wyscout",
        half=half,
        line_zorder=2,
        linewidth=linewidth,
        pad_top=pad_top,
        pad_bottom=pad_bottom,
        **style,
        **kwargs,
    )


def pitch_grid(
    pitch: VerticalPitch,
    ncols: int = 1,
    nrows: int = 1,
    fig_height: float = 10,
    title_height: float = 0.06,
    endnote_height: float = 0.03,
    grid_height: float = 0.8,
    title_space: float = 0,
    endnote_space: float = 0,
) -> tuple[Figure, dict[str, Any]]:
    fig, axs = pitch.grid(
        nrows=nrows,
        ncols=ncols,
        figheight=fig_height,
        grid_width=0.88,
        left=0.025,
        endnote_height=endnote_height,
        endnote_space=endnote_space,
        axis=False,
        title_space=title_space,
        title_height=title_height,
        grid_height=grid_height,
    )
    return fig, axs


def pitch_axes(axs: dict[str, Any]) -> list[Any]:
    """The pitch axes in reading order, whether the grid was 1x1, 1xN or NxM."""
    return list(np.atleast_1d(axs["pitch"]).ravel())


@dataclass
class Layout:
    """Font sizes and header placement that scale with the figure height."""

    title: float
    subtitle: float
    panel_title: float
    stats: float
    footer: float
    badge_scale: float
    badge_pos: tuple[float, float]
    title_pos: tuple[float, float]
    subtitle_pos: float


def layout(fig_height: float, ncols: int = 1, half: bool = False) -> Layout:
    """Sizes that look right for a given figure height and number of pitches."""
    wide = ncols > 1
    scale = fig_height * (1.3 if half else 1)
    return Layout(
        title=scale * (3.5 if wide else 2.2),
        subtitle=scale * (2 if wide else 1.2),
        panel_title=scale * (1.8 if wide else 1.5),
        stats=scale * (1.6 if wide else 1.3),
        footer=scale * 1.2,
        badge_scale=(1.6 if wide else 1.3) * (1.3 if half else 1),
        badge_pos=(0.1, 0.03) if wide else (0.13, 0.03),
        title_pos=(0, 0.5),
        subtitle_pos=-0.25,
    )
