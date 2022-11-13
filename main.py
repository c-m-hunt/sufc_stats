from wyscout.generate_data_files import generate_key_passes_file
from wyscout.events import get_key_pass_events
from wyscout.match import get_match_events, get_team_matches
from wyscout.api import set_auth
import os
import json
from dotenv import load_dotenv

load_dotenv()
# https://apidocs.wyscout.com/
# XEN - England
# 351 - National League
# 1687 - Southend United
# 188172 - 2022
# 368825 - SUFC v Torquay United

SOUTHEND = 1687
SEASON_2022 = 188172
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")


def main():
    generate_key_passes_file()


if __name__ == "__main__":
    main()
