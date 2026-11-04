"""Charts about one match."""

from collections.abc import Callable, Sequence
from typing import Any

from wyscout.data import filters
from wyscout.data.match import average_positions, events_by_half, pass_matrix, team_match
from wyscout.data.season import season_events
from wyscout.match import get_match_events
from wyscout.viz.arrows import ArrowOptions, passes_to_arrows
from wyscout.viz.consts import COLOUR_1, COLOUR_2, OPPO_COLOURS, TEAM_COLOURS
from wyscout.viz.event_map import EventPanel, Markers, plot_event_maps
from wyscout.viz.match import plot_average_positions, plot_final_third_passes, plot_xg_race
from wyscout.viz.player import plot_player_action_map
from wyscout.viz.shots import plot_shot_maps
from wyscout.viz.team import plot_pass_matrix

Event = dict[str, Any]

MATCH_TITLE = "{opponent} ({venue}), {date}, {result} {score}"
MATCH_TITLE_TWO_LINES = "{opponent} ({venue})\n{date}, {result} {score}"


def action_map(
    team_id: int,
    match_id: int,
    split_halves: bool = True,
    player_id: int | None = None,
    show_shots: bool = True,
    show_oppo_shots: bool = False,
    passes_received_by: int | None = None,
    subtitle: Sequence[str] | None = None,
    fig_height: float = 10,
    cmap: str = "Blues",
    shot_colors: tuple[str, str] = TEAM_COLOURS,
    oppo_shot_colors: tuple[str, str] = OPPO_COLOURS,
    show: bool = True,
):
    """Touch heat map with attempts on top - one pitch per half, or the whole match.

    player_id narrows the touches to one player. passes_received_by draws the
    passes to that player as arrows, red where the move ended in a goal.
    """
    tm = team_match(team_id, match_id)
    periods = events_by_half(tm.events) if split_halves else [tm.events]
    titles = ["1st half", "2nd half"] if split_halves else [""]

    panels = []
    for events, title in zip(periods, titles):
        ours = filters.for_team(events, team_id)
        subject = filters.for_player(ours, player_id) if player_id else ours
        panels.append(
            EventPanel(
                title=title,
                touches=filters.locations(subject),
                shots=filters.attempts(subject) if show_shots else [],
                oppo_shots=filters.attempts(filters.against_team(events, team_id)) if show_oppo_shots else [],
                arrows=passes_to_arrows(
                    filters.passes_to(ours, passes_received_by),
                    ArrowOptions(width=2, highlight=filters.led_to_goal),
                )
                if passes_received_by
                else [],
            )
        )

    return plot_event_maps(
        panels,
        tm.summary.title(MATCH_TITLE if split_halves else MATCH_TITLE_TWO_LINES),
        subtitle=subtitle,
        header_imgs=[tm.team_badge_url],
        fig_height=fig_height,
        cmap=cmap,
        shot_colors=shot_colors,
        oppo_shot_colors=oppo_shot_colors,
        show=show,
    )


def average_positions_map(
    team_id: int,
    match_id: int,
    split: str | None = "halves",
    filter_fn: Callable[[Event], bool] | None = None,
    titles: Sequence[str] = ("1st half", "2nd half"),
    fig_height: float = 10,
    colors: tuple[str, str] = ("blue", "cornflowerblue"),
    text_colors: tuple[str, str] = ("white", "black"),
    show: bool = True,
):
    """Mean position of every player who featured, shirt numbers on the markers.

    split="halves" gives one pitch per half; None gives the whole match. A
    filter_fn instead splits into the events it accepts and the events it
    rejects - e.g. before and after a sending off - titled with titles.
    """
    tm = team_match(team_id, match_id)
    ours = tm.team_events
    if filter_fn is not None:
        groups = [
            (titles[0], average_positions(ours, tm.formation, filter_fn=filter_fn)),
            (titles[1], average_positions(ours, tm.formation, filter_fn=lambda e: not filter_fn(e))),
        ]
    elif split == "halves":
        groups = [(t, average_positions(ours, tm.formation, period=p)) for t, p in zip(titles, ("1H", "2H"))]
    else:
        groups = [("", average_positions(ours, tm.formation))]

    return plot_average_positions(groups, tm.summary.title(MATCH_TITLE), badge=tm.team_badge_url,
                                  fig_height=fig_height, colors=colors, text_colors=text_colors, show=show)


def final_third_passes(
    team_id: int,
    match_id: int,
    subtitle: Sequence[str] = ("Passes in the final third",),
    pass_colors: tuple[str, str] = ("blue", "lightsteelblue"),
    fig_height: float = 10,
    cmap: str = "Blues",
    show: bool = True,
):
    """Every pass started in the final third, accurate ones in the first colour, over a touch map."""
    tm = team_match(team_id, match_id)
    ours = tm.team_events
    arrows = []
    for e in filters.where(filters.passes(ours), filters.in_final_third):
        colour = pass_colors[0] if e["pass"]["accurate"] else pass_colors[1]
        arrows.extend(passes_to_arrows([e], ArrowOptions(color=colour, width=2, highlight=filters.led_to_goal)))
    return plot_final_third_passes(filters.locations(ours), arrows, tm.summary.title(MATCH_TITLE),
                                   subtitle=subtitle, badge=tm.team_badge_url, fig_height=fig_height,
                                   cmap=cmap, show=show)


