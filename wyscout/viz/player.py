from PIL import Image
from urllib.request import urlopen
import matplotlib.pyplot as plt
from wyscout.match import get_team_matches
from wyscout.viz.heat_map import add_heat_map
from wyscout.viz.utils import format_match_details, add_footer, add_header
from wyscout.viz.shots import plot_shots
from wyscout.match import get_match_details_and_events
from mplsoccer import VerticalPitch


from wyscout.team import get_team_squad


def plot_player_season_heat_maps(player_id: int, team_id: int, season: int, cols=5, fig_height=30):
    squad = get_team_squad(team_id, season)
    squad = {p["wyId"]: p for p in squad["squad"]}

    matches = get_team_matches(team_id, season)
    matches["matches"] = [
        m for m in matches["matches"] if m["status"] == "Played"]
    match_count = len(matches["matches"])
    rows = match_count // cols if match_count % cols == 0 else match_count // cols + 1

    pitch = VerticalPitch(pitch_type="wyscout", line_zorder=2,
                          linewidth=1, line_color='black', pad_top=20)

    GRID_HEIGHT = 0.8
    CBAR_WIDTH = 0.03
    fig, axs = pitch.grid(nrows=rows, ncols=cols, figheight=fig_height,
                          # leaves some space on the right hand side for the colorbar
                          grid_width=0.88, left=0.025,
                          endnote_height=0.03, endnote_space=0,
                          # Turn off the endnote/title axis. I usually do this after
                          # I am happy with the chart layout and text placement
                          axis=False,
                          title_space=0.02, title_height=0.04, grid_height=GRID_HEIGHT)

    match_font_size = fig_height / 2.5
    title_font_size = fig_height * 1.3
    footer_font_size = fig_height / 2

    for i, m in enumerate(matches["matches"]):
        col = i % cols
        row = i // cols

        ax = axs["pitch"][row, col]

        match, match_details, squad, team_details = get_match_details_and_events(
            team_id, m["matchId"], False)

        touches = []
        shots = []
        for e in match["events"]:
            if e["player"]["id"] == player_id:
                touches.append([e["location"]["x"], e["location"]["y"]])
                if e["type"]["primary"] == "shot":
                    shots.append(e)

        fmt_str = '{opposition} ({venue})\n{match_date_formatted}\n{result} {score}'
        title = format_match_details(match_details, team_id, fmt_str)
        ax.text(50, 110, title,
                ha='center', va='center', fontsize=match_font_size)
        add_heat_map(touches, pitch, ax)
        plot_shots(shots, "blue", pitch, ax)

    player_img = Image.open(urlopen(squad[player_id]["imageDataURL"]))

    add_header(fig, axs["title"], f"{squad[player_id]['shortName']}\nHeat Maps for 2022/23",
               scale_img=1.3, font_size=title_font_size, title_va="center", title_pos=(0, 0.5), imgs=[player_img], img_rel_x_pos=0.1)

    add_footer(fig, axs["endnote"], scale_img=1, font_size=footer_font_size)

    plt.show()


def plot_team_season_heat_maps(
    team_id: int,
    season: int,
    cols=5,
    fig_height=30,
    cmap="Blues",
    shot_colors=("blue", "cornflowerblue"),
    oppo_shot_colors=("whitesmoke", "darkgrey"),
):
    matches = get_team_matches(team_id, season)
    matches["matches"] = [
        m for m in matches["matches"] if m["status"] == "Played"]
    match_count = len(matches["matches"])
    rows = match_count // cols if match_count % cols == 0 else match_count // cols + 1

    pitch = VerticalPitch(pitch_type="wyscout", line_zorder=2,
                          linewidth=1, line_color='black', pad_top=20)

    GRID_HEIGHT = 0.9
    CBAR_WIDTH = 0.03
    fig, axs = pitch.grid(nrows=rows, ncols=cols, figheight=fig_height,
                          # leaves some space on the right hand side for the colorbar
                          grid_width=0.88, left=0.025,
                          endnote_height=0.03, endnote_space=0,
                          # Turn off the endnote/title axis. I usually do this after
                          # I am happy with the chart layout and text placement
                          axis=False,
                          title_space=0.02, title_height=0.04, grid_height=GRID_HEIGHT)

    match_font_size = fig_height / 2.5 * (cols / 5)
    title_font_size = fig_height * 1.3
    subtitle_font_size = fig_height * 1
    footer_font_size = fig_height / 2

    for i, m in enumerate(matches["matches"]):
        col = i % cols
        row = i // cols

        ax = axs["pitch"][row, col]

        try:
            match, match_details, squad, team_details = get_match_details_and_events(
                team_id, m["matchId"], True)
        except:
            continue
        touches = []
        shots = []
        oppo_shots = []
        for e in match["events"]:
            if e["team"]["id"] == team_id and "location" in e and e["location"]:
                touches.append([e["location"]["x"], e["location"]["y"]])
                if e["type"]["primary"] == "shot":
                    shots.append(e)

            if e["team"]["id"] != team_id and "location" in e and e["location"]:
                if e["type"]["primary"] == "shot":
                    oppo_shots.append(e)

        fmt_str = '{opposition} ({venue})\n{match_date_formatted}\n{result} {score}'
        title = format_match_details(match_details, team_id, fmt_str)
        ax.text(50, 110, title,
                ha='center', va='center', fontsize=match_font_size)
        add_heat_map(touches, pitch, ax, levels=50, cmap=cmap)
        plot_shots(shots, shot_colors, pitch, ax)
        plot_shots(oppo_shots, oppo_shot_colors, pitch, ax, True)

    team = team_details[team_id]
    team_logo = Image.open(urlopen(team["imageDataURL"]))
    add_header(fig, axs["title"], f"{team['name']}", subtitle=["Action Maps for 2022/23"], subtitle_font_size=subtitle_font_size,
               subtitle_start_pos=0.2, scale_img=1.3 * (cols / 5), font_size=title_font_size, title_va="center", title_pos=(0, 0.7), imgs=[team_logo], img_rel_x_pos=0.1 * (5/cols))

    add_footer(fig, axs["endnote"], scale_img=1, font_size=footer_font_size)

    plt.show()
