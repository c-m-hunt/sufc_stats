from typing import List, Any
from mplsoccer import VerticalPitch, FontManager
import matplotlib.pyplot as plt
import math


def plot_shots_compare(
    match_events: any,
    last_x_games: int = None,
    first_x_games: int = None,
    include_pens: bool = False,
    colors: list = ["red", "blue"],
    style: str = "fivethirtyeight",
):
    pitch = VerticalPitch(pitch_type="wyscout", half=True, goal_type='box',
                          pad_bottom=-20, pitch_color='grass', line_color='white', stripe=True)
    fig, axs = pitch.grid(figheight=15, ncols=2,
                          title_height=0.1, title_space=0.02, axis=False,)

    plt.style.use(style)

    robotto_regular = FontManager()

    if last_x_games and not first_x_games:
        first_x_games = len(match_events) - last_x_games

    if first_x_games and not last_x_games:
        last_x_games = len(match_events) - first_x_games

    if not first_x_games and not last_x_games:
        first_x_games = math.floor(len(match_events) / 2)
        last_x_games = len(match_events) - first_x_games

    axs['title'].text(0.5, 0.5, f'Attempts on goal - first {first_x_games} games vs last {last_x_games} games', va='center',
                      ha='center', color='black', fontproperties=robotto_regular.prop, fontsize=50)

    event_types = ["shot"]
    if include_pens:
        event_types.append("penalty")

    def plot_matches(match_events, ax):
        for j, match in enumerate(match_events[:8]):
            events = [e for e in match["events"] if e["type"]
                      ["primary"] in event_types]
            for i, event in enumerate(events):
                size = event["shot"]["xg"] * 2000
                color = colors[0] if event["shot"]["isGoal"] is True else colors[1]
                pitch.scatter(
                    event["location"]["x"],
                    event["location"]["y"],
                    s=size,
                    label=event["player"]["name"],
                    color=color,
                    edgecolors=["black"],
                    marker='o',
                    ax=axs["pitch"][ax]
                )

    plot_matches(match_events[-1 * first_x_games:], 0)
    plot_matches(match_events[:last_x_games], 1)

    plt.show()


def plot_match_chances(
    match: any,
    team_id: int,
    include_pens: bool = False,
    colors: List[str] = None,
    style: str = "fivethirtyeight"
):

    if not colors:
        colors = ["red", "blue"]

    pitch = VerticalPitch(pitch_type="wyscout", half=True, goal_type='box',
                          pad_bottom=-20, pitch_color='grass', line_color='white', stripe=True)

    fig, axs = pitch.grid(figheight=8, endnote_height=0,
                          title_height=0.1, title_space=0.02,
                          axis=False,
                          grid_height=0.83)

    plt.style.use(style)

    robotto_regular = FontManager()

    axs['title'].text(0.5, 0.5, match["label"], va='center',
                      ha='center', color='black', fontproperties=robotto_regular.prop, fontsize=30)

    event_types = ["shot"]
    if include_pens:
        event_types.append("penalty")

    def plot_shots(events, team_id, oppo, color, ax):
        if oppo:
            shots = [e for e in events if e["type"]
                     ["primary"] in event_types and team_id != e["team"]["id"]]
        else:
            shots = [e for e in events if e["type"]
                     ["primary"] in event_types and team_id == e["team"]["id"]]

        for shot in shots:
            size = shot["shot"]["xg"] * 1000
            edge_color = "red" if shot["shot"]["isGoal"] is True else "black"
            pitch.scatter(
                shot["location"]["x"],
                shot["location"]["y"],
                s=size,
                label=shot["player"]["name"],
                color=color,
                edgecolors=[edge_color],
                linewidth=1.5,
                marker='o',
                ax=ax
            )

    plot_shots(match["events"], team_id, False, colors[0], axs["pitch"])
    plot_shots(match["events"], team_id, True, colors[1], axs["pitch"])

    plt.show()
