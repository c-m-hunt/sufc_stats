from typing import Dict, List, Union
from urllib.request import urlopen
from PIL import Image
from matplotlib import pyplot as plt
from matplotlib.hatch import VerticalHatch
from wyscout.events import get_average_positions
from wyscout.match import get_team_matches, get_match_details_and_events
from wyscout.viz.arrow import ArrowOptions, is_goal_pass, pass_event_to_arrow
from wyscout.viz.heat_map import add_heat_map
from wyscout.viz.key_passes import plot_arrows
from wyscout.viz.shots import plot_shots
from wyscout.viz.utils import add_footer, add_header, format_match_details
from mplsoccer import VerticalPitch


def plot_attempts_heat_map(
    matches: List[Dict],
    team_id: int,
    header_text: str,
    subtitle_text: str,
    cmap="Blues",
    fig_height=30,
    shot_colors=("blue", "cornflowerblue")
):
    pitch = VerticalPitch(pitch_type="wyscout", line_zorder=2, line_color='black',
                          linewidth=1, pad_top=20, half=True)

    GRID_HEIGHT = 0.8
    CBAR_WIDTH = 0.03

    cols = 1
    match_font_size = 15
    title_font_size = fig_height * 3
    subtitle_font_size = fig_height * 2
    footer_font_size = fig_height * 1.3
    scale_badge_img = 13
    badge_pos = (0.13, 0.1)
    title_height = 0.01
    title_space = -0.05
    subtitle_start_pos = -4
    title_start_height = 0

    fig, axs = pitch.grid(nrows=1, ncols=cols, figheight=fig_height,
                          # leaves some space on the right hand side for the colorbar
                          grid_width=0.88, left=0.025,
                          endnote_height=0.05, endnote_space=0.02,
                          # Turn off the endnote/title axis. I usually do this after
                          # I am happy with the chart layout and text placement
                          axis=False,
                          title_space=title_space, title_height=title_height, grid_height=GRID_HEIGHT)

    ax = axs["pitch"]
    touches = []
    shots = []
    oppo_shots = []
    passes = []

    for m in matches:
        match_id = m["matchId"]
        match, match_details, squad, team_details = get_match_details_and_events(
            team_id, match_id, True)
        for e in match["events"]:
            if e["team"]["id"] == team_id and "location" in e and e["location"]:

                if e["type"]["primary"] == "shot":
                    # for i in range(int(e["shot"]["xg"] * 100)):
                    touches.append(
                        [e["location"]["x"], e["location"]["y"]])
    add_heat_map(touches, pitch, ax, levels=50, cmap=cmap)
    team = team_details[team_id]
    team_logo = Image.open(urlopen(team["imageDataURL"]))
    add_header(fig, axs["title"], header_text, subtitle=subtitle_text, subtitle_font_size=subtitle_font_size,
               subtitle_start_pos=subtitle_start_pos, scale_img=scale_badge_img, font_size=title_font_size, title_va="center", title_pos=(0, title_start_height), imgs=[team_logo], img_rel_x_pos=badge_pos[0], img_rel_y_pos=badge_pos[1])

    add_footer(fig, axs["endnote"], scale_img=1.3, font_size=footer_font_size)

    plt.show()


