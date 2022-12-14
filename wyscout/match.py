from wyscout.api.api import get_request
from wyscout.api.mongo_cache import cache_request


@cache_request("competitionMatches", expires_hr=72)
def get_competition_matches(competition_id: int) -> any:
    url = f"competitions/{competition_id}/matches"
    params = {"fetch": "competition"}
    return get_request(url, params)


@cache_request("teamMatches", expires_hr=24)
def get_team_matches(team_id: int, season_id: int) -> any:
    url = f"teams/{team_id}/matches"
    params = {"seasonId": str(season_id), "fetch": "teams"}
    return get_request(url, params)


@cache_request("matchEvents")
def get_match_events(match_id: int) -> any:
    url = f"matches/{match_id}/events"
    params = {
        "details": "tag",
        "fetch": "teams, players, match"
    }
    return get_request(url, params)


@cache_request("matchDetail")
def get_match_details(match_id: int) -> any:
    url = f"matches/{match_id}"
    params = {
        "details": "tag",
        "fetch": "teams"
    }
    return get_request(url, params)
