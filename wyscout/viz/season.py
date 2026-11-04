"""Season charts - plain matplotlib, no pitches.

Every function takes prepared DataFrames from ``wyscout.data`` and draws
one figure. Nothing here fetches.
"""

from collections.abc import Sequence
from functools import lru_cache

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import gridspec, ticker
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from matplotlib.patches import Patch

from wyscout.viz.consts import (
    GA_COL,
    GA_PREV,
    GF_COL,
    GF_PREV,
    GRID,
    MUTED,
    NAVY,
    PREV_COL,
    RESULT_BG,
    RESULT_FG,
    TEXT,
    THIS_COL,
)
from wyscout.viz.utils import load_image

RESULT_CMAP = "RdYlGn"


def _shade_results(ax: plt.Axes, results: Sequence[int], alpha: float = 0.15) -> None:
    """A red-to-green wash behind the bars, one column per match result (0 loss, 1 draw, 2 win)."""
    ax.pcolorfast(ax.get_xlim(), ax.get_ylim(), np.array(results)[np.newaxis], cmap=RESULT_CMAP,
                  alpha=alpha, vmin=0, vmax=2)


# ── xG through the season ────────────────────────────────────────────────────


def plot_xg_per_shot_trend(df: pd.DataFrame, fig_size=(15, 9), show: bool = True):
    """Chance quality and volume game by game.

    df is wyscout.data.season.season_shot_table's output. Left axis: xG per
    shot per match (bars), the season rolling average and the last-five
    rolling average (lines). Right axis: attempts and goals. Background
    shaded by result.
    """
    with sns.axes_style("whitegrid"):
        fig, ax1 = plt.subplots(figsize=fig_size)
        ax2 = ax1.twinx()

    sns.lineplot(data=df, x="label", y="rolling_xg_per_shot", color="lightsteelblue", linewidth=2, ax=ax1)
    sns.lineplot(data=df, x="label", y="rolling_5_xg_per_shot", color="gold", linewidth=2, ax=ax1)
    sns.barplot(data=df, x="label", y="xg_per_shot", color="blue", ax=ax1)
    ax1.tick_params(axis="x", rotation=90)
    ax1.set(xlabel=None, ylabel="xG/shot")

    sns.barplot(data=df, x="label", y="shots", color="darkred", alpha=0.5, width=0.3, ax=ax2)
    sns.barplot(data=df, x="label", y="goals", color="red", ax=ax2)
    ax2.set(ylabel="Attempts and goals")
    ax2.grid(False)

    ax1.legend(
        handles=[
            Line2D([], [], color="lightsteelblue", label="Rolling xG/shot for season", linewidth=2),
            Line2D([], [], color="gold", label="Rolling xG/shot for last 5 games", linewidth=2),
            Line2D([], [], color="blue", label="xG/shot for game"),
            Line2D([], [], color="darkred", alpha=0.3, label="Attempts for game"),
            Line2D([], [], color="red", label="Goals"),
        ],
        loc="upper left",
    )
    _shade_results(ax1, df["result"].values, alpha=0.2)

    if show:
        plt.show()
    return fig, (ax1, ax2)


def plot_xg_vs_goals(df: pd.DataFrame, fig_size=(15, 6), show: bool = True):
    """Paired bars of xG and goals per match with a five-game rolling xG line."""
    with sns.axes_style("whitegrid"):
        fig, ax = plt.subplots(figsize=fig_size)
    x = np.arange(len(df))
    width = 0.35
    ax.bar(x - width / 2, df["xG"], width=width, color="royalblue", label="xG")
    ax.bar(x + width / 2, df["goals"], width=width, color="red", label="Goals")
    ax.plot(x, df["xG"].rolling(5, min_periods=1).mean(), color="lightsteelblue", linewidth=2,
            label="Rolling 5-game xG")
    ax.set_xticks(x)
    ax.set_xticklabels(df["label"], rotation=90)
    ax.set(ylabel="xG / Goals", xlabel=None)
    _shade_results(ax, df["result"].values)
    ax.legend()
    plt.tight_layout()
    if show:
        plt.show()
    return fig, ax


def plot_cumulative_xg(df: pd.DataFrame, title: str, fig_size=(17, 9), show: bool = True):
    """Dark two-panel chart: cumulative xG against cumulative goals, and the gap between them.

    df is wyscout.data.season.season_shot_table's output.
    """
    bg, panel = "#0f1117", "#161b22"
    xg_col, goal_col = "#58a6ff", "#f78166"
    text, muted, grid = "#c9d1d9", "#8b949e", "#21262d"
    result_col = {2: "#3fb950", 1: "#d29922", 0: "#da3633"}

    x = df["game"].values
    xg = df["cum_xG"].values
    goals = df["cum_goals"].values
    gap = xg - goals

    fig, (ax, ax2) = plt.subplots(2, 1, figsize=fig_size, sharex=True,
                                  gridspec_kw={"height_ratios": [3, 1], "hspace": 0.06})
    fig.patch.set_facecolor(bg)
    for a in (ax, ax2):
        a.set_facecolor(panel)
        for spine in a.spines.values():
            spine.set_visible(False)

    ax.fill_between(x, xg, goals, where=(xg >= goals), color=xg_col, alpha=0.12, zorder=2)
    ax.fill_between(x, xg, goals, where=(xg < goals), color=goal_col, alpha=0.12, zorder=2)
    ax.plot(x, xg, color=xg_col, linewidth=2.5, zorder=5, solid_capstyle="round")
    ax.plot(x, goals, color=goal_col, linewidth=2.5, zorder=5, solid_capstyle="round")
    ax.scatter(x, xg, color=xg_col, s=55, zorder=6, edgecolors=panel, linewidth=1.2)
    ax.scatter(x, goals, color=goal_col, s=55, zorder=6, edgecolors=panel, linewidth=1.2)
    for game, result in zip(x, df["result"]):
        ax.axvspan(game - 0.45, game + 0.45, ymin=0, ymax=0.025, color=result_col[result],
                   alpha=0.85, zorder=4, lw=0)

    ax.tick_params(axis="y", colors=muted, labelsize=9)
    ax.tick_params(axis="x", length=0, labelbottom=False)
    ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    ax.yaxis.grid(True, color=grid, linewidth=0.8, linestyle="--", zorder=0)
    ax.xaxis.grid(False)
    ax.set_axisbelow(True)
    ax.set_ylabel("Cumulative", fontsize=11, color=muted, labelpad=10)

    pad = 0.4
    ax.annotate(f"{xg[-1]:.1f} xG", xy=(x[-1], xg[-1]), xytext=(x[-1] + pad, xg[-1]), color=xg_col,
                fontsize=10, fontweight="bold", va="center",
                arrowprops={"arrowstyle": "-", "color": xg_col, "lw": 1, "alpha": 0.5})
    ax.annotate(f"{int(goals[-1])} goals", xy=(x[-1], goals[-1]), xytext=(x[-1] + pad, goals[-1]),
                color=goal_col, fontsize=10, fontweight="bold", va="center",
                arrowprops={"arrowstyle": "-", "color": goal_col, "lw": 1, "alpha": 0.5})
    ax.legend(
        handles=[
            Line2D([0], [0], color=xg_col, linewidth=2.5, marker="o", markersize=6, label="Cumulative xG"),
            Line2D([0], [0], color=goal_col, linewidth=2.5, marker="o", markersize=6, label="Cumulative goals"),
            Patch(color=result_col[2], label="Win"),
            Patch(color=result_col[1], label="Draw"),
            Patch(color=result_col[0], label="Loss"),
        ],
        loc="upper left", frameon=True, facecolor=bg, edgecolor=grid, labelcolor=text, fontsize=9,
    )

    ax2.bar(x, gap, color=[xg_col if g >= 0 else goal_col for g in gap], alpha=0.7, width=0.7, zorder=3)
    ax2.fill_between(x, gap, 0, where=(gap >= 0), color=xg_col, alpha=0.12, zorder=2)
    ax2.fill_between(x, gap, 0, where=(gap < 0), color=goal_col, alpha=0.12, zorder=2)
    ax2.axhline(0, color=muted, linewidth=0.8, alpha=0.4, zorder=4)
    gap_lim = max(abs(gap.min()), abs(gap.max()), 1) * 1.35
    ax2.set_ylim(-gap_lim, gap_lim)
    ax2.tick_params(axis="y", colors=muted, labelsize=8)
    ax2.tick_params(axis="x", length=0)
    ax2.yaxis.set_major_locator(ticker.MaxNLocator(nbins=4))
    ax2.yaxis.grid(True, color=grid, linewidth=0.8, linestyle="--", zorder=0)
    ax2.xaxis.grid(False)
    ax2.set_axisbelow(True)
    ax2.set_ylabel("xG gap", fontsize=10, color=muted, labelpad=10)
    ax2.set_xlim(0.2, len(df) + 0.8)
    ax2.set_xticks(x)
    ax2.set_xticklabels(df["short_label"], rotation=90, fontsize=7.5, color=muted)
    gap_color = xg_col if gap[-1] >= 0 else goal_col
    ax2.annotate(f"{gap[-1]:+.1f}", xy=(x[-1], gap[-1]), xytext=(x[-1] + pad, gap[-1]), color=gap_color,
                 fontsize=10, fontweight="bold", va="center",
                 arrowprops={"arrowstyle": "-", "color": gap_color, "lw": 1, "alpha": 0.5})

    fig.suptitle(title, fontsize=14, color=text, fontweight="bold", x=0.5, y=1.01, ha="center")
    ax.set_title("Bottom bars = W/D/L  ·  Blue = xG ahead  ·  Red = Goals ahead", fontsize=9,
                 color=muted, pad=6)
    plt.tight_layout()
    if show:
        plt.show()
    return fig, (ax, ax2)


