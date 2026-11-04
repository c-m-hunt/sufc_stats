"""Match and match-group pitch charts: attempts, average positions, final-third passes, xG race."""

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from wyscout.viz.arrows import Arrow, plot_arrows
from wyscout.viz.consts import APP_FONT, TEAM_COLOURS
from wyscout.viz.heat_map import add_heat_map
from wyscout.viz.pitch import make_pitch, pitch_axes, pitch_grid
from wyscout.viz.shots import plot_shots
from wyscout.viz.utils import add_footer, add_header, panel_title

Event = dict[str, Any]


# ── attempts ─────────────────────────────────────────────────────────────────


@dataclass
class AttemptGroup:
    """The attempts to draw on one half pitch, and what to divide them by."""

    label: str
    shots: list[Event]
    matches: int = 0  # per-game rates
    minutes: float | None = None  # given, per-90 rates are shown instead
    highlighted: list[Event] = field(default_factory=list)  # drawn in the highlight colours


def plot_attempts(
    groups: Sequence[AttemptGroup],
    header: str,
    fig_height: float = 10,
    shot_colors: tuple[str, str] = TEAM_COLOURS,
    highlight_colors: tuple[str, str] = ("gold", "khaki"),
    badge: Any = None,
    show: bool = True,
):
    """Half pitches of attempts, one per group, with totals and rates underneath.

    Marker area is xG, a red ring is a goal, the darker shade is on target.
    """
    cols = len(groups)
    pitch = make_pitch(half=True, pad_top=25, pad_bottom=-10)
    fig, axs = pitch_grid(pitch, ncols=cols, fig_height=fig_height, title_height=0.01,
                          title_space=-0.05, endnote_height=0.05, endnote_space=0.02)

    title_font = fig_height * (3 if cols == 1 else 5)
    text_font = fig_height * (2 if cols > 1 else 1.2)

    for group, ax in zip(groups, pitch_axes(axs)):
        shots = group.shots
        attempts = len(shots)
        goals = sum(1 for s in shots if s["shot"]["isGoal"])
        xg = sum(s["shot"]["xg"] for s in shots)
        xg_per_shot = xg / attempts if attempts else 0

        if group.minutes is not None:
            rate_label, count_label, count_value = "/90", "Minutes", f"{round(group.minutes)}"
            divisor = group.minutes / 90 if group.minutes else 0
        else:
            rate_label, count_label, count_value = "/game", "Matches", f"{group.matches}"
            divisor = group.matches

        def rate(value, divisor=divisor):
            return round(value / divisor, 1) if divisor else "-"

        tiles = [
            (50, 65, count_label, count_value),
            (15, 60, f"Attempts({rate_label})", f"{attempts} ({rate(attempts)})"),
            (40, 60, f"Goals({rate_label})", f"{goals} ({rate(goals)})"),
            (65, 60, f"xG({rate_label})", f"{round(xg, 1)} ({rate(xg)})"),
            (90, 60, "xG/shot", f"{round(xg_per_shot, 2)}"),
        ]
        for x, y, label, value in tiles:
            ax.text(x, y, label, ha="center", va="center", fontsize=text_font)
            ax.text(x, y - 2.5, value, ha="center", va="center", fontsize=text_font, weight="bold")

        highlighted = {id(s) for s in group.highlighted}
        plot_shots([s for s in shots if id(s) not in highlighted], shot_colors, pitch, ax)
        plot_shots([s for s in shots if id(s) in highlighted], highlight_colors, pitch, ax)
        panel_title(ax, group.label, text_font)

    add_header(fig, axs["title"], header, subtitle_start_pos=-4, scale_img=13, font_size=title_font,
               title_va="center", title_pos=(0, -3), imgs=[badge] if badge else None,
               img_rel_x_pos=0.13 if cols == 1 else 0.06, img_rel_y_pos=0.1)
    add_footer(fig, axs["endnote"], scale_img=1.3, font_size=fig_height * 1.3)

    if show:
        plt.show()
    return fig, axs, pitch


def plot_attempts_heat_map(
    locations: Sequence[Sequence[float]],
    header: str,
    subtitle: Sequence[str] | None = None,
    badge: Any = None,
    fig_height: float = 10,
    cmap: str = "Blues",
    show: bool = True,
):
    """Where attempts come from, as a density map on a half pitch."""
    pitch = make_pitch(half=True, pad_top=20, pad_bottom=0)
    fig, axs = pitch_grid(pitch, fig_height=fig_height, title_height=0.01, title_space=-0.05,
                          endnote_height=0.05, endnote_space=0.02)
    add_heat_map(locations, pitch, axs["pitch"], levels=50, cmap=cmap)
    add_header(fig, axs["title"], header, subtitle=subtitle, subtitle_font_size=fig_height * 2,
               subtitle_start_pos=-4, scale_img=13, font_size=fig_height * 3, title_va="center",
               title_pos=(0, 0), imgs=[badge] if badge else None, img_rel_x_pos=0.13, img_rel_y_pos=0.1)
    add_footer(fig, axs["endnote"], scale_img=1.3, font_size=fig_height * 1.3)
    if show:
        plt.show()
    return fig, axs, pitch


# ── average positions ────────────────────────────────────────────────────────


