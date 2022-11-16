from wyscout.api import get_request


def get_team_squad(team_id: int, season_id: int) -> any:
    url = f"teams/{team_id}/squad"
    params = {
        "seasonId": season_id,
        "fetch": "teams"
    }
    return get_request(url, params)