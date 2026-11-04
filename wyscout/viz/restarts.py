"""Restarts - goal kicks, throw-ins, free kicks and corners - and how often they find a team mate.

Every function takes the DataFrames from ``wyscout.data.restarts`` and draws
one figure. Nothing here fetches.
"""

from collections.abc import Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from wyscout.data.restarts import KEEP_SECONDS, RESTART_NAMES, RESTARTS
from wyscout.viz.consts import GRID, MUTED, PREV_COL, RESULT_FG, TEXT, THIS_COL
from wyscout.viz.pitch import make_pitch
from wyscout.viz.season import ordinal

OPPO_COL = "#b26a00"  # the opposition's restarts in our matches - orange against our blue
WON_COL = THIS_COL
LOST_COL = "#c62828"
HIGHLIGHT_BG = "#f3d98b"

# red below 50% (lost more than found), grey at a coin flip, blue above
COMPLETION_CMAP = LinearSegmentedColormap.from_list("completion", [LOST_COL, "#f4f4f4", THIS_COL])

# zone edges (x along the pitch, y across it) for the zone maps, by where the restarts are binned
ZONES = {
    "end": ([0, 100 / 6, 100 / 3, 50, 200 / 3, 500 / 6, 100], [0, 100 / 3, 200 / 3, 100]),
    "corner": ([50, 66, 84, 94, 100], [0, 19, 37, 63, 81, 100]),
}

METRICS = {
    "completion": "Found a team mate with the first contact",
    "kept_rate": f"Still had the ball {KEEP_SECONDS} seconds later",
}


def _pct(v: float) -> str:
    return "-" if pd.isna(v) else f"{v:.0%}"


def _rate(df: pd.DataFrame, column: str = "completed") -> str:
    return f"{_pct(df[column].mean()) if len(df) else '-'} ({int(df[column].sum())}/{len(df)})"


def plot_restart_overview(
    table: pd.DataFrame,
    team_id: int,
    team_name: str,
    title: str,
    fig_size=(16, 8),
    show: bool = True,
):
    """Each restart's completion rate for the team, its opponents and every club in the league.

    table is wyscout.data.restarts.league_restart_table's output. Left panel:
    first contact to a team mate; right: still in possession KEEP_SECONDS
    later. Each row is a kind of restart. Grey dots are every club's own
    rate, the grey tick the league average, the blue circle the team and the
    orange diamond the opposition's restarts in the team's matches.
    """
    with sns.axes_style("white"):
        fig, axes = plt.subplots(1, 2, figsize=fig_size, facecolor="white", sharey=True)

    rows = np.arange(len(RESTARTS))
    for ax, (metric, heading) in zip(axes, METRICS.items()):
        for i, kind in enumerate(RESTARTS):
            clubs = table[table["kind"] == kind]
            ours = clubs[clubs["team_id"] == team_id].iloc[0]
            rank = int((clubs[metric] > ours[metric]).sum()) + 1
            count = metric.replace("completion", "completed").replace("_rate", "")

            ax.scatter(clubs[metric], np.full(len(clubs), i), s=70, color=PREV_COL, alpha=0.55,
                       edgecolor="white", linewidth=0.8, zorder=2)
            league = clubs[count].sum() / clubs["taken"].sum()
            ax.plot([league, league], [i - 0.28, i + 0.28], color=MUTED, linewidth=2, zorder=3)
            ax.scatter(ours[f"{metric}_faced"], i, s=150, marker="D", color=OPPO_COL, edgecolor="white",
                       linewidth=1.5, zorder=4)
            ax.scatter(ours[metric], i, s=220, color=THIS_COL, edgecolor="white", linewidth=1.5, zorder=5)

            ax.text(ours[metric], i - 0.3, f"{ours[metric]:.0%}  ({ordinal(rank)})", ha="center", va="bottom",
                    fontsize=10, fontweight="bold", color=TEXT)
            ax.text(ours[f"{metric}_faced"], i + 0.3, f"{ours[f'{metric}_faced']:.0%}", ha="center", va="top",
                    fontsize=9, color=TEXT)
            ax.text(1.01, i, f"{int(ours[count])}/{int(ours['taken'])}\nopp. {int(ours[f'{count}_faced'])}/"
                    f"{int(ours['taken_faced'])}", transform=ax.get_yaxis_transform(), ha="left", va="center",
                    fontsize=8.5, color=MUTED)

        ax.set_yticks(rows)
        ax.set_yticklabels([RESTART_NAMES[k] for k in RESTARTS], fontsize=12, color=TEXT)
        ax.set_ylim(len(RESTARTS) - 0.4, -0.6)
        ax.set_xlim(0.25, 1.0)
        ax.xaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
        ax.grid(axis="x", color=GRID, zorder=0)
        ax.tick_params(axis="y", length=0)
        sns.despine(ax=ax, left=True)
        ax.set_title(heading, fontsize=12, fontweight="bold", color=TEXT, loc="left")

    axes[0].legend(handles=[
        Line2D([], [], marker="o", linestyle="", markersize=12, color=THIS_COL, label=team_name),
        Line2D([], [], marker="D", linestyle="", markersize=9, color=OPPO_COL,
               label=f"Opposition against {team_name}"),
        Line2D([], [], marker="o", linestyle="", markersize=8, color=PREV_COL, label="Every club"),
        Line2D([], [], marker="|", linestyle="", markersize=14, markeredgewidth=2, color=MUTED,
               label="League average"),
    ], loc="upper left", bbox_to_anchor=(0, -0.07), frameon=False, fontsize=9.5, ncol=4)
    fig.suptitle(title, fontsize=15, fontweight="bold", color=TEXT)
    fig.text(0.5, 0.01, "Our rank (in brackets) is out of every club in the league, best first. "
             "Counts on the right: ours, then the opposition's against us.", ha="center", fontsize=9, color=MUTED)
    fig.subplots_adjust(left=0.08, right=0.94, wspace=0.18, top=0.88, bottom=0.17)
    if show:
        plt.show()
    return fig, axes


