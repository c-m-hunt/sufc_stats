"""Tracking-data charts, drawn in metres on a horizontal pitch.

`plot_frame` shows the raw data, home side attacking left to right (as
`wyscout.data.tracking.get_match_tracking` gives it). The team charts below it are about one
side - Southend, in blue, attacking left to right - with the opposition as grey context, and
take their numbers from `wyscout.data.tracking_stats`.
"""

from collections.abc import Mapping

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from mplsoccer import Pitch
from scipy.spatial import ConvexHull

from wyscout.data import tracking_stats as ts
from wyscout.data.physical import PhysicalMatch
from wyscout.data.tracking import MatchTracking
from wyscout.viz.consts import APP_FONT, GRID, MUTED, NAVY, TEXT
from wyscout.viz.physical import (
    FOCUS,
    FOCUS_LIGHT,
    OTHER,
    POSITION_ORDER,
    SURFACE,
    match_header,
    match_line,
    team_sides,
)

HOME_COLOUR = "#1f4fbf"
AWAY_COLOUR = "#d7301f"
BALL_COLOUR = "#ffd23f"


def tracking_pitch(tracking: MatchTracking, **kwargs) -> Pitch:
    style = {
        "pitch_color": "#aabb97",
        "stripe_color": "#c2d59d",
        "stripe": True,
        "line_color": "white",
    } | kwargs
    return Pitch(
        pitch_type="skillcorner",
        pitch_length=tracking.length,
        pitch_width=tracking.width,
        line_zorder=1,
        **style,
    )


def clock_label(clock: float, period: int) -> str:
    """Match clock as 23:41, with stoppage time as 45+2:10."""
    limit = 45 * 60 * period
    if clock >= limit:
        extra = clock - limit
        return f"{45 * period}+{int(extra // 60)}:{int(extra % 60):02d}"
    return f"{int(clock // 60)}:{int(clock % 60):02d}"


def plot_frame(
    tracking: MatchTracking, frame: int, ax: Axes | None = None, velocity: bool = True
) -> Axes:
    """Every player and the ball at one frame. Arrows show where each player will be in
    one second at their current velocity; faded markers are positions the camera could not
    see and the model estimated."""
    pitch = tracking_pitch(tracking)
    if ax is None:
        _, ax = pitch.draw(figsize=(12, 8))
    else:
        pitch.draw(ax=ax)
    players, ball = tracking.frame(frame)
    for team, colour in (("home", HOME_COLOUR), ("away", AWAY_COLOUR)):
        side = players[players.team == team]
        for visible, alpha in ((True, 1.0), (False, 0.45)):
            these = side[side.visible == visible]
            pitch.scatter(
                these.x,
                these.y,
                s=320,
                color=colour,
                edgecolors="white",
                linewidth=1.5,
                alpha=alpha,
                zorder=3,
                ax=ax,
            )
        for row in side.itertuples():
            pitch.annotate(
                row.jersey,
                (row.x, row.y),
                ha="center",
                va="center",
                fontsize=9,
                color="white",
                fontweight="bold",
                zorder=4,
                ax=ax,
            )
        if velocity:
            pitch.arrows(
                side.x,
                side.y,
                side.x + side.vx,
                side.y + side.vy,
                width=1.5,
                headwidth=4,
                headlength=4,
                color=colour,
                alpha=0.8,
                zorder=2,
                ax=ax,
            )
    if len(ball):
        pitch.scatter(
            ball.x,
            ball.y,
            s=90,
            color=BALL_COLOUR,
            edgecolors="black",
            linewidth=1,
            zorder=5,
            ax=ax,
        )
    row = players.iloc[0]
    ax.set_title(
        f"{tracking.home} (blue, attacking left to right) v {tracking.away}  ·  "
        f"{clock_label(row.clock, row.period)}  ·  frame {frame}",
        fontproperties=APP_FONT.prop,
        fontsize=14,
        color=TEXT,
    )
    return ax