def plot_attempts(
    match_groups: List[List[Dict]],
    team_id: int,
    header_text: str,
    subtitle_text: Union[str, List[str]],
    fig_height=30,
    shot_colors=("blue", "cornflowerblue"),
    include_pens=False,
):
    pitch = VerticalPitch(pitch_type="wyscout", line_zorder=2, line_color='black',
                          linewidth=1, pad_top=25, pad_bottom=-10, half=True)

    GRID_HEIGHT = 0.8
    CBAR_WIDTH = 0.03

    cols = len(match_groups)
    title_font_size = fig_height * 3 if cols == 1 else fig_height * 5
    subtitle_font_size = fig_height * 2 if cols == 1 else fig_height * 2
    footer_font_size = fig_height * 1.3
    scale_badge_img = 13
    badge_pos = (0.13, 0.1) if cols == 1 else (0.06, 0.1)
    title_height = 0.01
    title_space = -0.05
    subtitle_start_pos = -4
    title_start_height = -3

    fig, axs = pitch.grid(nrows=1, ncols=cols, figheight=fig_height,
                          # leaves some space on the right hand side for the colorbar
                          grid_width=0.88, left=0.025,
                          endnote_height=0.05, endnote_space=0.02,
                          # Turn off the endnote/title axis. I usually do this after
                          # I am happy with the chart layout and text placement
                          axis=False,
                          title_space=title_space, title_height=title_height, grid_height=GRID_HEIGHT)

    for i, matches in enumerate(match_groups):
        ax = axs["pitch"] if cols == 1 else axs["pitch"][i]
        touches = []
        shots = []
        oppo_shots = []
        passes = []

        for m in matches:

            match_id = m["matchId"]
            match, match_details, squad, team_details = get_match_details_and_events(
                team_id, match_id, True)

            for e in match["events"]:
                if e["team"]["id"] == team_id and "location" in e and e["location"]:
                    touches.append([e["location"]["x"], e["location"]["y"]])

                    if e["type"]["primary"] == "shot":
                        shots.append(e)

                    if e["type"]["primary"] == "penalty" and include_pens:
                        shots.append(e)

                if e["team"]["id"] != team_id and "location" in e and e["location"]:
                    if e["type"]["primary"] == "shot":
                        oppo_shots.append(e)

        attempts_agg = len(shots)
        goals_agg = sum([s["shot"]["isGoal"] for s in shots])
        xg_agg = sum([s["shot"]["xg"] for s in shots])
        xg_per_shot = xg_agg / attempts_agg

        ax.text(50, 65, "Matches",
                ha='center', va='center', fontsize=subtitle_font_size)

        ax.text(50, 62.5, f"{len(matches)}",
                ha='center', va='center', fontsize=subtitle_font_size, weight='bold')

        ax.text(15, 60, "Attempts(/game)",
                ha='center', va='center', fontsize=subtitle_font_size)

        ax.text(15, 57.5, f"{attempts_agg} ({round(attempts_agg / len(matches), 1)})",
                ha='center', va='center', fontsize=subtitle_font_size, weight='bold')

        ax.text(40, 60, "Goals(/game)",
                ha='center', va='center', fontsize=subtitle_font_size)

        ax.text(40, 57.5, f"{goals_agg} ({round(goals_agg / len(matches), 1)})",
                ha='center', va='center', fontsize=subtitle_font_size, weight='bold')

        ax.text(65, 60, "xG(/game)",
                ha='center', va='center', fontsize=subtitle_font_size)

        ax.text(65, 57.5, f"{round(xg_agg, 1)} ({round(xg_agg / len(matches), 1)})",
                ha='center', va='center', fontsize=subtitle_font_size, weight='bold')

        ax.text(90, 60, "xG/shot",
                ha='center', va='center', fontsize=subtitle_font_size)

        ax.text(90, 57.5, f"{round(xg_per_shot, 2)}",
                ha='center', va='center', fontsize=subtitle_font_size, weight='bold')

        plot_shots(shots, shot_colors, pitch, ax)
        plot_arrows(passes, pitch, ax)

        ax.text(50, 103, subtitle_text[i],
                ha='center', va='center', fontsize=subtitle_font_size)

    team = team_details[team_id]
    team_logo = Image.open(urlopen(team["imageDataURL"]))
    add_header(fig, axs["title"], header_text,
               subtitle_start_pos=subtitle_start_pos, scale_img=scale_badge_img, font_size=title_font_size, title_va="center", title_pos=(0, title_start_height), imgs=[team_logo], img_rel_x_pos=badge_pos[0], img_rel_y_pos=badge_pos[1])

    add_footer(fig, axs["endnote"], scale_img=1.3, font_size=footer_font_size)

    plt.show()


