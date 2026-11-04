"""Season-long line and bar charts, and season-on-season comparisons."""

from collections.abc import Sequence

import pandas as pd

from wyscout.data.referees import league_referee_table, season_referee_table
from wyscout.data.restarts import (
    RESTART_NAMES,
    league_restart_table,
    league_restarts,
    season_restarts,
)
from wyscout.data.season import (
    league_box_table,
    league_corner_table,
    league_field_tilt_by_match,
    league_field_tilt_table,
    league_game_states,
    league_ppda_by_match,
    league_ppda_table,
    league_set_piece_table,
    league_substitutions,
    possession_by_match,
    season_box_table,
    season_field_tilt_timelines,
    season_label,
    season_ppda_table,
    season_results,
    season_shot_table,
    season_xg_table,
)
from wyscout.data.substitutions import (
    aligned_tilt_curve,
    match_changes,
    player_sub_impact,
    season_change_windows,
    squad_names,
)
from wyscout.league_table import table_progression
from wyscout.team import get_team_details
from wyscout.viz.restarts import (
    plot_league_restarts,
    plot_restart_arrows,
    plot_restart_dots,
    plot_restart_overview,
    plot_restart_trend,
    plot_restart_zones,
)
from wyscout.viz.season import (
    plot_box_table,
    plot_cumulative_xg,
    plot_field_tilt_timelines,
    plot_league_box_table,
    plot_league_field_tilt_table,
    plot_league_game_states,
    plot_league_position,
    plot_league_ppda_table,
    plot_league_referee_table,
    plot_league_set_pieces,
    plot_league_substitutions,
    plot_possession_histogram,
    plot_ppda_trend,
    plot_referee_table,
    plot_season_comparison,
    plot_xg_for_against,
    plot_xg_per_shot_trend,
    plot_xg_vs_goals,
)
from wyscout.viz.substitutions import (
    plot_aligned_tilt,
    plot_player_sub_impact,
    plot_sub_tilt_changes,
)


def xg_trend(team_id: int, season_id: int, include_pens: bool = False, show: bool = True):
    """xG per shot by match with rolling averages, attempts and goals on a second axis."""
    return plot_xg_per_shot_trend(season_shot_table(team_id, season_id, include_pens), show=show)


def xg_vs_goals(team_id: int, season_id: int, include_pens: bool = False, show: bool = True):
    """xG against goals, match by match."""
    return plot_xg_vs_goals(season_shot_table(team_id, season_id, include_pens), show=show)


def cumulative_xg(team_id: int, season_id: int, include_pens: bool = False, show: bool = True):
    """Cumulative xG against cumulative goals through the season, with the gap between them."""
    title = f"{get_team_details(team_id)['name']} {season_label(season_id)} - Cumulative xG vs Goals"
    return plot_cumulative_xg(season_shot_table(team_id, season_id, include_pens), title, show=show)


def xg_for_against(team_id: int, season_id: int, include_pens: bool = False, show: bool = True):
    """Cumulative xG and goals, for and against, with each game's goals and xG underneath.

    Non-penalty by default - penalties come out of both the xG and the goals.
    """
    kind = "goals and xG" if include_pens else "non-penalty goals and xG"
    title = f"{get_team_details(team_id)['name']} {season_label(season_id)} - {kind}, for and against"
    return plot_xg_for_against(season_xg_table(team_id, season_id, include_pens), title,
                               include_pens=include_pens, show=show)


def box_activity(team_id: int, season_id: int, show: bool = True):
    """Touches in the opposition box and penalties, won and conceded, match by match - colour coded."""
    title = f"{get_team_details(team_id)['name']} {season_label(season_id)} - box touches and penalties"
    return plot_box_table(season_box_table(team_id, season_id), title, show=show)


def league_box_activity(season_id: int, highlight_team_id: int | None = None, show: bool = True):
    """Box touches per game and penalties, won and conceded, for every club in league position order."""
    title = f"National League {season_label(season_id)} - box touches and penalties by league position"
    return plot_league_box_table(league_box_table(season_id), title, highlight_team_id=highlight_team_id, show=show)


def league_points_from_positions(season_id: int, highlight_team_id: int | None = None, show: bool = True):
    """Points won from losing positions and dropped from winning positions, every club. Returns (fig, ax, table)."""
    df = league_game_states(season_id)
    title = f"National League {season_label(season_id)} - points won from behind and dropped from ahead"
    fig, ax = plot_league_game_states(df, title, highlight_team_id=highlight_team_id, show=show)
    return fig, ax, df


