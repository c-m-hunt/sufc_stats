"""Team-level charts: a season of action maps, the pass matrix, attacking stats and the squad."""

import math
from collections.abc import Sequence
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.offsetbox import AnnotationBbox, OffsetImage

from wyscout.viz.consts import OPPO_COLOURS, TEAM_COLOURS
from wyscout.viz.event_map import EventPanel
from wyscout.viz.heat_map import add_heat_map
from wyscout.viz.pitch import make_pitch, pitch_axes, pitch_grid
from wyscout.viz.shots import plot_shots
from wyscout.viz.utils import add_footer, add_header, load_image


def plot_season_action_maps(
    panels: Sequence[EventPanel],
    header: str,
    subtitle: Sequence[str] | None = None,
    badge: Any = None,
    cols: int = 5,
    fig_height: float = 30,
    cmap: str = "Blues",
    shot_colors: tuple[str, str] = TEAM_COLOURS,
    oppo_shot_colors: tuple[str, str] = OPPO_COLOURS,
    show: bool = True,
):
    """A grid of full pitches, one per panel: touch heat map, attempts and the opposition's."""
    rows = math.ceil(len(panels) / cols)
    pitch = make_pitch(pad_top=35)
    title_height = min(0.1, 0.3 / rows)
    fig, axs = pitch_grid(pitch, ncols=cols, nrows=rows, fig_height=fig_height, title_height=title_height,
                          title_space=0.02, endnote_height=0.03, grid_height=0.75)
    panel_font = fig_height * 0.75 / rows * 2.2  # scales with the height of one pitch

    axes = pitch_axes(axs)
    for panel, ax in zip(panels, axes):
        ax.text(50, 110, panel.title, ha="center", va="center", fontsize=panel_font)
        add_heat_map(panel.touches, pitch, ax, levels=50, cmap=cmap)
        plot_shots(panel.shots, shot_colors, pitch, ax)
        plot_shots(panel.oppo_shots, oppo_shot_colors, pitch, ax, reverse=True)
    for ax in axes[len(panels):]:
        ax.set_visible(False)

    add_header(fig, axs["title"], header, subtitle=subtitle, subtitle_font_size=fig_height,
               subtitle_start_pos=0.1, scale_img=0.9, font_size=fig_height * 1.3,
               title_va="center", title_pos=(0, 0.7), imgs=[badge] if badge else None,
               img_rel_x_pos=0.1, img_rel_y_pos=0.01)
    add_footer(fig, axs["endnote"], scale_img=fig_height / 50, font_size=fig_height * 0.6)

    if show:
        plt.show()
    return fig, axs, pitch


def plot_pass_matrix(
    players: Sequence[str],
    counts: np.ndarray,
    title: str | None = None,
    cell_size: float = 0.55,
    cmap: str = "Blues",
    show: bool = True,
):
    """Who passes to whom: passers down the side, recipients along the top."""
    n = len(players)
    fig, ax = plt.subplots(figsize=(max(6, n * cell_size), max(5, n * cell_size)))
    ax.imshow(counts, cmap=cmap)
    ax.set_yticks(np.arange(n), labels=players)
    ax.set_xticks(np.arange(n), labels=players)
    ax.grid(False)
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
    ax.set_ylabel("From")
    ax.set_xlabel("To")
    threshold = counts.max() * 0.6 if counts.size else 0
    for i in range(n):
        for j in range(n):
            if counts[i, j]:
                ax.text(j, i, counts[i, j], ha="center", va="center",
                        color="white" if counts[i, j] > threshold else "black", fontsize=8)
    if title:
        ax.set_title(title, loc="left", fontweight="bold")
    fig.tight_layout()
    if show:
        plt.show()
    return fig, ax


def plot_attacking_stats(
    player_stats: Sequence[tuple[str, dict[str, float]]],
    badge: Any = None,
    colors: Sequence[str] = ("royalblue", "yellow"),
    edgecolors: Sequence[str] = ("royalblue", "royalblue"),
    fig_size: tuple[float, float] = (10, 10),
    show: bool = True,
):
    """Four stacked bar charts per player: finishing, xG v goals, attempts v on target, xG per attempt.

    player_stats is [(name, stats)] as wyscout.data.season.attacking_stats_by_player returns.
    """
    names = [name for name, _ in player_stats]
    stats = [s for _, s in player_stats]
    x = np.arange(len(names))
    width = 0.35

    fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=fig_size)

    ax1.bar(names, [s["xg_diff"] for s in stats], color=colors[0], label="Post-shot xG minus xG", zorder=3)
    ax1.xaxis.set_tick_params(labeltop=True, labelbottom=False)
    for tick in ax1.get_xticklabels():
        tick.set_rotation(90)
    ax1.legend(loc="lower left")

    ax2.bar(x - width / 2, [s["xg"] for s in stats], width=width, label="xG", color=colors[0],
            edgecolor=edgecolors[0], zorder=3)
    ax2.bar(x + width / 2, [s["goals"] for s in stats], width=width, label="Goals", color=colors[1],
            edgecolor=edgecolors[1], zorder=3)
    ax2.xaxis.set_tick_params(labelbottom=False)
    ax2.set_xticks(x, names)
    ax2.legend()

    ax3.bar(x - width / 2, [s["shots"] for s in stats], width=width, label="Attempts", color=colors[0],
            edgecolor=edgecolors[0], zorder=3)
    ax3.bar(x + width / 2, [s["on_target"] for s in stats], width=width, label="On target",
            color=colors[1], edgecolor=edgecolors[1], zorder=3)
    ax3.xaxis.set_tick_params(labelbottom=False)
    ax3.set_xticks(x, names)
    ax3.legend()

    ax4.bar(names, [s["xg_per_shot"] for s in stats], color=colors[0], label="Average xG per attempt", zorder=3)
    for tick in ax4.get_xticklabels():
        tick.set_rotation(90)
    ax4.legend()
    ax4.patch.set_alpha(0.5)

    plt.subplots_adjust(wspace=0, hspace=0.05)
    for ax in (ax1, ax2, ax3, ax4):
        ax.set_anchor("W")
        ax.grid(True, zorder=0)

    if badge is not None:
        image = OffsetImage(np.asarray(load_image(badge)), zoom=0.8)
        ax2.add_artist(AnnotationBbox(image, (ax2.get_xlim()[1] / 2, ax2.get_ylim()[1] / 2),
                                      frameon=False, zorder=2))

    if show:
        plt.show()
    return fig, (ax1, ax2, ax3, ax4)


def plot_squad_grid(
    players: Sequence[dict[str, Any]],
    captions: Sequence[str] | None = None,
    cols: int = 6,
    fig_width: float = 14,
    show: bool = True,
):
    """Player photos in a grid, with an optional caption under each."""
    rows = math.ceil(len(players) / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(fig_width, fig_width / cols * rows * 1.25))
    axes = np.atleast_1d(axes).ravel()
    for i, ax in enumerate(axes):
        ax.axis("off")
        if i >= len(players):
            continue
        ax.imshow(load_image(players[i]["imageDataURL"]))
        caption = captions[i] if captions else players[i].get("shortName", "")
        ax.set_title(caption, fontsize=9)
    fig.tight_layout()
    if show:
        plt.show()
    return fig, axes