def plot_match_heat_map(
    team_id: int,
    match_id: int,
    fig_height=30,
    cmap="Blues",
    shot_colors=("blue", "cornflowerblue"),
    oppo_shot_colors=("whitesmoke", "darkgrey"),
    subtitle=[],
    show_passes_received=[],
    split_halves=True
):
    cols = 2 if split_halves else 1
    pitch = VerticalPitch(pitch_type="wyscout", line_zorder=2,
                          linewidth=1, line_color='black', pad_top=20)

    GRID_HEIGHT = 0.8
    CBAR_WIDTH = 0.03

    match, match_details, squad, team_details = get_match_details_and_events(
        team_id, match_id, True)

    match_font_size = 15
    title_font_size = fig_height * 2.8 if split_halves else fig_height * 2
    subtitle_font_size = fig_height * 2 if split_halves else fig_height * 1.6
    footer_font_size = fig_height * 1.3
    scale_badge_img = 5 if split_halves else 7
    badge_pos = (0.11, 0.03) if split_halves else (0.17, 0.07)
    title_height = 0.025 if split_halves else 0.015
    title_space = 0.02 if split_halves else 0
    subtitle_start_pos = -0.5 if split_halves else -4
    title_start_height = 1.3 if split_halves else 0

    fmt_str = '{opposition} ({venue}), {match_date_formatted}, {result} {score}' if split_halves else '{opposition} ({venue})\n{match_date_formatted}, {result} {score}'
    header_text = format_match_details(match_details, team_id, fmt_str)

    fig, axs = pitch.grid(nrows=1, ncols=cols, figheight=fig_height,
                          # leaves some space on the right hand side for the colorbar
                          grid_width=0.88, left=0.025,
                          endnote_height=0.05, endnote_space=0,
                          # Turn off the endnote/title axis. I usually do this after
                          # I am happy with the chart layout and text placement
                          axis=False,
                          title_space=title_space, title_height=title_height, grid_height=GRID_HEIGHT)

    for i in range(cols):
        ax = axs["pitch"][i] if split_halves else axs["pitch"]
        touches = []
        shots = []
        oppo_shots = []
        passes = []
        for e in match["events"]:
            if split_halves and e["matchPeriod"] != f"{i+1}H":
                continue
            if e["team"]["id"] == team_id and "location" in e and e["location"]:
                touches.append([e["location"]["x"], e["location"]["y"]])
                if e["type"]["primary"] == "shot":
                    shots.append(e)

            if e["team"]["id"] != team_id and "location" in e and e["location"]:
                if e["type"]["primary"] == "shot":
                    oppo_shots.append(e)

            if show_passes_received and e["type"]["primary"] == "pass" and e["pass"]["recipient"]["id"] in show_passes_received:
                passes.append(pass_event_to_arrow(e, [], ArrowOptions(
                    width=2,
                    highlight=is_goal_pass
                )))

        if split_halves:
            title = "1st Half" if i == 0 else "2nd Half"
            ax.text(50, 104, title,
                    ha='center', va='center', fontsize=match_font_size)
        add_heat_map(touches, pitch, ax, levels=50, cmap=cmap)
        plot_shots(shots, shot_colors, pitch, ax)
        plot_shots(oppo_shots, oppo_shot_colors, pitch, ax, True)
        plot_arrows(passes, pitch, ax)

    team = team_details[team_id]
    team_logo = Image.open(urlopen(team["imageDataURL"]))
    add_header(fig, axs["title"], header_text, subtitle=subtitle, subtitle_font_size=subtitle_font_size,
               subtitle_start_pos=subtitle_start_pos, scale_img=scale_badge_img, font_size=title_font_size, title_va="center", title_pos=(0, title_start_height), imgs=[team_logo], img_rel_x_pos=badge_pos[0], img_rel_y_pos=badge_pos[1])

    add_footer(fig, axs["endnote"], scale_img=1.3, font_size=footer_font_size)

    plt.show()