def plot_xg_for_against(df: pd.DataFrame, title: str, include_pens: bool = False, fig_size=(17, 11),
                        show: bool = True):
    """Dark two-panel chart: xG and goals, for and against, through the season.

    df is wyscout.data.season.season_xg_table's output. The top panel runs
    cumulative xG (dashed) and goals (solid) for us in green and against us
    in red. The gap between each pair is shaded: bright where it is good for
    us (scoring above xG, conceding below xGA), hatched where it is bad. The
    bottom panel mirrors each game - goals scored up, conceded down - with
    the game's xG and xGA as white ticks. X labels are coloured by result.
    include_pens says whether df includes penalties; it only changes the labels.
    """
    xg_name = "xG" if include_pens else "npxG"
    bg, panel = "#0f1117", "#161b22"
    gf_col, ga_col = "#3fb950", "#f85149"
    text, muted, grid = "#c9d1d9", "#8b949e", "#21262d"
    result_col = {"W": "#3fb950", "D": "#d29922", "L": "#da3633"}

    x = df["game"].to_numpy()
    xgf, xga = df["cum_xg_for"].to_numpy(), df["cum_xg_against"].to_numpy()
    gf, ga = df["cum_gf"].to_numpy(), df["cum_ga"].to_numpy()

    fig, (ax, ax2) = plt.subplots(2, 1, figsize=fig_size, sharex=True,
                                  gridspec_kw={"height_ratios": [3, 1.6], "hspace": 0.05})
    fig.patch.set_facecolor(bg)
    for a in (ax, ax2):
        a.set_facecolor(panel)
        for spine in a.spines.values():
            spine.set_visible(False)
        a.yaxis.grid(True, color=grid, linewidth=0.8, linestyle="--", zorder=0)
        a.set_axisbelow(True)
        a.tick_params(axis="y", colors=muted, labelsize=9)
        a.tick_params(axis="x", length=0)

    # good gaps are filled, bad gaps hatched
    for goals, xg, col, good_when_above in ((gf, xgf, gf_col, True), (ga, xga, ga_col, False)):
        above = goals >= xg
        good, bad = (above, ~above) if good_when_above else (~above, above)
        ax.fill_between(x, goals, xg, where=good, interpolate=True, color=col, alpha=0.22, lw=0, zorder=2)
        ax.fill_between(x, goals, xg, where=bad, interpolate=True, facecolor="none", edgecolor=col, alpha=0.5,
                        hatch="///", lw=0, zorder=2)
        ax.plot(x, xg, color=col, linewidth=2, linestyle=(0, (5, 3)), alpha=0.85, zorder=4)
        ax.plot(x, goals, color=col, linewidth=2.8, zorder=5, solid_capstyle="round")
        ax.scatter(x, goals, color=col, s=45, zorder=6, edgecolors=panel, linewidth=1.2)

    end, pad = x[-1], 0.35
    labels = [(gf[-1], f"{gf[-1]:.0f} scored", gf_col, "bold"), (xgf[-1], f"{xgf[-1]:.1f} {xg_name}", gf_col, "normal"),
              (ga[-1], f"{ga[-1]:.0f} conceded", ga_col, "bold"), (xga[-1], f"{xga[-1]:.1f} {xg_name}A", ga_col, "normal")]
    labels.sort(key=lambda item: item[0])
    gap = (max(gf.max(), xgf.max(), ga.max(), xga.max()) or 1) * 0.045
    placed = []
    for value, label, col, weight in labels:  # nudge apart labels that would overlap
        y = max(value, placed[-1] + gap) if placed else value
        placed.append(y)
        ax.annotate(label, xy=(end, value), xytext=(end + pad, y), color=col, fontsize=10.5, fontweight=weight,
                    va="center", arrowprops={"arrowstyle": "-", "color": col, "lw": 0.8, "alpha": 0.5})

    def verdict(diff, good_if_positive, noun):
        word = "above" if diff >= 0 else "below"
        good = (diff >= 0) == good_if_positive
        return f"{noun} {abs(diff):.1f} {word} expected", gf_col if good else ga_col

    attack, attack_col = verdict(gf[-1] - xgf[-1], True, "Scored")
    defence, defence_col = verdict(ga[-1] - xga[-1], False, "Conceded")
    ax.text(0.01, 0.97, attack, transform=ax.transAxes, color=attack_col, fontsize=12, fontweight="bold", va="top")
    ax.text(0.01, 0.90, defence, transform=ax.transAxes, color=defence_col, fontsize=12, fontweight="bold", va="top")
    ax.text(0.01, 0.83, f"Goal difference {gf[-1] - ga[-1]:+.0f}  ·  {xg_name} difference {xgf[-1] - xga[-1]:+.1f}",
            transform=ax.transAxes, color=text, fontsize=10.5, va="top")
    ax.set_ylabel("Cumulative", fontsize=11, color=muted, labelpad=10)
    ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    ax.legend(
        handles=[
            Line2D([], [], color=gf_col, linewidth=2.8, marker="o", markersize=5, label="Goals for" if include_pens else "Non-penalty goals for"),
            Line2D([], [], color=gf_col, linewidth=2, linestyle=(0, (5, 3)), label=f"{xg_name} for"),
            Line2D([], [], color=ga_col, linewidth=2.8, marker="o", markersize=5, label="Goals against" if include_pens else "Non-penalty goals against"),
            Line2D([], [], color=ga_col, linewidth=2, linestyle=(0, (5, 3)), label=f"{xg_name} against"),
            Patch(facecolor=muted, alpha=0.35, label="Gap in our favour"),
            Patch(facecolor="none", edgecolor=muted, hatch="///", label="Gap against us"),
        ],
        loc="lower left", bbox_to_anchor=(0, 1.0), ncol=6, frameon=False, labelcolor=text, fontsize=9.5,
    )

    # each game, mirrored around zero
    ax2.bar(x, df["gf"], color=gf_col, alpha=0.75, width=0.6, zorder=3)
    ax2.bar(x, -df["ga"], color=ga_col, alpha=0.75, width=0.6, zorder=3)
    ax2.hlines(df["xg_for"], x - 0.38, x + 0.38, color="white", linewidth=2.2, zorder=4)
    ax2.hlines(-df["xg_against"], x - 0.38, x + 0.38, color="white", linewidth=2.2, zorder=4)
    backing = {"boxstyle": "round,pad=0.15", "facecolor": panel, "edgecolor": "none", "alpha": 0.85}
    for xi, value in zip(x, df["xg_for"]):
        ax2.annotate(f"{value:.1f}", (xi, value), xytext=(0, 3), textcoords="offset points", ha="center",
                     va="bottom", fontsize=8, color=text, zorder=5, bbox=backing)
    for xi, value in zip(x, df["xg_against"]):
        ax2.annotate(f"{value:.1f}", (xi, -value), xytext=(0, -3), textcoords="offset points", ha="center",
                     va="top", fontsize=8, color=text, zorder=5, bbox=backing)
    ax2.axhline(0, color=muted, linewidth=0.8, zorder=4)
    limit = max(df["gf"].max(), df["ga"].max(), df["xg_for"].max(), df["xg_against"].max()) + 1
    ax2.set_ylim(-limit, limit)
    ax2.yaxis.set_major_locator(ticker.MaxNLocator(integer=True, nbins=6))
    ax2.yaxis.set_major_formatter(lambda v, pos: f"{abs(v):.0f}")
    ax2.set_ylabel("Per game\nconceded  |  scored", fontsize=10, color=muted, labelpad=10)
    ax2.text(0.995, 0.97, f"white tick = {xg_name}", transform=ax2.transAxes, color=muted, fontsize=9, va="top",
             ha="right")
    ax2.set_xlim(0.4, len(df) + 1.9)
    ax2.set_xticks(x)
    ax2.set_xticklabels(df["short_label"], rotation=90, fontsize=8.5)
    for tick, result in zip(ax2.get_xticklabels(), df["result"]):
        tick.set_color(result_col[result])

    fig.suptitle(title, fontsize=15, color=text, fontweight="bold", x=0.06, ha="left", y=0.985)
    fig.subplots_adjust(left=0.06, right=0.93, top=0.91, bottom=0.12)
    if show:
        plt.show()
    return fig, (ax, ax2)


# ── season on season ─────────────────────────────────────────────────────────


def _style_axis(ax: plt.Axes, title: str, ylabel: str, games: int) -> None:
    ax.set_title(title, fontsize=12, fontweight="bold", color=TEXT, pad=8, loc="left")
    ax.set_ylabel(ylabel, fontsize=9.5, color=MUTED)
    ax.set_xlabel("Game", fontsize=9.5, color=MUTED)
    ax.grid(True, color=GRID, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(colors=MUTED, labelsize=9)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xlim(0.6, games + 0.4)
    ax.set_xticks(range(1, games + 1))
    ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))


def _compare_lines(ax, this: pd.DataFrame, prev: pd.DataFrame, column: str, this_label: str,
                   prev_label: str, title: str, ylabel: str, colour: str = THIS_COL) -> None:
    ax.plot(prev["game"], prev[column], color=PREV_COL, linewidth=2.4, marker="o", markersize=4,
            zorder=2, label=f"{prev_label} (same stage)")
    ax.plot(this["game"], this[column], color=colour, linewidth=2.6, marker="o", markersize=4.5,
            zorder=3, label=f"{this_label} (so far)")
    now, then = this[column].iloc[-1], prev[column].iloc[-1]
    _style_axis(ax, f"{title}  -  {now} vs {then} ({now - then:+d})", ylabel, len(this))
    ax.legend(fontsize=9, frameon=False, loc="upper left")


def plot_season_comparison(
    this: pd.DataFrame,
    prev: pd.DataFrame,
    this_label: str,
    prev_label: str,
    team_name: str,
    fig_size=(17, 12),
    show: bool = True,
):
    """A results table plus cumulative points, goal difference and goals, this season against last.

    this and prev are wyscout.data.season.season_results outputs. The table
    lines the seasons up by game number and also shows last season's result
    in the same fixture as this season's opponent and venue.
    """
    games = len(this)
    prev_stage = prev.head(games)
    prev_by_fixture = {(r.opponent, r.venue): r for r in prev.itertuples()}
    short_this, short_prev = this_label[-5:], prev_label[-5:]

    fig = plt.figure(figsize=fig_size, facecolor="white")
    grid = gridspec.GridSpec(3, 2, figure=fig, height_ratios=[1.35, 1, 1], hspace=0.38, wspace=0.16)

    # table
    ax_table = fig.add_subplot(grid[0, :])
    ax_table.axis("off")
    col_labels = ["Game", prev_label, this_label, f"Same fixture\nin {prev_label}", f"Pts\n{short_prev}",
                  f"Pts\n{short_this}", f"F-A\n{short_prev}", f"F-A\n{short_this}", f"GD\n{short_prev}",
                  f"GD\n{short_this}"]
    cell_text, result_cells = [], {}
    for r in this.itertuples():
        prev_game = prev[prev["game"] == r.game]
        p = prev_game.iloc[0] if len(prev_game) else None
        fixture = prev_by_fixture.get((r.opponent, r.venue))
        row = len(cell_text) + 1
        result_cells[(row, 2)] = r.result
        if p is not None:
            result_cells[(row, 1)] = p["result"]
        if fixture is not None:
            result_cells[(row, 3)] = fixture.result
        cell_text.append([
            str(r.game),
            f"{p['opponent']} ({p['venue']})   {p['result']} {p['gf']}-{p['ga']}" if p is not None else "-",
            f"{r.opponent} ({r.venue})   {r.result} {r.gf}-{r.ga}",
            f"{fixture.result} {fixture.gf}-{fixture.ga}" if fixture is not None else "not played",
            str(p["points"]) if p is not None else "-",
            str(r.points),
            f"{p['cum_gf']}-{p['cum_ga']}" if p is not None else "-",
            f"{r.cum_gf}-{r.cum_ga}",
            f"{p['cum_gd']:+d}" if p is not None else "-",
            f"{r.cum_gd:+d}",
        ])
    table = ax_table.table(cellText=cell_text, colLabels=col_labels, cellLoc="center",
                           colWidths=[0.05, 0.21, 0.21, 0.1, 0.07, 0.07, 0.085, 0.085, 0.06, 0.06],
                           bbox=[0, 0, 1, 0.9])
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor("#cfd6e0")
        cell.set_linewidth(0.6)
        if row == 0:
            cell.set_facecolor(NAVY)
            cell.set_text_props(color="white", fontweight="bold")
            continue
        cell.set_facecolor("#f4f7fa" if row % 2 else "white")
        if col in (1, 2):
            cell.set_text_props(ha="left")
            cell._text.set_x(0.025)
        if (row, col) in result_cells:
            res = result_cells[(row, col)]
            cell.set_facecolor(RESULT_BG[res])
            cell.set_text_props(color=RESULT_FG[res], fontweight="bold")
        if col in (5, 7, 9):
            cell.set_text_props(fontweight="bold")
    ax_table.set_title(f"{team_name} {this_label} vs {prev_label} - first {games} league games",
                       fontsize=15, fontweight="bold", color=TEXT, pad=14)

    # cumulative lines
    _compare_lines(fig.add_subplot(grid[1, 0]), this, prev_stage, "points", this_label, prev_label,
                   "Cumulative points", "Points")
    _compare_lines(fig.add_subplot(grid[1, 1]), this, prev_stage, "cum_gd", this_label, prev_label,
                   "Cumulative goal difference", "Goal difference")

    ax = fig.add_subplot(grid[2, :])
    ax.plot(prev_stage["game"], prev_stage["cum_gf"], color=GF_PREV, linewidth=2, linestyle="--",
            zorder=2, label=f"Scored {prev_label}")
    ax.plot(prev_stage["game"], prev_stage["cum_ga"], color=GA_PREV, linewidth=2, linestyle="--",
            zorder=2, label=f"Conceded {prev_label}")
    ax.fill_between(this["game"], this["cum_gf"], this["cum_ga"], color=GF_COL, alpha=0.07, zorder=1)
    ax.plot(this["game"], this["cum_gf"], color=GF_COL, linewidth=2.8, marker="o", markersize=5,
            zorder=3, label=f"Scored {this_label}")
    ax.plot(this["game"], this["cum_ga"], color=GA_COL, linewidth=2.8, marker="o", markersize=5,
            zorder=3, label=f"Conceded {this_label}")
    _style_axis(
        ax,
        f"Cumulative goals scored and conceded  -  {this['cum_gf'].iloc[-1]}-{this['cum_ga'].iloc[-1]} "
        f"vs {prev_stage['cum_gf'].iloc[-1]}-{prev_stage['cum_ga'].iloc[-1]}",
        "Goals", games,
    )
    ax.set_ylim(bottom=0)
    ax.legend(fontsize=9, frameon=False, loc="upper left", ncol=2)

    if show:
        plt.show()
    return fig


