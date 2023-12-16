from wyscout.match import (
    get_events_with_match,
    get_match_details,
    get_match_events,
    get_team_matches,
)


def get_touches_in_box(team_id: int, season: int, match_id: int = None):
    matches = get_team_matches(team_id, season)
    touches_in_box = {}
    for m in matches["matches"]:
        if match_id is not None and m["matchId"] != match_id:
            continue
        events = get_match_events(m["matchId"])
        if "events" in events:
            for e in events["events"]:
                if e["team"]["id"] == team_id and "touch_in_box" in (
                    e["type"]["secondary"]
                ):
                    if e["player"]["name"] not in touches_in_box.keys():
                        touches_in_box[e["player"]["name"]] = 0
                    touches_in_box[e["player"]["name"]] += 1

    touches_in_box = {
        k: v
        for k, v in sorted(
            touches_in_box.items(), key=lambda item: item[1], reverse=True
        )
    }
    return touches_in_box


def get_touches_for_player(
    player_id: int, team_id: int, season_id: int, made_received="made"
):
    matches = get_team_matches(team_id, season_id)
    events_out = []
    for m in matches["matches"]:
        events = get_match_events(m["matchId"])
        if "events" in events:
            if made_received == "made":
                touches = [
                    t
                    for t in get_events_with_match(m, events["events"], team_id)[
                        "events"
                    ]
                    if t["player"]["id"] == player_id
                ]
            else:
                touches = [
                    t
                    for t in get_events_with_match(m, events["events"], team_id)[
                        "events"
                    ]
                    if t["pass"]
                    and "recipient" in t["pass"]
                    and "id" in t["pass"]["recipient"]
                    and t["pass"]["recipient"]["id"] == player_id
                ]

            if len(touches) > 0:
                events_out.append(
                    {
                        "matchId": m["matchId"],
                        "matchDate": m["date"],
                        "opposition": touches[0]["opponentTeam"]["name"],
                        "events": touches,
                    }
                )
    return events_out


def get_matches_for_player(player_id: int, team_id: int, season_id: int):
    matches = get_team_matches(team_id, season_id)
    return [
        m
        for m in matches["matches"]
        if player_in_match(player_id, get_match_details(m["matchId"]))
    ]


def player_in_match(player_id: int, match_details):
    team_ids = match_details["teamsData"].keys()
    team1_lineup = [
        l["playerId"]
        for l in match_details["teamsData"][list(team_ids)[0]]["formation"]["lineup"]
    ]
    team2_lineup = [
        l["playerId"]
        for l in match_details["teamsData"][list(team_ids)[1]]["formation"]["lineup"]
    ]
    return player_id in team1_lineup or player_id in team2_lineup
