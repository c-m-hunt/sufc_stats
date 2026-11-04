"""Charts about a team across a season."""

from collections.abc import Sequence
from typing import Any

from wyscout.data import filters
from wyscout.data.lineups import Lineup, missing_lineups, season_lineups
from wyscout.data.player import birth_month_counts, squad, squad_with_stats
from wyscout.data.season import (
    attacking_stats_by_player,
    attempts_in_matches,
    played_matches,
    season_events,
    season_label,
    split_by_possession,
)
from wyscout.team import get_team_details
from wyscout.viz.arrows import ArrowOptions, passes_to_arrows, plot_key_passes
from wyscout.viz.consts import OPPO_COLOURS, TEAM_COLOURS
from wyscout.viz.event_map import EventPanel
from wyscout.viz.lineups import ElevenRow, LineupPanel, plot_lineup_matrix, plot_lineups
from wyscout.viz.match import AttemptGroup, plot_attempts, plot_attempts_heat_map
from wyscout.viz.season import plot_birth_months
from wyscout.viz.shots import plot_shot_maps
from wyscout.viz.team import plot_attacking_stats, plot_season_action_maps, plot_squad_grid

Event = dict[str, Any]


def _team(team_id: int) -> dict[str, Any]:
    return get_team_details(team_id)


def attempts_map(
    team_id: int,
    season_id: int,
    match_groups: Sequence[Sequence[dict[str, Any]]] | None = None,
    labels: Sequence[str] | None = None,
    header: str | None = None,
    include_pens: bool = False,
    include_free_kicks: bool = False,
    last_n: int | None = None,
    fig_height: float = 10,
    shot_colors: tuple[str, str] = TEAM_COLOURS,
    show: bool = True,
):
    """Every attempt of the season on a half pitch, with totals and per-game rates.

    Pass match_groups (lists of fixtures from wyscout.data.season.played_matches)
    to draw several pitches side by side, one per group, with labels.
    """
    if match_groups is None:
        matches = played_matches(team_id, season_id, oldest_first=False)
        match_groups = [matches[:last_n] if last_n else matches]
        labels = labels or [f"Last {last_n} games" if last_n else "All league games"]
    groups = [
        AttemptGroup(
            label=label,
            shots=attempts_in_matches(matches, team_id, include_pens, include_free_kicks),
            matches=len(matches),
        )
        for matches, label in zip(match_groups, labels or [""] * len(match_groups))
    ]
    return plot_attempts(groups, header or f"{_team(team_id)['name']} attempts - {season_label(season_id)}",
                         fig_height=fig_height, shot_colors=shot_colors, badge=_team(team_id)["imageDataURL"],
                         show=show)


def attempts_by_possession(team_id: int, season_id: int, pct: float = 55, **kwargs):
    """Attempts split into the matches with under and over pct% possession."""
    under, over = split_by_possession(team_id, season_id, pct)
    return attempts_map(team_id, season_id, [under, over],
                        [f"Matches with possession under {pct}%", f"Matches with possession over {pct}%"],
                        **kwargs)


def attempts_heat_map(
    team_id: int,
    season_id: int,
    subtitle: Sequence[str] | None = None,
    fig_height: float = 10,
    cmap: str = "Blues",
    show: bool = True,
):
    """Where the season's attempts were taken from, as a density map."""
    shots = attempts_in_matches(played_matches(team_id, season_id), team_id)
    return plot_attempts_heat_map(filters.locations(shots),
                                  f"{_team(team_id)['name']} attempts - {season_label(season_id)}",
                                  subtitle=subtitle, badge=_team(team_id)["imageDataURL"],
                                  fig_height=fig_height, cmap=cmap, show=show)


def season_action_maps(
    team_id: int,
    season_id: int,
    cols: int = 5,
    fig_height: float = 30,
    last_n: int | None = None,
    oldest_first: bool = True,
    cmap: str = "Blues",
    shot_colors: tuple[str, str] = TEAM_COLOURS,
    oppo_shot_colors: tuple[str, str] = OPPO_COLOURS,
    show: bool = True,
):
    """A pitch per match: touch heat map, our attempts and the opposition's."""
    matches = season_events(team_id, season_id, oldest_first=oldest_first)
    if last_n:
        matches = matches[-last_n:] if oldest_first else matches[:last_n]
    panels = [
        EventPanel(
            title=m["summary"].title("{opponent} ({venue})\n{date}\n{result} {score}"),
            touches=filters.locations(filters.for_team(m["events"], team_id)),
            shots=filters.attempts(m["events"], team_id),
            oppo_shots=filters.attempts(filters.against_team(m["events"], team_id)),
        )
        for m in matches
    ]
    subtitle = f"Action maps for the last {last_n} games" if last_n else f"Action maps for {season_label(season_id)}"
    return plot_season_action_maps(panels, _team(team_id)["name"], subtitle=[subtitle],
                                   badge=_team(team_id)["imageDataURL"], cols=cols, fig_height=fig_height,
                                   cmap=cmap, shot_colors=shot_colors, oppo_shot_colors=oppo_shot_colors,
                                   show=show)


