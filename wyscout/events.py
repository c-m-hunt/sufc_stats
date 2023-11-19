from typing import Any, Dict, List, Optional

from wyscout.api.api import get_request
from wyscout.api.mongo_cache import cache_request
from wyscout.match import get_match_details, get_match_details_and_events
from wyscout.team import get_team_squad


@cache_request("videos", expires_hr=10000)
def get_video_for_event(
    event: Any, padding: int = 5, length: int = 5, quality="hd"
) -> str:
    url = f"videos/{event['matchId']}"
    params = {
        "start": int(float(event["videoTimestamp"]) - padding),
        "end": int(float(event["videoTimestamp"]) + length),
        "quality": quality,
    }
    return get_request(url, params)


def add_team_to_match_details(match_details: Any) -> Any:
    team_ids = list(match_details["teamsData"].keys())
    squads = {t: get_team_squad(t, match_details["seasonId"]) for t in team_ids}
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


def get_average_positions(
    team_id: int,
    match_id: int,
    period: Optional[str] = None,
    filter_fn: callable = None,
):
    match, match_details, squad, team_details = get_match_details_and_events(
        team_id, match_id
    )

    events = match["events"]
    locations = {}
    for event in events:
        if period is not None and event["matchPeriod"] != period:
            continue
        if filter_fn is not None:
            if not filter_fn(event):
                continue
        player_id = event["player"]["id"]
        if player_id not in locations:
            locations[player_id] = []
        locations[player_id].append(event["location"])
        if event["type"]["primary"] == "pass" and event["pass"]["accurate"]:
            recipient_id = event["pass"]["recipient"]["id"]
            if recipient_id not in locations:
                locations[recipient_id] = []
            locations[recipient_id].append(event["pass"]["endLocation"])

    squad_average_locations = {}
    for player_id in locations:
        if player_id > 0:
            squad_average_locations[player_id] = {
                "x": sum([l["x"] for l in locations[player_id]])
                / len(locations[player_id]),
                "y": sum([l["y"] for l in locations[player_id]])
                / len(locations[player_id]),
            }

    team = match_details["teamsData"][str(team_id)]
    team_average_locations = {}
    for player_id in squad_average_locations:
        found = False
        for player in team["formation"]["lineup"]:
            player_id = player["playerId"]
            if player_id not in squad_average_locations:
                continue
            if player_id not in team_average_locations:
                team_average_locations[player_id] = {}
            lineup_player = [
                p for p in team["formation"]["lineup"] if p["playerId"] == player_id
            ]
            if not lineup_player:
                continue
            team_average_locations[player_id]["ave_location"] = squad_average_locations[
                player_id
            ]
            [p for p in team["formation"]["lineup"] if p["playerId"] == player_id][0]
            team_average_locations[player_id]["shirt"] = [
                p for p in team["formation"]["lineup"] if p["playerId"] == player_id
            ][0]["shirtNumber"]
            team_average_locations[player_id]["start"] = True
            found = True
        for player in team["formation"]["bench"]:
            player_id = player["playerId"]
            if player_id not in squad_average_locations:
                continue
            if player_id not in team_average_locations:
                team_average_locations[player_id] = {}
            lineup_player = [
                p for p in team["formation"]["bench"] if p["playerId"] == player_id
            ]
            if not lineup_player:
                continue
            team_average_locations[player_id]["ave_location"] = squad_average_locations[
                player_id
            ]
            team_average_locations[player_id]["shirt"] = lineup_player[0]["shirtNumber"]
            team_average_locations[player_id]["start"] = False
            found = True
        if not found:
            print("Player not found", player_id)

    return squad_average_locations, team_average_locations