def plot_average_positions(
    team_id: int,
    match_id: int,
    fig_height=10,
    colors=["blue", "cornflowerblue"],
    text_colors=["white", "black"],
):

    pitch = VerticalPitch(pitch_type="wyscout", line_zorder=2, pitch_color="grass",
                          linewidth=1, line_color='white', pad_top=20)

    GRID_HEIGHT = 0.8
    CBAR_WIDTH = 0.03

    title_font_size = fig_height * 3.5
    match_font_size = fig_height * 2
    footer_font_size = fig_height * 1.3
    img_size = fig_height * 1.5

    fig, axs = pitch.grid(nrows=1, ncols=2, figheight=fig_height,
                          # leaves some space on the right hand side for the colorbar
                          grid_width=0.88, left=0.025,
                          endnote_height=0.08, endnote_space=0,
                          # Turn off the endnote/title axis. I usually do this after
                          # I am happy with the chart layout and text placement
                          axis=False,
                          title_space=0.04, title_height=0.01, grid_height=GRID_HEIGHT)

    match, match_details, squad, team_details = get_match_details_and_events(
        team_id, match_id, True)

    fmt_str = '{opposition} ({venue}), {match_date_formatted}, {result} {score}'
    header_text = format_match_details(match_details, team_id, fmt_str)

    for i, period in enumerate(["1H", "2H"]):
        ax = axs["pitch"][i]
        _, positions = get_average_positions(team_id, match_id, period)

        for pos in positions.values():
            pitch.scatter(
                pos["ave_location"]["x"],
                pos["ave_location"]["y"],
                s=400,
                label="test",
                color=colors[0] if pos["start"] else colors[1],
                edgecolors=["black"],
                linewidth=0.5,
                marker='o',
                zorder=3,
                ax=ax
            )

            h_offset = fig_height / 13
            v_offset = fig_height * -0.02
            pitch.annotate(
                pos["shirt"],
                xy=(pos["ave_location"]["x"] - h_offset,
                    pos["ave_location"]["y"] - v_offset),
                xytext=(pos["ave_location"]["x"] - h_offset,
                        pos["ave_location"]["y"] - v_offset),
                fontsize=fig_height,
                color=text_colors[0] if pos["start"] else text_colors[1],
                ha="center",
                weight='bold',
                zorder=3,
                ax=ax
            )

        title = "1st Half" if i == 0 else "2nd Half"
        ax.text(50, 104, title,
                ha='center', va='center', fontsize=match_font_size)

    team = team_details[team_id]
    team_logo = Image.open(urlopen(team["imageDataURL"]))
    add_header(fig, axs["title"], header_text,
               subtitle_start_pos=-0.5, scale_img=img_size, font_size=title_font_size, title_va="center", title_pos=(0, 1.3), imgs=[team_logo], img_rel_x_pos=0.11, img_rel_y_pos=0.03)

    add_footer(fig, axs["endnote"], scale_img=fig_height /
               10, font_size=footer_font_size)


def plot_last_third_passes(
    team_id: int,
    match_id: int,
    fig_height=20,
    pass_colors=("blue", "cornflowerblue"),
    subtitle=["Passes in final third"],
    cmap="Blues",
):

    pitch = VerticalPitch(pitch_type="wyscout", line_zorder=2, half=True,
                          linewidth=1, line_color='black', pad_top=5)

    GRID_HEIGHT = 0.8
    CBAR_WIDTH = 0.03
    fig, axs = pitch.grid(nrows=1, ncols=1, figheight=fig_height,
                          # leaves some space on the right hand side for the colorbar
                          grid_width=0.88, left=0.025,
                          endnote_height=0.07, endnote_space=0,
                          # Turn off the endnote/title axis. I usually do this after
                          # I am happy with the chart layout and text placement
                          axis=False,
                          title_space=0.02, title_height=0.025, grid_height=GRID_HEIGHT)

    match_font_size = fig_height * 2
    title_font_size = fig_height * 3
    subtitle_font_size = fig_height * 2.5
    footer_font_size = fig_height * 1.3

    match, match_details, squad, team_details = get_match_details_and_events(
        team_id, match_id, True)

    fmt_str = '{opposition} ({venue}), {match_date_formatted}, {result} {score}'
    header_text = format_match_details(match_details, team_id, fmt_str)

    ax = axs["pitch"]
    passes = []
    touches = []
    for e in match["events"]:
        if e["team"]["id"] == team_id and "location" in e and e["location"]:
            touches.append([e["location"]["x"], e["location"]["y"]])

        if e["type"]["primary"] == "pass":
            if e["location"]["x"] > 66:
                color = pass_colors[0] if e["pass"]["accurate"] else pass_colors[1]
                passes.append(pass_event_to_arrow(e, [], ArrowOptions(
                    color=color,
                    width=2,
                    highlight=is_goal_pass
                )))
    add_heat_map(touches, pitch, ax, levels=50, cmap=cmap)
    plot_arrows(passes, pitch, ax)

    team = team_details[team_id]
    team_logo = Image.open(urlopen(team["imageDataURL"]))
    add_header(fig, axs["title"], header_text, subtitle=subtitle, subtitle_font_size=subtitle_font_size,
               subtitle_start_pos=-0.7, scale_img=5, font_size=title_font_size, title_va="center", title_pos=(0, 1.3), imgs=[team_logo], img_rel_x_pos=0.11, img_rel_y_pos=0.03)

    add_footer(fig, axs["endnote"], scale_img=1, font_size=footer_font_size)

    plt.show()
