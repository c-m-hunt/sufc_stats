"""Substitutions against field tilt."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import gridspec, ticker
from matplotlib.patches import Patch

from wyscout.viz.consts import GRID, MUTED, NAVY, RESULT_FG, TEXT
from wyscout.viz.season import OPPO_SUB_COL, SUB_STATES, TILT_AGAINST, TILT_FOR, _surname

# the substitutions module calls a level score "level", the season charts "drawing"
STATE_COLOURS = {"losing": SUB_STATES["losing"], "level": SUB_STATES["drawing"], "winning": SUB_STATES["winning"]}
UP, DOWN = TILT_FOR, TILT_AGAINST


def _tidy(ax: plt.Axes) -> None:
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=8.5)
    ax.set_axisbelow(True)


def plot_sub_tilt_changes(windows: pd.DataFrame, title: str, team_name: str, window: float = 15,
                          min_passes: int = 8, show: bool = True):
    """Every change window as a before-and-after dumbbell of field tilt.

    windows is wyscout.data.substitutions.season_change_windows' first output.
    One row per change, oldest at the top: a hollow dot for our field tilt in
    the window minutes before, a filled dot for the window after, joined by an
    arrow navy when the territory moved our way and red when it moved theirs.
    The chip on the left is the score state when the change was made. Rows with
    fewer than min_passes final-third passes after the change are faded.
    """
    df = windows.reset_index(drop=True)
    n = len(df)
    fig, ax = plt.subplots(figsize=(13, 0.34 * n + 2.4))
    ax.set_xlim(-64, 160)
    ax.set_ylim(n - 0.4, -1.4)
    ax.axis("off")

    # pitch for the dumbbells: 0-100% runs from x 0 to 100
    for v in (0, 25, 50, 75, 100):
        ax.plot([v, v], [-0.6, n - 0.5], color=TEXT if v == 50 else GRID, linewidth=1.1 if v == 50 else 0.7,
                zorder=1)
        ax.text(v, -0.8, f"{v}%", ha="center", va="bottom", fontsize=8.5, color=MUTED)

    last_match = None
    for i, r in df.iterrows():
        faded = (r["after_for"] + r["after_against"]) < min_passes
        alpha = 0.35 if faded else 1.0
        if r["match_id"] != last_match:
            if last_match is not None:
                ax.plot([-62, 160], [i - 0.5, i - 0.5], color=GRID, linewidth=0.8, zorder=0)
            venue = "vs" if r["venue"] == "H" else "@"
            ax.text(-63, i, f"{r['game']}. {venue} {r['opponent'][:22]}", ha="left", va="center", fontsize=9,
                    weight="bold", color=TEXT)
            ax.text(-23, i, f"{r['result']} {r['score']}", ha="left", va="center", fontsize=8.5, weight="bold",
                    color=RESULT_FG.get(r["result"], TEXT))
            last_match = r["match_id"]

        ax.text(-6, i, f"{r['minute']}'", ha="right", va="center", fontsize=8.5, color=MUTED)
        ax.add_patch(plt.Rectangle((-15.5, i - 0.3), 3.2, 0.6, color=STATE_COLOURS[r["state"]], zorder=2))

        b, a = r["tilt_before"], r["tilt_after"]
        colour = UP if a >= b else DOWN
        if np.isfinite(b) and np.isfinite(a):
            ax.annotate("", (a, i), (b, i), arrowprops={"arrowstyle": "-|>", "color": colour, "lw": 1.6,
                                                         "shrinkA": 4, "shrinkB": 4, "alpha": alpha}, zorder=3)
        ax.scatter(b, i, s=40, facecolor="white", edgecolor=MUTED, linewidth=1.3, zorder=4, alpha=alpha)
        ax.scatter(a, i, s=48, color=colour, edgecolor="white", linewidth=0.8, zorder=5, alpha=alpha)

        notes = []
        if r["goals_for_after"]:
            notes.append(f"scored {r['goals_for_after']}")
        if r["goals_against_after"]:
            notes.append(f"conceded {r['goals_against_after']}")
        if r["oppo_changed"]:
            notes.append("they changed too")
        ax.text(104, i, f"{r['change']:+.0f}", ha="left", va="center", fontsize=9, weight="bold", color=colour,
                alpha=alpha)
        on = ", ".join(_surname(p) for p in r["players_in"].split(", "))
        ax.text(113, i, f"on: {on}" + (f"   ({'; '.join(notes)})" if notes else ""), ha="left", va="center",
                fontsize=8, color=TEXT, alpha=alpha)

    ax.text(103, -0.8, "+/-", ha="left", va="bottom", fontsize=8.5, color=MUTED)
    ax.text(113, -0.8, "Brought on", ha="left", va="bottom", fontsize=8.5, color=MUTED)

    up = (df["change"] > 0).sum()
    fig.suptitle(title, x=0.01, ha="left", fontsize=15, weight="bold", color=TEXT, y=0.995)
    fig.text(0.01, 1 - 0.5 / fig.get_size_inches()[1],
             f"{team_name}'s field tilt in the {window:g} minutes before each change (hollow) and the {window:g} after "
             f"(filled). Territory moved our way after {up} of {n} changes. Faded rows have under {min_passes} "
             "final-third passes after the change.\nChanges a few minutes apart share some of the same passes, and "
             "goals move tilt on their own - check the notes.",
             fontsize=9.5, color=MUTED, va="top")
    fig.legend(handles=[Patch(color=c, label=f"Made when {s}") for s, c in STATE_COLOURS.items()],
               loc="lower left", ncol=3, frameon=False, fontsize=9, bbox_to_anchor=(0.01, 0.0))
    fig.tight_layout(rect=(0, 0.03, 1, 1 - 1.0 / fig.get_size_inches()[1]))
    if show:
        plt.show()
    return fig, ax


def _curve_panel(ax: plt.Axes, ours: pd.DataFrame, theirs: pd.DataFrame | None, title: str,
                 label_lines: bool = False) -> None:
    ax.axhline(50, color=TEXT, linewidth=1, zorder=2)
    ax.axvline(0, color=TEXT, linewidth=1, linestyle=":", zorder=2)
    if theirs is not None and theirs["n"].iloc[0] > 0:
        ax.plot(theirs["t"], theirs["tilt"], color=OPPO_SUB_COL, linewidth=1.8, linestyle="--", zorder=3,
                label=f"Around their changes ({theirs['n'].iloc[0]})")
    if ours["n"].iloc[0] > 0:
        ax.fill_between(ours["t"], ours["low"], ours["high"], color=NAVY, alpha=0.15, lw=0, zorder=3)
        ax.plot(ours["t"], ours["tilt"], color=NAVY, linewidth=2.4, zorder=4,
                label=f"Around our changes ({ours['n'].iloc[0]})")
    ax.set_title(title, loc="left", fontsize=11, weight="bold", color=TEXT)
    ax.set_ylim(30, 100)  # pooled tilt rarely leaves this band, and the full 0-100 flattens the dip at the change
    ax.yaxis.set_major_formatter(ticker.PercentFormatter())
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v:+.0f}'" if v else "sub"))
    ax.grid(axis="y", color=GRID, linewidth=0.6)
    if label_lines:
        ax.legend(loc="lower right", frameon=False, fontsize=8.5)
    _tidy(ax)


def plot_aligned_tilt(curves: dict[str, tuple[pd.DataFrame, pd.DataFrame | None]], title: str, team_name: str,
                      smooth: float = 5, show: bool = True):
    """The average field tilt in the minutes either side of a substitution.

    curves maps a panel name to (ours, theirs), each
    wyscout.data.substitutions.aligned_tilt_curve output - the first entry is
    drawn large, the rest as small panels beneath (e.g. by score state). Every
    change is lined up at 0; navy is the pooled tilt around our changes with a
    10-90% bootstrap band, dashed gray our tilt around the opposition's.
    """
    names = list(curves)
    small = len(names) - 1
    fig = plt.figure(figsize=(13, 8.5 if small else 5.5))
    gs = gridspec.GridSpec(2 if small else 1, max(small, 1), height_ratios=[1.5, 1] if small else [1], hspace=0.45,
                           wspace=0.18)
    main = fig.add_subplot(gs[0, :])
    _curve_panel(main, *curves[names[0]], names[0], label_lines=True)
    main.set_ylabel("Our field tilt", color=MUTED, fontsize=9.5)
    for k, name in enumerate(names[1:]):
        ax = fig.add_subplot(gs[1, k], sharey=main)
        _curve_panel(ax, *curves[name], name)
        ax.title.set_color(STATE_COLOURS.get(name.split()[-1], TEXT))

    fig.suptitle(title, x=0.01, ha="left", fontsize=15, weight="bold", color=TEXT, y=0.995)
    fig.text(0.01, 1 - 0.55 / fig.get_size_inches()[1],
             f"Every change lined up at 'sub'; the line at each minute is {team_name}'s share of all the completed "
             f"final-third passes in the {smooth:g} minutes before it, pooled over the changes. The shaded band is "
             "where 80% of resamples of the changes land - if it straddles the line before the sub, the change is "
             "inside the noise.",
             fontsize=9.5, color=MUTED, va="top", wrap=True)
    fig.subplots_adjust(top=1 - 1.4 / fig.get_size_inches()[1], left=0.06, right=0.98, bottom=0.07)
    if show:
        plt.show()
    return fig


def plot_player_sub_impact(df: pd.DataFrame, title: str, team_name: str, window: float = 15, show: bool = True):
    """Field tilt before and after each player came on (left) and went off (right).

    df is wyscout.data.substitutions.player_sub_impact's output. One dumbbell
    per player, biggest swing our way at the top: hollow is the pooled tilt in
    the window before the changes, filled the window after; the number of
    changes is beside the name.
    """
    roles = [("on", "Brought on"), ("off", "Taken off")]
    rows = max(int((df["role"] == r).sum()) for r, _ in roles)
    fig, axes = plt.subplots(1, 2, figsize=(13, 0.36 * rows + 2.2), sharex=True)
    for ax, (role, heading) in zip(axes, roles):
        d = df[df["role"] == role].reset_index(drop=True)
        for i, r in d.iterrows():
            colour = UP if r["change"] >= 0 else DOWN
            ax.annotate("", (r["tilt_after"], i), (r["tilt_before"], i),
                        arrowprops={"arrowstyle": "-|>", "color": colour, "lw": 1.8, "shrinkA": 4, "shrinkB": 4})
            ax.scatter(r["tilt_before"], i, s=44, facecolor="white", edgecolor=MUTED, linewidth=1.3, zorder=4)
            ax.scatter(r["tilt_after"], i, s=52, color=colour, edgecolor="white", linewidth=0.8, zorder=5)
            ax.text(101, i, f"{r['change']:+.0f}", ha="left", va="center", fontsize=9, weight="bold", color=colour)
        ax.set_yticks(range(len(d)))
        ax.set_yticklabels([f"{r.player}  ({r.apps})" for r in d.itertuples()], fontsize=9, color=TEXT)
        ax.set_ylim(rows - 0.5, -0.7)
        ax.set_xlim(0, 100)
        ax.axvline(50, color=TEXT, linewidth=1)
        ax.xaxis.set_major_formatter(ticker.PercentFormatter())
        ax.grid(axis="x", color=GRID, linewidth=0.6)
        ax.set_title(heading, loc="left", fontsize=12, weight="bold", color=TEXT)
        _tidy(ax)
        ax.tick_params(axis="y", length=0)

    fig.suptitle(title, x=0.01, ha="left", fontsize=15, weight="bold", color=TEXT, y=0.995)
    fig.text(0.01, 1 - 0.5 / fig.get_size_inches()[1],
             f"{team_name}'s field tilt in the {window:g} minutes before (hollow) and after (filled) the changes each "
             "player was part of, pooled. The number in brackets is how many changes. A double change counts for "
             "everyone in it, so this is association, not proof of one player's effect.",
             fontsize=9.5, color=MUTED, va="top", wrap=True)
    fig.tight_layout(rect=(0, 0, 1, 1 - 0.85 / fig.get_size_inches()[1]), w_pad=4)
    if show:
        plt.show()
    return fig, axes
