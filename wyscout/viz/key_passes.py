from typing import List, Dict, Any
import matplotlib.pyplot as plt
from mplsoccer import VerticalPitch, FontManager


def plot_key_passes(
    matches: List[Dict[str, Any]],
    last_x_games: int = 5,
    highlight_players: List[str] = []
) -> None:
    pitch = VerticalPitch(pitch_type="wyscout", half=True, goal_type='box',
                          pad_bottom=-20, pitch_color='grass', line_color='white', stripe=True)

    fig, axs = pitch.grid(figheight=8, endnote_height=0,  # no endnote
                          title_height=0.1, title_space=0.02,
                          # Turn off the endnote/title axis. I usually do this after
                          # I am happy with the chart layout and text placement
                          axis=False,
                          grid_height=0.83)

    plt.style.use('ggplot')

    robotto_regular = FontManager()

    axs['title'].text(0.5, 0.5, f'Key Passess - Last {last_x_games} games', va='center',
                      ha='center', color='black', fontproperties=robotto_regular.prop, fontsize=25)

    for j, match in enumerate(matches[:last_x_games]):
        for i, event in enumerate(match["events"]):
            color = "red" if event["player"]["name"] in highlight_players else "blue"
            width = 2
            if ("possession" in event and
                "attack" in event["possession"] and
                event["possession"]["attack"] and
                    event["possession"]["attack"]["withGoal"]):
                width = 4
            pitch.arrows(event["location"]["x"], event["location"]["y"], event["pass"]["endLocation"]["x"], event["pass"]["endLocation"]["y"],
                         color=color, width=width, ax=axs['pitch']
                         )

    plt.show()
