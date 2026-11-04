"""Charts about one player, or a few players side by side."""

from collections.abc import Sequence
from typing import Any

import pandas as pd

from wyscout.data import filters
from wyscout.data.player import (
    MIDFIELD_STATS,
    attempts_on_and_off_pitch,
    attempts_table,
    full_name,
    on_off_summary,
    player_events,
    player_season_events,
    season_stats_table,
    squad,
)
from wyscout.data.season import played_matches, season_label, shot_stats
from wyscout.team import get_team_details
from wyscout.viz.arrows import ArrowOptions, passes_to_arrows
from wyscout.viz.consts import COLOUR_1, COLOUR_2, COLOUR_3
from wyscout.viz.event_map import EventPanel, Markers, plot_event_maps
from wyscout.viz.match import AttemptGroup, plot_attempts
from wyscout.viz.player import (
    plot_attempts_table,
    plot_pass_map,
    plot_player_action_map,
    plot_player_season_heat_maps,
    plot_stat_comparison,
)

Event = dict[str, Any]

# the kinds of event map, and whether they need the whole pitch or just the attacking half
KINDS = {
    "attempts": True,
    "key_passes": True,
    "crosses": True,
    "aerial_duels": False,
    "defensive": False,
    "distribution": False,
}


def _player(player_id: int, team_id: int, season_id: int) -> dict[str, Any]:
    return squad(team_id, season_id)[player_id]


def _header(player: dict[str, Any], team_id: int, season_id: int) -> str:
    return f"{full_name(player)}"


def _season_title(team_id: int, season_id: int) -> str:
    return f"{get_team_details(team_id)['name']} {season_label(season_id)}"


def _panel(kind: str, own: list[Event], received: list[Event], title: str = "") -> EventPanel:
    """Build the pitch contents for one kind of map from a player's events."""
    if kind == "attempts":
        shots = filters.attempts(own, include_pens=True)
        s = shot_stats(shots)
        return EventPanel(title=title, shots=shots, stats={
            "Shots": s["shots"], "On target": s["on_target"], "Percent on target": s["pct_on_target"],
            "Goals": s["goals"], "Goals per shot": s["goals_per_shot"], "Ave xG per shot": s["xg_per_shot"],
        })

    if kind == "key_passes":
        keys_and_crosses = [e for e in filters.passes(own) if filters.is_key_pass(e) or "cross" in filters.secondary(e)]
        options = ArrowOptions(color=COLOUR_1, width=1, highlighted_color=COLOUR_3, highlighted_width=1,
                               highlight=filters.is_key_pass)
        return EventPanel(title=title, arrows=passes_to_arrows(keys_and_crosses, options))

    if kind == "crosses":
        crosses = filters.crosses(own)
        open_play = [c for c in crosses if not filters.led_to_goal(c) and not filters.is_cross_blocked(c)]
        return EventPanel(
            title=title,
            touches=filters.locations(open_play),
            markers=[
                Markers(filters.locations([c for c in crosses if filters.led_to_goal(c)]), color="red", size=120, label="Led to a goal"),
                Markers(filters.locations([c for c in crosses if filters.is_cross_blocked(c)]), color="cornflowerblue", marker="x", size=120, label="Blocked"),
            ],
        )

    if kind == "aerial_duels":
        duels = filters.duels(own, "aerial")
        won = [d for d in duels if filters.duel_won(d)]
        lost = [d for d in duels if not filters.duel_won(d)]
        return EventPanel(
            title=title,
            touches=filters.locations(won),
            markers=[
                Markers(filters.locations(won), color=COLOUR_1, size=40, label="Won"),
                Markers(filters.locations(lost), color=COLOUR_3, size=40, label="Lost"),
            ],
            stats={"Aerial duels": len(duels), "Won": len(won), "Lost": len(lost),
                   "Won %": len(won) / len(duels) if duels else 0.0},
        )

    if kind == "defensive":
        return EventPanel(
            title=title,
            markers=[
                Markers(filters.locations(filters.interceptions(own)), color=COLOUR_1, size=40, label="Interceptions"),
                Markers(filters.locations(filters.duels(own, "defensive")), color=COLOUR_3, size=40, label="Defensive duels"),
                Markers(filters.locations(filters.fouls(own)), color="black", marker="x", size=40, linewidth=2, label="Fouls"),
            ],
        )

    if kind == "distribution":
        options = ArrowOptions(color=COLOUR_2, width=1, highlighted_color=COLOUR_3, highlighted_width=1,
                               highlight=lambda e: bool(e["pass"]["accurate"]))
        return EventPanel(title=title, arrows=passes_to_arrows(filters.passes(own), options))

    raise ValueError(f"Unknown kind {kind!r}; choose from {', '.join(KINDS)}")


