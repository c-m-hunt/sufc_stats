
from collections import Counter
from typing import Any

from wyscout.competitions import get_competition_teams, get_season_matches
from wyscout.match import get_match_details
from wyscout.team import get_team_details


def add_match_to_table(table: dict[int, dict[str, int]], m: dict[str, Any]) -> None:
    """Fold one match's result into a running table, keyed by team id."""
    if m["status"] != "Played":
        return

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

    if None in teams or None in score:
        return
    if teams[0] == teams[1]:
        return

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


def sort_table(table: dict[int, dict[str, int]]) -> list[Any]:
    """Points, then goal difference, then goals scored - the National League order."""
    return sorted(
        table.items(),
        key=lambda x: (x[1]["points"], x[1]["goal_difference"], x[1]["goals_for"]),
        reverse=True,
    )


def league_table(matches: list[dict[str, Any]]) -> dict[str, Any]:
    table = {}
    for m in matches:
        add_match_to_table(table, m)

    return sort_table(table)

def league_table_at_date(season_id: int, competition_id: int, end_date: str, start_date: str | None = None) -> list[dict[str, Any]]:
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

def league_match_details(season_id: int) -> list[dict[str, Any]]:
    """Played league matches for a season, oldest first, with play-offs dropped.

    Play-offs sit in their own round, so the league round is taken to be the
    one nearly every match of the season belongs to.

    Each detail dict gains a "kickoff" key holding the local kick-off time as
    "YYYY-MM-DD HH:MM:SS" - the details' own "date" field is a display string
    ("September 19, 2026 at 6:30:00 PM GMT+2"), which does not sort.
    """
    matches = [
        m for m in get_season_matches(season_id)["matches"] if m["status"] == "Played"
    ]
    league_round = Counter(m["roundId"] for m in matches).most_common(1)[0][0]
    matches = [m for m in matches if m["roundId"] == league_round]

    details = []
    for m in matches:
        detail = dict(get_match_details(m["matchId"]))
        detail["kickoff"] = m["date"]
        details.append(detail)

    return sorted(details, key=lambda m: m["kickoff"])


def table_progression(
    season_id: int, competition_id: int, team_id: int
) -> list[dict[str, Any]]:
    """How a team stood after each of its match days, and how far off the top.

    One row per match the team played, in date order. The table behind each row
    is every league match played up to and including that calendar day, so a
    position reflects the day's other results too - and, as in a real table,
    teams may have played different numbers of games.
    """
    details = league_match_details(season_id)
    teams = get_competition_teams(competition_id)
    team_map = {t["wyId"]: t["name"] for t in teams["teams"]}

    def team_name(tid: int) -> str:
        if tid not in team_map:
            team_map[tid] = get_team_details(tid)["name"]
        return team_map[tid]

    our_matches = [
        m for m in details if str(team_id) in m["teamsData"]
    ]

    rows = []
    running: dict[int, dict[str, int]] = {}
    applied = 0

    for game, m in enumerate(our_matches, start=1):
        day = m["kickoff"][:10]

        # everything played up to the end of this match day counts towards the table
        while applied < len(details) and details[applied]["kickoff"][:10] <= day:
            add_match_to_table(running, details[applied])
            applied += 1

        standings = sort_table(running)
        position = next(
            i for i, (tid, _) in enumerate(standings, start=1) if tid == team_id
        )
        us = running[team_id]
        leader_id, leader = standings[0]
        is_leader = leader_id == team_id

        # when we are top, the gap that matters is the one back to second
        rival_id, rival = standings[1] if is_leader and len(standings) > 1 else (leader_id, leader)

        opponent_id = next(
            t["teamId"] for t in m["teamsData"].values() if t["teamId"] != team_id
        )
        us_data = m["teamsData"][str(team_id)]
        them_data = m["teamsData"][str(opponent_id)]

        rows.append(
            {
                "game": game,
                "date": day,
                "opponent": team_name(opponent_id),
                "venue": "H" if us_data["side"] == "home" else "A",
                "score": f"{us_data['score']}-{them_data['score']}",
                "position": position,
                "played": us["played"],
                "points": us["points"],
                "goals_for": us["goals_for"],
                "goals_against": us["goals_against"],
                "goal_difference": us["goal_difference"],
                "is_leader": is_leader,
                "leader": team_name(rival_id),
                "leader_played": rival["played"],
                "leader_points": rival["points"],
                "leader_goal_difference": rival["goal_difference"],
                # positive means we are behind, negative means we lead
                "points_behind": rival["points"] - us["points"],
                "goal_difference_behind": rival["goal_difference"] - us["goal_difference"],
            }
        )

    return rows