LONG_LABEL = {"goal_kick": "Played\nlong", "corner": "Crossed", "free_kick": "Crossed", "throw_in": "Into\nthe box"}


def plot_league_restarts(
    table: pd.DataFrame,
    kind: str,
    title: str,
    highlight_team_id: int | None = None,
    sort_by: str = "completion",
    fig_size=(13, 10),
    show: bool = True,
):
    """Every club's restarts of one kind, ranked - completion as a bar, kept-the-ball as a diamond.

    table is wyscout.data.restarts.league_restart_table's output. sort_by is
    any of its columns, highest first. The columns on the right are the
    restarts taken (per game), the share played long (or crossed, or thrown
    into the box) and the opposition's completion in the club's matches.
    """
    df = table[table["kind"] == kind].sort_values(sort_by, ascending=False).reset_index(drop=True)
    y = np.arange(len(df))
    with sns.axes_style("white"):
        fig, ax = plt.subplots(figsize=fig_size, facecolor="white")

    ax.barh(y, df["completion"], height=0.68, color=THIS_COL, alpha=0.75, zorder=2, label=METRICS["completion"])
    ax.scatter(df["kept_rate"], y, marker="D", s=46, color=TEXT, edgecolor="white", linewidth=0.8, zorder=4,
               label=METRICS["kept_rate"])
    for metric, style in (("completion", "--"), ("kept_rate", ":")):
        count = "completed" if metric == "completion" else "kept"
        ax.axvline(df[count].sum() / df["taken"].sum(), color=MUTED, linestyle=style, linewidth=1, zorder=3)
    for i, r in df.iterrows():
        ax.text(0.01, i, _pct(r["completion"]), ha="left", va="center", fontsize=8.5,
                color="white", fontweight="bold", zorder=5)

    columns = [  # (axes-fraction x, header, value)
        (1.07, "Taken\n(/ game)", lambda r: f"{int(r['taken'])} ({r['per_game']:.1f})"),
        (1.2, LONG_LABEL[kind], lambda r: _pct(r["share_long"])),
        (1.33, "Opposition\ncompletion", lambda r: _pct(r["completion_faced"])),
    ]
    to_axes = ax.get_yaxis_transform()
    for x, header, _ in columns:
        ax.text(x, -1.1, header, transform=to_axes, ha="center", va="center", fontsize=8.5, fontweight="bold",
                color=MUTED)
    for i, r in df.iterrows():
        highlight = r["team_id"] == highlight_team_id
        for x, _, value in columns:
            ax.text(x, i, value(r), transform=to_axes, ha="center", va="center", fontsize=9, color=TEXT,
                    fontweight="bold" if highlight else "normal")
        if highlight:
            ax.axhspan(i - 0.5, i + 0.5, xmax=1.4, color=HIGHLIGHT_BG, alpha=0.45, zorder=0, clip_on=False)

    ax.set_yticks(y)
    ax.set_yticklabels([f"{r.position}. {r.team}" for r in df.itertuples()], fontsize=9.5, color=TEXT)
    ax.set_ylim(len(df) - 0.4, -1.8)
    ax.set_xlim(0, 1)
    ax.xaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    ax.grid(axis="x", color=GRID, zorder=0)
    ax.tick_params(axis="y", length=0)
    sns.despine(ax=ax, left=True)
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), frameon=False, fontsize=9, ncol=2)
    ax.set_xlabel("Dashed line: league completion.  Dotted line: league kept-the-ball rate.", color=MUTED,
                  fontsize=9)
    fig.suptitle(title, fontsize=14, fontweight="bold", color=TEXT, x=0.05, ha="left")
    fig.subplots_adjust(left=0.2, right=0.74, top=0.9, bottom=0.07)
    if show:
        plt.show()
    return fig, ax


