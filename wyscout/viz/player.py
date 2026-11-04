"""Player charts: a season of heat maps, a pass map between two players, an action map."""

import math
from collections.abc import Sequence
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D
from mplsoccer import add_image

from wyscout.viz.arrows import Arrow, plot_arrows
from wyscout.viz.consts import APP_FONT, COLOUR_1, COLOUR_2, TEAM_COLOURS
from wyscout.viz.event_map import EventPanel
from wyscout.viz.heat_map import add_heat_map
from wyscout.viz.pitch import make_pitch, pitch_axes, pitch_grid
from wyscout.viz.shots import plot_shots
from wyscout.viz.utils import TEXT_COLOUR, add_footer, add_header, load_image


def plot_player_season_heat_maps(
    panels: Sequence[EventPanel],
    header: str,
    player_img: Any = None,
    cols: int = 5,
    fig_height: float = 30,
    cmap: str = "Blues",
    shot_colors=TEAM_COLOURS,
    show: bool = True,
):
    """A grid of full pitches, one per match: the player's touches and attempts."""
    rows = math.ceil(len(panels) / cols)
    pitch = make_pitch(pad_top=20)
    title_height = min(0.1, 0.3 / rows)
    fig, axs = pitch_grid(pitch, ncols=cols, nrows=rows, fig_height=fig_height, title_height=title_height,
                          title_space=0.02, endnote_height=0.03)
    panel_font = fig_height * 0.8 / rows * 2.2

    axes = pitch_axes(axs)
    for panel, ax in zip(panels, axes):
        ax.text(50, 110, panel.title, ha="center", va="center", fontsize=panel_font)
        add_heat_map(panel.touches, pitch, ax, cmap=cmap)
        plot_shots(panel.shots, shot_colors, pitch, ax)
    for ax in axes[len(panels):]:
        ax.set_visible(False)

    add_header(fig, axs["title"], header, scale_img=0.9, font_size=fig_height * 1.3, title_va="center",
               title_pos=(0, 0.5), imgs=[player_img] if player_img else None, img_rel_x_pos=0.1)
    add_footer(fig, axs["endnote"], scale_img=1, font_size=fig_height / 2)

    if show:
        plt.show()
    return fig, axs, pitch


def plot_pass_map(
    arrows: Sequence[Arrow],
    title: str,
    subtitle: Sequence[str] | None = None,
    imgs: Sequence[Any] | None = None,
    legend: Sequence[str] = ("Low pass", "High pass", "Led to shot"),
    fig_height: float = 8,
    show: bool = True,
):
    """Passes between two players on a striped pitch, with a legend for the arrow styles."""
    pitch = make_pitch(grass=True, pad_top=4)
    fig, axs = pitch_grid(pitch, fig_height=fig_height, title_height=0.08, grid_height=0.82,
                          endnote_height=0.05)
    plot_arrows(arrows, pitch, axs["pitch"])

    add_header(fig, axs["title"], title, subtitle, imgs=imgs, font_size=15, subtitle_font_size=9,
               scale_img=1.0, img_rel_x_pos=0.1, title_pos=(0, 0.75), subtitle_start_pos=0.25)
    add_footer(fig, axs["endnote"], scale_img=1)

    lines = [
        Line2D([0], [0], color=COLOUR_1, lw=1),
        Line2D([0], [0], color=COLOUR_2, lw=1),
        Line2D([0], [0], color=COLOUR_1, lw=2),
    ]
    leg = axs["pitch"].legend(lines, list(legend), loc="lower left")
    plt.setp(leg.texts, fontproperties=APP_FONT.prop, size=8)

    if show:
        plt.show()
    return fig, axs, pitch


