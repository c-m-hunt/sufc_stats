from typing import Dict, List, Any, Optional


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