def _pitch_pair(team_name: str, half: bool, fig_size, title: str, subtitle: str | None = None):
    pitch = make_pitch(half=half, pad_top=4, pad_bottom=4 if not half else -2, line_color="#b9c2cc",
                       linewidth=1)
    fig, axes = plt.subplots(1, 2, figsize=fig_size, facecolor="white")
    for ax in axes:
        pitch.draw(ax=ax)
    fig.suptitle(title, fontsize=15, fontweight="bold", color=TEXT, y=0.985)
    if subtitle:
        fig.text(0.5, 0.925, subtitle, ha="center", fontsize=10, color=MUTED)
    return pitch, axes


def _side_heading(ax, df: pd.DataFrame, heading: str, colour: str, kind: str) -> None:
    lines = [f"{len(df)} taken  ·  found a team mate {_rate(df)}  ·  kept {KEEP_SECONDS}s {_rate(df, 'kept')}"]
    split = "  ·  ".join(f"{d} {_rate(g)}" for d, g in df.groupby("delivery"))
    if split and kind != "throw_in":
        lines.append(split)
    ax.set_title(heading + "\n" + "\n".join(lines), fontsize=10.5, color=TEXT, loc="center")
    ax.title.set_color(colour)


SIDES = (("for", "{team}'s {name}", WON_COL), ("against", "The opposition's {name} against {team}", OPPO_COL))


def plot_restart_zones(
    df: pd.DataFrame,
    kind: str,
    team_name: str,
    title: str,
    min_count: int = 3,
    fig_size=(16, 12),
    show: bool = True,
):
    """Where the restarts landed, in zones coloured by how often they found a team mate.

    df is wyscout.data.restarts.season_restarts' output. One pitch for the
    team's restarts and one for the opposition's, each attacking up the page
    from the taker's own goal. A zone is red under 50%, grey at 50% and blue
    above; it carries "completed / taken". Zones with fewer than min_count
    restarts are faded and show no percentage. Corners use a half pitch with
    the box cut into zones.
    """
    half = kind == "corner"
    if half:
        fig_size = (fig_size[0], fig_size[1] * 0.7)
    xs, ys = ZONES["corner" if half else "end"]
    df = df[df["kind"] == kind]
    pitch, axes = _pitch_pair(team_name, half, fig_size, title,
                              "Each zone: completed / taken, where the ball landed. "
                              f"Red = lost more often than found, blue = found a team mate more often. "
                              f"Faded = fewer than {min_count}.")
    for ax, (side, heading, colour) in zip(axes, SIDES):
        mine = df[df["side"] == side]
        name = RESTART_NAMES[kind].lower()
        _side_heading(ax, mine, heading.format(team=team_name, name=name), colour, kind)
        counts = pitch.bin_statistic(mine["end_x"], mine["end_y"], statistic="count", bins=(xs, ys))
        done = pitch.bin_statistic(mine["end_x"], mine["end_y"], mine["completed"].astype(float),
                                   statistic="sum", bins=(xs, ys))
        n = counts["statistic"]
        rate = np.where(n > 0, done["statistic"] / np.where(n > 0, n, 1), np.nan)
        shown = counts | {"statistic": np.where(n >= min_count, rate, np.nan)}
        faded = counts | {"statistic": np.where((n > 0) & (n < min_count), rate, np.nan)}
        pitch.heatmap(shown, ax=ax, cmap=COMPLETION_CMAP, vmin=0, vmax=1, edgecolor="white", linewidth=2, zorder=1)
        pitch.heatmap(faded, ax=ax, cmap=COMPLETION_CMAP, vmin=0, vmax=1, edgecolor="white", linewidth=2,
                      alpha=0.3, zorder=1)
        for (r, c), count in np.ndenumerate(n):
            if not count:
                continue
            cx, cy = counts["cx"][r, c], counts["cy"][r, c]
            strong = count >= min_count and abs(rate[r, c] - 0.5) > 0.3
            label = f"{int(done['statistic'][r, c])}/{int(count)}"
            if count >= min_count:
                label = f"{rate[r, c]:.0%}\n{label}"
            pitch.text(cx, cy, label, ax=ax, ha="center", va="center", fontsize=10 if count >= min_count else 8.5,
                       fontweight="bold" if count >= min_count else "normal",
                       color="white" if strong else TEXT, zorder=3)
        if kind == "goal_kick":
            pitch.scatter(mine["x"], mine["y"], ax=ax, s=40, marker="s", color=TEXT, zorder=4)
    plt.subplots_adjust(left=0.02, right=0.98, top=0.86, bottom=0.02, wspace=0.05)
    if show:
        plt.show()
    return plt.gcf(), axes


