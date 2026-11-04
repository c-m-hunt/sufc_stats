from typing import Any

from wyscout.api.api import get_request
from wyscout.api.mongo_cache import cache_request
from wyscout.team import get_team_details, get_team_squad


@cache_request("competitionMatches", expires_hr=72)
def get_competition_matches(competition_id: int) -> any:
    url = f"competitions/{competition_id}/matches"
    params = {"fetch": "competition"}
    return get_request(url, params)


@cache_request("teamMatches", expires_hr=24)
def get_team_matches(team_id: int, season_id: int) -> any:
    url = f"teams/{team_id}/matches"
    params = {"seasonId": str(season_id), "fetch": "team"}
    return get_request(url, params)


@cache_request("matchEvents")
def get_match_events(match_id: int) -> any:
    url = f"matches/{match_id}/events"
    params = {"details": "tag", "fetch": "teams, players, match"}
    return get_request(url, params)


@cache_request("matchDetail")
def get_match_details(match_id: int) -> any:
    url = f"matches/{match_id}"
    params = {"details": "tag", "fetch": "teams"}
    return get_request(url, params)

@cache_request("videoDetails")
def get_video_details(match_id: int) -> any:
    url = f"videos/{match_id}"
    params = {}
    return get_request(url, params)

@cache_request("advancedMatchStats", expires_hr=10000)
def get_match_advanced_stats(match_id: int) -> any:
    url = f"matches/{match_id}/advancedstats"
    params = {}
    return get_request(url, params)

# not cached: the download link it returns is signed and expires within a day
def get_match_tracking_url(match_id: int) -> any:
    url = f"matches/{match_id}/fulltracking"
    params = {}
    return get_request(url, params)

@cache_request("matchPhysicalData", expires_hr=10000)
def get_match_physical_data(match_id: int) -> any:
    url = f"matches/{match_id}/physicaldata"
    params = {}
    return get_request(url, params)

def get_match_details_and_events(team_id: int, match_id: int, all_events: bool = False):
    match_details = get_match_details(match_id)
    season_id = match_details["seasonId"]
    matches = get_match_events_for_season(
        team_id, season_id, match_id=match_id, all_events=all_events
    )
    squad = get_team_squad(team_id, season_id)
    squad = {p["wyId"]: p for p in squad["squad"]}

    team_details = {
        int(t): get_team_details(int(t)) for t in match_details["teamsData"]
    }

    filtered_matches = [m for m in matches if m["matchId"] == match_id]
    if len(filtered_matches) == 0:
        raise ValueError(f"No events found for match {match_id}")

    match = filtered_matches[0]

    return match, match_details, squad, team_details


def get_match_events_for_season(
    team_id: int, season_id: int, match_id: int | None = None, all_events=False
):
    matches = get_team_matches(team_id, season_id)
    events_out = []
    for m in matches["matches"]:
        if match_id is not None and m["matchId"] != match_id:
            continue
        events = get_match_events(m["matchId"])
        if "events" in events:
            events_out.append(
                get_events_with_match(
                    m, events["events"], team_id if not all_events else None
                )
            )
    return events_out


def get_events_with_match(
    match: dict[str, Any], events: list[dict[str, Any]], team_id: str | None
) -> list[dict[str, Any]]:
    events_out = []
    for event in events:
        if not team_id or event["team"]["id"] == team_id:
            events_out.append(event)
    return {
        "matchId": match["matchId"],
        "matchDate": match["date"],
        "opposition": events[0]["opponentTeam"]["name"],
        "events": events_out,
    }


@cache_request("videos", expires_hr=10000)
def get_video_for_event(event: Any, padding: int = 5, length: int = 5, quality: str = "hd") -> Any:
    """A clip URL around one event, from padding seconds before it to length after."""
    url = f"videos/{event['matchId']}"
    params = {
        "start": int(float(event["videoTimestamp"]) - padding),
        "end": int(float(event["videoTimestamp"]) + length),
        "quality": quality,
    }
    return get_request(url, params)


@cache_request("referees", expires_hr=10000)
def get_referee(referee_id: int) -> any:
    return get_request(f"referees/{referee_id}", {})
