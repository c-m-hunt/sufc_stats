
from typing import Any, Dict, List

from wyscout.competitions import get_competition_teams, get_season_matches
from wyscout.match import get_match_details
from wyscout.team import get_team_details


def league_table(matches: List[Dict[str, Any]]) -> Dict[str, Any]:
    table = {}
    for m in matches:
        if m["status"] != "Played":
            continue

        teams_data = m["teamsData"]
        teams = [None, None]
        score = [None, None]
        for t in teams_data.values():
            if t["side"] == "home":
                teams[0] = t["teamId"]
                score[0] = t["score"]
            else:
                teams[1] = t["teamId"]
                score[1] = t["score"]

        if len(teams) != 2:
            continue
        if len(score) != 2:
            continue
        if teams[0] == teams[1]:
            continue

        for team in teams:
            if team not in table:
                table[team] = {
                    "played":0,
                    "won": 0,
                    "drawn": 0, 
                    "lost": 0,
                    "goals_for": 0,
                    "goals_against": 0,
                    "goal_difference": 0,
                    "points": 0,
                }
        if score[0] > score[1]:
            table[teams[0]]["points"] += 3
            table[teams[0]]["won"] += 1
            table[teams[1]]["lost"] += 1
        elif score[0] < score[1]:
            table[teams[1]]["points"] += 3
            table[teams[1]]["won"] += 1
            table[teams[0]]["lost"] += 1
        else:
            table[teams[0]]["points"] += 1
            table[teams[1]]["points"] += 1
            table[teams[0]]["drawn"] += 1
            table[teams[1]]["drawn"] += 1
        table[teams[0]]["played"] += 1
        table[teams[1]]["played"] += 1
        table[teams[0]]["goals_for"] += score[0]
        table[teams[0]]["goals_against"] += score[1]
        table[teams[1]]["goals_for"] += score[1]
        table[teams[1]]["goals_against"] += score[0]
        table[teams[0]]["goal_difference"] = table[teams[0]]["goals_for"] - table[teams[0]]["goals_against"]
        table[teams[1]]["goal_difference"] = table[teams[1]]["goals_for"] - table[teams[1]]["goals_against"]
    table = sorted(table.items(), key=lambda x: (x[1]["points"], x[1]["goal_difference"]), reverse=True)

    return table

def league_table_at_date(season_id: int, competition_id: int, end_date: str, start_date: str = None) -> List[Dict[str, Any]]:
    matches = get_season_matches(season_id)
    teams = get_competition_teams(competition_id)
    team_map = { t["wyId"]: t["name"] for t in teams["teams"] }
    matches = [m for m in matches["matches"] if m["date"] <= end_date]
    if start_date is not None:
        matches = [m for m in matches if m["date"] >= start_date]
    matches = [m for m in matches if m["status"] == "Played"]
    table_match_details = []
    for m in matches:
        match_details = get_match_details(m["matchId"])
        table_match_details.append(match_details)

    table = league_table(table_match_details)
    for i, t in enumerate(table):
        team_id = t[0]
        try:
            team_name = team_map[team_id]
        except KeyError:
            team_detail = get_team_details(team_id)
            team_name = team_detail["name"]
        table[i] = {
            "position": i + 1,
            "team_id": team_id,
            "team_name": team_name,
            "played": t[1]["played"],
            "won": t[1]["won"],
            "drawn": t[1]["drawn"],
            "lost": t[1]["lost"],
            "goals_for": t[1]["goals_for"],
            "goals_against": t[1]["goals_against"],
            "goal_difference": t[1]["goal_difference"],
            "points": t[1]["points"],
        }
    return table