def plot_frames(tracking: MatchTracking, frames: list[int], ncols: int = 2) -> plt.Figure:
    nrows = -(-len(frames) // ncols)
    fig, axs = plt.subplots(nrows, ncols, figsize=(9 * ncols, 6.2 * nrows))
    for ax, frame in zip(axs.flat, frames):
        plot_frame(tracking, frame, ax=ax)
    for ax in list(axs.flat)[len(frames) :]:
        ax.remove()
    fig.tight_layout()
    return fig


# --- team charts ------------------------------------------------------------------------------

LINE_COLOUR = "#c9d1d9"
TERRITORY = ["#f4f6f8", "#dde2e8", "#c4cbd3", "#a7b0ba"]


def plain_pitch(length: float = 105, width: float = 68) -> Pitch:
    return Pitch(
        pitch_type="skillcorner",
        pitch_length=length,
        pitch_width=width,
        pitch_color=SURFACE,
        line_color=LINE_COLOUR,
        linewidth=1.2,
        line_zorder=1,
    )


def _attack_arrow(fig: Figure, x: float, y: float, text: str = "attacking") -> None:
    fig.text(x, y, f"{text}  >>", fontsize=10, color=MUTED, ha="right", va="center")


def plot_player_territories(
    tracking: MatchTracking,
    pm: PhysicalMatch,
    team: str,
    runs: pd.DataFrame,
    ncols: int = 4,
    min_minutes: float = 10,
) -> Figure:
    """One pitch per outfield player: where they were (grey, darker where they spent longer)
    and every sprint they made (ts.sprints - dark arrows forward, light arrows back towards
    their own goal). Runs flagged suspect are left out."""
    side, _ = team_sides(pm, team)
    frames = ts.team_frames(tracking, side)
    frames = frames[frames.position != "GK"]
    runs = runs[~runs.suspect]
    players = frames.groupby(["jersey", "name", "position"]).size().rename("frames").reset_index()
    players["minutes"] = players.frames / tracking.fps / 60
    players = players[players.minutes >= min_minutes]
    players = players.assign(order=players.position.map(POSITION_ORDER)).sort_values(
        ["order", "minutes"], ascending=[True, False]
    )
    n = len(players)
    nrows = -(-n // ncols)
    pitch = plain_pitch(tracking.length, tracking.width)
    fig, axs = pitch.grid(
        nrows=nrows,
        ncols=ncols,
        figheight=3.1 * nrows + 2.2,
        grid_height=0.8,
        title_height=0.08,
        endnote_height=0.02,
        space=0.12,
        axis=False,
    )
    fig.set_facecolor(SURFACE)
    grid = axs["pitch"].reshape(nrows, ncols)
    most = runs.groupby("name").size().idxmax() if len(runs) else None
    match_header(
        fig,
        pm,
        f"Territory and sprints - {most} made {(runs.name == most).sum()} sprints"
        if most
        else "Territory and sprints",
        f"{match_line(pm)}  ·  {team} outfield players, attacking left to right. Grey is where "
        "they spent their time; arrows are runs that hit sprint speed (over 25 km/h).",
    )
    for ax, row in zip(grid.flat, players.itertuples()):
        mine = frames[frames.jersey == row.jersey].iloc[:: tracking.fps]
        pitch.kdeplot(
            mine.x,
            mine.y,
            ax=ax,
            fill=True,
            levels=6,
            thresh=0.12,
            cmap=_territory_cmap(),
            zorder=0,
        )
        own = runs[runs["name"] == row.name]
        for forward, colour in ((True, NAVY), (False, FOCUS_LIGHT)):
            r = own[own.forward == forward]
            if len(r):
                pitch.arrows(
                    r.x0,
                    r.y0,
                    r.x1,
                    r.y1,
                    ax=ax,
                    color=colour,
                    width=1.8,
                    headwidth=4.5,
                    headlength=4.5,
                    zorder=3,
                )
        ax.set_title(
            f"{row.name}  {row.minutes:.0f}'\n",
            loc="left",
            fontproperties=APP_FONT.prop,
            fontsize=13,
            color=TEXT,
            pad=2,
        )
        ax.text(
            0,
            1.0,
            f"{len(own)} sprints  ·  {int(own.forward.sum())} forward",
            transform=ax.transAxes,
            fontsize=9.5,
            color=MUTED,
            va="bottom",
        )
    for ax in list(grid.flat)[n:]:
        ax.remove()
    legend = [
        Line2D([], [], color=NAVY, linewidth=2.5, label="sprint forward"),
        Line2D([], [], color=FOCUS_LIGHT, linewidth=2.5, label="sprint back"),
    ]
    fig.legend(
        handles=legend,
        loc="lower right",
        frameon=False,
        ncols=2,
        fontsize=10.5,
        bbox_to_anchor=(0.98, 0.0),
    )
    _attack_arrow(fig, 0.6, 0.012)
    return fig


def _territory_cmap() -> LinearSegmentedColormap:
    return LinearSegmentedColormap.from_list("territory", TERRITORY)


def plot_average_shapes(
    tracking: MatchTracking,
    pm: PhysicalMatch,
    team: str,
    groups: Mapping[str, pd.Index],
    title: str,
    subtitle: str,
) -> Figure:
    """The team's average shape over each group of frames, side by side: each player's median
    position (shirt number), the outfield players' outline shaded, and the opposition's
    average positions as grey dots. Players on for under a fifth of a group are left out."""
    side, other = team_sides(pm, team)
    pitch = plain_pitch(tracking.length, tracking.width)
    n = len(groups)
    fig, axs = pitch.grid(
        nrows=1,
        ncols=n,
        figheight=6.4,
        grid_height=0.6,
        title_height=0.2,
        endnote_height=0.04,
        space=0.06,
        axis=False,
    )
    fig.set_facecolor(SURFACE)
    axs = np.atleast_1d(axs["pitch"])
    match_header(fig, pm, title, f"{match_line(pm)}  ·  {subtitle}")
    for ax, (label, frames) in zip(axs, groups.items()):
        theirs = ts.average_positions(tracking, other, frames)
        # the opposition's positions, turned into this side's orientation
        pitch.scatter(
            -theirs.x,
            -theirs.y,
            ax=ax,
            s=110,
            color=OTHER,
            alpha=0.6,
            edgecolors=SURFACE,
            linewidth=1.5,
            zorder=2,
        )
        ours = ts.average_positions(tracking, side, frames)
        outfield = ours[ours.position != "GK"][["x", "y"]].to_numpy()
        if len(outfield) >= 3:
            hull = outfield[ConvexHull(outfield).vertices]
            ax.fill(hull[:, 0], hull[:, 1], color=FOCUS, alpha=0.1, zorder=1, linewidth=0)
            ax.plot(*np.vstack([hull, hull[:1]]).T, color=FOCUS, alpha=0.5, linewidth=1.2, zorder=1)
        pitch.scatter(
            ours.x, ours.y, ax=ax, s=430, color=FOCUS, edgecolors=SURFACE, linewidth=2, zorder=3
        )
        for r in ours.itertuples():
            pitch.annotate(
                r.jersey,
                (r.x, r.y),
                ax=ax,
                ha="center",
                va="center",
                fontsize=10,
                color="white",
                weight="bold",
                zorder=4,
            )
        minutes = len(frames) / tracking.fps / 60
        ax.set_title(
            f"{label}\n", loc="left", fontproperties=APP_FONT.prop, fontsize=15, color=TEXT, pad=2
        )
        ax.text(
            0,
            1.0,
            f"{minutes:.0f} minutes of play",
            transform=ax.transAxes,
            fontsize=10,
            color=MUTED,
            va="bottom",
        )
    names = (
        tracking.roster[tracking.roster.team == side]
        .merge(ts.team_frames(tracking, side)[["jersey"]].drop_duplicates(), on="jersey")
        .assign(order=lambda d: d.position.map({"GK": -1, **POSITION_ORDER}))
        .sort_values(["order", "jersey"])
    )
    key = "   ".join(f"{r.jersey} {r['name'].split()[-1]}" for _, r in names.iterrows())
    fig.text(0.02, 0.03, key, fontsize=9.5, color=MUTED, va="bottom")
    fig.text(
        0.02,
        0.005,
        f"Grey dots: {pm.team_name(other)}'s average positions.",
        fontsize=9.5,
        color=MUTED,
        va="bottom",
    )
    _attack_arrow(fig, 0.98, 0.015, f"{team} attacking")
    return fig


def plot_shape_timeline(
    tracking: MatchTracking, pm: PhysicalMatch, team: str, smooth_minutes: int = 5
) -> Figure:
    """Line height, length and width minute by minute (ts.shape_by_minute, smoothed over
    smooth_minutes), the team in blue and the opposition in grey, with the goals and the
    team's substitutions marked."""
    side, other = team_sides(pm, team)
    ours, theirs = ts.shape_by_minute(tracking, side), ts.shape_by_minute(tracking, other)
    metrics = [
        ("line_height", "Back line", "metres from own goal to the deepest four"),
        ("length", "Length", "metres from deepest to furthest forward"),
        ("width", "Width", "metres between the widest two"),
    ]
    spans = {p: ours[ours.period == p].minute for p in (1, 2)}
    fig, axs = plt.subplots(
        3,
        2,
        figsize=(16, 11),
        sharey="row",
        facecolor=SURFACE,
        gridspec_kw={
            "width_ratios": [len(spans[1]), len(spans[2])],
            "wspace": 0.04,
            "hspace": 0.45,
        },
    )
    fig.subplots_adjust(left=0.07, right=0.97, top=0.84, bottom=0.05)
    by_score = ts.shape_by_score(tracking, side, pm.goals)
    title = "Shape through the match"
    if len(by_score) >= 2:
        before, after = by_score.iloc[-2], by_score.iloc[-1]
        change = after.line_height - before.line_height
        title += (
            f" - {team}'s back line went {abs(change):.0f} m "
            f"{'higher' if change > 0 else 'deeper'} at {after.score}"
        )
    levels = "  ·  ".join(f"{r.score}: {r.line_height:.0f} m" for r in by_score.itertuples())
    match_header(
        fig,
        pm,
        title,
        f"{match_line(pm)}  ·  outfield shape with the ball in play, each minute's median "
        f"smoothed over {smooth_minutes} minutes; grey is {pm.team_name(other)}. "
        f"Back line by score - {levels}.",
    )
    subs = _substitutions(tracking, side)
    for row, (col, label, unit) in enumerate(metrics):
        for c, period in enumerate((1, 2)):
            ax = axs[row, c]
            for data, colour, width, z in ((theirs, OTHER, 1.8, 2), (ours, FOCUS, 2.6, 3)):
                d = data[data.period == period].set_index("minute")[col]
                d = d.rolling(smooth_minutes, center=True, min_periods=1).mean()
                ax.plot(d.index + 0.5, d.values, color=colour, linewidth=width, zorder=z)
            for g in pm.goals:
                if g.period == period:
                    ax.axvline(
                        g.minute,
                        color=FOCUS if g.team == side else OTHER,
                        linewidth=1.1,
                        alpha=0.7,
                        zorder=1,
                    )
                    if row == 0:
                        who = g.scorer + (" (og)" if g.own_goal else "")
                        ax.text(
                            g.minute,
                            1.0,
                            f" {who} {int(g.minute) + 1}'",
                            transform=ax.get_xaxis_transform(),
                            fontsize=9,
                            color=TEXT if g.team == side else MUTED,
                            va="top",
                            rotation=90,
                            ha="right",
                        )
            changes = subs[subs.period == period]
            for minute, group in changes.groupby(changes.minute.round()):
                ax.scatter(
                    minute,
                    0.03,
                    transform=ax.get_xaxis_transform(),
                    marker="^",
                    s=40,
                    color=MUTED,
                    zorder=4,
                    clip_on=False,
                )
                if row == len(metrics) - 1:
                    names = ", ".join(n.split()[-1] for n in group["name"])
                    ax.text(
                        minute,
                        -0.14,
                        f"{names} on",
                        transform=ax.get_xaxis_transform(),
                        fontsize=8.5,
                        color=MUTED,
                        ha="center",
                        va="top",
                    )
            for spine in ax.spines.values():
                spine.set_visible(False)
            ax.grid(True, axis="y", color=GRID, linewidth=0.8)
            ax.tick_params(colors=MUTED, labelsize=9.5, length=0)
            ax.set_xlim(spans[period].min(), spans[period].max() + 1)
            if c == 0:
                ax.set_title(
                    label, loc="left", fontproperties=APP_FONT.prop, fontsize=15, color=TEXT, pad=18
                )
                ax.text(
                    0, 1.02, unit, transform=ax.transAxes, fontsize=10, color=MUTED, va="bottom"
                )
            else:
                ax.text(
                    0.01,
                    1.02,
                    "second half",
                    transform=ax.transAxes,
                    fontsize=10,
                    color=MUTED,
                    va="bottom",
                )
    legend = [
        Line2D([], [], color=FOCUS, linewidth=2.6, label=team),
        Line2D([], [], color=OTHER, linewidth=1.8, label=pm.team_name(other)),
        Line2D([], [], color=MUTED, marker="^", linewidth=0, label=f"{team} substitution"),
    ]
    fig.legend(
        handles=legend,
        loc="upper right",
        frameon=False,
        ncols=3,
        fontsize=10.5,
        bbox_to_anchor=(0.97, 0.885),
    )
    return fig


def _substitutions(tracking: MatchTracking, side: str) -> pd.DataFrame:
    """The side's substitutes: name, period and match minute they came on."""
    frames = ts.team_frames(tracking, side)
    on = tracking.roster[(tracking.roster.team == side) & tracking.roster.on.notna()]
    rows = []
    for r in on.itertuples():
        first = frames[frames.jersey == r.jersey].iloc[0]
        rows.append({"name": r.name, "period": first.period, "minute": first.clock / 60})
    return pd.DataFrame(rows, columns=["name", "period", "minute"])


# --- goal moments -----------------------------------------------------------------------------


def plot_goal_moment(
    tracking: MatchTracking,
    pm: PhysicalMatch,
    team: str,
    moment: ts.GoalMoment,
    save_path: str | None = None,
) -> Figure:
    """Every player at the frame a goal was struck (ts.goal_moments), the team in blue
    attacking left to right, the opposition grey. Faded players are ones the camera could
    not see, their positions estimated; arrows show where each player would be a second
    later. The ball is drawn at the scorer's feet - the tracked ball is unreliable around a
    shot - with a line to the goal it went into."""
    side, other = team_sides(pm, team)
    flip = -1 if side == "away" else 1
    frames = tracking.players.frame
    frame = (
        moment.frame
        if (frames == moment.frame).any()
        else int(frames.iloc[(frames - moment.frame).abs().argmin()])
    )
    players = tracking.players[tracking.players.frame == frame].copy()
    for c in ("x", "y", "vx", "vy"):
        players[c] = players[c] * flip

    pitch = plain_pitch(tracking.length, tracking.width)
    fig, ax = pitch.draw(figsize=(14, 10.4))
    fig.set_facecolor(SURFACE)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.83, bottom=0.06)

    ours = moment.team == side
    who = moment.scorer + (" (og)" if moment.own_goal else "")
    minute = f"{int(moment.minute) + 1}'"
    home_goals, away_goals = moment.score.split("-")
    score = f"{home_goals}-{away_goals}" if side == "home" else f"{away_goals}-{home_goals}"
    label = f"{team} goal" if ours else f"{pm.team_name(other)} goal"
    detail = [f"makes it {score}"]
    if moment.xg is not None:
        detail.append(f"xG {moment.xg:.2f}")
    match_header(
        fig,
        pm,
        f"{label} - {who} {minute}",
        f"{match_line(pm)}  ·  {'  ·  '.join(detail)}  ·  every player at the moment it was "
        "struck; faded = off camera, position estimated; arrows = where they were going.",
    )

    for name, colour, size in ((other, OTHER, 330), (side, FOCUS, 380)):
        these = players[players.team == name]
        pitch.arrows(
            these.x,
            these.y,
            these.x + these.vx,
            these.y + these.vy,
            ax=ax,
            color=colour,
            alpha=0.55,
            width=1.6,
            headwidth=4,
            headlength=4,
            zorder=2,
        )
        for visible, alpha in ((True, 1.0), (False, 0.4)):
            group = these[these.visible == visible]
            pitch.scatter(
                group.x,
                group.y,
                ax=ax,
                s=size,
                color=colour,
                alpha=alpha,
                edgecolors=SURFACE,
                linewidth=2,
                zorder=3,
            )
        for r in these.itertuples():
            pitch.annotate(
                r.jersey,
                (r.x, r.y),
                ax=ax,
                ha="center",
                va="center",
                fontsize=10,
                color="white",
                weight="bold",
                zorder=4,
            )

    scorer = players[
        (players.team == moment.scorer_side) & (players.jersey == moment.scorer_jersey)
    ]
    # the team attacks +x, so its goals go in at +52.5 and the opposition's at -52.5
    goal_x = tracking.length / 2 if ours else -tracking.length / 2
    if len(scorer):
        sx, sy = scorer.x.iloc[0], scorer.y.iloc[0]
    else:  # not tracked at that frame: fall back on Wyscout's location
        sx, sy = moment.ball_x * flip, moment.ball_y * flip
    ax.plot([sx, goal_x], [sy, 0], color=TEXT, linewidth=1.2, alpha=0.5, zorder=1)
    pitch.scatter(sx, sy, ax=ax, s=900, facecolors="none", edgecolors=TEXT, linewidth=2, zorder=5)
    pitch.scatter(
        sx + (1.6 if goal_x > 0 else -1.6),
        sy,
        ax=ax,
        s=110,
        color="white",
        edgecolors=TEXT,
        linewidth=1.6,
        zorder=6,
    )
    ax.annotate(
        moment.scorer,
        (sx, sy),
        xytext=(0, 26),
        textcoords="offset points",
        ha="center",
        fontsize=12,
        color=TEXT,
        weight="bold",
        zorder=6,
    )

    legend = [
        Line2D([], [], color=FOCUS, marker="o", linewidth=0, markersize=11, label=team),
        Line2D(
            [], [], color=OTHER, marker="o", linewidth=0, markersize=11, label=pm.team_name(other)
        ),
        Line2D(
            [],
            [],
            color=FOCUS,
            marker="o",
            linewidth=0,
            markersize=11,
            alpha=0.4,
            label="off camera (estimated)",
        ),
        Line2D(
            [],
            [],
            color="white",
            marker="o",
            markeredgecolor=TEXT,
            linewidth=0,
            markersize=8,
            label="ball",
        ),
    ]
    fig.legend(
        handles=legend,
        loc="lower left",
        frameon=False,
        ncols=4,
        fontsize=10.5,
        bbox_to_anchor=(0.02, 0.0),
    )
    _attack_arrow(fig, 0.98, 0.03, f"{team} attacking")
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight", facecolor=SURFACE)
    return fig