def plot_player_action_map(
    player_name: str,
    title: str,
    subtitle: str,
    touches: Sequence[Sequence[float]],
    arrows: Sequence[Arrow] = (),
    crosses: Sequence[Arrow] = (),
    player_img: Any = None,
    fig_height: float = 16,
    show: bool = True,
):
    """One full pitch: the player's touch heat map with passes and crosses over it."""
    pitch = make_pitch(line_color="grey", pad_top=4)
    fig, axs = pitch_grid(pitch, fig_height=fig_height, title_height=0.08, grid_height=0.82,
                          endnote_height=0.03)
    fig.patch.set_facecolor("white")

    add_heat_map(touches, pitch, axs["pitch"])
    plot_arrows(arrows, pitch, axs["pitch"])
    plot_arrows(crosses, pitch, axs["pitch"])

    ax = axs["title"]
    ax.text(0, 0.9, player_name, fontsize=24, color=TEXT_COLOUR, fontproperties=APP_FONT.prop,
            ha="left", va="center")
    ax.text(0, 0.4, title, fontsize=14, color=TEXT_COLOUR, fontproperties=APP_FONT.prop,
            ha="left", va="center")
    if subtitle:
        ax.text(0, 0, subtitle, fontsize=10, color=TEXT_COLOUR, fontproperties=APP_FONT.prop,
                ha="left", va="center")
    if player_img:
        add_image(load_image(player_img), fig, interpolation="hanning",
                  left=ax.get_position().x1 - 0.15, bottom=ax.get_position().y0,
                  height=ax.get_position().height * 1.3)

    add_footer(fig, axs["endnote"])

    if show:
        plt.show()
    return fig, axs, pitch


def plot_attempts_table(
    df: pd.DataFrame,
    title: str,
    save_path: str | None = None,
    show: bool = True,
):
    """A styled table of a player's attempts, one row each, with a totals row.

    df is wyscout.data.player.attempts_table's output. Each row: when and against whom, which
    foot or head, how the chance arose, distance out, who set it up, xG (and the running
    total), post-shot xG for anything on target, where in the goal it went, and the outcome.
    Goals are picked out in green.
    """
    table = df.copy()
    table["cum_xG"] = table["xG"].cumsum()
    table["opponent"] = table["opponent"] + " (" + table["venue"] + ")"
    columns = {"date": "Date", "opponent": "Opponent", "minute": "Min", "body_part": "How",
               "situation": "Situation", "distance_m": "Dist (m)", "assisted_by": "Assist", "xG": "xG",
               "cum_xG": "Cum. xG", "post_shot_xG": "Post-shot xG", "placement": "Placement",
               "outcome": "Outcome", "score": "Score"}
    table = table[list(columns)].rename(columns=columns)
    totals = {c: "" for c in table.columns}
    totals.update({"Date": "Total", "xG": table["xG"].sum(), "Post-shot xG": table["Post-shot xG"].sum()})
    table = pd.concat([table, pd.DataFrame([totals])], ignore_index=True)

    decimals = {"Dist (m)": 1, "xG": 2, "Cum. xG": 2, "Post-shot xG": 2}

    def fmt(column, value):
        if pd.isna(value) if not isinstance(value, str) else False:
            return ""
        if column in decimals and value != "":
            return f"{float(value):.{decimals[column]}f}"
        return str(value)

    cell_text = [[fmt(c, v) for c, v in zip(table.columns, row)] for row in table.itertuples(index=False)]
    n_rows = len(table)
    col_widths = [1.0, 3.0, 0.5, 0.9, 1.4, 0.8, 2.4, 0.6, 0.8, 1.1, 1.4, 1.0, 0.6]
    row_h, title_h = 0.3, 0.35
    fig_w, fig_h = sum(col_widths), row_h * (n_rows + 1) + title_h

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.axis("off")
    fig.patch.set_facecolor("white")
    plt.subplots_adjust(top=1, bottom=0, left=0, right=1)
    title_frac = title_h / fig_h
    ax.text(0.5, 1 - title_frac / 2, title, transform=ax.transAxes, fontsize=11, fontweight="bold",
            ha="center", va="center")

    tbl = ax.table(cellText=cell_text, colLabels=list(table.columns), cellLoc="center",
                   colWidths=[w / fig_w for w in col_widths], bbox=[0, 0, 1, 1 - title_frac])
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8.5)
    outcome_col = list(table.columns).index("Outcome")
    for (r, c), cell in tbl.get_celld().items():
        cell.set_edgecolor("#cccccc")
        cell.set_linewidth(0.5)
        if r == 0:
            cell.set_facecolor("#1a3a5c")
            cell.set_text_props(color="white", fontweight="bold")
        elif r == n_rows:
            cell.set_facecolor("#dce8f5")
            cell.set_text_props(fontweight="bold")
        else:
            cell.set_facecolor("#f0f4f8" if r % 2 else "white")
            if c == outcome_col and cell.get_text().get_text() == "Goal":
                cell.set_text_props(color="#1a7a1a", fontweight="bold")

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight", facecolor="white")
    if show:
        plt.show()
    return fig, ax


