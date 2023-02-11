from wyscout.match import get_match_details, get_match_events, get_team_matches
from wyscout.events import get_key_pass_events
from wyscout.stats import get_match_events_for_season
from wyscout.team import get_team_details, get_team_squad


def get_match_details_and_events(
    team_id: int,
    match_id: int,
    all_events: bool = False
):
    match_details = get_match_details(match_id)
    season_id = match_details["seasonId"]
    matches = get_match_events_for_season(
        team_id, season_id, match_id=match_id, all_events=all_events)
    squad = get_team_squad(team_id, season_id)
    squad = {p["wyId"]: p for p in squad["squad"]}

    team_details = {
        int(t): get_team_details(int(t)) for t in match_details["teamsData"]
    }

    filtered_matches = [m for m in matches if m["matchId"] == match_id]
    if len(filtered_matches) == 0:
        print("No no match found")
        return

    match = filtered_matches[0]

    return match, match_details, squad, team_details


def get_shots(team_id: int, season_id: int, all_events=False):
    matches = get_team_matches(team_id, season_id)
    events_out = []
    for m in matches["matches"]:
        events = get_match_events(m["matchId"])
        if "events" in events:
            events_out.append({
                "matchId": m["matchId"],
                "date": m["date"],
                "label": m["label"],
                "events": [e for e in events["events"] if e["team"]["id"] == team_id] if not all_events else events["events"]
            })
    return events_out


def get_key_passes(team_id: int, season_id: int):
    matches = get_team_matches(team_id, season_id)
    key_pass_events = []
    for m in matches["matches"]:
        events = get_match_events(m["matchId"])
        if "events" in events:
            key_pass_events.append(get_key_pass_events(
                m, events["events"], team_id))
    return key_pass_events