def plot_league_position(
    this: pd.DataFrame,
    prev: pd.DataFrame,
    this_label: str,
    prev_label: str,
    team_name: str,
    teams_in_league: int = 24,
    promotion_places: int = 1,
    playoff_places: int = 7,
    fig_size=(17, 11),
    show: bool = True,
):
    """League position after each match day, and the points and goal-difference gap to the leaders.

    this and prev are wyscout.league_table.table_progression outputs as DataFrames.
    """
    prev_stage = prev.head(len(this))
    latest = this.iloc[-1]
    games = len(this)

    fig = plt.figure(figsize=fig_size, facecolor="white")
    grid = gridspec.GridSpec(2, 2, figure=fig, height_ratios=[1.25, 1], hspace=0.32, wspace=0.16)
    fig.suptitle(f"{team_name} {this_label} - league position and the gap to the top", fontsize=15,
                 fontweight="bold", color=TEXT, y=0.96)

    ax = fig.add_subplot(grid[0, :])
    ax.axhspan(0.5, promotion_places + 0.5, color="#f3d98b", alpha=0.45, zorder=0)
    ax.axhspan(promotion_places + 0.5, playoff_places + 0.5, color="#cfe6cf", alpha=0.5, zorder=0)
    ax.text(0.7, promotion_places, " promotion", fontsize=8.5, color="#8a6d00", va="center")
    ax.text(0.7, playoff_places - 0.3, " play-offs", fontsize=8.5, color="#3b6b3b", va="center")
    ax.plot(prev_stage["game"], prev_stage["position"], color=PREV_COL, linewidth=2.4, marker="o",
            markersize=4, zorder=2, label=f"{prev_label} (same stage)")
    ax.plot(this["game"], this["position"], color=THIS_COL, linewidth=2.8, marker="o", markersize=5.5,
            zorder=3, label=this_label)
    for r in this.itertuples():
        ax.annotate(f"{r.position}", xy=(r.game, r.position), xytext=(0, 9), textcoords="offset points",
                    ha="center", fontsize=8.5, fontweight="bold", color=THIS_COL, zorder=4)
    _style_axis(ax, f"League position after each match day  -  {int(latest['position'])} of {teams_in_league}",
                "Position", games)
    worst = int(max(this["position"].max(), prev_stage["position"].max()))
    ax.set_ylim(worst + 1.2, 0.4)
    ax.set_yticks(range(1, worst + 2))
    ax.scatter([], [], s=70, color="#e0a800", edgecolor="white", linewidth=1.2, label="top of the league")
    ax.legend(fontsize=9, frameon=False, loc="lower right", ncol=3)

    def gap_chart(ax, column, title, ylabel, behind_label, ahead_label):
        this_gap, prev_gap = -this[column], -prev_stage[column]
        ax.axhline(0, color=MUTED, linewidth=1, zorder=2)
        ax.plot(prev_stage["game"], prev_gap, color=PREV_COL, linewidth=2.4, marker="o", markersize=4, zorder=3)
        ax.fill_between(this["game"], this_gap, 0, where=this_gap < 0, color=THIS_COL, alpha=0.08, zorder=1)
        ax.plot(this["game"], this_gap, color=THIS_COL, linewidth=2.8, marker="o", markersize=5.5, zorder=4)
        top = this["is_leader"]
        if top.any():
            ax.scatter(this["game"][top], this_gap[top], s=70, color="#e0a800", edgecolor="white",
                       linewidth=1.2, zorder=5)
        _style_axis(ax, title, ylabel, games)
        low, high = min(this_gap.min(), prev_gap.min()), max(this_gap.max(), prev_gap.max())
        ax.set_ylim(low - 0.8, high + 0.8)
        ax.annotate(ahead_label, xy=(0.012, 0.92), xycoords="axes fraction", fontsize=8.5, color=MUTED)
        ax.annotate(behind_label, xy=(0.012, 0.05), xycoords="axes fraction", fontsize=8.5, color=MUTED)

    def describe(gap: int, behind: str, ahead: str) -> str:
        if gap > 0:
            return f"{gap} {behind} {latest['leader']}"
        if gap == 0:
            return f"level with {latest['leader']}"
        return f"{-gap} {ahead} {latest['leader']}"

    gap_chart(fig.add_subplot(grid[1, 0]), "points_behind",
              "Points behind the leaders  -  " + describe(int(latest["points_behind"]), "behind", "clear of"),
              "Points", "further behind", "ahead of them")
    gap_chart(fig.add_subplot(grid[1, 1]), "goal_difference_behind",
              "Goal difference against the leaders  -  "
              + describe(int(latest["goal_difference_behind"]), "worse than", "better than"),
              "Goal difference", "worse than them", "better")

    if show:
        plt.show()
    return fig


# ── box activity ─────────────────────────────────────────────────────────────

# (column, header, colour map, diverging) - "for" columns in greens, "against" in reds
BOX_COLUMNS = [
    ("box_touches_for", "Box touches\nfor", "Greens", False),
    ("box_touches_against", "Box touches\nagainst", "Reds", False),
    ("box_touches_diff", "Box touch\ndifference", "RdYlGn", True),
    ("pens_won", "Penalties\nwon", "Greens", False),
    ("pens_conceded", "Penalties\nconceded", "Reds", False),
]


def _box_grid(
    df: pd.DataFrame,
    title: str,
    labels: Sequence[str],
    label_colours: Sequence[str],
    summary: Sequence[tuple[str, pd.Series]],
    decimals: int,
    highlight: int | None = None,
    breaks: Sequence[int] = (),
    label_width: float = 3.2,
):
    """Draw BOX_COLUMNS as a colour-coded grid, one row per df row, summary rows underneath.

    Each column is shaded on its own scale. Penalty cells with none stay white
    so the ones with a penalty stand out. highlight outlines one row; breaks
    draws a dashed line under those row numbers (e.g. promotion, play-offs).
    """
    df = df.reset_index(drop=True).assign(box_touches_diff=lambda d: d["box_touches_for"] - d["box_touches_against"])
    n = len(df)
    fig, ax = plt.subplots(figsize=(11, 1.6 + 0.36 * (n + len(summary) + 1)))
    ax.set_xlim(-label_width, len(BOX_COLUMNS))
    ax.set_ylim(n + len(summary) + 0.6, -1.2)
    ax.axis("off")

    for j, (column, header, cmap_name, diverging) in enumerate(BOX_COLUMNS):
        values = df[column]
        cmap = plt.get_cmap(cmap_name)
        if diverging:
            limit = max(abs(values.min()), abs(values.max()), 1)
            norm = plt.Normalize(-limit, limit)
        elif column.startswith("pens"):
            norm = plt.Normalize(0, max(values.max(), 1))
        else:
            # lowest to highest, so the spread between rows shows rather than every cell looking dark
            norm = plt.Normalize(values.min() - (values.max() - values.min()) * 0.15, max(values.max(), values.min() + 1))
        places = 0 if column.startswith("pens") else decimals
        ax.text(j + 0.5, -0.6, header, ha="center", va="center", fontsize=10, weight="bold", color=TEXT)
        for i, v in enumerate(values):
            colour = "white" if (column.startswith("pens") and v == 0) else cmap(norm(v) * 0.85)
            ax.add_patch(plt.Rectangle((j, i), 1, 1, facecolor=colour, edgecolor="white", linewidth=1.5))
            dark = norm(v) > 0.6 if not diverging else abs(norm(v) - 0.5) > 0.35
            ax.text(j + 0.5, i + 0.5, f"{v:{'+' if diverging else ''}.{places}f}", ha="center", va="center",
                    fontsize=10, color="white" if dark and colour != "white" else TEXT)
        for k, (label, row) in enumerate(summary, start=1):
            value = row[column]
            fmt = f"{'+' if diverging else ''}.{0 if label == 'Total' else 1}f"
            ax.add_patch(plt.Rectangle((j, n + k - 0.6), 1, 1, facecolor="#eef1f4", edgecolor="white", linewidth=1.5))
            ax.text(j + 0.5, n + k - 0.1, f"{value:{fmt}}", ha="center", va="center", fontsize=10,
                    weight="bold", color=TEXT)

    for i, (label, colour) in enumerate(zip(labels, label_colours)):
        ax.text(-0.1, i + 0.5, label, ha="right", va="center", fontsize=9.5, color=colour,
                weight="bold" if i == highlight else "normal")
    for k, (label, _) in enumerate(summary, start=1):
        ax.text(-0.1, n + k - 0.1, label, ha="right", va="center", fontsize=10, weight="bold", color=TEXT)
    if highlight is not None:
        ax.add_patch(plt.Rectangle((-label_width + 0.05, highlight + 0.04), label_width - 0.05 + len(BOX_COLUMNS), 0.92,
                                   facecolor="none", edgecolor=NAVY, linewidth=2, zorder=5))
    for b in breaks:
        ax.plot([-label_width + 0.05, len(BOX_COLUMNS)], [b, b], color=MUTED, linewidth=1, linestyle="--", zorder=4)

    plt.tight_layout(rect=(0, 0, 1, 0.95))
    fig.suptitle(title, x=0.02, ha="left", fontsize=14, weight="bold", color=TEXT)
    return fig, ax


def plot_box_table(df: pd.DataFrame, title: str, show: bool = True):
    """A colour-coded grid of box touches and penalties, for and against, one row per match.

    df is wyscout.data.season.season_box_table's output. Darker green is more
    for us, darker red more against us, and the difference column runs red to
    green around zero. Opponent labels are coloured by result; the last two
    rows are the season total and the per-game average.
    """
    df = df.assign(box_touches_diff=df["box_touches_for"] - df["box_touches_against"])
    columns = [c[0] for c in BOX_COLUMNS]
    fig, ax = _box_grid(
        df, title, df["label"], [RESULT_FG[r] for r in df["result"]],
        [("Total", df[columns].sum()), ("Per game", df[columns].mean())], decimals=0,
    )
    if show:
        plt.show()
    return fig, ax


def plot_league_box_table(
    df: pd.DataFrame,
    title: str,
    highlight_team_id: int | None = None,
    promotion_places: int = 1,
    playoff_places: int = 7,
    relegation_places: int = 4,
    show: bool = True,
):
    """The same grid for every club in the division, in league position order.

    df is wyscout.data.season.league_box_table's output. Box touches are per
    game, penalties season totals. Dashed lines mark the promotion, play-off
    and relegation places; highlight_team_id outlines one club. The bottom row
    is the league average.
    """
    df = df.sort_values("position").reset_index(drop=True)
    df = df.assign(box_touches_diff=df["box_touches_for"] - df["box_touches_against"])
    columns = [c[0] for c in BOX_COLUMNS]
    labels = [f"{r.position}. {r.team} ({r.points} pts)" for r in df.itertuples()]
    highlight = None
    if highlight_team_id is not None and (df["team_id"] == highlight_team_id).any():
        highlight = int(df.index[df["team_id"] == highlight_team_id][0])
    breaks = [b for b in (promotion_places, playoff_places, len(df) - relegation_places) if 0 < b < len(df)]
    fig, ax = _box_grid(
        df, title, labels, [TEXT] * len(df), [("League average", df[columns].mean())], decimals=1,
        highlight=highlight, breaks=breaks, label_width=3.4,
    )
    if show:
        plt.show()
    return fig, ax


# ── game states ──────────────────────────────────────────────────────────────


def plot_league_game_states(
    df: pd.DataFrame,
    title: str,
    highlight_team_id: int | None = None,
    promotion_places: int = 1,
    playoff_places: int = 7,
    relegation_places: int = 4,
    fig_size=(15, 11),
    show: bool = True,
):
    """Points dropped from winning positions (left) and won from losing positions (right), every club.

    df is wyscout.data.season.league_game_states's output. Clubs run in league
    position order; each bar is labelled with its wins, draws and losses out of
    the games the club was ahead or behind in. The column on the right is the
    net - points won from behind less points dropped from ahead. Dashed lines
    mark the promotion, play-off and relegation places; highlight_team_id
    shades one club's row.
    """
    df = df.sort_values("position").reset_index(drop=True)
    y = np.arange(len(df))
    dropped, won = df["points_dropped_from_ahead"], df["points_won_from_behind"]
    reach = max(dropped.max(), won.max(), 1)

    with sns.axes_style("white"):
        fig, ax = plt.subplots(figsize=fig_size, facecolor="white")
    ax.barh(y, -dropped, color=GA_COL, height=0.66, zorder=2, label="Points dropped from winning positions")
    ax.barh(y, won, color=GF_COL, height=0.66, zorder=2, label="Points won from losing positions")
    ax.axvline(0, color=TEXT, linewidth=1, zorder=3)

    pad = reach * 0.02
    for i, r in enumerate(df.itertuples()):
        if r.games_ahead:
            ax.text(-r.points_dropped_from_ahead - pad, i,
                    f"{r.points_dropped_from_ahead}  (D{r.draws_from_ahead} L{r.losses_from_ahead} of {r.games_ahead})",
                    ha="right", va="center", fontsize=8.5, color=GA_COL)
        if r.games_behind:
            ax.text(r.points_won_from_behind + pad, i,
                    f"{r.points_won_from_behind}  (W{r.wins_from_behind} D{r.draws_from_behind} of {r.games_behind})",
                    ha="left", va="center", fontsize=8.5, color=GF_COL)
        net = r.points_won_from_behind - r.points_dropped_from_ahead
        ax.text(1.01, i, f"{net:+d}" if net else "0", transform=ax.get_yaxis_transform(), ha="left", va="center", fontsize=9.5,
                fontweight="bold", color=GF_COL if net > 0 else GA_COL if net < 0 else MUTED)
    ax.text(1.01, -1, "Net", transform=ax.get_yaxis_transform(), ha="left", va="center", fontsize=9.5,
            fontweight="bold", color=TEXT)

    if highlight_team_id is not None and (df["team_id"] == highlight_team_id).any():
        row = int(df.index[df["team_id"] == highlight_team_id][0])
        ax.axhspan(row - 0.5, row + 0.5, color="#f3d98b", alpha=0.45, zorder=0)
    for b in (promotion_places, playoff_places, len(df) - relegation_places):
        if 0 < b < len(df):
            ax.axhline(b - 0.5, color=MUTED, linestyle="--", linewidth=0.8, zorder=1)

    ax.set_yticks(y)
    ax.set_yticklabels([f"{r.position}. {r.team} ({r.points} pts)" for r in df.itertuples()], fontsize=9.5,
                       color=TEXT)
    ax.set_ylim(len(df) - 0.4, -1.6)
    ax.set_xlim(-reach * 1.6, reach * 1.6)
    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    ax.xaxis.set_major_formatter(lambda v, pos: f"{abs(v):.0f}")
    ax.set_xlabel("Points dropped from winning positions    |    Points won from losing positions", color=MUTED)
    ax.grid(axis="x", color=GRID, zorder=0)
    sns.despine(ax=ax, left=True)
    ax.tick_params(axis="y", length=0)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.0), ncols=2, frameon=False, fontsize=9.5)
    ax.set_title(title, fontsize=15, fontweight="bold", color=TEXT, pad=12)
    plt.tight_layout()
    if show:
        plt.show()
    return fig, ax


# ── substitutions ────────────────────────────────────────────────────────────

# the score when a change was made - a diverging pair with a gray midpoint, checked for colour blindness
SUB_STATES = {"losing": "#c62828", "drawing": "#858585", "winning": "#1660c2"}
LABEL_DROP = 0.25  # club names and numbers sit low in the row, level with where the dots pile up