def plot_stat_comparison(
    df: pd.DataFrame,
    stats: Sequence[tuple[str, str, str, bool, str]],
    title: str,
    subtitle: str = "",
    highlight_player_id: int | None = None,
    show: bool = True,
):
    """A table of players (columns) against statistics (rows), each cell coloured by its rank in the row.

    df is wyscout.data.player.season_stats_table's output and stats the same
    list it was built with. Green is the best in the row, red the worst - for a
    "lower is better" stat such as losses that is flipped. The small number in
    the corner of a cell is the rank. highlight_player_id is put first and
    outlined.
    """
    df = df.copy()
    df["_first"] = df["player_id"] == highlight_player_id
    df = df.sort_values(["_first", "minutes"], ascending=False).reset_index(drop=True)
    cmap = plt.get_cmap("RdYlGn")
    n_players = len(df)

    # one line per stat, plus a heading line for each group
    lines: list[tuple[str, Any]] = []
    group = None
    for stat in stats:
        if stat[4] != group:
            group = stat[4]
            lines.append(("group", group))
        lines.append(("stat", stat))

    label_width = 3.2
    fig, ax = plt.subplots(figsize=(2.2 + 1.25 * n_players + label_width * 0.9, 1.8 + 0.33 * (len(lines) + 4)))
    ax.set_xlim(-label_width, n_players)
    ax.set_ylim(len(lines) + 0.2, -2.5)
    ax.axis("off")

    for j, r in df.iterrows():
        bold = "bold" if r["_first"] else "normal"
        # a long name loses its initial so it fits the column
        name = r["name"] if len(r["name"]) <= 14 else r["name"].split(". ", 1)[-1]
        ax.text(j + 0.5, -2.1, name, ha="center", va="center", fontsize=10, weight="bold", color=TEXT_COLOUR)
        ax.text(j + 0.5, -1.6, r["team"], ha="center", va="center", fontsize=8, color="#6b7785", weight=bold)
        ax.text(j + 0.5, -1.15, r["position"].replace("Defensive", "Def.").replace("Midfielder", "Mid")
                .replace("Attacking", "Att.").replace("Centre", "C."), ha="center", va="center", fontsize=7.5,
                color="#6b7785")
        ax.text(j + 0.5, -0.7, f"{r['minutes']} mins", ha="center", va="center", fontsize=8, color="#6b7785")

    for i, (kind, item) in enumerate(lines):
        if kind == "group":
            ax.text(-label_width + 0.05, i + 0.65, item.upper(), ha="left", va="center", fontsize=9, weight="bold",
                    color="#12385c")
            continue
        label, section, _, higher_is_better, _ = item
        values = df[label]
        ranks = values.rank(ascending=not higher_is_better, method="min")
        ax.text(-0.1, i + 0.5, label, ha="right", va="center", fontsize=9.5, color=TEXT_COLOUR)
        for j, v in enumerate(values):
            if pd.isna(v):
                ax.add_patch(plt.Rectangle((j, i), 1, 1, facecolor="#f2f2f2", edgecolor="white", linewidth=1.5))
                continue
            # rank 1 is the top of the scale; ties share a colour
            position = 1 - (ranks[j] - 1) / max(n_players - 1, 1)
            ax.add_patch(plt.Rectangle((j, i), 1, 1, facecolor=cmap(0.08 + position * 0.84), edgecolor="white",
                                       linewidth=1.5))
            text = f"{v:.0f}%" if section == "percent" else f"{v:.2f}"
            ax.text(j + 0.5, i + 0.52, text, ha="center", va="center", fontsize=9.5, color=TEXT_COLOUR)
            ax.text(j + 0.95, i + 0.2, f"{int(ranks[j])}", ha="right", va="center", fontsize=6, color="#3d4a57")

    if highlight_player_id is not None and df["_first"].any():
        ax.add_patch(plt.Rectangle((0.02, -2.45), 0.96, len(lines) + 2.4, facecolor="none", edgecolor="#12385c",
                                   linewidth=2.5, zorder=5))

    fig.text(0.02, 0.985, title, ha="left", va="top", fontsize=14, weight="bold", color=TEXT_COLOUR)
    if subtitle:
        fig.text(0.02, 0.955, subtitle, ha="left", va="top", fontsize=10, color="#6b7785")
    plt.tight_layout(rect=(0, 0, 1, 0.94))
    if show:
        plt.show()
    return fig, ax
