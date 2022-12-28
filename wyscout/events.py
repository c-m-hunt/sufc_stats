from typing import Dict, List, Any, Optional
from wyscout.api.api import get_request
from wyscout.api.mongo_cache import cache_request
from wyscout.team import get_team_squad
from wyscout.match import get_match_details


def get_key_pass_events(match: Dict[str, Any], events: List[Dict[str, Any]], team_id: Optional[str]) -> List[Dict[str, Any]]:
    key_pass_events = []
    for event in events:
        if "key_pass" in event["type"]["secondary"] and (not team_id or event["team"]["id"] == team_id):
            key_pass_events.append(event)
    return {
        "matchDate": match["date"],
        "opposition": events[0]["opponentTeam"]["name"],
        "events": key_pass_events
    }


def get_events_with_match(match: Dict[str, Any], events: List[Dict[str, Any]], team_id: Optional[str]) -> List[Dict[str, Any]]:
    events_out = []
    for event in events:
        if (not team_id or event["team"]["id"] == team_id):
            events_out.append(event)
    return {
        "matchId": match["matchId"],
        "matchDate": match["date"],
        "opposition": events[0]["opponentTeam"]["name"],
        "events": events_out
    }


@cache_request("videos", expires_hr=10000)
def get_video_for_event(event: Any, padding: int = 5, length: int = 5, quality="hd") -> str:
    url = f"videos/{event['matchId']}"
    params = {
        "start": int(float(event["videoTimestamp"]) - padding),
        "end": int(float(event["videoTimestamp"]) + length),
        "quality": quality,
    }
    return get_request(url, params)


def add_team_to_match_details(match_details: Any) -> Any:
    team_ids = list(match_details["teamsData"].keys())
    squads = {
        t: get_team_squad(t, match_details["seasonId"])
        for t in team_ids
    }
    for k in squads.keys():
        squads[k] = {p["wyId"]: p for p in squads[k]["squad"]}
    for t_id in match_details["teamsData"]:
        players = {}
        keys = ["lineup", "bench"]
        for k in keys:
            for p in match_details["teamsData"][t_id]["formation"][k]:
                p["playerDetails"] = squads[t_id][p["playerId"]]
                players[p["playerId"]] = p
        match_details["teamsData"][t_id]["players"] = players
    return match_details


def get_match_details_with_teams(match_id: int) -> Dict[int, Any]:
    match_details = get_match_details(match_id)
    return add_team_to_match_details(match_details)
