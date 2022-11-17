from wyscout.api import get_request


def get_team_squad(team_id: int, season_id: int) -> any:
    url = f"teams/{team_id}/squad"
    params = {
        "seasonId": season_id,
        "fetch": "teams"
    }
    return get_request(url, params)


def get_player_stats(player_id: int, season_id: int, competition_id: int, round_id: int) -> any:
    url = f"players/{player_id}/advancedstats"
    params = {
        "seasonId": season_id,
        "compId": competition_id,
        "roundId": round_id,
    }
    return get_request(url, params)
