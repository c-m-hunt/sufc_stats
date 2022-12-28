from typing import List, Optional
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from urllib.request import urlopen
from mplsoccer import VerticalPitch, FontManager, Pitch, add_image
from matplotlib.colors import LinearSegmentedColormap
from PIL import Image
from wyscout.viz.consts import SPONSOR_LOGO, SPONSOR_TEXT, COLOUR_1, COLOUR_2, APP_FONT
from wyscout.viz.arrow import Arrow
from wyscout.viz.key_passes import plot_arrows


# From https://mplsoccer.readthedocs.io/en/latest/gallery/pitch_plots/plot_kde.html#sphx-glr-gallery-pitch-plots-plot-kde-py


def plot_pass_map(
    player1: any,
    player2: any,
    team: any,
    passes: List[Arrow],
    title: str = None,
    subtitle: Optional[str] = None
):
    pitch = VerticalPitch(pitch_type="wyscout", pitch_color='#aabb97', line_color='white',
                          stripe_color='#c2d59d', stripe=True, line_zorder=2)
    fig, axs = pitch.grid(figheight=8, title_height=0.08, endnote_space=0, title_space=0,
                          # Turn off the endnote/title axis. I usually do this after
                          # I am happy with the chart layout and text placement
                          axis=False,
                          grid_height=0.82, endnote_height=0.05)
    plot_arrows(passes, pitch, axs["pitch"])

    if not title:
        title = f"{player1['lastName']} to {player2['lastName']}"

    if title:
        axs['title'].text(0, 0.9, title, color='#000009',
                          va='center', ha='left', fontproperties=APP_FONT.prop, fontsize=20)
    if subtitle:
        height = 0.4
        for s in subtitle:
            axs['title'].text(0, height, s, color='#000009',
                              va='center', ha='left', fontproperties=APP_FONT.prop, fontsize=10)
            height -= 0.25

    player1_img = Image.open(urlopen(player1["imageDataURL"]))
    ax_img = add_image(player1_img, fig, interpolation='hanning',
                       # set the left, bottom and height to align with the title
                       left=axs['title'].get_position().x1 - 0.35,
                       bottom=axs['title'].get_position().y0,
                       height=axs['title'].get_position().height * 1.3)

    player2_img = Image.open(urlopen(player2["imageDataURL"]))
    ax_img = add_image(player2_img, fig, interpolation='hanning',
                       # set the left, bottom and height to align with the title
                       left=axs['title'].get_position().x1 - 0.15,
                       bottom=axs['title'].get_position().y0,
                       height=axs['title'].get_position().height * 1.3)

    logo = Image.open(urlopen(SPONSOR_LOGO))
    ax_img = add_image(logo, fig, interpolation='hanning',
                       # set the left, bottom and height to align with the title
                       left=axs['endnote'].get_position().x0,
                       bottom=axs['endnote'].get_position().y0,
                       height=axs['endnote'].get_position().height * 1)

    team_badge = Image.open(urlopen(team["imageDataURL"]))
    ax_img = add_image(team_badge, fig, interpolation='hanning',
                       # set the left, bottom and height to align with the title
                       left=axs['pitch'].get_position().x1 - 0.16,
                       bottom=axs['pitch'].get_position().y0 + 0.008,
                       height=axs['pitch'].get_position().height * 0.1)

    axs['endnote'].text(1, 0.3, SPONSOR_TEXT, color='#000009',
                        va='bottom', ha='right', fontproperties=APP_FONT.prop, fontsize=10)

    custom_lines = [Line2D([0], [0], color=COLOUR_1, lw=1),
                    Line2D([0], [0], color=COLOUR_2, lw=1),
                    Line2D([0], [0], color=COLOUR_1, lw=2)]

    legend = axs["pitch"].legend(
        custom_lines, ['Low pass', 'High pass', 'Led to shot'],
        loc="lower left"
    )

    plt.setp(legend.texts, fontproperties=APP_FONT.prop)
    plt.setp(legend.texts, size=8)

    plt.show()


def plot_player_action_map(
    player: any,
    title: str,
    subtitle: str,
    events: any,
    passes: List[Arrow],
    crosses: List[Arrow],
):
    pitch = VerticalPitch(pitch_type="wyscout",
                          line_color='grey', line_zorder=2)
    fig, axs = pitch.grid(figheight=8, title_height=0.08, endnote_space=0, title_space=0,
                          # Turn off the endnote/title axis. I usually do this after
                          # I am happy with the chart layout and text placement
                          axis=False,
                          grid_height=0.82, endnote_height=0.03)

    # pitch = VerticalPitch(line_color='#000009', line_zorder=2)
    # fig, ax = pitch.draw(figsize=(4.4, 6.4))

    fig.patch.set_facecolor('white')
    add_heat_map(events, pitch, axs["pitch"])

    player_img = Image.open(urlopen(player["imageDataURL"]))
    name = f"{player['firstName']} {player['lastName']}"
    axs['title'].text(0, 0.9, name, fontsize=24, color='#000009',
                      fontproperties=APP_FONT.prop,
                      ha='left', va='center')

    axs['title'].text(0, 0.4, title, color='#000009',
                      va='center', ha='left', fontproperties=APP_FONT.prop, fontsize=14)
    if subtitle:
        axs['title'].text(0, 0, subtitle, color='#000009',
                          va='center', ha='left', fontproperties=APP_FONT.prop, fontsize=10)

    axs['endnote'].text(1, 0.5, SPONSOR_TEXT, color='#000009',
                        va='bottom', ha='right', fontproperties=APP_FONT.prop, fontsize=10)

    ax_img = add_image(player_img, fig, interpolation='hanning',
                       # set the left, bottom and height to align with the title
                       left=axs['title'].get_position().x1 - 0.15,
                       bottom=axs['title'].get_position().y0,
                       height=axs['title'].get_position().height * 1.3)

    logo = Image.open(urlopen(SPONSOR_LOGO))
    ax_img = add_image(logo, fig, interpolation='hanning',
                       # set the left, bottom and height to align with the title
                       left=axs['endnote'].get_position().x0,
                       bottom=axs['endnote'].get_position().y0,
                       height=axs['endnote'].get_position().height * 1.5)

    plot_arrows(passes, pitch, axs["pitch"])
    plot_arrows(crosses, pitch, axs["pitch"])
    plt.show()


def add_heat_map(locations, pitch, ax):
    xs = [e[0] for e in locations]
    ys = [e[1] for e in locations]

    kde = pitch.kdeplot(xs, ys, ax=ax,
                        # shade using 100 levels so it looks smooth
                        shade=True, levels=100,
                        # shade the lowest area so it looks smooth
                        # so even if there are no events it gets some color
                        shade_lowest=True,
                        cmap="Blues")