def league_subs(season_id: int, highlight_team_id: int | None = None, show: bool = True):
    """When every club makes its substitutions, and the score when it does. Returns (fig, ax, substitutions)."""
    df = league_substitutions(season_id)
    title = f"National League {season_label(season_id)} - when clubs make their changes"
    fig, ax = plot_league_substitutions(df, title, highlight_team_id=highlight_team_id, show=show)
    return fig, ax, df


def league_corners(season_id: int, highlight_team_id: int | None = None, per_game: bool = False,
                   show: bool = True):
    """Goals and xG from corners, for and against, every club ranked by xG. Returns (fig, axes, table)."""
    df = league_corner_table(season_id)
    kind = "per game" if per_game else "season totals"
    title = f"National League {season_label(season_id)} - goals and xG from corners, {kind}"
    fig, axes = plot_league_set_pieces(df, title, name="corners", taken_label="Corners",
                                       highlight_team_id=highlight_team_id, per_game=per_game, show=show)
    return fig, axes, df


def league_set_pieces(season_id: int, highlight_team_id: int | None = None, per_game: bool = False,
                      include_pens: bool = True, show: bool = True):
    """Goals and xG from corners, free kicks and penalties, for and against, every club ranked by xG.

    xG is split by kind. include_pens=False leaves penalties out. Returns (fig, axes, table).
    """
    kinds = ("corner", "free_kick", "penalty") if include_pens else ("corner", "free_kick")
    df = league_set_piece_table(season_id, kinds)
    kind = "per game" if per_game else "season totals"
    pens = "" if include_pens else " (no penalties)"
    title = f"National League {season_label(season_id)} - goals and xG from set pieces{pens}, {kind}"
    fig, axes = plot_league_set_pieces(df, title, highlight_team_id=highlight_team_id, per_game=per_game, show=show)
    return fig, axes, df


def restart_overview(team_id: int, season_id: int, show: bool = True):
    """How often goal kicks, throw-ins, free kicks and corners find a team mate, against every club.

    Returns (fig, axes, table) - the table is every club's rates by kind
    (wyscout.data.restarts.league_restart_table). The first run fetches every
    match in the division.
    """
    df = league_restart_table(season_id, league_restarts(season_id))
    name = get_team_details(team_id)["name"]
    title = f"{name} {season_label(season_id)} - do our restarts find a team mate?"
    fig, axes = plot_restart_overview(df, team_id, name, title, show=show)
    return fig, axes, df


def league_restart_ladder(season_id: int, kind: str = "goal_kick", highlight_team_id: int | None = None,
                          sort_by: str = "completion", table=None, show: bool = True):
    """Every club's restarts of one kind, ranked by sort_by. Returns (fig, ax, table).

    kind is "goal_kick", "throw_in", "free_kick" or "corner". Pass the table
    restart_overview returned to save rebuilding it.
    """
    if table is None:
        table = league_restart_table(season_id)
    title = f"National League {season_label(season_id)} - {RESTART_NAMES[kind].lower()}: who finds a team mate?"
    fig, ax = plot_league_restarts(table, kind, title, highlight_team_id=highlight_team_id, sort_by=sort_by,
                                   show=show)
    return fig, ax, table


def _restart_title(team_id: int, season_id: int, kind: str, what: str) -> tuple[str, str]:
    name = get_team_details(team_id)["name"]
    return name, f"{name} {season_label(season_id)} - {RESTART_NAMES[kind].lower()}, {what}"


def restart_zones(team_id: int, season_id: int, kind: str = "goal_kick", min_count: int = 3, show: bool = True):
    """Where the team's restarts, and the opposition's, landed - zones coloured by completion.

    Best for goal kicks and corners. Returns (fig, axes, restarts).
    """
    df = season_restarts(team_id, season_id)
    name, title = _restart_title(team_id, season_id, kind, "where they land and how often they find a team mate")
    fig, axes = plot_restart_zones(df, kind, name, title, min_count=min_count, show=show)
    return fig, axes, df


def restart_dots(team_id: int, season_id: int, kind: str = "throw_in", at: str = "start", show: bool = True):
    """Every restart of one kind as a dot, found a team mate or not. Returns (fig, axes, restarts).

    at="start" draws where it was taken (throw-ins, free kicks), "end" where it landed (corners).
    """
    df = season_restarts(team_id, season_id)
    where = "where they were taken" if at == "start" else "where they landed"
    name, title = _restart_title(team_id, season_id, kind, where)
    fig, axes = plot_restart_dots(df, kind, name, title, at=at, show=show)
    return fig, axes, df