def plot_league_substitutions(
    df: pd.DataFrame,
    title: str,
    highlight_team_id: int | None = None,
    row_height: float = 0.8,
    show: bool = True,
):
    """When every club makes its changes, and the score when it does.

    df is wyscout.data.season.league_substitutions's output. Each club is a row
    on a 0-90 minute line and every substitution a dot, stacked at the minute
    it was made - so a triple change or a habit of changing at the break builds
    a tall pile. Dots are coloured by the score at the time (hollow when the
    match has no published events). Clubs run from the earliest average first
    change to the latest, marked with a triangle; the panel on top is the whole
    division by minute. On the right: changes per game, average first change,
    and the share made while losing.
    """
    first = df.groupby(["team_id", "match_id"])["minute"].min().groupby("team_id").mean()
    clubs = (
        df.groupby("team_id")
        .agg(team=("team", "first"), position=("position", "first"), games=("games", "first"), subs=("minute", "size"),
             losing=("state", lambda s: (s == "losing").sum()), known=("state", lambda s: s.notna().sum()))
        .assign(first=first)
        .sort_values(["first", "position"])
        .reset_index()
    )
    row_of = {t: i for i, t in enumerate(clubs["team_id"])}
    n = len(clubs)

    # within a stack: losing at the bottom, then drawing, winning on top, unknown last
    order = {state: k for k, state in enumerate(SUB_STATES)}
    subs = df.assign(rank=df["state"].map(order).fillna(len(order))).sort_values(["team_id", "minute", "rank"])
    subs["level"] = subs.groupby(["team_id", "minute"]).cumcount()
    tallest = int(subs["level"].max()) + 1

    header_h = 2.0
    fig = plt.figure(figsize=(16, header_h + 1.4 + n * row_height), facecolor="white")
    grid = gridspec.GridSpec(2, 1, height_ratios=[header_h, n * row_height], hspace=0.06, figure=fig,
                             left=0.17, right=0.80, top=1 - 0.9 / fig.get_figheight(), bottom=0.5 / fig.get_figheight())
    head = fig.add_subplot(grid[0])
    ax = fig.add_subplot(grid[1], sharex=head)

    # the division as a whole: changes at each minute, split by the score
    minutes = np.arange(1, 91)
    bottom = np.zeros(len(minutes))
    for state, colour in SUB_STATES.items():
        counts = df[df["state"] == state].groupby("minute").size().reindex(minutes, fill_value=0).to_numpy()
        head.bar(minutes, counts, bottom=bottom, width=0.8, color=colour, edgecolor="white", linewidth=0.6, zorder=2)
        bottom += counts
    head.set_ylabel("Changes,\nwhole league", color=MUTED, fontsize=9)
    head.yaxis.set_major_locator(ticker.MaxNLocator(4, integer=True))
    head.grid(axis="y", color=GRID, zorder=0)
    head.tick_params(axis="x", labelbottom=False, length=0)
    head.tick_params(axis="y", labelsize=8.5, colors=MUTED, length=0)
    sns.despine(ax=head, left=True, bottom=True)
    peak = bottom.max()
    for minute, label in ((45.5, "half time"), (90, "added time")):
        head.text(minute, peak * 1.04, label, ha="center", va="bottom", fontsize=8.5, color=MUTED)
    head.set_ylim(0, peak * 1.3)

    # one row per club: a dot per change, stacked by minute
    pitch = 0.88 / tallest  # stack step in row units
    # diameter in points: a touch more than the step, so a stack reads as a column, but narrower than a minute
    dot = min(row_height * pitch * 1.1, 11.5 / 92 * 0.85) * 72
    y = subs["team_id"].map(row_of) + 0.44 - subs["level"] * pitch - pitch / 2
    colours = subs["state"].map(SUB_STATES)
    known = colours.notna()
    ax.scatter(subs["minute"][known], y[known], s=dot ** 2, c=colours[known], edgecolors="white", linewidths=0.6,
               zorder=3)
    ax.scatter(subs["minute"][~known], y[~known], s=dot ** 2, facecolors="white", edgecolors=MUTED, linewidths=0.8,
               zorder=3)

    for i, r in clubs.iterrows():
        ax.plot([1, 90], [i + 0.44, i + 0.44], color=GRID, linewidth=0.8, zorder=1)
        ax.scatter(r["first"], i + 0.47, marker="^", s=34, color=TEXT, edgecolors="white", linewidths=0.6, zorder=4)
    league_first = first.mean()
    for a in (head, ax):
        a.axvline(league_first, color=TEXT, linestyle=":", linewidth=0.9, zorder=1)
    head.text(league_first + 0.6, peak * 1.04, f"league average\nfirst change {league_first:.0f}'", ha="left",
              va="bottom", fontsize=8.5, color=TEXT)

    for a in (head, ax):
        a.axvspan(44.5, 46.5, color="#eef1f4", zorder=0)
    if highlight_team_id in row_of:
        row = row_of[highlight_team_id]
        ax.axhspan(row - 0.5, row + 0.5, color="#f3d98b", alpha=0.45, zorder=0)

    # numbers on the right
    columns = (("Changes\nper game", 1.03), ("Average\n1st change", 1.12), ("Made while\nlosing", 1.21))
    for label, x in columns:
        ax.text(x, -0.75, label, transform=ax.get_yaxis_transform(), ha="center", va="bottom", fontsize=9,
                fontweight="bold", color=TEXT)
    for i, r in clubs.iterrows():
        values = (f"{r['subs'] / r['games']:.1f}", f"{r['first']:.0f}'",
                  f"{r['losing'] / r['known']:.0%}" if r["known"] else "-")
        for (_, x), value in zip(columns, values):
            ax.text(x, i + LABEL_DROP, value, transform=ax.get_yaxis_transform(), ha="center", va="center", fontsize=9.5,
                    color=TEXT)

    ax.set_yticks(np.arange(n) + LABEL_DROP)
    ax.set_yticklabels([f"{r.team}  ({ordinal(r.position)})" for r in clubs.itertuples()], fontsize=10, color=TEXT)
    ax.set_ylim(n - 0.5, -0.5)
    ax.set_xlim(0, 92)
    ax.set_xticks([1, 15, 30, 45, 60, 75, 90])
    ax.set_xticklabels(["1'", "15'", "30'", "45'", "60'", "75'", "90+'"], fontsize=9, color=MUTED)
    ax.tick_params(axis="both", length=0)
    sns.despine(ax=ax, left=True, bottom=True)
    ax.set_xlabel("Minute of the change (each half counts as 45 - added time sits at 45 and 90)", color=MUTED,
                  fontsize=9)

    handles = [Line2D([], [], marker="o", linestyle="", markersize=8, markerfacecolor=c, markeredgecolor="white",
                      label=f"Change made while {s}") for s, c in reversed(SUB_STATES.items())]
    handles.append(Line2D([], [], marker="^", linestyle="", markersize=7, color=TEXT,
                          label="Club's average first change"))
    if (~known).any():
        handles.append(Line2D([], [], marker="o", linestyle="", markersize=8, markerfacecolor="white",
                              markeredgecolor=MUTED, label="No events published"))
    head.legend(handles=handles, loc="lower left", bbox_to_anchor=(0, 1.08), ncols=len(handles), frameon=False,
                fontsize=9.5, handletextpad=0.3, columnspacing=1.4)
    fig.suptitle(title, x=0.17, ha="left", fontsize=16, fontweight="bold", color=TEXT,
                 y=1 - 0.25 / fig.get_figheight())
    if show:
        plt.show()
    return fig, ax


# ── set pieces ───────────────────────────────────────────────────────────────

# set-piece kind -> (label, bar alpha) for the stacked xG split
SET_PIECE_STYLE = {"corner": ("corners", 0.3), "free_kick": ("free kicks", 0.55), "penalty": ("penalties", 0.85)}


def plot_league_set_pieces(
    df: pd.DataFrame,
    title: str,
    name: str = "set pieces",
    taken_label: str = "Set pieces",
    highlight_team_id: int | None = None,
    per_game: bool = False,
    fig_size=(20, 11),
    show: bool = True,
):
    """Goals and xG from set pieces for (left) and against (right) every club, each panel ranked by xG.

    df is wyscout.data.season.league_set_piece_table's output (or
    league_corner_table's). Bars are xG - stacked by kind, darker for free
    kicks and penalties, when df splits it - and the diamonds goals; per_game
    draws and ranks by the per-game averages instead of season totals. The
    columns on each row give totals and per-game averages, and the set pieces
    taken or faced (taken_label heads that column). name goes in the panel
    titles. highlight_team_id shades and bolds one club's row in both panels;
    the dashed line is the league average.
    """
    suffix = "_per_game" if per_game else ""
    kinds = [k for k in SET_PIECE_STYLE if f"xg_for_{k}" in df]
    with sns.axes_style("white"):
        fig, axes = plt.subplots(1, 2, figsize=fig_size, facecolor="white")

    reach = max(df[[f"{s}_{side}{suffix}" for s in ("xg", "goals") for side in ("for", "against")]].max())
    for ax, side, colour, heading in (
        (axes[0], "for", GF_COL, f"Created from our {name}"),
        (axes[1], "against", GA_COL, f"Conceded from the opposition's {name}"),
    ):
        ranked = df.sort_values([f"xg_{side}{suffix}", f"goals_{side}{suffix}"], ascending=False).reset_index(drop=True)
        y = np.arange(len(ranked))
        if kinds:
            left = np.zeros(len(ranked))
            for kind in kinds:
                label, alpha = SET_PIECE_STYLE[kind]
                xg = ranked[f"xg_{side}_{kind}"] / (ranked["games"] if per_game else 1)
                ax.barh(y, xg, left=left, color=colour, alpha=alpha, height=0.7, zorder=2, label=f"xG - {label}")
                left += xg
        else:
            ax.barh(y, ranked[f"xg_{side}{suffix}"], color=colour, alpha=0.35, height=0.7, zorder=2, label="xG")
        ax.scatter(ranked[f"goals_{side}{suffix}"], y, marker="D", s=46, color=colour, edgecolor="white",
                   linewidth=0.8, zorder=4, label="Goals")
        ax.axvline(df[f"xg_{side}{suffix}"].mean(), color=MUTED, linestyle="--", linewidth=0.9, zorder=3,
                   label="League average xG")

        columns = [  # (axes-fraction x, header, value template filled from the row)
            (1.06, "Goals", "{goals}"),
            (1.18, "xG", "{xg:.2f}"),
            (1.31, "Goals\n/ game", "{goals_per_game:.2f}"),
            (1.44, "xG\n/ game", "{xg_per_game:.2f}"),
            (1.58, f"{taken_label}\n(/ game)", "{taken} ({taken_per_game:.1f})"),
        ]
        to_axes = ax.get_yaxis_transform()
        for x, header, _ in columns:
            ax.text(x, -1, header, transform=to_axes, ha="center", va="center", fontsize=8.5, fontweight="bold",
                    color=MUTED)
        for i, r in ranked.iterrows():
            highlight = r["team_id"] == highlight_team_id
            values = {stat: r[f"{stat}_{side}"] for stat in ("goals", "xg", "taken")}
            values |= {f"{stat}_per_game": r[f"{stat}_{side}_per_game"] for stat in ("goals", "xg", "taken")}
            for x, _, template in columns:
                ax.text(x, i, template.format(**values), transform=to_axes, ha="center", va="center", fontsize=9, color=TEXT,
                        fontweight="bold" if highlight else "normal")
            if highlight:
                ax.axhspan(i - 0.5, i + 0.5, xmax=1.66, color="#f3d98b", alpha=0.45, zorder=0, clip_on=False)

        ax.set_yticks(y)
        ax.set_yticklabels([f"{r.position}. {r.team}" for r in ranked.itertuples()], fontsize=9.5, color=TEXT)
        ax.set_ylim(len(ranked) - 0.4, -1.6)
        ax.set_xlim(-reach * 0.03, reach * 1.06)
        ax.set_xlabel("Per game" if per_game else "Season total", color=MUTED)
        ax.grid(axis="x", color=GRID, zorder=0)
        sns.despine(ax=ax, left=True)
        ax.tick_params(axis="y", length=0)
        ax.set_title(heading, fontsize=12, fontweight="bold", color=colour, loc="left")
        ax.legend(loc="lower right", frameon=False, fontsize=9)

    fig.suptitle(title, fontsize=15, fontweight="bold", color=TEXT)
    fig.subplots_adjust(left=0.1, right=0.83, wspace=1.15, top=0.9, bottom=0.07)
    if show:
        plt.show()
    return fig, axes


# ── pressing ─────────────────────────────────────────────────────────────────

PRESS_BG, PRESS_PANEL = "#0f1117", "#161b22"
PRESS_HOT = "#ff6b3d"  # a hard press
PRESS_TEXT, PRESS_MUTED, PRESS_GRID = "#e6edf3", "#8b949e", "#262c36"
PRESS_RESULT = {"W": "#3fb950", "D": "#d29922", "L": "#da3633"}


def ordinal(n: int) -> str:
    """1 -> "1st", 22 -> "22nd"."""
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


@lru_cache(maxsize=64)
def _badge(url: str, size: int = 64) -> np.ndarray | None:
    """A club badge as an RGBA array, size pixels on its longer side, or None if it cannot be loaded."""
    try:
        image = load_image(url).convert("RGBA")
    except (OSError, ValueError):  # a missing badge should never stop the chart
        return None
    image.thumbnail((size, size))
    return np.asarray(image)