def event_map(
    player_id: int,
    team_id: int,
    season_id: int,
    kind: str = "attempts",
    subtitle: str | None = None,
    half: bool | None = None,
    fig_height: float = 10,
    legend: bool = True,
    save_path: str | None = None,
    show: bool = True,
):
    """One pitch of a player's season. kind is one of:

    attempts, key_passes, crosses (attacking half); aerial_duels, defensive,
    distribution (whole pitch). Subtitle defaults to a description of the kind.
    """
    player = _player(player_id, team_id, season_id)
    own = player_events(player_id, team_id, season_id)
    labels = {
        "attempts": "Goal attempts", "key_passes": "Key passes (red) and crosses", "crosses": "Crosses",
        "aerial_duels": "Aerial duels", "defensive": "Defensive duels, interceptions and fouls",
        "distribution": "Distribution (accurate passes in red)",
    }
    result = plot_event_maps(
        [_panel(kind, own, [])],
        _header(player, team_id, season_id),
        subtitle=[subtitle or labels[kind], _season_title(team_id, season_id)],
        header_imgs=[player["imageDataURL"]],
        fig_height=fig_height,
        half=KINDS[kind] if half is None else half,
        legend=legend,
        show=False,
    )
    fig = result[0]
    if save_path:
        fig.savefig(save_path, bbox_inches="tight", dpi=150)
    if show:
        import matplotlib.pyplot as plt

        plt.show()
    return result


def comparison(
    subjects: Sequence[tuple[int, int, int]],
    kind: str = "attempts",
    header: str = "Comparison",
    panel_titles: Sequence[str] | None = None,
    half: bool | None = None,
    fig_height: float = 12,
    legend: bool = True,
    show: bool = True,
):
    """The same kind of map for several (player_id, team_id, season_id), side by side."""
    panels, imgs = [], []
    for i, (player_id, team_id, season_id) in enumerate(subjects):
        player = _player(player_id, team_id, season_id)
        own = player_events(player_id, team_id, season_id)
        title = panel_titles[i] if panel_titles else f"{player['shortName']}, {_season_title(team_id, season_id)}"
        panels.append(_panel(kind, own, [], title))
        imgs.append(player["imageDataURL"])
    imgs.reverse()  # add_header lays images out right to left
    return plot_event_maps(panels, header, header_imgs=imgs, fig_height=fig_height,
                           half=KINDS[kind] if half is None else half, legend=legend, show=show)


def passes_received_comparison(
    subjects: Sequence[tuple[int, int, int]],
    header: str,
    panel_titles: Sequence[str] | None = None,
    fig_height: float = 12,
    show: bool = True,
):
    """Where a player receives the ball (heat map) with their attempts, for several player-seasons."""
    panels, imgs = [], []
    for i, (player_id, team_id, season_id) in enumerate(subjects):
        player = _player(player_id, team_id, season_id)
        received = player_events(player_id, team_id, season_id, received=True)
        own = player_events(player_id, team_id, season_id)
        shots = filters.attempts(own, include_pens=True)
        s = shot_stats(shots)
        panels.append(EventPanel(
            title=panel_titles[i] if panel_titles else f"{player['shortName']}, {_season_title(team_id, season_id)}",
            touches=[filters.end_location(e) for e in received],
            shots=shots,
            stats={"Shots": s["shots"], "On target": s["on_target"], "Goals": s["goals"],
                   "Ave xG per shot": s["xg_per_shot"]},
        ))
        imgs.append(player["imageDataURL"])
    imgs.reverse()
    return plot_event_maps(panels, header, header_imgs=imgs, fig_height=fig_height, stats_pos=(5, 45),
                           stats_step=3.5, show=show)


def season_heat_maps(
    player_id: int,
    team_id: int,
    season_id: int,
    cols: int = 5,
    fig_height: float = 30,
    show: bool = True,
):
    """A pitch per match of the player's touches, with their attempts marked."""
    player = _player(player_id, team_id, season_id)
    panels = [
        EventPanel(
            title=m["summary"].title("{opponent} ({venue})\n{date}\n{result} {score}"),
            touches=filters.locations(m["events"]),
            shots=filters.attempts(m["events"], include_pens=True),
        )
        for m in player_season_events(player_id, team_id, season_id)
    ]
    return plot_player_season_heat_maps(
        panels, f"{player['shortName']}\nHeat maps for {season_label(season_id)}",
        player_img=player["imageDataURL"], cols=cols, fig_height=fig_height, show=show,
    )