def restart_arrows(team_id: int, season_id: int, kind: str = "goal_kick", show: bool = True):
    """Every restart of one kind as an arrow, blue found a team mate, red did not. Returns (fig, axes, restarts)."""
    df = season_restarts(team_id, season_id)
    name, title = _restart_title(team_id, season_id, kind, "every one")
    fig, axes = plot_restart_arrows(df, kind, name, title, show=show)
    return fig, axes, df


def restart_trend(team_id: int, season_id: int, rolling: int = 3, show: bool = True):
    """Restart completion game by game, ours against the opposition's. Returns (fig, axes, restarts)."""
    df = season_restarts(team_id, season_id)
    name = get_team_details(team_id)["name"]
    title = f"{name} {season_label(season_id)} - restarts that found a team mate, game by game"
    fig, axes = plot_restart_trend(df, name, title, rolling=rolling, show=show)
    return fig, axes, df


def ppda_trend(team_id: int, season_id: int, league_context: bool = True, show: bool = True):
    """The pressing battle (PPDA, ours and the opposition's) match by match.

    league_context draws the league average and middle-50% band, which
    fetches the advanced stats for every match in the division.
    """
    df = season_ppda_table(team_id, season_id)
    league = league_ppda_by_match(season_id)["ppda"] if league_context else None
    badges = {t: get_team_details(t)["imageDataURL"] for t in df["opponent_id"].unique()}
    title = f"{get_team_details(team_id)['name']} {season_label(season_id)} - how hard did we press?"
    return plot_ppda_trend(df, title, league=league, badges=badges, show=show)


def league_ppda(season_id: int, highlight_team_id: int | None = None, sort_by: str = "ppda", show: bool = True):
    """Every club's average PPDA for the season, as a ranked table. Returns (fig, ax, table).

    sort_by is "ppda" (hardest press first) or "dominance" (PPDA faced minus own PPDA, highest first).
    """
    by_match = league_ppda_by_match(season_id)
    df = league_ppda_table(season_id, by_match)
    title = f"National League {season_label(season_id)} - the pressing ladder"
    fig, ax = plot_league_ppda_table(df, by_match, title, highlight_team_id=highlight_team_id, sort_by=sort_by,
                                     show=show)
    return fig, ax, df


def league_field_tilt(season_id: int, highlight_team_id: int | None = None, sort_by: str = "tilt",
                      show: bool = True):
    """Every club's average field tilt for the season, as a ranked table. Returns (fig, ax, table).

    sort_by is "tilt" (most territory first), "tilt_losing", "tilt_level", "tilt_winning" (tilt in that
    score state) or "tilt_vs_possession" (tilt minus possession), highest first.
    """
    by_match = league_field_tilt_by_match(season_id)
    df = league_field_tilt_table(season_id, by_match)
    title = f"National League {season_label(season_id)} - the territory ladder"
    fig, ax = plot_league_field_tilt_table(df, by_match, title, highlight_team_id=highlight_team_id,
                                           sort_by=sort_by, show=show)
    return fig, ax, df


def field_tilt_timelines(
    team_id: int, season_id: int, window: float = 10, cols: int = 4, show_subs: bool = False,
    show_ppda: bool = False, show: bool = True,
):
    """A grid of every league match: the team's field tilt through the game, with the goals marked.

    show_subs=True marks both sides' substitutions as well; show_ppda=True
    overlays our PPDA over the same moving window.
    """
    matches = season_field_tilt_timelines(team_id, season_id, window, ppda=show_ppda)
    if show_subs:
        names = squad_names(team_id, season_id)
        for m in matches:
            changes = match_changes(m["summary"].match_id, team_id, names)
            m["changes"] = changes["changes"] if changes else None
    name = get_team_details(team_id)["name"]
    title = f"{name} {season_label(season_id)} - field tilt through every match ({window:g}-minute moving average)"
    return plot_field_tilt_timelines(matches, title, name, window=window, cols=cols, show=show)


def _seasons_label(season_ids: Sequence[int]) -> str:
    return " and ".join(season_label(s) for s in season_ids)


def sub_tilt_changes(team_id: int, season_id: int, window: float = 15, show: bool = True):
    """Field tilt in the window minutes before and after each of the team's changes. Returns (fig, ax, windows)."""
    windows, _ = season_change_windows(team_id, [season_id], window)
    name = get_team_details(team_id)["name"]
    title = f"{name} {season_label(season_id)} - did the substitutions shift the territory?"
    fig, ax = plot_sub_tilt_changes(windows, title, name, window=window, show=show)
    return fig, ax, windows


