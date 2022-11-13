from wyscout.api import get_request


def get_team_matches(team_id: int, season_id: int) -> any:
    url = f"teams/{team_id}/matches"
    params = {"seasonId": str(season_id), "fetch": "team"}
    return get_request(url, params)


def get_match_events(match_id: int) -> any:
    url = f"matches/{match_id}/events"
    params = {
        "details": "tag",
        "fetch": "teams, players, match"
    }
    return get_request(url, params)


def get_match_details(match_id: int) -> any:
    url = f"matches/{match_id}"
    params = {
        "details": "tag",
        "fetch": "teams"
    }
    return get_request(url, params)