def plot_restart_dots(
    df: pd.DataFrame,
    kind: str,
    team_name: str,
    title: str,
    at: str = "start",
    fig_size=(16, 12),
    show: bool = True,
):
    """Every restart as a dot - a blue circle when it found a team mate, a red cross when it did not.

    df is wyscout.data.restarts.season_restarts' output. at="start" puts the
    dot where it was taken (throw-ins, free kicks), at="end" where it landed
    (corners). A dot ringed in black was lost at first contact but won back
    within KEEP_SECONDS. One pitch for the team and one for the opposition,
    both attacking up the page; each third carries its completion rate.
    """
    half = kind == "corner"
    if half:
        fig_size = (fig_size[0], fig_size[1] * 0.7)
    df = df[df["kind"] == kind]
    pitch, axes = _pitch_pair(team_name, half, fig_size, title)
    px, py = ("x", "y") if at == "start" else ("end_x", "end_y")
    for ax, (side, heading, colour) in zip(axes, SIDES):
        mine = df[df["side"] == side]
        _side_heading(ax, mine, heading.format(team=team_name, name=RESTART_NAMES[kind].lower()), colour, kind)
        won, lost = mine[mine["completed"]], mine[~mine["completed"]]
        pitch.scatter(won[px], won[py], ax=ax, s=55, color=WON_COL, alpha=0.65, edgecolor="white", linewidth=0.6,
                      zorder=3)
        recovered = lost[lost["kept"]]
        pitch.scatter(recovered[px], recovered[py], ax=ax, s=170, facecolor="none", edgecolor=TEXT, linewidth=1.2,
                      zorder=3)
        pitch.scatter(lost[px], lost[py], ax=ax, s=90, marker="X", color=LOST_COL, edgecolor="white",
                      linewidth=0.6, zorder=4)
        if not half:
            for i, third in enumerate(("own third", "middle third", "final third")):
                part = mine[(mine[px] >= i * 100 / 3) & (mine[px] < (i + 1) * 100 / 3 + (i == 2))]
                if len(part):
                    pitch.text(i * 100 / 3 + 100 / 6, 50, f"{third}\n{_rate(part)}", ax=ax, ha="center",
                               va="center", fontsize=11, color=TEXT, zorder=5,
                               bbox={"facecolor": "white", "edgecolor": GRID, "alpha": 0.9, "boxstyle": "round"})
    axes[0].legend(handles=[
        Line2D([], [], marker="o", linestyle="", markersize=9, color=WON_COL, label="Found a team mate"),
        Line2D([], [], marker="X", linestyle="", markersize=9, color=LOST_COL, label="First contact lost"),
        Line2D([], [], marker="o", linestyle="", markersize=12, markerfacecolor="none", markeredgecolor=TEXT,
               label=f"...but won back within {KEEP_SECONDS}s"),
    ], loc="upper left", bbox_to_anchor=(0, 0.0), frameon=False, fontsize=10, ncol=3)
    plt.subplots_adjust(left=0.02, right=0.98, top=0.86, bottom=0.06, wspace=0.05)
    if show:
        plt.show()
    return plt.gcf(), axes


