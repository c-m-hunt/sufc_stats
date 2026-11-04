"""Density shading of where things happened."""

from collections.abc import Sequence

import matplotlib.pyplot as plt
from mplsoccer import VerticalPitch


def add_heat_map(
    locations: Sequence[Sequence[float]],
    pitch: VerticalPitch,
    ax: plt.Axes,
    levels: int = 100,
    cmap: str = "Blues",
) -> None:
    """Smooth KDE shading of the given [x, y] points. Needs a handful of points to draw."""
    if len(locations) < 3:
        return
    xs: list[float] = [loc[0] for loc in locations]
    ys: list[float] = [loc[1] for loc in locations]
    pitch.kdeplot(xs, ys, ax=ax, fill=True, levels=levels, thresh=0, cmap=cmap)


def add_points(
    locations: Sequence[Sequence[float]],
    pitch: VerticalPitch,
    ax: plt.Axes,
    color: str = "darkblue",
    size: float = 40,
    marker: str = "o",
    edgecolor: str = "black",
    linewidth: float = 1,
    label: str | None = None,
    zorder: float = 3,
):
    """Plain markers at the given [x, y] points. Returns the scatter for legends."""
    if not locations:
        return None
    return pitch.scatter(
        [loc[0] for loc in locations],
        [loc[1] for loc in locations],
        s=size,
        color=color,
        edgecolors=edgecolor,
        linewidth=linewidth,
        marker=marker,
        label=label,
        zorder=zorder,
        ax=ax,
    )