def pass_map(
    from_player_id: int,
    to_player_id: int,
    team_id: int,
    season_id: int,
    subtitle: Sequence[str] | None = None,
    fig_height: float = 8,
    show: bool = True,
):
    """Every pass from one player to another over a season; high passes lighter, thicker if it led to a shot."""
    players = squad(team_id, season_id)
    passes = filters.passes_to(player_events(from_player_id, team_id, season_id), to_player_id)
    arrows = []
    for e in passes:
        options = ArrowOptions(width=3 if filters.led_to_shot(e) else 2,
                               color=COLOUR_2 if filters.is_high_pass(e) else COLOUR_1, edgecolor=COLOUR_3)
        arrows.extend(passes_to_arrows([e], options))
    a, b = players[from_player_id], players[to_player_id]
    return plot_pass_map(arrows, f"{a['lastName']} to {b['lastName']}", subtitle=subtitle,
                         imgs=[a["imageDataURL"], b["imageDataURL"]], fig_height=fig_height, show=show)


def distribution_map(
    player_id: int,
    team_id: int,
    season_id: int,
    title: str | None = None,
    subtitle: str = "",
    received: bool = False,
    fig_height: float = 16,
    show: bool = True,
):
    """A player's passes as arrows over the season (accurate ones in red), or the passes they received."""
    player = _player(player_id, team_id, season_id)
    events = player_events(player_id, team_id, season_id, received=received)
    options = ArrowOptions(color=COLOUR_2 if not received else COLOUR_1, width=1 if not received else 0.4,
                           highlighted_color=COLOUR_3, highlighted_width=1,
                           highlight=(lambda e: bool(e["pass"]["accurate"])) if not received else (lambda e: False))
    return plot_player_action_map(
        full_name(player),
        title or f"{'Passes received' if received else 'Distribution'} - {_season_title(team_id, season_id)}",
        subtitle,
        [] if received else filters.locations(events),
        passes_to_arrows(filters.passes(events), options),
        player_img=player["imageDataURL"],
        fig_height=fig_height,
        show=show,
    )


def attempts_table_chart(
    player_id: int,
    team_id: int,
    season_id: int,
    save_path: str | None = None,
    show: bool = True,
) -> pd.DataFrame:
    """A styled table of every attempt the player has taken this season. Returns the data too."""
    player = _player(player_id, team_id, season_id)
    df = attempts_table(player_id, team_id, season_id)
    if df.empty:
        print(f"No attempts found for {player['shortName']}")
        return df
    plot_attempts_table(df, f"{player['shortName']} - Attempts on goal {season_label(season_id)}",
                        save_path=save_path, show=show)
    return df


def on_off_pitch(
    player_id: int,
    team_id: int,
    season_id: int,
    include_pens: bool = True,
    include_free_kicks: bool = True,
    highlight_own: bool = True,
    fig_height: float = 10,
    show: bool = True,
) -> dict[str, Any]:
    """The team's attempts with the player on the pitch beside those with them off, per 90.

    Returns the split from wyscout.data.player.attempts_on_and_off_pitch plus a
    "summary" table. The player's own attempts are picked out in yellow.
    """
    player = _player(player_id, team_id, season_id)
    name = full_name(player)
    split = attempts_on_and_off_pitch(player_id, team_id, season_id, include_pens, include_free_kicks)
    groups = [
        AttemptGroup(label=f"{name} on the pitch" + (" (his own attempts in yellow)" if highlight_own else ""),
                     shots=split["on"]["shots"], minutes=split["on"]["minutes"],
                     highlighted=split["on"]["player_shots"] if highlight_own else []),
        AttemptGroup(label=f"{name} off the pitch", shots=split["off"]["shots"], minutes=split["off"]["minutes"]),
    ]
    plot_attempts(groups, f"{get_team_details(team_id)['name']} attempts - {name} on vs off the pitch",
                  fig_height=fig_height, badge=get_team_details(team_id)["imageDataURL"], show=show)
    split["summary"] = on_off_summary(split, name)
    return split


def matches_played(player_id: int, team_id: int, season_id: int) -> list[dict[str, Any]]:
    """Fixtures the player appeared in."""
    played = {m["summary"].match_id for m in player_season_events(player_id, team_id, season_id)}
    return [m for m in played_matches(team_id, season_id) if m["matchId"] in played]


def stat_comparison(
    players: Sequence[tuple[int, int]],
    season_id: int,
    competition_id: int,
    title: str,
    highlight_player_id: int | None = None,
    stats: Sequence[tuple[str, str, str, bool, str]] = MIDFIELD_STATS,
    min_minutes: int = 270,
    show: bool = True,
) -> pd.DataFrame:
    """Season statistics for several (player_id, team_id), each cell coloured by rank among them.

    League matches only - the league round is taken from the first player's
    club. Players under min_minutes are left out. Returns the table behind the chart.
    """
    round_id = played_matches(players[0][1], season_id)[0]["roundId"]
    df = season_stats_table(players, season_id, competition_id, stats, round_id, min_minutes)
    subtitle = (f"{season_label(season_id)}, league only, players with {min_minutes}+ minutes. Colour and the small "
                "number are the rank in each row - green best, red worst.")
    plot_stat_comparison(df, stats, title, subtitle, highlight_player_id, show=show)
    return df
