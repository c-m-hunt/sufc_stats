"""Physical-report charts for one match, drawn from wyscout.data.physical.PhysicalMatch.

Every chart is about Southend: their players are the marks, in blue, and the opposition is
context - grey reference lines and dots. Goalkeepers are left out throughout; their running
is a different job and the API does not always include them.
"""

from collections.abc import Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.figure import Figure
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from matplotlib.transforms import Bbox

from wyscout.data.physical import BLOCK_STARTS, BLOCKS, PhysicalMatch
from wyscout.viz.consts import APP_FONT, GRID, MUTED, NAVY, TEXT
from wyscout.viz.utils import load_image

FOCUS = "#1f6fb2"  # Southend
FOCUS_DARK = NAVY  # sprinting, the top of the blue ramp
FOCUS_LIGHT = "#6d9fd3"  # high-speed running
OTHER = "#848f9b"  # the opposition, always context
SURFACE = "white"
INTENSITY = LinearSegmentedColormap.from_list("intensity", ["#f1f6fc", FOCUS_LIGHT, FOCUS, NAVY])

POSITION_ORDER = {"DF": 0, "MD": 1, "FW": 2}


# --- shared pieces ----------------------------------------------------------------------------


def team_sides(pm: PhysicalMatch, team: str) -> tuple[str, str]:
    """(focus side, other side) - "home"/"away" for the team being reported on."""
    focus = "home" if pm.home == team else "away"
    if pm.team_name(focus) != team:
        raise ValueError(f"{team} did not play in {pm.label}")
    return focus, "away" if focus == "home" else "home"


def _badge(url: str | None, size: int = 96) -> np.ndarray | None:
    if not url:
        return None
    try:
        image = load_image(url).convert("RGBA")
    except (OSError, ValueError):  # a missing badge should never stop the chart
        return None
    image.thumbnail((size, size))
    return np.asarray(image)


def match_header(
    fig: Figure, pm: PhysicalMatch, title: str, subtitle: str, top: float = 0.97
) -> None:
    fig.text(
        0.02,
        top,
        title,
        fontproperties=APP_FONT.prop,
        fontsize=22,
        color=TEXT,
        weight="bold",
        va="top",
    )
    fig.text(
        0.02,
        top - 0.055 * (10 / fig.get_figheight()),
        subtitle,
        fontproperties=APP_FONT.prop,
        fontsize=12.5,
        color=MUTED,
        va="top",
    )
    for i, url in enumerate((pm.away_badge, pm.home_badge)):
        badge = _badge(url)
        if badge is not None:
            fig.add_artist(
                AnnotationBbox(
                    OffsetImage(badge, zoom=0.42),
                    (0.975 - i * 0.045, top - 0.035 * (10 / fig.get_figheight())),
                    xycoords="figure fraction",
                    frameon=False,
                )
            )


def match_line(pm: PhysicalMatch) -> str:
    home_goals = sum(g.team == "home" for g in pm.goals)
    away_goals = sum(g.team == "away" for g in pm.goals)
    return f"{pm.home} {home_goals}-{away_goals} {pm.away}"


