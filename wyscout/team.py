from typing import Optional

from wyscout.api.api import get_request
from wyscout.api.mongo_cache import cache_request


@cache_request("teamSquad", expires_hr=72)
def get_team_squad(team_id: int, season_id: int) -> any:
    url = f"teams/{team_id}/squad"
    params = {"seasonId": season_id, "fetch": "team"}
    return get_request(url, params)


@cache_request("playerStats", expires_hr=24)
def get_player_stats(
    player_id: int, season_id: int, competition_id: int, round_id: Optional[int] = None
) -> any:
    url = f"players/{player_id}/advancedstats"
    params = {
        "seasonId": season_id,
        "compId": competition_id,
    }
    if round_id:
        params["roundId"] = round_id
    return get_request(url, params)


@cache_request("teamDetail", expires_hr=240)
def get_team_details(team_id: int):
    url = f"teams/{team_id}"
    return get_request(url, {})
