from typing import Any, Dict, List, Optional

from wyscout.match import (
    get_match_details,
    get_match_events,
    get_match_events_for_season,
    get_team_matches,
)
from wyscout.team import get_team_details, get_team_squad


def get_shots(team_id: int, season_id: int, all_events=False):
    matches = get_team_matches(team_id, season_id)
    events_out = []
    for m in matches["matches"]:
        events = get_match_events(m["matchId"])
        if "events" in events:
            events_out.append(
                {
                    "matchId": m["matchId"],
                    "date": m["date"],
                    "label": m["label"],
                    "events": [
                        e for e in events["events"] if e["team"]["id"] == team_id
                    ]
                    if not all_events
                    else events["events"],
                }
            )
    return events_out


def get_key_passes(team_id: int, season_id: int):
    matches = get_team_matches(team_id, season_id)
    key_pass_events = []
    for m in matches["matches"]:
        events = get_match_events(m["matchId"])
        if "events" in events:
            key_pass_events.append(get_key_pass_events(m, events["events"], team_id))
    return key_pass_events


def get_key_pass_events(
    match: Dict[str, Any], events: List[Dict[str, Any]], team_id: Optional[str]
) -> List[Dict[str, Any]]:
    key_pass_events = []
    for event in events:
        if "key_pass" in event["type"]["secondary"] and (
            not team_id or event["team"]["id"] == team_id
        ):
            key_pass_events.append(event)
    return {
        "matchDate": match["date"],
        "opposition": events[0]["opponentTeam"]["name"],
        "events": key_pass_events,
    }
