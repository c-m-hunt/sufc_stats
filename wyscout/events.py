from typing import Dict, List, Any, Optional
from wyscout.api.api import get_request
from wyscout.api.mongo_cache import cache_request


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


@cache_request("videos", expires_hr=10000)
def get_video_for_event(event: Any, padding: int = 5, length: int = 5, quality="hd") -> str:
    url = f"videos/{event['matchId']}"
    params = {
        "start": int(float(event["videoTimestamp"]) - padding),
        "end": int(float(event["videoTimestamp"]) + length),
        "quality": quality,
    }
    return get_request(url, params)