def shots_first_vs_last(
    team_id: int,
    season_id: int,
    first_n: int | None = None,
    last_n: int | None = None,
    include_pens: bool = False,
    fig_height: float = 10,
    show: bool = True,
):
    """Attempts in the first N games beside attempts in the last N - is the shot profile changing?"""
    matches = played_matches(team_id, season_id)
    if first_n is None and last_n is None:
        first_n = len(matches) // 2
    first_n = first_n or len(matches) - last_n
    last_n = last_n or len(matches) - first_n
    groups = [
        attempts_in_matches(matches[:first_n], team_id, include_pens),
        attempts_in_matches(matches[-last_n:], team_id, include_pens),
    ]
    return plot_shot_maps(groups, f"Attempts on goal - first {first_n} games vs last {last_n} games",
                          fig_height=fig_height, panel_titles=[f"First {first_n}", f"Last {last_n}"], show=show)


def shots_for_and_against(
    team_id: int,
    season_id: int,
    matches: Sequence[dict[str, Any]] | None = None,
    include_pens: bool = False,
    fig_height: float = 10,
    show: bool = True,
):
    """Our attempts beside the attempts we faced, over the season or the given fixtures."""
    matches = matches or played_matches(team_id, season_id)
    groups = [
        attempts_in_matches(matches, team_id, include_pens),
        attempts_in_matches(matches, team_id, include_pens, against=True),
    ]
    return plot_shot_maps(groups, f"{_team(team_id)['name']} - attempts for and against, {season_label(season_id)}",
                          fig_height=fig_height, panel_titles=["For", "Against"], show=show)


def attacking_stats(
    team_id: int,
    season_id: int,
    colors: Sequence[str] = ("royalblue", "yellow"),
    edgecolors: Sequence[str] = ("royalblue", "royalblue"),
    include_pens: bool = False,
    show: bool = True,
):
    """Per player: finishing (post-shot xG minus xG), xG v goals, attempts v on target, xG per attempt."""
    stats = attacking_stats_by_player(team_id, season_id, include_pens)
    return plot_attacking_stats(stats, badge=_team(team_id)["imageDataURL"], colors=colors,
                                edgecolors=edgecolors, show=show)


def key_passes_map(
    team_id: int,
    season_id: int,
    last_n: int = 5,
    highlight_players: Sequence[int] = (),
    fig_height: float = 8,
    show: bool = True,
):
    """Every key pass in the last N games; the highlighted players' passes in red."""
    matches = season_events(team_id, season_id, oldest_first=False)[:last_n]
    arrows = []
    for m in matches:
        options = ArrowOptions(highlight=lambda e: e["player"]["id"] in highlight_players)
        arrows.extend(passes_to_arrows(filters.key_passes(filters.for_team(m["events"], team_id)), options))
    return plot_key_passes(arrows, f"Key passes - last {last_n} games", fig_height=fig_height, show=show)


def squad_grid(
    team_id: int,
    season_id: int,
    competition_id: int,
    round_id: int | None = None,
    cols: int = 6,
    show: bool = True,
):
    """Photos of everyone who has played, most appearances first, with their games and minutes."""
    players = squad_with_stats(team_id, season_id, competition_id, round_id)
    captions = [f"{p['player']['shortName']}\n{p['stats']['total']['matches']} games, "
                f"{p['stats']['total']['minutesOnField']} mins" for p in players]
    return plot_squad_grid([p["player"] for p in players], captions=captions, cols=cols, show=show)


def birth_months(team_id: int, season_id: int, show: bool = True):
    """When the squad were born - the relative age effect in one chart."""
    players = squad(team_id, season_id).values()
    return plot_birth_months(birth_month_counts(players),
                             f"{_team(team_id)['name']} squad {season_label(season_id)} - month of birth", show=show)


def squad_list(team_id: int, season_id: int) -> list[tuple[int, str]]:
    """(id, short name) for the squad - for finding a player's id."""
    return [(p["wyId"], p["shortName"]) for p in squad(team_id, season_id).values()]


