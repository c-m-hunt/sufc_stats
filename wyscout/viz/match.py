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


def plot_match_heat_map(
    team_id: int,
    match_id: int,
    season: int,
    fig_height=30,
    cmap="Blues",
    shot_colors=("blue", "cornflowerblue"),
    oppo_shot_colors=("whitesmoke", "darkgrey"),
    subtitle=[],
    show_passes_received=[]
):
    cols = 2
    matches = get_team_matches(team_id, season)
    matches["matches"] = [
        m for m in matches["matches"] if m["status"] == "Played"]
    match_count = len(matches["matches"])
    pitch = VerticalPitch(pitch_type="wyscout", line_zorder=2,
                          linewidth=1, line_color='black', pad_top=20)

    GRID_HEIGHT = 0.8
    CBAR_WIDTH = 0.03
    fig, axs = pitch.grid(nrows=1, ncols=cols, figheight=fig_height,
                          # leaves some space on the right hand side for the colorbar
                          grid_width=0.88, left=0.025,
                          endnote_height=0.05, endnote_space=0,
                          # Turn off the endnote/title axis. I usually do this after
                          # I am happy with the chart layout and text placement
                          axis=False,
                          title_space=0.02, title_height=0.025, grid_height=GRID_HEIGHT)

    match_font_size = 15
    title_font_size = fig_height * 2.8
    subtitle_font_size = fig_height * 2
    footer_font_size = fig_height * 1.3

    match, match_details, squad, team_details = get_match_details_and_events(
        team_id, match_id, True)

    fmt_str = '{opposition} ({venue}), {match_date_formatted}, {result} {score}'
    header_text = format_match_details(match_details, team_id, fmt_str)

    for i in range(2):
        ax = axs["pitch"][i]
        touches = []
        shots = []
        oppo_shots = []
        passes = []
        for e in match["events"]:
            if e["matchPeriod"] != f"{i+1}H":
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
               subtitle_start_pos=-0.5, scale_img=5, font_size=title_font_size, title_va="center", title_pos=(0, 1.3), imgs=[team_logo], img_rel_x_pos=0.11, img_rel_y_pos=0.03)

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