def _style(ax: plt.Axes, grid_axis: str = "x") -> None:
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(colors=MUTED, labelsize=10, length=0)
    if grid_axis:
        ax.grid(True, axis=grid_axis, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def _panel_title(ax: plt.Axes, title: str, unit: str) -> None:
    ax.set_title(title, loc="left", fontproperties=APP_FONT.prop, fontsize=15, color=TEXT, pad=30)
    ax.text(0, 1.0, unit, transform=ax.transAxes, fontsize=10, color=MUTED, va="bottom")


def _reference(ax: plt.Axes, x: float, label: str, rows: int) -> None:
    """A grey line across a bar panel: where the opposition's best or average sits."""
    ax.axvline(x, color=OTHER, linewidth=1.4, zorder=1)
    ax.text(x, rows - 0.45, f" {label}", color=OTHER, fontsize=9.5, va="bottom", ha="left")


def _minutes(m: float) -> str:
    return f"{m:.0f}'"


def _focus_rows(pm: PhysicalMatch, focus: str, by: str = "distance") -> pd.DataFrame:
    return pm.outfield(focus).sort_values(by, ascending=True).reset_index(drop=True)


# --- 1. headline ------------------------------------------------------------------------------


def plot_physical_headline(pm: PhysicalMatch, team: str) -> Figure:
    """The match in four numbers: the team's outfield totals against the opposition's. No top
    speed - the API's is a single frame, and the tracking cannot settle who was fastest."""
    focus, other = team_sides(pm, team)
    us, them = pm.outfield(focus), pm.outfield(other)

    def rate(p: pd.DataFrame) -> float:
        return p.distance.sum() / p.minutes.sum()

    tiles = [
        (
            "Distance covered",
            f"{us.distance.sum() / 1000:.1f}",
            "km",
            f"{them.distance.sum() / 1000:.1f} km",
            f"{(us.distance.sum() - them.distance.sum()) / 1000:+.1f} km",
        ),
        (
            "Work rate",
            f"{rate(us):.0f}",
            "m/min",
            f"{rate(them):.0f} m/min",
            f"{rate(us) - rate(them):+.0f} m/min",
        ),
        (
            "High-intensity running",
            f"{us.hi.sum() / 1000:.2f}",
            "km",
            f"{them.hi.sum() / 1000:.2f} km",
            f"{(us.hi.sum() - them.hi.sum()):+,.0f} m",
        ),
        (
            "Sprints",
            f"{us.sprints.sum():.0f}",
            "",
            f"{them.sprints.sum():.0f}",
            f"{us.sprints.sum() - them.sprints.sum():+.0f}",
        ),
    ]

    fig = plt.figure(figsize=(16, 4.4), facecolor=SURFACE)
    match_header(
        fig,
        pm,
        f"{match_line(pm)}  ·  physical report",
        f"{team}'s outfield players against {pm.team_name(other)}'s. High intensity is "
        "running over 20 km/h, a sprint over 25 km/h.",
        top=0.95,
    )
    for i, (label, value, unit, theirs, note) in enumerate(tiles):
        ax = fig.add_axes((0.02 + i * 0.245, 0.08, 0.225, 0.56))
        ax.set_axis_off()
        ax.add_patch(
            plt.Rectangle(
                (0, 0), 1, 1, transform=ax.transAxes, color="#f4f6f8", zorder=0, linewidth=0
            )
        )
        ax.text(
            0.07,
            0.86,
            label.upper(),
            transform=ax.transAxes,
            fontsize=10.5,
            color=MUTED,
            weight="bold",
        )
        big = ax.text(
            0.07,
            0.47,
            value,
            transform=ax.transAxes,
            fontsize=38,
            color=FOCUS,
            fontproperties=APP_FONT.prop,
            weight="bold",
            va="center",
        )
        fig.canvas.draw()
        right = ax.transAxes.inverted().transform(
            big.get_window_extent(fig.canvas.get_renderer()).corners()[-1]
        )[0]
        ax.text(
            right + 0.03, 0.40, unit, transform=ax.transAxes, fontsize=13, color=FOCUS, va="center"
        )
        ax.text(
            0.07,
            0.13,
            f"{pm.team_name(other)}  {theirs}",
            transform=ax.transAxes,
            fontsize=10.5,
            color=MUTED,
        )
        ax.text(
            0.93,
            0.13,
            note,
            transform=ax.transAxes,
            fontsize=10.5,
            color=TEXT,
            ha="right",
            weight="bold",
        )
    return fig


# --- 2. who ran furthest ----------------------------------------------------------------------


def plot_distance_ladder(pm: PhysicalMatch, team: str) -> Figure:
    """Each outfield player's distance, work rate and high-intensity metres, with the
    opposition's best (or average) as a grey line in each panel."""
    focus, other = team_sides(pm, team)
    rows = _focus_rows(pm, focus)
    them = pm.outfield(other)
    n = len(rows)
    y = np.arange(n)

    fig, axs = plt.subplots(
        1,
        3,
        figsize=(16, 2.4 + 0.5 * n),
        sharey=True,
        facecolor=SURFACE,
        gridspec_kw={"width_ratios": [1.25, 0.9, 1.25], "wspace": 0.08},
    )
    fig.subplots_adjust(left=0.13, right=0.98, top=1 - 1.9 / (2.4 + 0.5 * n), bottom=0.03)
    leader = rows.loc[rows.distance.idxmax()]
    match_header(
        fig,
        pm,
        f"Who ran furthest - {leader['name']}, {leader.distance / 1000:.2f} km",
        f"{match_line(pm)}  ·  {team} outfield players, by distance. Grey lines are "
        f"{pm.team_name(other)}'s best (average for work rate).",
    )

    # distance
    ax = axs[0]
    ax.barh(y, rows.distance / 1000, height=0.62, color=FOCUS, zorder=2)
    for yi, r in zip(y, rows.itertuples()):
        ax.text(
            r.distance / 1000 + 0.12,
            yi,
            f"{r.distance / 1000:.2f}",
            va="center",
            fontsize=10.5,
            color=TEXT,
            weight="bold" if r.Index == leader.name else "normal",
        )
        ax.text(
            1.0,
            yi,
            _minutes(r.minutes),
            va="center",
            ha="right",
            fontsize=10,
            color=MUTED,
            transform=ax.get_yaxis_transform(),
        )
    best = them.loc[them.distance.idxmax()]
    _reference(ax, best.distance / 1000, f"{best['name']} {best.distance / 1000:.1f}", n)
    ax.set_xlim(0, rows.distance.max() / 1000 * 1.3)
    ax.text(
        1.0,
        n + 0.2,
        "MINS",
        transform=ax.get_yaxis_transform(),
        ha="right",
        va="bottom",
        fontsize=9,
        color=MUTED,
        weight="bold",
    )
    _panel_title(ax, "Distance", "km")

    # work rate
    ax = axs[1]
    lo = min(rows.m_per_min.min(), them.m_per_min.min()) - 8
    ax.hlines(y, lo, rows.m_per_min, color=GRID, linewidth=2, zorder=1)
    ax.scatter(rows.m_per_min, y, s=110, color=FOCUS, edgecolors=SURFACE, linewidths=2, zorder=3)
    top_rate = rows.m_per_min.idxmax()
    for yi, r in zip(y, rows.itertuples()):
        ax.text(
            r.m_per_min + 1.6,
            yi,
            f"{r.m_per_min:.0f}",
            va="center",
            fontsize=10.5,
            color=TEXT,
            weight="bold" if r.Index == top_rate else "normal",
        )
    avg = them.distance.sum() / them.minutes.sum()
    _reference(ax, avg, f"avg {avg:.0f}", n)
    ax.set_xlim(lo, rows.m_per_min.max() + 9)
    _panel_title(ax, "Work rate", "metres per minute on the pitch")

    # high intensity, split HSR / sprint
    ax = axs[2]
    ax.barh(
        y, rows.hsr, height=0.62, color=FOCUS_LIGHT, zorder=2, label="High-speed running 20-25 km/h"
    )
    ax.barh(
        y,
        rows.sprinting,
        left=rows.hsr,
        height=0.62,
        color=FOCUS_DARK,
        zorder=2,
        edgecolor=SURFACE,
        linewidth=2,
        label="Sprinting over 25 km/h",
    )
    top_hi = rows.hi.idxmax()
    for yi, r in zip(y, rows.itertuples()):
        ax.text(
            r.hi + 18,
            yi,
            f"{r.hi:,.0f}",
            va="center",
            fontsize=10.5,
            color=TEXT,
            weight="bold" if r.Index == top_hi else "normal",
        )
    best = them.loc[them.hi.idxmax()]
    _reference(ax, best.hi, f"{best['name']} {best.hi:,.0f}", n)
    ax.set_xlim(0, max(rows.hi.max(), best.hi) * 1.18)
    ax.legend(loc="lower right", frameon=False, fontsize=9.5, labelcolor=TEXT)
    _panel_title(ax, "High-intensity running", "metres over 20 km/h")

    for ax in axs:
        _style(ax)
        ax.set_ylim(-0.6, n + 0.2)
        ax.tick_params(axis="x", labelbottom=False)
        ax.grid(False)
    axs[0].set_yticks(y, rows.name, fontsize=11.5, color=TEXT)
    return fig


# --- 3. high-speed runs and sprints ------------------------------------------------------------


def _place_labels(
    ax: plt.Axes,
    points: Sequence[tuple[float, float, str]],
    fontsize: float,
    color: str,
    avoid: np.ndarray,
    dot_radius: float = 9,
) -> None:
    """Label each point beside it, at whichever of a ring of offsets overlaps the fewest
    labels already placed and dots (dot_radius in pixels), nearest offsets first."""
    fig = ax.figure
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    dots = [
        Bbox.from_bounds(px - dot_radius, py - dot_radius, 2 * dot_radius, 2 * dot_radius)
        for px, py in ax.transData.transform(avoid)
    ]
    offsets = [
        (dx * r, dy * r, ha, va)
        for r in (1, 1.8, 2.8)
        for dx, dy, ha, va in (
            (9, 0, "left", "center"),
            (-9, 0, "right", "center"),
            (0, 10, "center", "bottom"),
            (0, -10, "center", "top"),
            (8, 8, "left", "bottom"),
            (8, -8, "left", "top"),
            (-8, 8, "right", "bottom"),
            (-8, -8, "right", "top"),
        )
    ]
    placed: list[Bbox] = []
    for x, y, text in points:
        own = ax.transData.transform([(x, y)])[0]
        best = None
        for dx, dy, ha, va in offsets:
            far = abs(dx) > 10 or abs(dy) > 11
            t = ax.annotate(
                text,
                (x, y),
                xytext=(dx, dy),
                textcoords="offset points",
                ha=ha,
                va=va,
                fontsize=fontsize,
                color=color,
                zorder=5,
                arrowprops={
                    "arrowstyle": "-",
                    "color": MUTED,
                    "linewidth": 0.8,
                    "shrinkA": 0,
                    "shrinkB": 6,
                }
                if far
                else None,
            )
            box = t.get_window_extent(renderer).expanded(1.04, 1.15)
            inside = ax.bbox.contains(box.x0, box.y0) and ax.bbox.contains(box.x1, box.y1)
            clashes = sum(box.overlaps(b) for b in placed) + sum(
                box.overlaps(d) and not d.contains(*own) for d in dots
            )
            score = clashes + (0 if inside else 100)
            if best is None or score < best[0]:
                if best is not None:
                    best[1].remove()
                best = (score, t, box)
            else:
                t.remove()
            if score == 0:
                break
        placed.append(best[2])


def plot_runs_and_sprints(pm: PhysicalMatch, team: str) -> Figure:
    """High-speed runs (20-25 km/h) against sprints (over 25 km/h), every outfield player. The
    team's players are named; the opposition's are grey dots, with their busiest named for
    reference. The grey cross is the median of everyone on the pitch.

    Top speed is deliberately not here: the API's is the single fastest frame, which spikes,
    and checked against the positions the tracking cannot reliably say who was fastest."""
    focus, other = team_sides(pm, team)
    everyone = pm.outfield()
    us, them = pm.outfield(focus), pm.outfield(other)

    fig, ax = plt.subplots(figsize=(14, 9.5), facecolor=SURFACE)
    fig.subplots_adjust(left=0.07, right=0.97, top=0.85, bottom=0.08)
    most = us.loc[us.sprints.idxmax()]
    title = f"{most['name']} sprinted {most.sprints:.0f} times" + (
        " - more than anyone on the pitch" if most.sprints >= everyone.sprints.max() else ""
    )
    match_header(
        fig,
        pm,
        title,
        f"{match_line(pm)}  ·  high-speed runs (20-25 km/h) and sprints (over 25 km/h), "
        "outfield players. Players not on for the whole match show their minutes.",
    )

    mx, my = everyone.hsr_efforts.median(), everyone.sprints.median()
    ax.axvline(mx, color=GRID, linewidth=1.4, zorder=0)
    ax.axhline(my, color=GRID, linewidth=1.4, zorder=0)
    ax.scatter(
        them.hsr_efforts,
        them.sprints,
        s=90,
        color=OTHER,
        alpha=0.75,
        edgecolors=SURFACE,
        linewidths=2,
        zorder=2,
        label=pm.team_name(other),
    )
    ax.scatter(
        us.hsr_efforts,
        us.sprints,
        s=170,
        color=FOCUS,
        edgecolors=SURFACE,
        linewidths=2,
        zorder=3,
        label=team,
    )

    ax.set_xlim(0, everyone.hsr_efforts.max() * 1.12)
    ax.set_ylim(-1, everyone.sprints.max() * 1.15 + 1)
    for x, y, ha, va, text in (
        (0.99, 0.98, "right", "top", "LOTS OF BOTH"),
        (0.01, 0.98, "left", "top", "MORE FLAT-OUT SPRINTS"),
        (0.99, 0.02, "right", "bottom", "MORE HIGH-SPEED RUNS"),
        (0.01, 0.02, "left", "bottom", "FEWER OF EITHER"),
    ):
        ax.text(
            x,
            y,
            text,
            transform=ax.transAxes,
            ha=ha,
            va=va,
            fontsize=10.5,
            color=MUTED,
            weight="bold",
            alpha=0.8,
        )
    _style(ax, grid_axis="")
    ax.set_xlabel("High-speed runs, 20-25 km/h", fontsize=11, color=MUTED)
    ax.set_ylabel("Sprints, over 25 km/h", fontsize=11, color=MUTED)
    ax.legend(
        loc="upper center",
        frameon=False,
        fontsize=10.5,
        ncols=2,
        labelcolor=TEXT,
        bbox_to_anchor=(0.5, 1.0),
    )

    labels = [
        (r.hsr_efforts, r.sprints, r.name + ("" if r.minutes > 90 else f" ({_minutes(r.minutes)})"))
        for r in us.sort_values("sprints", ascending=False).itertuples()
    ]
    dots = everyone[["hsr_efforts", "sprints"]].to_numpy()
    _place_labels(ax, labels, 10.5, TEXT, dots)
    busiest = them.loc[(them.hsr_efforts + them.sprints).idxmax()]
    _place_labels(
        ax,
        [(busiest.hsr_efforts, busiest.sprints, busiest["name"])],
        9.5,
        MUTED,
        dots,
    )
    return fig


# --- 4. intensity through the match -----------------------------------------------------------


def _block_x(minute: float, durations: Sequence[float]) -> float:
    """Where a match minute falls on the block axis (block i spans i-0.5 to i+0.5)."""
    for i, (start, length) in enumerate(zip(BLOCK_STARTS, durations)):
        if minute < start + length or i == len(durations) - 1:
            return i - 0.5 + min(max((minute - start) / length, 0), 1)
    return len(durations) - 0.5


def plot_intensity_timeline(pm: PhysicalMatch, team: str, min_minutes: float = 5) -> Figure:
    """High-intensity running per minute through the match: both teams by 15-minute block, the
    goals marked, then every outfield player of the team block by block (blank when they were
    on for under min_minutes of it)."""
    focus, other = team_sides(pm, team)
    blocks = pm.blocks.merge(pm.players[["player_id", "position"]], on="player_id")
    blocks = blocks[blocks.position != "GK"]
    labels = list(BLOCKS.values())
    durations = blocks.groupby("block", observed=True).minutes.max().reindex(labels).to_numpy()

    def team_rate(side: str) -> np.ndarray:
        b = blocks[blocks.team == side].groupby("block", observed=True).hi.sum().reindex(labels)
        return b.to_numpy() / durations

    players = pm.outfield(focus).assign(order=lambda d: d.position.map(POSITION_ORDER))
    players = players.sort_values(["order", "minutes"], ascending=[True, False])
    grid = (
        blocks[(blocks.team == focus) & (blocks.minutes >= min_minutes)]
        .pivot_table(index="player_id", columns="block", values="hi_per_min", observed=False)
        .reindex(index=players.player_id, columns=labels)
    )
    n = len(players)

    fig = plt.figure(figsize=(15, 6.0 + 0.48 * n), facecolor=SURFACE)
    height = fig.get_figheight()
    top_ax = fig.add_axes((0.16, 1 - 4.3 / height, 0.8, 2.7 / height))
    heat_ax = fig.add_axes((0.16, 0.02, 0.8, (0.48 * n) / height))

    us, them = team_rate(focus), team_rate(other)
    ahead = int((us > them).sum())
    match_header(
        fig,
        pm,
        f"Intensity through the match - {team} out-ran {pm.team_name(other)} "
        f"at high intensity in {ahead} of {len(labels)} spells",
        f"{match_line(pm)}  ·  high-intensity running (over 20 km/h), metres per minute. "
        "Team lines add up every outfield player.",
    )

    x = np.arange(len(labels))
    top_ax.plot(
        x,
        them,
        color=OTHER,
        linewidth=2,
        marker="o",
        markersize=8,
        markeredgecolor=SURFACE,
        markeredgewidth=2,
        label=pm.team_name(other),
        zorder=2,
    )
    top_ax.plot(
        x,
        us,
        color=FOCUS,
        linewidth=2.6,
        marker="o",
        markersize=10,
        markeredgecolor=SURFACE,
        markeredgewidth=2,
        label=team,
        zorder=3,
    )
    nudge = 0 if abs(us[-1] - them[-1]) > 3 else 2.2
    top_ax.text(
        x[-1] + 0.1,
        us[-1] + nudge,
        f"{us[-1]:.0f}",
        color=TEXT,
        fontsize=10.5,
        va="center",
        weight="bold",
    )
    top_ax.text(
        x[-1] + 0.1, them[-1] - nudge, f"{them[-1]:.0f}", color=MUTED, fontsize=10.5, va="center"
    )
    lo, hi = min(us.min(), them.min()), max(us.max(), them.max())
    top_ax.set_ylim(lo - (hi - lo) * 0.35, hi + (hi - lo) * 0.6)
    for g in pm.goals:
        gx = _block_x(g.minute, durations)
        ours = g.team == focus
        colour = FOCUS if ours else OTHER
        top_ax.axvline(gx, color=colour, linewidth=1.2, alpha=0.7, zorder=1)
        who = g.scorer + (" (og)" if g.own_goal else "")
        top_ax.text(
            gx,
            1.0,
            f"{who} {int(g.minute) + 1}'",
            transform=top_ax.get_xaxis_transform(),
            rotation=90,
            ha="right",
            va="top",
            fontsize=9,
            color=TEXT if ours else MUTED,
        )
    top_ax.axvline(2.5, color=MUTED, linewidth=1, zorder=1)
    top_ax.text(
        2.5,
        0.02,
        " half-time",
        transform=top_ax.get_xaxis_transform(),
        fontsize=9,
        color=MUTED,
        va="bottom",
    )
    top_ax.set_xlim(-0.5, len(labels) - 0.5)
    top_ax.set_xticks(x, [])
    top_ax.legend(loc="lower left", frameon=False, fontsize=10, ncols=2, labelcolor=TEXT)
    top_ax.set_ylabel("team m/min", fontsize=10, color=MUTED)
    _style(top_ax, grid_axis="y")

    values = grid.to_numpy()
    vmax = np.nanpercentile(values, 95)
    heat_ax.imshow(
        np.ma.masked_invalid(values),
        cmap=INTENSITY,
        vmin=0,
        vmax=vmax,
        aspect="auto",
        extent=(-0.5, len(labels) - 0.5, n - 0.5, -0.5),
    )
    for i in range(n):
        for j in range(len(labels)):
            v = values[i, j]
            if np.isnan(v):
                heat_ax.add_patch(plt.Rectangle((j - 0.5, i - 0.5), 1, 1, color="#f4f6f8", lw=0))
                continue
            heat_ax.text(
                j,
                i,
                f"{v:.0f}",
                ha="center",
                va="center",
                fontsize=10.5,
                color="white" if v > vmax * 0.55 else TEXT,
            )
    for edge in np.arange(-0.5, len(labels)):
        heat_ax.axvline(edge, color=SURFACE, linewidth=3)
    for edge in np.arange(-0.5, n):
        heat_ax.axhline(edge, color=SURFACE, linewidth=3)
    heat_ax.axvline(2.5, color=MUTED, linewidth=1)
    names = [f"{r['name']}  {_minutes(r.minutes)}" for _, r in players.iterrows()]
    heat_ax.set_yticks(range(n), names, fontsize=11, color=TEXT)
    heat_ax.set_xticks(x, labels, fontsize=11, color=TEXT)
    heat_ax.xaxis.set_ticks_position("top")
    _style(heat_ax, grid_axis="")
    heat_ax.set_title(
        f"Each player, metres per minute over 20 km/h  ·  defenders, midfielders, "
        f"forwards  ·  blank when on for under {min_minutes:.0f} minutes of a spell",
        loc="left",
        fontproperties=APP_FONT.prop,
        fontsize=14,
        color=TEXT,
        pad=30,
    )
    return fig


# --- 5. bursts --------------------------------------------------------------------------------


def plot_accelerations(
    pm: PhysicalMatch, team: str, bursts: pd.DataFrame | None = None, min_minutes: float = 30
) -> Figure:
    """High accelerations and decelerations per player, back to back, per 90 minutes so a
    substitute's bursts compare with a starter's. Grey lines are the opposition's average.

    bursts (player_id, high_accels, high_decels - wyscout.data.tracking.burst_counts) replaces
    the API's counts, which include false bursts wherever the tracking lost a player. Players
    on for under min_minutes are faded: a per-90 rate from a short cameo is mostly noise."""
    focus, other = team_sides(pm, team)
    players = pm.outfield()
    if bursts is not None:
        players = players.drop(columns=["high_accels", "high_decels"]).merge(
            bursts[["player_id", "high_accels", "high_decels"]], on="player_id"
        )
    rows = players[players.team == focus].copy()
    them = players[players.team == other]
    for col in ("high_accels", "high_decels"):
        rows[f"{col}_90"] = rows[col] / rows.minutes * 90
    rows["total_90"] = rows.high_accels_90 + rows.high_decels_90
    rows = rows.sort_values("total_90").reset_index(drop=True)
    n = len(rows)
    y = np.arange(n)
    avg_acc = them.high_accels.sum() / them.minutes.sum() * 90
    avg_dec = them.high_decels.sum() / them.minutes.sum() * 90

    fig, ax = plt.subplots(figsize=(14, 2.4 + 0.5 * n), facecolor=SURFACE)
    fig.subplots_adjust(left=0.16, right=0.97, top=1 - 2.0 / (2.4 + 0.5 * n), bottom=0.03)
    most = rows.loc[(rows.high_accels + rows.high_decels).idxmax()]
    match_header(
        fig,
        pm,
        f"Bursts - {most['name']} made {most.high_accels + most.high_decels:.0f} "
        "sharp changes of pace",
        f"{match_line(pm)}  ·  speeding up or slowing down faster than 3 m/s², per 90 minutes "
        f"on the pitch. Grey lines are {pm.team_name(other)}'s average; faded bars are under "
        f"{min_minutes:.0f} minutes.",
    )

    short = (rows.minutes < min_minutes).to_numpy()
    for values, colour in ((-rows.high_accels_90, FOCUS_LIGHT), (rows.high_decels_90, FOCUS_DARK)):
        for bar, faded in zip(ax.barh(y, values, height=0.62, color=colour), short):
            bar.set_alpha(0.4 if faded else 1.0)
    span = max(rows.high_accels_90.max(), rows.high_decels_90.max()) * 1.15
    for yi, r in zip(y, rows.itertuples()):
        ax.text(
            -r.high_accels_90 - span * 0.012,
            yi,
            f"{r.high_accels_90:.0f}",
            ha="right",
            va="center",
            fontsize=10.5,
            color=TEXT,
        )
        ax.text(
            r.high_decels_90 + span * 0.012,
            yi,
            f"{r.high_decels_90:.0f}",
            ha="left",
            va="center",
            fontsize=10.5,
            color=TEXT,
        )
    ax.vlines([-avg_acc, avg_dec], -0.5, n - 0.4, color=OTHER, linewidth=1.4, zorder=3)
    ax.text(
        -avg_acc,
        n - 0.4,
        f"{pm.team_name(other)} avg {avg_acc:.0f} ",
        color=OTHER,
        fontsize=9.5,
        ha="right",
        va="bottom",
    )
    ax.text(
        avg_dec,
        n - 0.4,
        f" {pm.team_name(other)} avg {avg_dec:.0f}",
        color=OTHER,
        fontsize=9.5,
        ha="left",
        va="bottom",
    )
    ax.axvline(0, color=SURFACE, linewidth=3, zorder=2)
    ax.set_xlim(-span, span)
    ax.set_ylim(-0.6, n + 0.5)
    ax.set_yticks(
        y,
        [f"{r['name']}  {_minutes(r.minutes)}" for _, r in rows.iterrows()],
        fontsize=11.5,
        color=TEXT,
    )
    ax.set_xticks([])
    ax.text(-span, n + 0.1, "ACCELERATIONS", color=FOCUS, fontsize=11, weight="bold")
    ax.text(
        span, n + 0.1, "DECELERATIONS", color=FOCUS_DARK, fontsize=11, weight="bold", ha="right"
    )
    _style(ax, grid_axis="")
    return fig
