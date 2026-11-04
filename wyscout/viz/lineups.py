"""Every eleven a team has used: a grid of pitches, or one row each in a who-played matrix,
with the minutes it played and the goals either way."""

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

import matplotlib.pyplot as plt

from wyscout.viz.consts import APP_FONT, GRID, MUTED, NAVY, RESULT_FG, TEXT
from wyscout.viz.pitch import make_pitch, pitch_grid
from wyscout.viz.utils import add_header


@dataclass
class LineupPanel:
    """One pitch: the players at their mean positions and the eleven's record together.

    positions is {player_id: {"x", "y", "shirt", "name"}}; players in subs are
    drawn in the second colour.
    """

    title: str
    positions: dict[int, dict[str, Any]]
    minutes: int
    goals_for: int
    goals_against: int
    subs: set[int] = field(default_factory=set)
    note: str = ""  # a line under the record, e.g. the other games the eleven played

    def per_90(self) -> tuple[float, float]:
        if not self.minutes:
            return 0.0, 0.0
        return self.goals_for * 90 / self.minutes, self.goals_against * 90 / self.minutes


def _result(goals_for: float, goals_against: float) -> str:
    if round(goals_for, 1) > round(goals_against, 1):
        return "W"
    if round(goals_for, 1) < round(goals_against, 1):
        return "L"
    return "D"


def plot_lineups(
    rows: Sequence[Sequence[LineupPanel]],
    header: str,
    subtitle: str | list[str] | None = None,
    badge: Any = None,
    short_minutes: int = 20,
    panel_height: float = 4.2,
    colors: tuple[str, str] = ("blue", "cornflowerblue"),
    text_colors: tuple[str, str] = ("white", "black"),
    show: bool = True,
):
    """Rows of pitches, one per eleven, with the record underneath.

    Under each pitch: minutes together, goals for and against, and the per-90
    scoreline coloured as a win, draw or loss. Elevens with fewer than
    short_minutes together have the per-90 line greyed - a goal in five
    minutes projects to eighteen.
    """
    ncols = max(len(r) for r in rows)
    nrows = len(rows)
    fig_height = panel_height * nrows + 2
    header_frac = 1.6 / fig_height

    pitch = make_pitch(grass=True, pad_top=14, pad_bottom=16, linewidth=0.8)
    fig, axs = pitch_grid(pitch, ncols=ncols, nrows=nrows, fig_height=fig_height,
                          title_height=header_frac, title_space=0.15 / fig_height,
                          endnote_height=0.1 / fig_height, endnote_space=0,
                          grid_height=1 - header_frac - 0.6 / fig_height)
    grid = axs["pitch"].reshape(nrows, ncols)

    for r, row in enumerate(rows):
        for c in range(ncols):
            ax = grid[r, c]
            if c >= len(row):
                ax.remove()
                continue
            _draw_panel(pitch, ax, row[c], short_minutes, colors, text_colors)

    add_header(fig, axs["title"], header, subtitle=subtitle, font_size=30, subtitle_font_size=13,
               title_pos=(0, 0.85), subtitle_start_pos=0.52, subtitle_gap=0.16,
               imgs=[badge] if badge else None, scale_img=0.9, img_rel_x_pos=0.08, img_rel_y_pos=-0.005)
    if show:
        plt.show()
    return fig, axs


def _draw_panel(pitch, ax, panel: LineupPanel, short_minutes: int,
                colors: tuple[str, str], text_colors: tuple[str, str]) -> None:
    font = APP_FONT.prop
    for pid, pos in panel.positions.items():
        sub = pid in panel.subs
        pitch.scatter(pos["x"], pos["y"], s=260, color=colors[1] if sub else colors[0],
                      edgecolors="black", linewidth=0.5, zorder=3, ax=ax)
        pitch.annotate(pos["shirt"] if pos["shirt"] is not None else "", xy=(pos["x"], pos["y"]),
                       fontsize=8, color=text_colors[1] if sub else text_colors[0], ha="center", va="center", zorder=4, fontproperties=font, ax=ax)
        pitch.annotate(pos["name"].split(". ")[-1], xy=(pos["x"] - 4.6, pos["y"]), fontsize=7,
                       color=TEXT, ha="center", va="center", zorder=4, fontproperties=font,
                       bbox={"boxstyle": "round,pad=0.12", "fc": "white", "ec": "none", "alpha": 0.7},
                       ax=ax)

    # pitch y runs across, x up: text above the pitch sits at x > 100, below it at x < 0
    ax.text(50, 108, panel.title, ha="center", va="center", fontsize=11,
            color=TEXT, fontproperties=font)

    gf, ga = panel.per_90()
    short = panel.minutes < short_minutes
    ax.text(50, -4.5, f"{panel.minutes} min together  ·  {panel.goals_for}-{panel.goals_against}",
            ha="center", va="center", fontsize=10, color=TEXT, fontproperties=font)
    ax.text(50, -10, f"Per 90: {gf:.1f} - {ga:.1f}" + ("  (short spell)" if short else ""),
            ha="center", va="center", fontsize=11, fontproperties=font,
            color=MUTED if short else RESULT_FG[_result(gf, ga)])
    if panel.note:
        ax.text(50, -14.5, panel.note, ha="center", va="center", fontsize=8, color=MUTED, fontproperties=font)