def plot_restart_arrows(
    df: pd.DataFrame,
    kind: str,
    team_name: str,
    title: str,
    fig_size=(16, 12),
    show: bool = True,
):
    """Every restart as an arrow from where it was taken to where it landed - blue found a team mate, red did not.

    df is wyscout.data.restarts.season_restarts' output. The lost ones are
    drawn on top. One pitch for the team and one for the opposition.
    """
    df = df[df["kind"] == kind]
    pitch, axes = _pitch_pair(team_name, False, fig_size, title)
    for ax, (side, heading, colour) in zip(axes, SIDES):
        mine = df[df["side"] == side]
        _side_heading(ax, mine, heading.format(team=team_name, name=RESTART_NAMES[kind].lower()), colour, kind)
        for done, col, alpha, z in ((True, WON_COL, 0.35, 2), (False, LOST_COL, 0.75, 3)):
            part = mine[mine["completed"] == done]
            pitch.arrows(part["x"], part["y"], part["end_x"], part["end_y"], ax=ax, color=col, alpha=alpha,
                         width=1.6, headwidth=5, headlength=5, zorder=z)
    axes[0].legend(handles=[Patch(color=WON_COL, label="Found a team mate"),
                            Patch(color=LOST_COL, label="First contact lost")],
                   loc="upper left", bbox_to_anchor=(0, 0.0), frameon=False, fontsize=10, ncol=2)
    plt.subplots_adjust(left=0.02, right=0.98, top=0.86, bottom=0.05, wspace=0.05)
    if show:
        plt.show()
    return plt.gcf(), axes


def plot_restart_trend(
    df: pd.DataFrame,
    team_name: str,
    title: str,
    kinds: Sequence[str] = RESTARTS,
    rolling: int = 3,
    fig_size=(16, 10),
    show: bool = True,
):
    """Completion game by game, one panel per restart - ours against the opposition's.

    df is wyscout.data.restarts.season_restarts' output. Dots are each game,
    sized by how many restarts there were; the line is the rate over the last
    `rolling` games pooled, so a game with two corners counts for less than
    one with ten.
    """
    games = df.drop_duplicates("game").set_index("game").sort_index()
    with sns.axes_style("white"):
        fig, axes = plt.subplots(2, 2, figsize=fig_size, facecolor="white", sharex=True, sharey=True)
    for ax, kind in zip(axes.ravel(), kinds):
        for side, colour, marker, label in (("for", WON_COL, "o", team_name), ("against", OPPO_COL, "D", "Opposition")):
            part = df[(df["kind"] == kind) & (df["side"] == side)]
            per_game = part.groupby("game")["completed"].agg(["sum", "count"]).reindex(games.index, fill_value=0)
            rate = per_game["sum"] / per_game["count"].replace(0, np.nan)
            pooled = (per_game["sum"].rolling(rolling, min_periods=1).sum()
                      / per_game["count"].rolling(rolling, min_periods=1).sum().replace(0, np.nan))
            ax.plot(per_game.index, pooled, color=colour, linewidth=2, zorder=3,
                    label=f"{label} - last {rolling} games")
            ax.scatter(per_game.index, rate, s=per_game["count"] * 12 + 10, color=colour, marker=marker, alpha=0.4,
                       edgecolor="white", linewidth=0.8, zorder=2, label=f"{label} - one game")
            total = part["completed"].mean()
            ax.text(1.01, total, f"{total:.0%}", transform=ax.get_yaxis_transform(), color=colour, va="center",
                    fontsize=10, fontweight="bold")
        ax.set_title(RESTART_NAMES[kind], fontsize=12, fontweight="bold", color=TEXT, loc="left")
        ax.set_ylim(0, 1.05)
        ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
        ax.grid(axis="y", color=GRID, zorder=0)
        sns.despine(ax=ax)
    for ax in axes[-1]:
        ax.set_xticks(games.index)
        ax.set_xticklabels(games["short_label"], rotation=90, fontsize=9)
        for tick, result in zip(ax.get_xticklabels(), games["result"]):
            tick.set_color(RESULT_FG[result])
    axes[0, 0].legend(loc="lower left", frameon=False, fontsize=9, ncol=2)
    fig.suptitle(title, fontsize=15, fontweight="bold", color=TEXT)
    fig.text(0.5, 0.94, "Share of restarts whose first contact was a team mate. Season rate on the right of each "
             "panel. Opponent names coloured by result.", ha="center", fontsize=10, color=MUTED)
    fig.subplots_adjust(left=0.06, right=0.95, top=0.88, bottom=0.14, hspace=0.25, wspace=0.12)
    if show:
        plt.show()
    return fig, axes