def _place_badge(ax: plt.Axes, url: str | None, xy: tuple[float, float], zoom: float, zorder: int = 6,
                 xycoords="data") -> bool:
    badge = _badge(url) if url else None
    if badge is None:
        return False
    ax.add_artist(AnnotationBbox(OffsetImage(badge, zoom=zoom), xy, xycoords=xycoords, frameon=False,
                                 zorder=zorder))
    return True


def plot_ppda_trend(
    df: pd.DataFrame,
    title: str,
    league: pd.Series | None = None,
    badges: dict[int, str] | None = None,
    colour: str = "#4ea1ff",
    fig_size=(17, 10),
    show: bool = True,
):
    """The pressing battle, match by match.

    df is wyscout.data.season.season_ppda_table's output. The y axis is
    upside down so a harder press (lower PPDA) sits higher, over a background
    that glows hotter towards the top. Each match is a vertical "tug of war"
    between our PPDA (the glowing dot) and the opposition's PPDA against us
    (their badge): green when we pressed harder, red when they did. The thick
    line is our three-game rolling average. league is every club's PPDA in
    every match, drawn as the league average and its middle 50% band;
    badges is {team_id: image URL}. The strip underneath is the results.
    """
    badges = badges or {}
    x = df["game"].to_numpy()
    ours, theirs = df["ppda"].to_numpy(), df["oppo_ppda"].to_numpy()
    rolling = df["ppda"].rolling(3, min_periods=1).mean().to_numpy()
    top = max(ours.max(), theirs.max(), league.quantile(0.95) if league is not None else 0) * 1.12
    left, right = x.min() - 0.7, x.max() + 2.2

    fig, (ax, strip) = plt.subplots(2, 1, figsize=fig_size, sharex=True,
                                    gridspec_kw={"height_ratios": [9, 1], "hspace": 0.04})
    fig.patch.set_facecolor(PRESS_BG)
    for a in (ax, strip):
        a.set_facecolor(PRESS_PANEL)
        for spine in a.spines.values():
            spine.set_visible(False)

    # the heat: hottest at PPDA 0, fading out by the bottom of the axis
    heat = LinearSegmentedColormap.from_list("press", [PRESS_PANEL, "#4a1a12"])
    ax.imshow(np.linspace(1, 0, 256)[:, np.newaxis] ** 1.6, cmap=heat, aspect="auto", origin="lower",
              extent=(left, right, 0, top), zorder=0, interpolation="bicubic")

    if league is not None:
        q1, q3, mean = league.quantile(0.25), league.quantile(0.75), league.mean()
        ax.axhspan(q1, q3, color="white", alpha=0.05, zorder=1, lw=0)
        ax.axhline(mean, color=PRESS_MUTED, linestyle=(0, (6, 4)), linewidth=1.2, zorder=2)

    # the tug of war in each match
    for xi, us, them in zip(x, ours, theirs):
        won = us < them
        ax.plot([xi, xi], [us, them], color=PRESS_RESULT["W" if won else "L"], linewidth=3, alpha=0.55,
                solid_capstyle="round", zorder=3)

    ax.plot(x, rolling, color=colour, linewidth=6, alpha=0.18, zorder=4, solid_capstyle="round")
    ax.plot(x, rolling, color=colour, linewidth=2.2, alpha=0.9, zorder=4, solid_capstyle="round")

    for size, alpha in ((900, 0.06), (480, 0.12), (220, 0.25)):  # a soft glow behind each dot
        ax.scatter(x, ours, s=size, color=colour, alpha=alpha, lw=0, zorder=5)
    ax.scatter(x, ours, s=110, color=colour, edgecolor="white", linewidth=1.4, zorder=7)
    for xi, us, them in zip(x, ours, theirs):
        ax.annotate(f"{us:.1f}", (xi, us), xytext=(0, 14 if us < them else -14), textcoords="offset points",
                    ha="center", va="center", fontsize=10, fontweight="bold", color=PRESS_TEXT, zorder=7)

    for r in df.itertuples():
        if not _place_badge(ax, badges.get(r.opponent_id), (r.game, r.oppo_ppda), zoom=0.42):
            ax.scatter(r.game, r.oppo_ppda, s=140, facecolor=PRESS_PANEL, edgecolor=PRESS_MUTED, linewidth=1.5,
                       zorder=6)
        ax.annotate(f"{r.oppo_ppda:.1f}", (r.game, r.oppo_ppda), xytext=(0, -20 if r.ppda < r.oppo_ppda else 20),
                    textcoords="offset points", ha="center", va="center", fontsize=8.5, color=PRESS_MUTED, zorder=7)

    # season averages, at the right-hand end
    averages = [(ours.mean(), "Us", colour), (theirs.mean(), "Opponents", PRESS_MUTED)]
    if league is not None:
        averages.append((league.mean(), "League", "#c0c7d0"))
    for value, label, col in averages:
        ax.annotate(f"{label} {value:.1f}", (x.max() + 0.6, value), ha="left", va="center", fontsize=10.5,
                    fontweight="bold", color=col, zorder=7,
                    bbox={"boxstyle": "square,pad=0.15", "facecolor": PRESS_PANEL, "edgecolor": "none", "alpha": 0.8})
        ax.plot([x.max() + 0.35, x.max() + 0.55], [value, value], color=col, linewidth=2.5)

    ax.set_xlim(left, right)
    ax.set_ylim(top, 0)
    ax.tick_params(axis="y", colors=PRESS_MUTED, labelsize=9)
    ax.tick_params(axis="x", length=0)
    ax.yaxis.grid(True, color=PRESS_GRID, linewidth=0.8, linestyle="--", zorder=1)
    ax.set_axisbelow(True)
    ax.set_ylabel("PPDA  -  passes allowed per defensive action", fontsize=11, color=PRESS_MUTED, labelpad=10)
    ax.text(left + 0.1, top * 0.03, "▲ HARDER PRESS", fontsize=10, fontweight="bold", color=PRESS_HOT,
            va="top", alpha=0.9)
    ax.text(left + 0.1, top * 0.97, "▼ SITTING OFF", fontsize=10, fontweight="bold", color="#6e8fb5",
            va="bottom", alpha=0.9)
    ax.legend(
        handles=[
            Line2D([], [], marker="o", linestyle="", markersize=9, color=colour, markeredgecolor="white",
                   label="Our PPDA"),
            Line2D([], [], marker="o", linestyle="", markersize=9, markerfacecolor=PRESS_PANEL,
                   markeredgecolor=PRESS_MUTED, label="Opponent's PPDA (badge)"),
            Line2D([], [], color=colour, linewidth=2.2, label="Our 3-game average"),
            Line2D([], [], color=PRESS_RESULT["W"], linewidth=3, alpha=0.7, label="We pressed harder"),
            Line2D([], [], color=PRESS_RESULT["L"], linewidth=3, alpha=0.7, label="They pressed harder"),
        ],
        loc="lower left", bbox_to_anchor=(0.0, 1.0), ncol=5, frameon=False, labelcolor=PRESS_TEXT, fontsize=9.5,
    )

    strip.set_ylim(0, 1)
    strip.set_yticks([])
    for r in df.itertuples():
        strip.add_patch(plt.Rectangle((r.game - 0.42, 0.12), 0.84, 0.76, color=PRESS_RESULT[r.result], alpha=0.85,
                                      lw=0))
        strip.text(r.game, 0.5, f"{r.result} {r.score}", ha="center", va="center", fontsize=9, fontweight="bold",
                   color=PRESS_BG)
    strip.set_xticks(x)
    strip.set_xticklabels(df["short_label"], rotation=90, fontsize=8.5, color=PRESS_MUTED)
    strip.tick_params(axis="x", length=0)

    fig.suptitle(title, x=0.06, ha="left", fontsize=17, color=PRESS_TEXT, fontweight="bold", y=0.985)
    fig.text(0.06, 0.935, "Lower PPDA = fewer passes allowed before we win the ball back = a more aggressive press. "
             "Each line is the pressing battle in one match; the pale band is the middle half of the league.", fontsize=10.5, color=PRESS_MUTED)
    fig.subplots_adjust(left=0.06, right=0.98, top=0.87, bottom=0.13)
    if show:
        plt.show()
    return fig, (ax, strip)


def plot_league_ppda_table(
    df: pd.DataFrame,
    by_match: pd.DataFrame,
    title: str,
    highlight_team_id: int | None = None,
    sort_by: str = "ppda",
    show: bool = True,
):
    """The pressing ladder: every club ranked by season PPDA, hardest press at the top.

    df is wyscout.data.season.league_ppda_table's output and by_match
    league_ppda_by_match's. Columns are the rank, badge and club (with league
    position), the average PPDA as a heat-coloured cell, every match as a dot
    on a shared strip (the diamond is the average, the dashed line the league
    average), how hard opponents pressed them, and the dominance - PPDA
    faced minus PPDA, green where the club pressed harder than it was
    pressed. sort_by="dominance" ranks by that instead. highlight_team_id
    outlines one club.
    """
    df = df.sort_values(sort_by, ascending=sort_by == "ppda").reset_index(drop=True)
    n = len(df)
    league_mean = by_match["ppda"].mean()
    hot = LinearSegmentedColormap.from_list("press", ["#b71c1c", "#ef6c00", "#ffcc80", "#eef1f4", "#90caf9"])
    lo, hi = df["ppda"].min(), df["ppda"].max()
    faced_lo, faced_hi = df["ppda_faced"].min(), df["ppda_faced"].max()

    # column layout, in data units
    rank_x, badge_x, name_x = 0.35, 0.95, 1.35
    ppda_x0, ppda_w = 5.0, 1.1
    strip_x0, strip_w = 6.4, 5.2
    faced_x0, faced_w = 11.9, 1.1
    dom_x0, dom_w = 13.15, 1.1
    width = dom_x0 + dom_w + 0.1
    dom_limit = max(df["dominance"].abs().max(), 1)
    strip_max = np.ceil(max(by_match["ppda"].max(), 1) / 5) * 5

    def strip_pos(v):
        return strip_x0 + 0.15 + (strip_w - 0.3) * min(v, strip_max) / strip_max

    fig, ax = plt.subplots(figsize=(14, 1.6 + 0.42 * (n + 2)))
    ax.set_xlim(0, width)
    ax.set_ylim(n + 1.3, -1.5)
    ax.axis("off")

    headers = [(rank_x, "#"), (name_x, "Club (league position)"), (ppda_x0 + ppda_w / 2, "Average\nPPDA"),
               (strip_x0 + strip_w / 2, "Every match"), (faced_x0 + faced_w / 2, "PPDA\nfaced"),
               (dom_x0 + dom_w / 2, "Dominance\n(faced - own)")]
    for hx, label in headers:
        ax.text(hx, -0.7, label, ha="left" if hx == name_x else "center", va="center", fontsize=10.5,
                weight="bold", color=TEXT)

    # strip scale and league average across the whole column
    for tick in range(0, int(strip_max) + 1, 5):
        tx = strip_pos(tick)
        ax.plot([tx, tx], [-0.05, n + 0.05], color=GRID, linewidth=0.8, zorder=1)
        ax.text(tx, n + 0.35, f"{tick}", ha="center", va="center", fontsize=8, color=MUTED)
    mean_x = strip_pos(league_mean)
    ax.plot([mean_x, mean_x], [-0.15, n + 0.05], color=MUTED, linestyle=(0, (4, 3)), linewidth=1.2, zorder=2)
    ax.text(mean_x, -0.2, f"league {league_mean:.1f}", ha="center", va="bottom", fontsize=8, color=MUTED)
    ax.text(strip_x0 + 0.15, n + 0.75, "◀ harder press", ha="left", va="center", fontsize=8.5, color="#b71c1c")
    ax.text(strip_x0 + strip_w - 0.15, n + 0.75, "sitting off ▶", ha="right", va="center", fontsize=8.5,
            color="#1565c0")

    for i, r in df.iterrows():
        mine = r.team_id == highlight_team_id
        if i % 2 == 0 or mine:
            ax.add_patch(plt.Rectangle((0.05, i), width - 0.1, 1, facecolor="#e8f0fb" if mine else "#f6f8fa",
                                       edgecolor="none", zorder=0))
        ax.text(rank_x, i + 0.5, f"{i + 1}", ha="center", va="center", fontsize=11, weight="bold",
                color=NAVY if mine else MUTED)
        _place_badge(ax, r.badge, (badge_x, i + 0.5), zoom=0.28, zorder=3)
        ax.text(name_x, i + 0.5, f"{r.team}  ({ordinal(r.position)})", ha="left", va="center", fontsize=10.5,
                color=NAVY if mine else TEXT, weight="bold" if mine else "normal")

        norm = (r.ppda - lo) / (hi - lo) if hi > lo else 0.5
        cell = hot(norm)
        ax.add_patch(plt.Rectangle((ppda_x0, i + 0.08), ppda_w, 0.84, facecolor=cell, edgecolor="white", lw=1.5))
        ax.text(ppda_x0 + ppda_w / 2, i + 0.5, f"{r.ppda:.1f}", ha="center", va="center", fontsize=11,
                weight="bold", color="white" if norm < 0.3 else TEXT)

        games = by_match.loc[by_match["team_id"] == r.team_id, "ppda"]
        jitter = np.random.default_rng(int(r.team_id)).uniform(-0.18, 0.18, len(games))
        ax.plot([strip_pos(r.best), strip_pos(r.worst)], [i + 0.5, i + 0.5], color=GRID, linewidth=5,
                solid_capstyle="round", zorder=2)
        ax.scatter([strip_pos(v) for v in games], i + 0.5 + jitter, s=22,
                   c=[hot((min(max(v, lo), hi) - lo) / (hi - lo) if hi > lo else 0.5) for v in games],
                   edgecolor="white", linewidth=0.5, alpha=0.9, zorder=3)
        ax.scatter(strip_pos(r.ppda), i + 0.5, s=110, marker="D", color=NAVY if mine else TEXT,
                   edgecolor="white", linewidth=1.2, zorder=4)

        faced_norm = (r.ppda_faced - faced_lo) / (faced_hi - faced_lo) if faced_hi > faced_lo else 0.5
        ax.add_patch(plt.Rectangle((faced_x0, i + 0.08), faced_w, 0.84, facecolor=plt.get_cmap("Purples_r")(
            0.25 + faced_norm * 0.7), edgecolor="white", lw=1.5))
        ax.text(faced_x0 + faced_w / 2, i + 0.5, f"{r.ppda_faced:.1f}", ha="center", va="center", fontsize=10.5,
                color="white" if faced_norm < 0.35 else TEXT)

        dom_norm = 0.5 + r.dominance / dom_limit / 2
        ax.add_patch(plt.Rectangle((dom_x0, i + 0.08), dom_w, 0.84, facecolor=plt.get_cmap("RdYlGn")(
            0.1 + dom_norm * 0.8), edgecolor="white", lw=1.5))
        ax.text(dom_x0 + dom_w / 2, i + 0.5, f"{round(r.dominance, 1) + 0.0:+.1f}", ha="center", va="center", fontsize=10.5,
                weight="bold", color="white" if abs(dom_norm - 0.5) > 0.35 else TEXT)

        if mine:
            ax.add_patch(plt.Rectangle((0.05, i + 0.03), width - 0.1, 0.94, facecolor="none", edgecolor=NAVY,
                                       linewidth=2, zorder=5))

    ax.text(name_x, n + 0.35, f"Games with stats: {df['games'].min()}-{df['games'].max()} per club",
            ha="left", va="center", fontsize=8.5, color=MUTED)

    fig.suptitle(title, x=0.02, ha="left", fontsize=15, weight="bold", color=TEXT, y=0.995)
    fig.text(0.02, 0.968 - 0.2 / fig.get_size_inches()[1],
             ("Ranked by average PPDA, hardest press first. " if sort_by == "ppda" else "Ranked by dominance. ")
             + "PPDA faced: how hard opponents pressed them - lower means they were pressed more.\n"
             "Dominance: PPDA faced minus own PPDA - above zero, they pressed harder than they were pressed "
             "(opponents sat off them).", fontsize=10, color=MUTED, va="top")
    fig.subplots_adjust(left=0.01, right=0.99, top=0.93, bottom=0.01)
    if show:
        plt.show()
    return fig, ax