def xg_race(
    team_id: int,
    match_id: int,
    colours: Sequence[str] = ("blue", "green"),
    ax=None,
    show: bool = True,
):
    """Cumulative xG for both sides through the match; our team takes the first colour."""
    tm = team_match(team_id, match_id)
    teams = [(team_id, tm.summary.team), (tm.summary.opponent_id, tm.summary.opponent)]
    return plot_xg_race(filters.attempts(tm.events, include_pens=True), teams, colours, ax=ax,
                        title=tm.summary.title(MATCH_TITLE), show=show)


def shot_map(
    team_id: int,
    match_id: int,
    include_pens: bool = False,
    both_teams: bool = False,
    fig_height: float = 8,
    show: bool = True,
):
    """Attempts on a striped half pitch - ours, or ours beside the opposition's."""
    tm = team_match(team_id, match_id)
    groups = [filters.attempts(tm.team_events, include_pens=include_pens)]
    titles = [tm.summary.team]
    if both_teams:
        groups.append(filters.attempts(tm.opponent_events, include_pens=include_pens))
        titles.append(tm.summary.opponent)
    return plot_shot_maps(groups, tm.summary.title(MATCH_TITLE), fig_height=fig_height,
                          panel_titles=titles if both_teams else None, show=show)


def foul_map(
    team_id: int,
    match_id: int,
    colors: tuple[str, str] = ("blue", "red"),
    card_edge: str = "gold",
    fig_height: float = 10,
    show: bool = True,
):
    """Every foul on one pitch - won by us in the first colour, conceded in the second,
    ringed gold where it drew a yellow card.

    Wyscout locations are oriented to the event's own team, attacking towards x=100 -
    so the opposition's fouls are flipped (100-x, 100-y) to share our attacking end.
    """
    tm = team_match(team_id, match_id)
    fouls = filters.fouls(tm.events)
    groups = [
        ("Won", filters.against_team(fouls, team_id), colors[0], True),
        ("Conceded", filters.for_team(fouls, team_id), colors[1], False),
    ]

    markers = []
    for label, events, color, flip in groups:
        carded = [e for e in events if filters.is_yellow(e)]
        plain = [e for e in events if not filters.is_yellow(e)]
        card_note = f", {len(carded)} yellow" if carded else ""

        def locs(subset: list[Event], flip: bool = flip) -> list[list[float]]:
            points = filters.locations(subset)
            return [[100 - x, 100 - y] for x, y in points] if flip else points

        markers.append(Markers(locations=locs(plain), color=color,
                               label=f"{label} ({len(events)}{card_note})"))
        markers.append(Markers(locations=locs(carded), color=color,
                               edgecolor=card_edge, linewidth=2.5))

    panel = EventPanel(markers=markers)
    return plot_event_maps(
        [panel],
        tm.summary.title(MATCH_TITLE_TWO_LINES),
        subtitle=["Fouls won and conceded, ringed gold for a yellow card"],
        header_imgs=[tm.team_badge_url],
        fig_height=fig_height,
        legend=True,
        show=show,
    )


def player_action_map(
    player_id: int,
    team_id: int,
    match_id: int,
    show_passes: bool = False,
    show_crosses: bool = False,
    show_passes_received: bool = False,
    period: str | None = None,
    subtitle: str = "",
    highlight_first_half: bool = False,
    fig_height: float = 16,
    show: bool = True,
):
    """One player's touches in a match, with their passes, crosses or the passes they received."""
    tm = team_match(team_id, match_id)
    events = filters.in_period(tm.team_events, period) if period else tm.team_events
    own = filters.for_player(events, player_id)
    options = ArrowOptions(width=2, highlight=filters.is_first_half if highlight_first_half else lambda e: False)

    arrows = []
    if show_passes:
        arrows = passes_to_arrows(filters.passes(own), options)
    elif show_passes_received:
        arrows = passes_to_arrows(filters.passes_to(events, player_id), options)
    crosses = passes_to_arrows(filters.crosses(own), options) if show_crosses else []

    player = tm.player(player_id)
    return plot_player_action_map(
        f"{player['firstName']} {player['lastName']}",
        tm.summary.title("{opponent} ({venue}) {date}"),
        subtitle,
        filters.locations(own),
        arrows,
        crosses,
        player_img=player["imageDataURL"],
        fig_height=fig_height,
        show=show,
    )


def pass_matrix_chart(
    team_id: int,
    season_id: int | None = None,
    match_ids: Sequence[int] | None = None,
    title: str | None = None,
    show: bool = True,
):
    """Who passes to whom, over a whole season or the given matches."""
    if match_ids is None:
        # only the matches whose events have been published
        match_ids = [m["summary"].match_id for m in season_events(team_id, season_id)]
    events: list[Event] = []
    squad: dict[int, Any] = {}
    for match_id in match_ids:
        tm = team_match(team_id, match_id)
        events.extend(tm.team_events)
        squad.update(tm.squad)
    players, counts = pass_matrix(events, squad)
    return plot_pass_matrix(players, counts, title=title or f"Passes between team mates - {len(match_ids)} matches", show=show)


def events_for(team_id: int, match_id: int) -> list[Event]:
    """The raw events of a match, both teams - for poking around."""
    return get_match_events(match_id).get("events", [])


DEFAULT_PASS_COLOURS = (COLOUR_1, COLOUR_2)
