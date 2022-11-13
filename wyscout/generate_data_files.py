from wyscout.events import get_key_pass_events
from wyscout.match import get_match_events, get_team_matches
from wyscout.api import set_auth
import os
import json
# https://apidocs.wyscout.com/
# XEN - England
# 351 - National League
# 1687 - Southend United
# 188172 - 2022
# 368825 - SUFC v Torquay United

SOUTHEND = 1687
SEASON_2022 = 188172


def generate_key_passes_file():
    matches = get_team_matches(SOUTHEND, SEASON_2022)
    key_pass_events = []
    for m in matches["matches"]:
        events = get_match_events(m["matchId"])
        if "events" in events:
            key_pass_events.append(get_key_pass_events(
                m, events["events"], SOUTHEND))

    # Save to file
    with open(f"{os.getcwd()}/data/key_pass_events.json", "w") as f:
        f.write(json.dumps(key_pass_events))