def plot_league_field_tilt_table(
    df: pd.DataFrame,
    by_match: pd.DataFrame,
    title: str,
    highlight_team_id: int | None = None,
    sort_by: str = "tilt",
    state_min_passes: int = 60,
    show: bool = True,
):
    """The territory ladder: every club ranked by season field tilt, most territory at the top.

    df is wyscout.data.season.league_field_tilt_table's output and by_match
    league_field_tilt_by_match's. Columns are the rank, badge and club (with
    league position), the average tilt as a cell coloured either side of
    50%, every match as a dot on a 0-100% strip (the diamond is the average),
    the tilt while losing, level and winning (faded where fewer than
    state_min_passes final-third passes sit behind it), the average possession, and tilt minus possession - green where the club
    gets more territory than its share of the ball. sort_by="tilt_vs_possession"
    ranks by that instead. highlight_team_id outlines one club.
    """
    df = df.sort_values(sort_by, ascending=False).reset_index(drop=True)
    n = len(df)
    # tilt is zero-sum, so 50% is the league average by construction
    tilt_cmap = LinearSegmentedColormap.from_list("tilt", ["#1565c0", "#90caf9", "#eef1f4", "#ffab91", "#c62828"])
    edge_cmap = LinearSegmentedColormap.from_list("edge", ["#c2185b", "#f8bbd0", "#eef1f4", "#a5d6a7", "#2e7d32"])
    tilt_limit = max((df["tilt"] - 50).abs().max(), 1)
    pos_lo, pos_hi = df["possession"].min(), df["possession"].max()

    def tilt_norm(v):
        return 0.5 + np.clip((v - 50) / tilt_limit, -1, 1) / 2

    # column layout, in data units
    rank_x, badge_x, name_x = 0.35, 0.95, 1.35
    tilt_x0, tilt_w = 5.0, 1.1
    strip_x0, strip_w = 6.4, 5.2
    state_x0, state_w = 11.9, 1.05
    pos_x0, pos_w = state_x0 + 3 * state_w + 0.25, 1.1
    edge_x0, edge_w = pos_x0 + pos_w + 0.15, 1.1
    width = edge_x0 + edge_w + 0.1
    edge_limit = max(df["tilt_vs_possession"].abs().max(), 1)

    def strip_pos(v):
        return strip_x0 + 0.15 + (strip_w - 0.3) * v / 100

    fig, ax = plt.subplots(figsize=(14 * width / 14.35, 1.6 + 0.42 * (n + 2)))
    ax.set_xlim(0, width)
    ax.set_ylim(n + 1.3, -1.5)
    ax.axis("off")

    states = [("losing", "When\nlosing"), ("level", "When\nlevel"), ("winning", "When\nwinning")]
    headers = [(rank_x, "#"), (name_x, "Club (league position)"), (tilt_x0 + tilt_w / 2, "Average\nfield tilt"),
               (strip_x0 + strip_w / 2, "Every match"),
               *[(state_x0 + (k + 0.5) * state_w, label) for k, (_, label) in enumerate(states)],
               (pos_x0 + pos_w / 2, "Average\npossession"),
               (edge_x0 + edge_w / 2, "Tilt minus\npossession")]
    for hx, label in headers:
        ax.text(hx, -0.7, label, ha="left" if hx == name_x else "center", va="center", fontsize=10.5,
                weight="bold", color=TEXT)

    # strip scale and the even-split line across the whole column
    for tick in range(0, 101, 25):
        tx = strip_pos(tick)
        ax.plot([tx, tx], [-0.05, n + 0.05], color=GRID, linewidth=0.8, zorder=1)
        ax.text(tx, n + 0.35, f"{tick}%", ha="center", va="center", fontsize=8, color=MUTED)
    mid_x = strip_pos(50)
    ax.plot([mid_x, mid_x], [-0.15, n + 0.05], color=MUTED, linestyle=(0, (4, 3)), linewidth=1.2, zorder=2)
    ax.text(mid_x, -0.2, "even split", ha="center", va="bottom", fontsize=8, color=MUTED)
    ax.text(strip_x0 + 0.15, n + 0.75, "◀ pinned back", ha="left", va="center", fontsize=8.5, color="#1565c0")
    ax.text(strip_x0 + strip_w - 0.15, n + 0.75, "camped in their third ▶", ha="right", va="center", fontsize=8.5,
            color="#c62828")

    for i, r in df.iterrows():
        mine = r.team_id == highlight_team_id
        if i % 2 == 0 or mine:
            ax.add_patch(plt.Rectangle((0.05, i), width - 0.1, 1, facecolor="#e8f0fb" if mine else "#f6f8fa",
                                       edgecolor="none", zorder=0))
        ax.text(rank_x, i + 0.5, f"{i + 1}", ha="center", va="center", fontsize=11, weight="bold",
                color=NAVY if mine else MUTED)
        _place_badge(ax, r.badge, (badge_x, i + 0.5), zoom=0.28, zorder=3)
        ax.text(name_x, i + 0.5, f"{r.team}  ({ordinal(r.position)})", ha="left", va="center", fontsize=10.5,
                color=NAVY if mine else TEXT, weight="bold" if mine else "normal")

        norm = tilt_norm(r.tilt)
        ax.add_patch(plt.Rectangle((tilt_x0, i + 0.08), tilt_w, 0.84, facecolor=tilt_cmap(norm), edgecolor="white",
                                   lw=1.5))
        ax.text(tilt_x0 + tilt_w / 2, i + 0.5, f"{r.tilt:.1f}%", ha="center", va="center", fontsize=11,
                weight="bold", color="white" if abs(norm - 0.5) > 0.35 else TEXT)

        games = by_match.loc[by_match["team_id"] == r.team_id, "tilt"]
        jitter = np.random.default_rng(int(r.team_id)).uniform(-0.18, 0.18, len(games))
        ax.plot([strip_pos(r.worst), strip_pos(r.best)], [i + 0.5, i + 0.5], color=GRID, linewidth=5,
                solid_capstyle="round", zorder=2)
        ax.scatter([strip_pos(v) for v in games], i + 0.5 + jitter, s=22, c=[tilt_cmap(tilt_norm(v)) for v in games],
                   edgecolor="white", linewidth=0.5, alpha=0.9, zorder=3)
        ax.scatter(strip_pos(r.tilt), i + 0.5, s=110, marker="D", color=NAVY if mine else TEXT,
                   edgecolor="white", linewidth=1.2, zorder=4)

        for k, (state, _) in enumerate(states):
            value, sample = r[f"tilt_{state}"], r[f"passes_{state}"]
            x0 = state_x0 + k * state_w
            if np.isnan(value):
                ax.text(x0 + state_w / 2, i + 0.5, "-", ha="center", va="center", fontsize=10.5, color=MUTED)
                continue
            thin = sample < state_min_passes
            s_norm = tilt_norm(value)
            ax.add_patch(plt.Rectangle((x0 + 0.03, i + 0.08), state_w - 0.06, 0.84, facecolor=tilt_cmap(s_norm),
                                       alpha=0.35 if thin else 1, edgecolor="white", lw=1.5))
            ax.text(x0 + state_w / 2, i + 0.5, f"{value:.0f}%", ha="center", va="center", fontsize=10.5,
                    style="italic" if thin else "normal", color=MUTED if thin else
                    "white" if abs(s_norm - 0.5) > 0.35 else TEXT)

        pos_norm = (r.possession - pos_lo) / (pos_hi - pos_lo) if pos_hi > pos_lo else 0.5
        ax.add_patch(plt.Rectangle((pos_x0, i + 0.08), pos_w, 0.84, facecolor=plt.get_cmap("Purples")(
            0.15 + pos_norm * 0.7), edgecolor="white", lw=1.5))
        ax.text(pos_x0 + pos_w / 2, i + 0.5, f"{r.possession:.1f}%", ha="center", va="center", fontsize=10.5,
                color="white" if pos_norm > 0.65 else TEXT)

        edge_norm = 0.5 + r.tilt_vs_possession / edge_limit / 2
        ax.add_patch(plt.Rectangle((edge_x0, i + 0.08), edge_w, 0.84, facecolor=edge_cmap(edge_norm),
                                   edgecolor="white", lw=1.5))
        ax.text(edge_x0 + edge_w / 2, i + 0.5, f"{round(r.tilt_vs_possession, 1) + 0.0:+.1f}", ha="center",
                va="center", fontsize=10.5, weight="bold", color="white" if abs(edge_norm - 0.5) > 0.35 else TEXT)

        if mine:
            ax.add_patch(plt.Rectangle((0.05, i + 0.03), width - 0.1, 0.94, facecolor="none", edgecolor=NAVY,
                                       linewidth=2, zorder=5))

    ax.text(name_x, n + 0.35, f"Games with events: {df['games'].min()}-{df['games'].max()} per club",
            ha="left", va="center", fontsize=8.5, color=MUTED)
    ax.text(state_x0 + 1.5 * state_w, n + 0.35, f"faded: under {state_min_passes} passes in that state",
            ha="center", va="center", fontsize=8, color=MUTED)

    fig.suptitle(title, x=0.02, ha="left", fontsize=15, weight="bold", color=TEXT, y=0.995)
    fig.text(0.02, 0.968 - 0.2 / fig.get_size_inches()[1],
             ("Ranked by average field tilt. " if sort_by == "tilt" else
              f"Ranked by tilt when {sort_by.removeprefix('tilt_')}. " if sort_by.startswith("tilt_") and
              sort_by != "tilt_vs_possession" else "Ranked by tilt minus possession. ")
             + "Field tilt: a club's share of the completed passes both sides made in their attacking third.\n"
             "When losing / level / winning: the same share, using only the passes made in that score state. "
             "Tilt minus possession: above zero, they get more territory than their share of the ball.",
             fontsize=10, color=MUTED, va="top")
    fig.subplots_adjust(left=0.01, right=0.99, top=0.93, bottom=0.01)
    if show:
        plt.show()
    return fig, ax


TILT_FOR = NAVY
TILT_AGAINST = "#d84343"
OPPO_SUB_COL = "#9aa5b1"
PPDA_COL = "#f2a900"  # amber reads on both the navy and the red fills
PPDA_MAX = 25  # top of the inverted PPDA axis; a quieter spell is clipped to it


def _surname(name: str) -> str:
    return name.split(". ", 1)[-1] if ". " in name else name.split(" ")[-1]


