"""The general-purpose pitch chart: one or more pitches, each layering whatever
you hand it - a touch heat map, attempts, the opposition's attempts, arrows,
marker sets and a block of statistics.

Every other pitch visualisation in the package is a special case of this.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

import matplotlib.pyplot as plt

from wyscout.viz.arrows import Arrow, plot_arrows
from wyscout.viz.consts import OPPO_COLOURS, TEAM_COLOURS
from wyscout.viz.heat_map import add_heat_map, add_points
from wyscout.viz.pitch import layout, make_pitch, pitch_axes, pitch_grid
from wyscout.viz.shots import plot_shots
from wyscout.viz.utils import add_footer, add_header, add_stat_lines, panel_title

Event = dict[str, Any]
Location = Sequence[float]


@dataclass
class Markers:
    """A set of plain markers, e.g. every interception."""

    locations: list[Location]
    color: str = "blue"
    marker: str = "o"
    size: float = 40
    edgecolor: str | None = None
    linewidth: float = 1
    label: str | None = None


@dataclass
class EventPanel:
    """What to draw on one pitch. Leave out anything you don't want."""

    title: str = ""
    touches: list[Location] = field(default_factory=list)  # heat map
    shots: list[Event] = field(default_factory=list)
    oppo_shots: list[Event] = field(default_factory=list)  # drawn at the other end
    arrows: list[Arrow] = field(default_factory=list)
    markers: list[Markers] = field(default_factory=list)
    stats: dict[str, Any] = field(default_factory=dict)  # "label": value lines
    show_touch_points: bool = False  # dots for the touches as well as the heat map


def plot_event_maps(
    panels: Sequence[EventPanel],
    header: str,
    subtitle: Sequence[str] | None = None,
    header_imgs: Sequence[Any] | None = None,
    fig_height: float = 10,
    half: bool = False,
    cmap: str = "Blues",
    heat_levels: int = 50,
    shot_colors: tuple[str, str] = TEAM_COLOURS,
    oppo_shot_colors: tuple[str, str] = OPPO_COLOURS,
    shot_size: float = 1000,
    stats_pos: tuple[float, float] = (5, 70),
    stats_step: float = 2.5,
    legend: bool = False,
    legend_loc: Any = "lower left",
    footer: bool = True,
    show: bool = True,
):
    """Draw the panels side by side under a shared header. Returns (fig, axs, pitch)."""
    ncols = len(panels)
    sizes = layout(fig_height, ncols, half)
    pitch = make_pitch(half=half, linewidth=2 if half else 1.5)
    fig, axs = pitch_grid(
        pitch,
        ncols=ncols,
        fig_height=fig_height,
        title_height=0.07,
        endnote_height=0.03 if footer else 0.005,
        grid_height=0.8,
    )

    for panel, ax in zip(panels, pitch_axes(axs)):
        panel_title(ax, panel.title, sizes.panel_title)
        if panel.touches:
            add_heat_map(panel.touches, pitch, ax, levels=heat_levels, cmap=cmap)
            if panel.show_touch_points:
                add_points(panel.touches, pitch, ax, color="darkblue", size=fig_height * 4)
        if panel.shots:
            plot_shots(panel.shots, shot_colors, pitch, ax, base_size=shot_size, line_width=2)
        if panel.oppo_shots:
            plot_shots(panel.oppo_shots, oppo_shot_colors, pitch, ax, reverse=True,
                       base_size=shot_size, line_width=2)
        if panel.arrows:
            plot_arrows(panel.arrows, pitch, ax)
        handles = []
        for m in panel.markers:
            handle = add_points(m.locations, pitch, ax, color=m.color, size=m.size, marker=m.marker,
                                edgecolor=m.edgecolor or m.color, linewidth=m.linewidth, label=m.label)
            if handle is not None and m.label:
                handles.append(handle)
        if panel.stats:
            add_stat_lines(ax, panel.stats, x=stats_pos[0], y=stats_pos[1], step=stats_step,
                           fontsize=sizes.stats)
        if legend and handles:
            ax.legend(handles=handles, loc=legend_loc, fontsize=sizes.stats)

    add_header(
        fig,
        axs["title"],
        header,
        subtitle=subtitle,
        subtitle_font_size=sizes.subtitle,
        subtitle_start_pos=sizes.subtitle_pos,
        scale_img=sizes.badge_scale,
        font_size=sizes.title,
        title_va="center",
        title_pos=sizes.title_pos,
        imgs=header_imgs,
        img_rel_x_pos=sizes.badge_pos[0],
        img_rel_y_pos=sizes.badge_pos[1],
        subtitle_gap=0.5,
    )

    if footer:
        add_footer(fig, axs["endnote"], scale_img=1.3, font_size=sizes.footer)

    if show:
        plt.show()
    return fig, axs, pitch


def plot_event_map(panel: EventPanel, header: str, **kwargs):
    """One pitch. Same options as plot_event_maps."""
    return plot_event_maps([panel], header, **kwargs)
