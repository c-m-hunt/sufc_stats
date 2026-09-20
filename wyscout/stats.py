from wyscout.match import (
    get_events_with_match,
    get_match_details,
    get_match_events,
    get_team_matches,
)


def get_touches_in_box(team_id: int, season: int, match_id: int = None):
    matches = get_team_matches(team_id, season)
    touches_in_box = {}
    for m in matches["matches"]:
        if match_id is not None and m["matchId"] != match_id:
            continue
        events = get_match_events(m["matchId"])
        if "events" in events:
            for e in events["events"]:
                if e["team"]["id"] == team_id and "touch_in_box" in (
                    e["type"]["secondary"]
                ):
                    if e["player"]["name"] not in touches_in_box.keys():
                        touches_in_box[e["player"]["name"]] = 0
                    touches_in_box[e["player"]["name"]] += 1

    touches_in_box = {
        k: v
        for k, v in sorted(
            touches_in_box.items(), key=lambda item: item[1], reverse=True
        )
    }
    return touches_in_box


def get_touches_for_player(
    player_id: int, team_id: int, season_id: int, made_received="made"
):
    matches = get_team_matches(team_id, season_id)
    events_out = []
    for m in matches["matches"]:
        events = get_match_events(m["matchId"])
        if "events" in events:
            if made_received == "made":
                touches = [
                    t
                    for t in get_events_with_match(m, events["events"], team_id)[
                        "events"
                    ]
                    if t["player"]["id"] == player_id
                ]
            else:
                touches = [
                    t
                    for t in get_events_with_match(m, events["events"], team_id)[
                        "events"
                    ]
                    if t["pass"]
                    and "recipient" in t["pass"]
                    and "id" in t["pass"]["recipient"]
                    and t["pass"]["recipient"]["id"] == player_id
                ]

            if len(touches) > 0:
                events_out.append(
                    {
                        "matchId": m["matchId"],
                        "matchDate": m["date"],
                        "opposition": touches[0]["opponentTeam"]["name"],
                        "events": touches,
                    }
                )
    return events_out


def get_events_for_player(player_id: int, team_id: int, matches: list):
    event_types = [
        "infraction",
        "interception",
        "pass",
        "shot",
        "duel",
        "pass_received",
    ]

    all_events = []
    for m in matches["matches"]:
        events_out = {}
        events = get_match_events(m["matchId"])
        if "events" in events:
            oppo = (events["events"][0]["opponentTeam"]["name"],)
            for event_type in event_types:
                events_out[event_type] = [
                    t
                    for t in get_events_with_match(m, events["events"], team_id)[
                        "events"
                    ]
                    if t["player"]["id"] == player_id
                    and t["type"]["primary"] == event_type
                ]
            if "passes_received" in events_out.keys():
                events_out["passes_received"] = [
                    t
                    for t in get_events_with_match(m, events["events"], team_id)[
                        "events"
                    ]
                    if t["pass"]
                    and "recipient" in t["pass"]
                    and "id" in t["pass"]["recipient"]
                    and t["pass"]["recipient"]["id"] == player_id
                ]

            if sum([len(e) for e in events_out.values()]) > 0:
                all_events.append(
                    {
                        "matchId": m["matchId"],
                        "matchDate": m["date"],
                        "opposition": oppo,
                        "events": events_out,
                    }
                )
    return all_events


def get_matches_for_player(player_id: int, team_id: int, season_id: int):
    matches = get_team_matches(team_id, season_id)
    return [
        m
        for m in matches["matches"]
        if player_in_match(player_id, get_match_details(m["matchId"]))
    ]


def player_in_match(player_id: int, match_details):
    team_ids = match_details["teamsData"].keys()
    team1_lineup = [
        l["playerId"]
        for l in match_details["teamsData"][list(team_ids)[0]]["formation"]["lineup"]
    ]
    team2_lineup = [
        l["playerId"]
        for l in match_details["teamsData"][list(team_ids)[1]]["formation"]["lineup"]
    ]
    return player_id in team1_lineup or player_id in team2_lineup


HALF_LENGTH = 45
FULL_TIME = 90


def get_player_spells(player_id: int, team_id: int, match_details):
    """Spells of (start, end) match minutes the player was on the pitch.

    Minutes are nominal - each half counts as 45, so a full match is 90 and a
    half time substitution is 45, regardless of stoppage time played.
    """
    formation = match_details["teamsData"][str(team_id)].get("formation") or {}
    lineup = formation.get("lineup") or []
    subs = formation.get("substitutions") or []
    if not isinstance(subs, list):
        subs = []

    start = 0 if player_id in [l["playerId"] for l in lineup] else None
    end = FULL_TIME

    for s in subs:
        if s["playerIn"] == player_id:
            start = s["minute"]
        if s["playerOut"] == player_id:
            end = s["minute"]

    if start is None:
        return []

    for entry in lineup + (formation.get("bench") or []):
        if entry["playerId"] == player_id:
            red_card = int(entry.get("redCards") or 0)
            if red_card > 0:
                end = min(end, red_card)

    return [(start, end)] if end > start else []


def get_minutes_played(spells):
    return sum(end - start for start, end in spells)


def event_minute(event) -> float:
    """Event minute on the same nominal timeline as get_player_spells."""
    minute = event["minute"]
    if event["matchPeriod"] == "1H":
        return min(minute, HALF_LENGTH - 0.01)
    if event["matchPeriod"] == "2H":
        return min(max(minute, HALF_LENGTH), FULL_TIME - 0.01)
    return minute


def event_in_spells(event, spells) -> bool:
    minute = event_minute(event)
    return any(start <= minute < end for start, end in spells)