def add_changes_to_timeline(ax: plt.Axes, changes: pd.DataFrame, names: bool = True) -> None:
    """Mark the substitutions on a field tilt timeline panel.

    changes is wyscout.data.substitutions.match_changes' "changes". Our changes
    hang from the top edge as navy triangles with a faint dashed line down the
    panel and the players brought on named beside them; the opposition's sit
    on the bottom edge as gray triangles.
    """
    last_x, drop, prev = -99.0, 0.0, []
    for _, c in changes.sort_values("x").iterrows():
        if c["side"] == "for":
            ax.axvline(c["x"], color=NAVY, linestyle=(0, (2, 2)), linewidth=0.8, alpha=0.55, zorder=4)
            ax.scatter(c["x"], 100, marker="v", s=55, color=NAVY, edgecolor="white", linewidth=0.8, zorder=7,
                       clip_on=False)
            if names:
                # changes a few minutes apart stack their names further down
                drop = drop + 8 * len(prev) + 2 if c["x"] - last_x < 8 else 0
                last_x, prev = c["x"], c["players_in"]
                ax.annotate("\n".join(_surname(p) for p in c["players_in"]), (c["x"], 100), xytext=(3, -4 - drop),
                            textcoords="offset points", ha="left", va="top", fontsize=6.3, color=NAVY, zorder=7,
                            bbox={"boxstyle": "round,pad=0.1", "facecolor": "white", "edgecolor": "none",
                                  "alpha": 0.75})
        else:
            ax.scatter(c["x"], 0, marker="^", s=40, color=OPPO_SUB_COL, edgecolor="white", linewidth=0.8, zorder=7,
                       clip_on=False)


def plot_field_tilt_timelines(
    matches: list[dict],
    title: str,
    team_name: str,
    window: float = 10,
    cols: int = 4,
    show: bool = True,
):
    """One small panel per match: the team's field tilt through the game, with the goals marked.

    matches is wyscout.data.season.season_field_tilt_timelines' output. Above
    the 50% line (navy) the team had the territory in the last window
    minutes, below it (red) the opposition did. Goals sit on the 50% line -
    navy dots for the team's, red for the opposition's - labelled with the
    score after the goal and the minute. The dotted line is half time.
    A match dict with "changes" (wyscout.data.substitutions.match_changes')
    has its substitutions marked too - see add_changes_to_timeline. One with
    "ppda_timeline" (season_field_tilt_timelines(ppda=True)) gets our PPDA as
    an amber line on an inverted right-hand axis, so higher is a harder press
    - the same way up as more territory.
    """
    rows = int(np.ceil(len(matches) / cols))
    with_subs = any(m.get("changes") is not None for m in matches)
    with_ppda = any(m.get("ppda_timeline") is not None for m in matches)
    fig, axes = plt.subplots(rows, cols, figsize=(4.4 * cols, 3.0 * rows + 1.2), sharey=True, squeeze=False)

    for ax, m in zip(axes.flat, matches):
        s, line, shift = m["summary"], m["timeline"], m["half_time"] - 45
        x, y = line["x"].to_numpy(), line["tilt"].to_numpy()
        fill = 0.6 if with_ppda else 0.85  # lighter under the PPDA line
        ax.fill_between(x, 50, y, where=y >= 50, interpolate=True, color=TILT_FOR, alpha=fill, lw=0)
        ax.fill_between(x, 50, y, where=y < 50, interpolate=True, color=TILT_AGAINST, alpha=fill, lw=0)
        ax.axhline(50, color=TEXT, linewidth=1.2, zorder=3)
        ax.axvline(m["half_time"], color=MUTED, linestyle=":", linewidth=1, zorder=2)

        # goals close together on the same side stack their labels further out
        last_x, level = {"for": -99.0, "against": -99.0}, {"for": 0, "against": 0}
        for g in m["goals"]:
            ours = g["side"] == "for"
            colour = TILT_FOR if ours else TILT_AGAINST
            side = g["side"]
            level[side] = level[side] + 1 if g["x"] - last_x[side] < 9 else 0
            last_x[side] = g["x"]
            offset = 12 + 24 * (level[side] % 3)
            ax.axvline(g["x"], color=colour, linewidth=0.8, alpha=0.4, zorder=2)
            ax.scatter(g["x"], 50, s=70, color=colour, edgecolor="white", linewidth=1.5, zorder=5)
            ax.annotate(f"{g['score']}\n{g['minute']}", (g["x"], 50), xytext=(0, offset if ours else -offset),
                        textcoords="offset points", ha="center", va="bottom" if ours else "top", fontsize=7.5,
                        weight="bold", color=colour, zorder=6,
                        bbox={"boxstyle": "round,pad=0.15", "facecolor": "white", "edgecolor": "none", "alpha": 0.8})

        if m.get("ppda_timeline") is not None:
            # drawn on the tilt axes (PPDA 0 at the top, PPDA_MAX at the bottom) so it sits between the fill
            # and the goal markers; the twin axis only carries the PPDA scale
            p = m["ppda_timeline"]
            py = 100 * (1 - p["ppda"].clip(upper=PPDA_MAX) / PPDA_MAX)
            ax.plot(p["x"], py, color="white", linewidth=3.4, alpha=0.9, zorder=2.5)
            ax.plot(p["x"], py, color=PPDA_COL, linewidth=1.8, zorder=2.6)
            press = ax.twinx()
            press.set_ylim(PPDA_MAX, 0)
            press.set_yticks([5, 10, 15, 20, 25])
            press.tick_params(axis="y", labelsize=7.5, colors=PPDA_COL, length=2)
            for side in ("top", "left", "bottom"):
                press.spines[side].set_visible(False)
            press.spines["right"].set_color(GRID)

        if m.get("changes") is not None:
            add_changes_to_timeline(ax, m["changes"])

        end = line["x"].max()
        ticks = [0, 15, 30, 45] + [t + shift for t in (60, 75, 90)]
        ax.set_xticks([t for t in ticks if t <= end + 1])
        ax.set_xticklabels([str(t) for t in (0, 15, 30, 45, 60, 75, 90)][: len(ax.get_xticks())], fontsize=8,
                           color=MUTED)
        ax.set_xlim(0, end)
        ax.set_ylim(0, 100)
        ax.set_yticks([0, 25, 50, 75, 100])
        ax.yaxis.set_major_formatter(ticker.PercentFormatter())
        ax.tick_params(axis="y", labelsize=8, colors=MUTED)
        ax.grid(axis="y", color=GRID, linewidth=0.6)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color(GRID)

        venue = "vs" if s.venue == "H" else "@"
        ax.set_title(f"{m['game']}. {venue} {s.opponent}", loc="left", fontsize=10.5, weight="bold", color=TEXT,
                     pad=16)
        ax.text(0, 1.03, f"{s.result} {s.score}", transform=ax.transAxes, fontsize=9, weight="bold",
                color=RESULT_FG[s.result], va="bottom")
        header = f"tilt {m['tilt']:.0f}%" + (f" · PPDA {m['ppda']:.1f}" if m.get("ppda") is not None else "")
        ax.text(1, 1.03, header, transform=ax.transAxes, fontsize=9, color=MUTED, ha="right",
                va="bottom")

    for ax in axes.flat[len(matches):]:
        ax.set_visible(False)

    fig.suptitle(title, x=0.01, ha="left", fontsize=15, weight="bold", color=TEXT, y=0.995)
    fig.text(0.01, 1 - 0.55 / fig.get_size_inches()[1],
             f"Share of the completed final-third passes in the last {window:g} minutes, quiet spells eased towards 50%. "
             f"Above 50%, {team_name} had the territory; below it, the opposition did. "
             "Dots on the line are goals, labelled with the score after the goal."
             + (" Triangles are substitutions - ours on top with the players brought on, theirs underneath."
                if with_subs else "")
             + (f"\nAmber line: our PPDA over the same {window:g} minutes (right axis, upside down - higher up is a harder "
                "press), scaled so the whole match matches Wyscout's published PPDA."
                if with_ppda else ""),
             fontsize=9.5, color=MUTED, va="top")
    handles = [Patch(color=TILT_FOR, label=f"{team_name} on top"),
               Patch(color=TILT_AGAINST, label="Opposition on top"),
               Line2D([], [], color=MUTED, linestyle=":", label="Half time")]
    if with_subs:
        handles += [Line2D([], [], marker="v", color=NAVY, linestyle=(0, (2, 2)), markersize=7, label="Our sub"),
                    Line2D([], [], marker="^", color=OPPO_SUB_COL, linestyle="none", markersize=7, label="Their sub")]
    if with_ppda:
        handles.append(Line2D([], [], color=PPDA_COL, linewidth=2, label="Our PPDA (right axis)"))
    head = 0.95 if with_ppda else 0.75  # the PPDA note adds a line to the description
    fig.legend(handles=handles,
               loc="upper left", ncol=len(handles), frameon=False, fontsize=9,
               bbox_to_anchor=(0.005, 1 - head / fig.get_size_inches()[1]))
    fig.tight_layout(rect=(0, 0, 1, 1 - (head + 0.15) / fig.get_size_inches()[1]), h_pad=2.2, w_pad=1.5)
    if show:
        plt.show()
    return fig, axes


# ── referees ─────────────────────────────────────────────────────────────────

# (column, header, match format, average format, deviation that reaches full colour)
REFEREE_STATS = [
    ("fouls", "Fouls", "{:.0f}", "{:.1f}", 6),
    ("yellows", "Yellows", "{:.0f}", "{:.1f}", 2),
    ("reds", "Reds", "{:.0f}", "{:.2f}", 1),
    ("fouls_per_card", "Fouls per\ncard", "{:.1f}", "{:.1f}", 4),
    ("penalties", "Penalties", "{:.0f}", "{:.2f}", 1),
    ("added_1h", "Added time\n1st half", "{:.1f}'", "{:.1f}'", 2),
    ("added_2h", "Added time\n2nd half", "{:.1f}'", "{:.1f}'", 3),
    ("home_foul_share", "Home side's\nshare of fouls", "{:.0f}%", "{:.0f}%", 15),
]


VENUE_BG = {"H": "#e3ecf7", "A": "#fbf0e1"}
VENUE_EDGE = {"H": NAVY, "A": "#b26a00"}