def sub_tilt_curve(
    team_id: int, season_ids: Sequence[int], window: float = 15, smooth: float = 5, by_state: bool = True,
    show: bool = True,
):
    """The average field tilt around a substitution, ours against theirs, optionally split by score state.

    season_ids pools several seasons - one season gives only 30 or so changes.
    """
    _, aligned = season_change_windows(team_id, season_ids, window)

    def curves(a):
        return (aligned_tilt_curve(a, "for", window, smooth), aligned_tilt_curve(a, "against", window, smooth))

    panels = {"Every change": curves(aligned)}
    if by_state:
        for state in ("losing", "level", "winning"):
            panels[f"Made when {state}"] = curves(aligned[aligned["state"] == state])
    name = get_team_details(team_id)["name"]
    title = f"{name} {_seasons_label(season_ids)} - field tilt either side of a substitution"
    return plot_aligned_tilt(panels, title, name, smooth=smooth, show=show)


def player_sub_tilt(
    team_id: int, season_ids: Sequence[int], window: float = 15, min_apps: int = 2, show: bool = True
):
    """Pooled field tilt before and after the changes each player came on or went off in. Returns (fig, axes, df)."""
    windows, _ = season_change_windows(team_id, season_ids, window)
    df = player_sub_impact(windows, min_apps)
    name = get_team_details(team_id)["name"]
    title = f"{name} {_seasons_label(season_ids)} - field tilt around each player's substitutions"
    fig, axes = plot_player_sub_impact(df, title, name, window=window, show=show)
    return fig, axes, df


def referees(team_id: int, season_id: int, history_season_ids: list[int] | None = None, show: bool = True):
    """Every league match's referee, what they gave and what they usually give. Returns (fig, ax, table).

    The referees' averages come from their other league games in season_id
    and history_season_ids (e.g. [PREV_SEASON]) - more seasons, steadier
    averages. The first run fetches every match in those seasons.
    """
    df = season_referee_table(team_id, season_id, history_season_ids)
    name = get_team_details(team_id)["name"]
    title = f"{name} {season_label(season_id)} - the referees"
    fig, ax = plot_referee_table(df, title, name, show=show)
    return fig, ax, df


def league_referees(
    season_id: int,
    history_season_ids: list[int] | None = None,
    team_id: int | None = None,
    sort_by: str = "yellows",
    min_games: int = 3,
    show: bool = True,
):
    """Every referee with a league game this season, ranked. Returns (fig, ax, table).

    Their numbers cover season_id and history_season_ids (e.g. [PREV_SEASON]):
    one season alone gives most referees only a handful of games. team_id
    highlights the referees that club has had and lists its results under
    them. sort_by is any stat column - see plot_league_referee_table.
    """
    seasons = [season_id, *(history_season_ids or [])]
    df = league_referee_table(seasons, team_id)
    name = get_team_details(team_id)["name"] if team_id else None
    span = season_label(season_id) + (f" (with {', '.join(season_label(s) for s in history_season_ids)})"
                                      if history_season_ids else "")
    title = f"National League {span} - the referees"
    fig, ax = plot_league_referee_table(df, title, name, sort_by=sort_by, min_games=min_games, show=show)
    return fig, ax, df


def season_comparison(team_id: int, season_id: int, previous_season_id: int, show: bool = True):
    """This season against last at the same stage: results table and cumulative charts."""
    return plot_season_comparison(
        season_results(team_id, season_id),
        season_results(team_id, previous_season_id),
        season_label(season_id),
        season_label(previous_season_id),
        get_team_details(team_id)["name"],
        show=show,
    )


def league_position(
    team_id: int,
    season_id: int,
    previous_season_id: int,
    competition_id: int,
    teams_in_league: int = 24,
    promotion_places: int = 1,
    playoff_places: int = 7,
    show: bool = True,
):
    """League position after each match day, and the gap to the leaders, against last season."""
    return plot_league_position(
        pd.DataFrame(table_progression(season_id, competition_id, team_id)),
        pd.DataFrame(table_progression(previous_season_id, competition_id, team_id)),
        season_label(season_id),
        season_label(previous_season_id),
        get_team_details(team_id)["name"],
        teams_in_league=teams_in_league,
        promotion_places=promotion_places,
        playoff_places=playoff_places,
        show=show,
    )


def possession_histogram(
    teams: dict[int, str],
    season_id: int,
    palette: Sequence[str] | None = None,
    bins: int = 10,
    show: bool = True,
):
    """How often each team had a given share of possession. teams is {id: label}."""
    frames = []
    for team_id, label in teams.items():
        df = possession_by_match(team_id, season_id)
        df["team"] = label
        frames.append(df)
    return plot_possession_histogram(pd.concat(frames, ignore_index=True), palette=palette, bins=bins, show=show)
