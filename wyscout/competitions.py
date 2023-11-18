from wyscout.api.api import get_request
from wyscout.api.mongo_cache import cache_request


@cache_request("competitions", expires_hr=1000)
def get_competitions(area_id: str) -> any:
    url = f"competitions"
    params = {"areaId": area_id}
    return get_request(url, params)


@cache_request("competitions", expires_hr=1000)
def get_competition_seasons(competition_id: str) -> any:
    url = f"competitions/{competition_id}/seasons"
    params = {"fetch": "competition"}
    return get_request(url, params)


def get_competition_rounds(competition_id: str) -> any:
    url = f"rounds/{competition_id}"
    return get_request(url, {})


# @cache_request("competitionPlayers", expires_hr=24)


def get_competition_players(
    competition_id: int, limit: int = 100, page: int = 1
) -> any:
    url = f"competitions/{competition_id}/players"
    params = {"limit": limit, "page": page}
    return get_request(url, params)


def get_all_competition_players(competition_id: int) -> any:
    players = []
    resp = get_competition_players(competition_id)
    players.extend(resp["players"])
    if resp["meta"]["page_count"] > 1:
        for page in range(2, resp["meta"]["page_count"] + 1):
            resp = get_competition_players(competition_id, page=page)
            players.extend(resp["players"])
    return players