def plot_average_positions(
    groups: Sequence[tuple[str, dict[int, dict[str, Any]]]],
    header: str,
    badge: Any = None,
    fig_height: float = 10,
    colors: tuple[str, str] = ("blue", "cornflowerblue"),
    text_colors: tuple[str, str] = ("white", "black"),
    show: bool = True,
):
    """Shirt numbers at each player's mean position; starters in the first colour.

    groups is a list of (title, positions) where positions is
    {player_id: {"x", "y", "shirt", "start"}} as wyscout.data.match.average_positions returns.
    """
    pitch = make_pitch(grass=True, pad_top=20)
    fig, axs = pitch_grid(pitch, ncols=len(groups), fig_height=fig_height, title_height=0.01,
                          title_space=0.04, endnote_height=0.08)

    for (title, positions), ax in zip(groups, pitch_axes(axs)):
        for pos in positions.values():
            started = pos["start"]
            pitch.scatter(pos["x"], pos["y"], s=400, color=colors[0] if started else colors[1],
                          edgecolors=["black"], linewidth=0.5, marker="o", zorder=3, ax=ax)
            pitch.annotate(
                pos["shirt"],
                xy=(pos["x"] - fig_height / 13, pos["y"] + fig_height * 0.02),
                fontsize=fig_height,
                color=text_colors[0] if started else text_colors[1],
                ha="center",
                weight="bold",
                zorder=3,
                ax=ax,
            )
        panel_title(ax, title, fig_height * 2, y=104)

    add_header(fig, axs["title"], header, subtitle_start_pos=-0.5, scale_img=fig_height * 1.5,
               font_size=fig_height * (3.5 if len(groups) > 1 else 2.2), title_va="center", title_pos=(0, 7),
               imgs=[badge] if badge else None, img_rel_x_pos=0.11, img_rel_y_pos=0.03)
    if show:
        plt.show()
    return fig, axs, pitch


# ── final third passes ───────────────────────────────────────────────────────


def plot_final_third_passes(
    touches: Sequence[Sequence[float]],
    arrows: Sequence[Arrow],
    header: str,
    subtitle: Sequence[str] | None = None,
    badge: Any = None,
    fig_height: float = 10,
    cmap: str = "Blues",
    show: bool = True,
):
    """Pass arrows over a touch heat map on the attacking half."""
    pitch = make_pitch(half=True, pad_top=5, pad_bottom=0)
    fig, axs = pitch_grid(pitch, fig_height=fig_height, title_height=0.025, title_space=0.02,
                          endnote_height=0.07)
    add_heat_map(touches, pitch, axs["pitch"], levels=50, cmap=cmap)
    plot_arrows(arrows, pitch, axs["pitch"])
    add_header(fig, axs["title"], header, subtitle=subtitle, subtitle_font_size=fig_height * 2.5,
               subtitle_start_pos=-0.7, scale_img=5, font_size=fig_height * 3, title_va="center",
               title_pos=(0, 1.3), imgs=[badge] if badge else None, img_rel_x_pos=0.11, img_rel_y_pos=0.03)
    add_footer(fig, axs["endnote"], scale_img=1, font_size=fig_height * 1.3)
    if show:
        plt.show()
    return fig, axs, pitch


# ── xG race ──────────────────────────────────────────────────────────────────


def plot_xg_race(
    shots: Sequence[Event],
    teams: Sequence[tuple[int, str]],
    colours: Sequence[str] = ("blue", "green"),
    ax: plt.Axes | None = None,
    title: str | None = None,
    show: bool = True,
) -> plt.Axes:
    """Cumulative xG for each team through the match, stepping up at every attempt.

    teams is [(team_id, name), ...] in the order the colours apply.
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(14, 6))

    steps: dict[int, list[tuple[float, float]]] = defaultdict(lambda: [(0, 0)])
    totals: dict[int, float] = defaultdict(float)
    for e in sorted(shots, key=lambda s: (s["matchPeriod"], s["minute"], s["second"])):
        if not e.get("shot"):
            continue
        minute = e["minute"] + e["second"] / 60
        if e["matchPeriod"] == "1H":
            minute = min(minute, 45)
        elif e["matchPeriod"] == "2H":
            minute = min(minute, 90)
        totals[e["team"]["id"]] += e["shot"]["xg"]
        steps[e["team"]["id"]].append((minute, totals[e["team"]["id"]]))

    for (team_id, _), colour in zip(teams, colours):
        points = steps[team_id] + [(90, totals[team_id])]
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        ax.step(xs, ys, where="post", color=colour, linewidth=2)
        ax.annotate(f"{totals[team_id]:.2f}", xy=(90, totals[team_id]), xytext=(4, 0),
                    textcoords="offset points", color=colour, va="center", fontweight="bold")

    ax.set_xlim(0, 95)
    ax.set_xticks([0, 15, 30, 45, 60, 75, 90])
    ax.set_xlabel("Minute")
    ax.set_ylabel("Cumulative xG")
    ax.yaxis.grid(True, alpha=0.4)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.legend(
        [Line2D([0], [0], color=c, lw=2) for _, c in zip(teams, colours)],
        [name for _, name in teams],
        loc="upper left",
        frameon=False,
    )
    if title:
        ax.set_title(title, fontproperties=APP_FONT.prop, fontsize=14, loc="left")
    if show:
        plt.show()
    return ax