@dataclass
class ElevenRow:
    """One row of the matrix: who was in the eleven and its record together."""

    players: frozenset[int]
    minutes: int
    goals_for: int
    goals_against: int
    label: str = ""  # e.g. where it played

    def per_90(self) -> tuple[float, float]:
        if not self.minutes:
            return 0.0, 0.0
        return self.goals_for * 90 / self.minutes, self.goals_against * 90 / self.minutes


def plot_lineup_matrix(
    rows: Sequence[ElevenRow],
    players: Sequence[tuple[int, str]],
    header: str,
    subtitle: str | list[str] | None = None,
    badge: Any = None,
    short_minutes: int = 20,
    show: bool = True,
):
    """One row per eleven in the order given, a dot under each player in it.

    players is [(player_id, name)] in column order. To the right: a bar of
    minutes together, the goals for and against, and the per-90 scoreline
    coloured as a win, draw or loss - greyed under short_minutes.
    """
    font = APP_FONT.prop
    n, cols = len(rows), len(players)
    fig_height = 0.32 * n + 4.4
    fig = plt.figure(figsize=(0.42 * cols + 12, fig_height))
    top = 1 - 2.8 / fig_height
    bottom = 0.3 / fig_height
    gs = fig.add_gridspec(1, 3, width_ratios=[cols * 0.42, 3.2, 3.4], left=0.2, right=0.98,
                          top=top, bottom=bottom, wspace=0.03)
    ax_dots, ax_bar, ax_text = (fig.add_subplot(gs[0, i]) for i in range(3))
    header_ax = fig.add_axes((0.02, top + 1.3 / fig_height, 0.96, 1.4 / fig_height))
    header_ax.axis("off")

    ys = range(n)
    for ax in (ax_dots, ax_bar, ax_text):
        ax.set_ylim(n - 0.5, -0.5)
        ax.tick_params(length=0)
        for side in ax.spines.values():
            side.set_visible(False)
        for y in ys:
            if y % 2 == 0:
                ax.axhspan(y - 0.5, y + 0.5, color=GRID, alpha=0.45, zorder=0, lw=0)

    # who was in it
    column = {pid: i for i, (pid, _) in enumerate(players)}
    for y, row in enumerate(rows):
        xs = sorted(column[pid] for pid in row.players if pid in column)
        ax_dots.scatter(xs, [y] * len(xs), s=70, color=NAVY, zorder=3)
    ax_dots.set_xlim(-0.6, cols - 0.4)
    ax_dots.set_xticks(range(cols))
    ax_dots.set_xticklabels([name for _, name in players], rotation=60, ha="left", fontsize=10,
                            fontproperties=font, color=TEXT)
    ax_dots.xaxis.tick_top()
    for x in range(cols):
        ax_dots.axvline(x, color=GRID, lw=0.6, zorder=1)
    ax_dots.set_yticks(list(ys))
    ax_dots.set_yticklabels([r.label for r in rows], fontsize=9, fontproperties=font, color=TEXT)

    # minutes together
    minutes = [r.minutes for r in rows]
    ax_bar.barh(list(ys), minutes, height=0.6, color=NAVY, zorder=2)
    for y, m in zip(ys, minutes):
        ax_bar.text(m + max(minutes) * 0.02, y, f"{m}'", va="center", fontsize=9, fontproperties=font, color=TEXT)
    ax_bar.set_xlim(0, max(minutes) * 1.25)
    ax_bar.set_xticks([])
    ax_bar.set_yticks([])
    ax_bar.set_title("Minutes together", loc="left", fontsize=11, fontproperties=font, color=TEXT)

    # goals and the per-90 scoreline
    ax_text.set_xlim(0, 1)
    ax_text.set_xticks([])
    ax_text.set_yticks([])
    ax_text.text(0.05, -0.9, "Goals", fontsize=11, fontproperties=font, color=TEXT, va="bottom")
    ax_text.text(0.38, -0.9, "Per 90", fontsize=11, fontproperties=font, color=TEXT, va="bottom")
    for y, row in zip(ys, rows):
        gf, ga = row.per_90()
        short = row.minutes < short_minutes
        ax_text.text(0.05, y, f"{row.goals_for}-{row.goals_against}", va="center", fontsize=10,
                     fontproperties=font, color=TEXT)
        ax_text.text(0.38, y, f"{gf:.1f} - {ga:.1f}" + ("  short" if short else ""), va="center", fontsize=10,
                     fontproperties=font, color=MUTED if short else RESULT_FG[_result(gf, ga)])

    add_header(fig, header_ax, header, subtitle=subtitle, font_size=24, subtitle_font_size=11,
               title_pos=(0, 0.85), subtitle_start_pos=0.45, subtitle_gap=0.2,
               imgs=[badge] if badge else None, scale_img=1, img_rel_x_pos=0.07)
    if show:
        plt.show()
    return fig, (ax_dots, ax_bar, ax_text)