def lineups(
    team_id: int,
    season_id: int,
    by_match: bool = True,
    cols: int = 5,
    league_only: bool = True,
    short_minutes: int = 20,
    show: bool = True,
):
    """Every eleven the team has had on the pitch, each on its own pitch at the players' mean positions.

    Under each pitch: minutes that eleven has played together, goals for and
    against, and the per-90 scoreline. by_match=True gives a row per game with
    its spells left to right, starters in the darker colour; False gives every
    distinct eleven once, most minutes together first, cols to a row.
    """
    team = _team(team_id)
    season = season_lineups(team_id, season_id, league_only)

    def panel(lineup: Lineup, title: str, subs: set[int], note: str = "") -> LineupPanel:
        return LineupPanel(title=title, positions=lineup.positions, minutes=lineup.minutes,
                           goals_for=lineup.goals_for, goals_against=lineup.goals_against,
                           subs=subs, note=note)

    if by_match:
        spells = sorted(((s, lu) for lu in season for s in lu.spells), key=lambda t: (t[0].match.date, t[0].start))
        rows: list[list[LineupPanel]] = []
        for spell, lineup in spells:
            if spell.start == 0:
                rows.append([])
                starters = spell.players
            others = [m.opponent for m in lineup.matches if m.match_id != spell.match.match_id]
            title = f"{spell.match.title('{opponent} ({venue}) {result} {score}')}  {spell.start}'-{spell.end}'"
            rows[-1].append(panel(lineup, title, set(spell.players - starters),
                                  f"also v {', '.join(others)}" if others else ""))
        layout = "One row per game, a pitch per spell with an unchanged side. Dark: started, light: came on"
    else:
        panels = [panel(lu, ", ".join(m.opponent for m in lu.matches), set()) for lu in season]
        rows = [panels[i:i + cols] for i in range(0, len(panels), cols)]
        layout = "Every distinct eleven, most minutes together first"

    subtitle = [
        f"{len(season)} different elevens. {layout}.",
        "Players at their mean on-ball position while that eleven was on.",
        "Minutes are nominal (45 a half, added time not counted). Per 90 = goals for and against scaled to a full match.",
    ]
    missing = missing_lineups(team_id, season_id, league_only)
    if missing:
        subtitle.append("Not yet included, lineup unpublished: "
                        + ", ".join(m.title("{opponent} ({venue}) {result} {score}") for m in missing) + ".")

    return plot_lineups(rows, f"{team['name']} - every eleven, {season_label(season_id)}", subtitle=subtitle,
                        badge=team["imageDataURL"], short_minutes=short_minutes, show=show)


def lineup_matrix(team_id: int, season_id: int, league_only: bool = True, short_minutes: int = 20,
                  show: bool = True):
    """Every distinct eleven as one row, most minutes together first, with a dot under each player in it.

    Players run goalkeeper to forwards by their mean on-ball position across
    the season. Each row: where the eleven played, minutes together, goals for
    and against, and the per-90 scoreline.
    """
    team = _team(team_id)
    season = season_lineups(team_id, season_id, league_only)

    # each player's season position, weighted by minutes, to order the columns
    weighted: dict[int, list[float]] = {}
    names: dict[int, str] = {}
    for lu in season:
        for pid, pos in lu.positions.items():
            w = weighted.setdefault(pid, [0.0, 0.0, 0.0])
            w[0] += pos["x"] * lu.minutes
            w[1] += pos["y"] * lu.minutes
            w[2] += lu.minutes
            names[pid] = pos["name"].split(". ")[-1]
    order = sorted(weighted, key=lambda pid: (round(weighted[pid][0] / weighted[pid][2] / 12), weighted[pid][1] / weighted[pid][2]))

    rows = [
        ElevenRow(players=lu.players, minutes=lu.minutes, goals_for=lu.goals_for, goals_against=lu.goals_against,
                  label="; ".join(f"{s.match.title('{opponent} ({venue})')} {s.start}'-{s.end}'" for s in lu.spells))
        for lu in season
    ]
    subtitle = [
        f"{len(season)} different elevens, most minutes together first. A dot means the player was on the pitch.",
        "Players from goalkeeper to forwards by their average position. Minutes are nominal (45 a half).",
        "Per 90 = goals for and against scaled to a full match, greyed under "
        f"{short_minutes} minutes together.",
    ]
    missing = missing_lineups(team_id, season_id, league_only)
    if missing:
        subtitle.append("Not yet included, lineup unpublished: "
                        + ", ".join(m.title("{opponent} ({venue}) {result} {score}") for m in missing) + ".")
    return plot_lineup_matrix(rows, [(pid, names[pid]) for pid in order],
                              f"{team['name']} - every eleven, {season_label(season_id)}", subtitle=subtitle,
                              badge=team["imageDataURL"], short_minutes=short_minutes, show=show)
