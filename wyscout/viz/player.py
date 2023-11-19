from urllib.request import urlopen

import matplotlib.pyplot as plt
from mplsoccer import VerticalPitch
from PIL import Image

from wyscout.match import get_match_details_and_events, get_team_matches
from wyscout.team import get_team_squad
from wyscout.viz.heat_map import add_heat_map
from wyscout.viz.shots import plot_shots
from wyscout.viz.utils import add_footer, add_header, format_match_details


def plot_player_season_heat_maps(
    player_id: int, team_id: int, season: int, cols=5, fig_height=30
):
    squad = get_team_squad(team_id, season)
    squad = {p["wyId"]: p for p in squad["squad"]}

    matches = get_team_matches(team_id, season)
    matches["matches"] = [m for m in matches["matches"] if m["status"] == "Played"]
    match_count = len(matches["matches"])
    rows = match_count // cols if match_count % cols == 0 else match_count // cols + 1

    pitch = VerticalPitch(
        pitch_type="wyscout", line_zorder=2, linewidth=1, line_color="black", pad_top=20
    )

    GRID_HEIGHT = 0.8
    CBAR_WIDTH = 0.03
    fig, axs = pitch.grid(
        nrows=rows,
        ncols=cols,
        figheight=fig_height,
        # leaves some space on the right hand side for the colorbar
        grid_width=0.88,
        left=0.025,
        endnote_height=0.03,
        endnote_space=0,
        # Turn off the endnote/title axis. I usually do this after
        # I am happy with the chart layout and text placement
        axis=False,
        title_space=0.02,
        title_height=0.04,
        grid_height=GRID_HEIGHT,
    )

    match_font_size = fig_height / 2.5
    title_font_size = fig_height * 1.3
    footer_font_size = fig_height / 2

    for i, m in enumerate(matches["matches"]):
        col = i % cols
        row = i // cols

        ax = axs["pitch"][row, col]

        match, match_details, squad, team_details = get_match_details_and_events(
            team_id, m["matchId"], False
        )

        touches = []
        shots = []
        for e in match["events"]:
            if e["player"]["id"] == player_id:
                touches.append([e["location"]["x"], e["location"]["y"]])
                if e["type"]["primary"] == "shot":
                    shots.append(e)

        fmt_str = "{opposition} ({venue})\n{match_date_formatted}\n{result} {score}"
        title = format_match_details(match_details, team_id, fmt_str)
        ax.text(50, 110, title, ha="center", va="center", fontsize=match_font_size)
        add_heat_map(touches, pitch, ax)
        plot_shots(shots, "blue", pitch, ax)

    player_img = Image.open(urlopen(squad[player_id]["imageDataURL"]))

    add_header(
        fig,
        axs["title"],
        f"{squad[player_id]['shortName']}\nHeat Maps for 2022/23",
        scale_img=1.3,
        font_size=title_font_size,
        title_va="center",
        title_pos=(0, 0.5),
        imgs=[player_img],
        img_rel_x_pos=0.1,
    )

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
    subtitle="Action Maps for 2022/23",
    last_x_games=None,
    reversed=False,
):
    matches = get_team_matches(team_id, season)
    matches["matches"] = [m for m in matches["matches"] if m["status"] == "Played"]
    if reversed:
        matches["matches"].reverse()
    if last_x_games:
        matches["matches"] = matches["matches"][:last_x_games]
        subtitle = "Action Maps for last {} games".format(last_x_games)
    match_count = len(matches["matches"])
    rows = match_count // cols if match_count % cols == 0 else match_count // cols + 1

    pitch = VerticalPitch(
        pitch_type="wyscout", line_zorder=2, linewidth=1, line_color="black", pad_top=35
    )

    GRID_HEIGHT = 0.75
    CBAR_WIDTH = 0.03

    # match_font_size = fig_height / 2.5 * (cols / 5)
    # title_font_size = fig_height * 1.3
    # subtitle_font_size = fig_height * 1
    # footer_font_size = fig_height / 2

    # Three games
    # title_height = 0.15
    # footer_height = 0.06
    # match_font_size = fig_height * 2
    # title_font_size = fig_height * 4
    # subtitle_start_pos = 0.4
    # header_img_scale = 1.3 * (cols / 5)
    # header_img_pos_x = 0.07
    # header_img_pos_y = -0.02
    # subtitle_font_size = fig_height * 3
    # footer_font_size = fig_height * 1.5
    # footer_img_scale = fig_height / 6

    title_height = 0.03
    footer_height = 0.03
    match_font_size = fig_height * 0.3
    title_font_size = fig_height * 1.3
    subtitle_font_size = fig_height * 1
    subtitle_start_pos = 0.1
    header_img_scale = 1.2 * (cols / 5)
    header_img_pos_x = 0.1
    header_img_pos_y = 0.01

    footer_font_size = fig_height * 0.6
    footer_img_scale = fig_height / 50

    fig, axs = pitch.grid(
        nrows=rows,
        ncols=cols,
        figheight=fig_height,
        left=0.025,
        endnote_height=footer_height,
        endnote_space=0,
        axis=False,
        title_space=0.02,
        title_height=title_height,
        grid_height=GRID_HEIGHT,
    )

    for i, m in enumerate(matches["matches"]):
        col = i % cols
        row = i // cols
        if rows == 1:
            ax = axs["pitch"][col]
        else:
            ax = axs["pitch"][row, col]

        try:
            match, match_details, squad, team_details = get_match_details_and_events(
                team_id, m["matchId"], True
            )
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

        fmt_str = "{opposition} ({venue})\n{match_date_formatted}\n{result} {score}"
        title = format_match_details(match_details, team_id, fmt_str)
        ax.text(50, 110, title, ha="center", va="center", fontsize=match_font_size)
        add_heat_map(touches, pitch, ax, levels=50, cmap=cmap)
        plot_shots(shots, shot_colors, pitch, ax)
        plot_shots(oppo_shots, oppo_shot_colors, pitch, ax, True)

    if rows > 1:
        for i in range(cols - len(matches["matches"]) % cols):
            ax = axs["pitch"][rows - 1, cols - i - 1]
            ax.clear()

    team = team_details[team_id]
    team_logo = Image.open(urlopen(team["imageDataURL"]))

    add_header(
        fig,
        axs["title"],
        f"{team['name']}",
        subtitle=[subtitle],
        subtitle_font_size=subtitle_font_size,
        subtitle_start_pos=subtitle_start_pos,
        scale_img=header_img_scale,
        font_size=title_font_size,
        title_va="center",
        title_pos=(0, 0.7),
        imgs=[team_logo],
        img_rel_x_pos=header_img_pos_x,
        img_rel_y_pos=header_img_pos_y,
    )

    add_footer(
        fig, axs["endnote"], scale_img=footer_img_scale, font_size=footer_font_size
    )

    plt.show()