def plot_referee_table(df: pd.DataFrame, title: str, team_name: str, show: bool = True):
    """Every match's referee, what they gave, and what they usually give.

    df is wyscout.data.referees.season_referee_table's output. Each stat cell
    shows the match value large and the referee's average over their other
    games small beneath it; orange where the match was above that average,
    teal where below, grey where about the same. A referee with no other
    games is set against the league average instead (dashed cell edge). The
    last three columns split the fouls, cards and penalties between the team
    and the opposition - "us - them". Home rows are tinted blue, away rows sand.
    """
    n = len(df)
    cmap = LinearSegmentedColormap.from_list("ref", ["#00897b", "#80cbc4", "#eef1f4", "#ffcc80", "#ef6c00"])
    splits = [("fouls_for", "fouls_against", "Fouls\nus - them"), ("cards_for", "cards_against", "Cards\nus - them"),
              ("penalties_for", "penalties_against", "Pens\nus - them")]

    game_x, ref_x = 0.2, 3.6
    stat_x0, stat_w = 6.9, 1.12
    split_x0, split_w = stat_x0 + len(REFEREE_STATS) * stat_w + 0.25, 1.15
    width = split_x0 + len(splits) * split_w + 0.1

    fig, ax = plt.subplots(figsize=(width * 1.08, 1.9 + 0.62 * (n + 2)))
    ax.set_xlim(0, width)
    ax.set_ylim(n + 1.6, -1.4)
    ax.axis("off")

    ax.text(game_x, -0.6, "Match", ha="left", va="center", fontsize=10.5, weight="bold", color=TEXT)
    ax.text(ref_x, -0.6, "Referee (other games)", ha="left", va="center", fontsize=10.5, weight="bold", color=TEXT)
    for k, (_, label, _, _, _) in enumerate(REFEREE_STATS):
        ax.text(stat_x0 + (k + 0.5) * stat_w, -0.6, label, ha="center", va="center", fontsize=9.5, weight="bold",
                color=TEXT)
    for k, (_, _, label) in enumerate(splits):
        ax.text(split_x0 + (k + 0.5) * split_w, -0.6, label, ha="center", va="center", fontsize=9.5,
                weight="bold", color=TEXT)

    def stat_cell(x0, y, value, usual, fmt, avg_fmt, scale, dashed=False):
        if pd.isna(value):
            ax.text(x0 + stat_w / 2, y + 0.5, "-", ha="center", va="center", fontsize=11, color=MUTED)
            return
        norm = 0.5 if pd.isna(usual) else 0.5 + float(np.clip((value - usual) / scale, -1, 1)) / 2
        ax.add_patch(plt.Rectangle((x0 + 0.04, y + 0.07), stat_w - 0.08, 0.86, facecolor=cmap(norm),
                                   edgecolor=MUTED if dashed else "white", linestyle=(0, (3, 2)) if dashed else "-",
                                   lw=1 if dashed else 1.5))
        ax.text(x0 + stat_w / 2, y + 0.4, fmt.format(value), ha="center", va="center", fontsize=12, weight="bold",
                color=TEXT)
        if not pd.isna(usual):
            ax.text(x0 + stat_w / 2, y + 0.76, f"avg {avg_fmt.format(usual)}", ha="center", va="center", fontsize=7.5,
                    color=TEXT if abs(norm - 0.5) > 0.3 else MUTED)

    for i, r in df.iterrows():
        ax.add_patch(plt.Rectangle((0.05, i + 0.02), width - 0.1, 0.96, facecolor=VENUE_BG[r.venue],
                                   edgecolor="none", zorder=0))
        ax.add_patch(plt.Rectangle((0.05, i + 0.02), 0.07, 0.96, facecolor=VENUE_EDGE[r.venue], edgecolor="none",
                                   zorder=1))
        venue = "vs" if r.venue == "H" else "@"
        ax.text(game_x, i + 0.38, f"{r.game}. {venue} {r.opponent}", ha="left", va="center", fontsize=10.5,
                color=TEXT)
        ax.text(game_x, i + 0.72, f"{r.result} {r.score}", ha="left", va="center", fontsize=9, weight="bold",
                color=RESULT_FG[r.result])
        ax.text(ref_x - 0.25, i + 0.5, "HOME" if r.venue == "H" else "AWAY", ha="right", va="center", fontsize=7.5,
                weight="bold", color=VENUE_EDGE[r.venue])
        ax.text(ref_x, i + 0.38, r.referee, ha="left", va="center", fontsize=10.5, weight="bold",
                color=MUTED if r.referee_id is None else TEXT)
        ax.text(ref_x, i + 0.72, f"{r.ref_games} games" if r.ref_games else "new - vs league average",
                ha="left", va="center", fontsize=8.5, color=MUTED)

        new_ref = r.ref_games == 0
        for k, (stat, _, fmt, avg_fmt, scale) in enumerate(REFEREE_STATS):
            usual = r[f"league_{stat}"] if new_ref else r[f"ref_{stat}"]
            stat_cell(stat_x0 + k * stat_w, i, r[stat], usual, fmt, avg_fmt, scale, dashed=new_ref)

        for k, (ours, theirs, _) in enumerate(splits):
            cx = split_x0 + (k + 0.5) * split_w
            a, b = int(r[ours]), int(r[theirs])
            ax.text(cx - 0.1, i + 0.5, f"{a}", ha="right", va="center", fontsize=11.5, weight="bold",
                    color=NAVY if a > b else TEXT)
            ax.text(cx, i + 0.5, "-", ha="center", va="center", fontsize=11, color=MUTED)
            ax.text(cx + 0.1, i + 0.5, f"{b}", ha="left", va="center", fontsize=11.5, weight="bold",
                    color=NAVY if b > a else TEXT)

    # the league average as a footer row
    y = n + 0.15
    ax.plot([0.05, width - 0.05], [y - 0.05, y - 0.05], color=GRID, linewidth=1)
    ax.text(ref_x, y + 0.45, "League average", ha="left", va="center", fontsize=10, weight="bold", color=MUTED)
    first = df.iloc[0]
    for k, (stat, _, _, avg_fmt, _) in enumerate(REFEREE_STATS):
        ax.text(stat_x0 + (k + 0.5) * stat_w, y + 0.45, avg_fmt.format(first[f"league_{stat}"]), ha="center",
                va="center", fontsize=10.5, color=MUTED)
    totals = [(df[a].sum(), df[b].sum()) for a, b, _ in splits]
    for k, (a, b) in enumerate(totals):
        ax.text(split_x0 + (k + 0.5) * split_w, y + 0.45, f"{a:.0f} - {b:.0f}", ha="center", va="center",
                fontsize=10.5, weight="bold", color=MUTED)
    ax.text(split_x0 + 1.5 * split_w, y + 0.95, "season totals", ha="center", va="center", fontsize=8, color=MUTED)

    fig.suptitle(title, x=0.01, ha="left", fontsize=15, weight="bold", color=TEXT, y=0.995)
    fig.text(0.01, 1 - 0.5 / fig.get_size_inches()[1],
             "Large: what the referee gave in the match. Small: their average over their other National League "
             "games (this season and last). Orange = more than they usually give, teal = fewer.\n"
             f"Fouls are every infraction logged; added time is the time played past 45 and 90 minutes. "
             f"Us - them: {team_name}'s count first, the higher one in navy. Blue rows are home games, sand rows away.",
             fontsize=9.5, color=MUTED, va="top")
    fig.subplots_adjust(left=0.005, right=0.995, top=1 - 1.1 / fig.get_size_inches()[1], bottom=0.01)
    if show:
        plt.show()
    return fig, ax


# (column, header, format) for the league referee table
LEAGUE_REFEREE_STATS = [
    ("fouls", "Fouls\nper game", "{:.1f}"),
    ("home_fouls", "Home\nfouls", "{:.1f}"),
    ("away_fouls", "Away\nfouls", "{:.1f}"),
    ("home_foul_share", "Home share\nof fouls", "{:.0f}%"),
    ("yellows", "Yellows\nper game", "{:.1f}"),
    ("home_card_share", "Home share\nof cards", "{:.0f}%"),
    ("fouls_per_card", "Fouls\nper card", "{:.1f}"),
    ("reds", "Reds\nper game", "{:.2f}"),
    ("penalties", "Pens\nper game", "{:.2f}"),
    ("home_win", "Home\nwin %", "{:.0f}%"),
    ("added_1h", "Added time\n1st half", "{:.1f}'"),
    ("added_2h", "Added time\n2nd half", "{:.1f}'"),
]


TEAM_GAME_W = 1.75  # room for one result chip and its date and opponent


def plot_league_referee_table(
    df: pd.DataFrame,
    title: str,
    team_name: str | None = None,
    sort_by: str = "yellows",
    min_games: int = 3,
    show: bool = True,
):
    """Every referee in the league, ranked, with their per-game numbers against the league average.

    df is wyscout.data.referees.league_referee_table's output; referees with
    no games this season ("season_games" 0) or fewer than min_games in all
    are left out. Each cell is coloured by how far it sits from the average
    over every match - orange above, teal below, grey about level - scaled
    by the spread between referees, so one colour step means the same in
    every column. sort_by is any stat column, highest first ("fouls_per_card"
    sorts lowest first: quickest to book at the top). With team_name, the
    last column lists that club's results under each referee.
    """
    df = df[(df["season_games"] > 0) & (df["games"] >= min_games)]
    df = df.sort_values(sort_by, ascending=sort_by == "fouls_per_card").reset_index(drop=True)
    n = len(df)
    cmap = LinearSegmentedColormap.from_list("ref", ["#00897b", "#80cbc4", "#eef1f4", "#ffcc80", "#ef6c00"])
    # weighted by games, so the centre is the per-match league average
    centre = {stat: np.average(df[stat].fillna(df[stat].mean()), weights=df["games"])
              for stat, _, _ in LEAGUE_REFEREE_STATS}
    spread = {stat: max(df[stat].std() * 2, 1e-9) for stat, _, _ in LEAGUE_REFEREE_STATS}

    rank_x, name_x = 0.35, 0.8
    stat_x0, stat_w = 4.4, 1.0
    team_x = stat_x0 + len(LEAGUE_REFEREE_STATS) * stat_w + 0.25
    width = team_x + (3 * TEAM_GAME_W + 0.3 if team_name else 0) + 0.1

    fig, ax = plt.subplots(figsize=(width * 1.08, 1.9 + 0.42 * (n + 2)))
    ax.set_xlim(0, width)
    ax.set_ylim(n + 1.4, -1.5)
    ax.axis("off")

    ax.text(rank_x, -0.7, "#", ha="center", va="center", fontsize=10.5, weight="bold", color=TEXT)
    ax.text(name_x, -0.7, "Referee (games: all / this season)", ha="left", va="center", fontsize=10.5,
            weight="bold", color=TEXT)
    for k, (stat, label, _) in enumerate(LEAGUE_REFEREE_STATS):
        ax.text(stat_x0 + (k + 0.5) * stat_w, -0.7, label, ha="center", va="center", fontsize=9,
                weight="bold", color=NAVY if stat == sort_by else TEXT)
    if team_name:
        ax.text(team_x, -0.7, f"{team_name} games", ha="left", va="center", fontsize=10.5, weight="bold",
                color=TEXT)

    for i, r in df.iterrows():
        mine = team_name and r.team_games > 0
        if i % 2 == 0 or mine:
            ax.add_patch(plt.Rectangle((0.05, i), width - 0.1, 1, facecolor="#e8f0fb" if mine else "#f6f8fa",
                                       edgecolor="none", zorder=0))
        ax.text(rank_x, i + 0.5, f"{i + 1}", ha="center", va="center", fontsize=10, weight="bold", color=MUTED)
        ax.text(name_x, i + 0.5, r.referee, ha="left", va="center", fontsize=10.5, color=TEXT,
                weight="bold" if mine else "normal")
        ax.text(stat_x0 - 0.15, i + 0.5, f"{r.games} / {r.season_games}", ha="right", va="center", fontsize=9,
                color=MUTED)

        for k, (stat, _, fmt) in enumerate(LEAGUE_REFEREE_STATS):
            x0, value = stat_x0 + k * stat_w, r[stat]
            if pd.isna(value):
                ax.text(x0 + stat_w / 2, i + 0.5, "-", ha="center", va="center", fontsize=10, color=MUTED)
                continue
            norm = 0.5 + float(np.clip((value - centre[stat]) / spread[stat], -1, 1)) / 2
            ax.add_patch(plt.Rectangle((x0 + 0.03, i + 0.08), stat_w - 0.06, 0.84, facecolor=cmap(norm),
                                       edgecolor="white", lw=1.2))
            ax.text(x0 + stat_w / 2, i + 0.5, fmt.format(value), ha="center", va="center", fontsize=10,
                    weight="bold" if stat == sort_by else "normal", color=TEXT)

        if team_name and r.team_games:
            for k, t in enumerate(r.team_matches[:3]):
                x = team_x + k * TEAM_GAME_W
                ax.text(x, i + 0.36, f"{t['result']} {t['score']}", ha="left", va="center", fontsize=8.5,
                        weight="bold", color=RESULT_FG[t["result"]],
                        bbox={"boxstyle": "round,pad=0.15", "facecolor": RESULT_BG[t["result"]], "edgecolor": "none"})
                when = pd.Timestamp(t["date"]).strftime("%-d %b %y")
                where = "vs" if t["venue"] == "H" else "@"
                ax.text(x, i + 0.8, f"{when} {where} {t['opponent'][:14]}", ha="left", va="center", fontsize=6.5,
                        color=MUTED)
            if r.team_games > 3:
                ax.text(team_x + 3 * TEAM_GAME_W, i + 0.5, f"+{r.team_games - 3}", ha="left", va="center",
                        fontsize=9, color=MUTED)

    # league average footer
    y = n + 0.1
    ax.plot([0.05, width - 0.05], [y, y], color=GRID, linewidth=1)
    ax.text(name_x, y + 0.5, "League average (per match)", ha="left", va="center", fontsize=10, weight="bold",
            color=MUTED)
    for k, (stat, _, fmt) in enumerate(LEAGUE_REFEREE_STATS):
        ax.text(stat_x0 + (k + 0.5) * stat_w, y + 0.5, fmt.format(centre[stat]), ha="center", va="center",
                fontsize=10, weight="bold", color=MUTED)

    sort_label = {stat: label.replace("\n", " ").lower() for stat, label, _ in LEAGUE_REFEREE_STATS}.get(sort_by, sort_by)
    ranked = ("Ranked by fouls per card, quickest to book first. " if sort_by == "fouls_per_card" else
              f"Ranked by {sort_label}, highest first. ")
    fig.suptitle(title, x=0.01, ha="left", fontsize=15, weight="bold", color=TEXT, y=0.995)
    fig.text(0.01, 1 - 0.5 / fig.get_size_inches()[1],
             ranked + f"Referees with a game this season and {min_games}+ games in the sample. "
             "Orange = above the league average, teal = below.\n"
             "Fouls are every infraction logged. Home share: the home side's % of the fouls or cards given. "
             "Added time is the time played past 45 and 90 minutes."
             + (f" Highlighted: referees who have had {team_name}." if team_name else ""),
             fontsize=9.5, color=MUTED, va="top")
    fig.subplots_adjust(left=0.005, right=0.995, top=1 - 1.05 / fig.get_size_inches()[1], bottom=0.01)
    if show:
        plt.show()
    return fig, ax


# ── odds and ends ────────────────────────────────────────────────────────────


def plot_possession_histogram(df: pd.DataFrame, palette: Sequence[str] | None = None,
                              bins: int = 10, show: bool = True):
    """Distribution of possession share per match, one colour per team.

    df needs "team" and "possession" columns.
    """
    with sns.axes_style("darkgrid"):
        _fig, ax = plt.subplots(figsize=(10, 5))
    sns.histplot(ax=ax, data=df, x="possession", hue="team", multiple="dodge", bins=bins, palette=palette)
    ax.set(xlabel="Possession %", ylabel="Matches")
    ax.get_legend().set_title("Team")
    if show:
        plt.show()
    return ax


def plot_birth_months(counts: pd.Series, title: str, show: bool = True):
    """Bar chart of players born in each month - the relative age effect."""
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar([months[m - 1] for m in counts.index], counts.values, color=THIS_COL)
    ax.set(ylabel="Players", title=title)
    ax.axvline(7.5, color=MUTED, linestyle="--", linewidth=1)
    ax.text(7.6, ax.get_ylim()[1] * 0.95, "school year starts", color=MUTED, fontsize=8, va="top")
    if show:
        plt.show()
    return fig, ax


def plot_goals_table(df_on: pd.DataFrame, df_off: pd.DataFrame, labels: Sequence[str]) -> None:
    """Print two goal lists side by side - a convenience for the on/off pitch split."""
    for df, label in zip((df_on, df_off), labels):
        print(label)
        print(df.to_string(index=False) if len(df) else "  none")
        print()
