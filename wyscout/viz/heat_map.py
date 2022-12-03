from typing import List
from urllib.request import urlopen
from mplsoccer import VerticalPitch, FontManager, Pitch, add_image
from matplotlib.colors import LinearSegmentedColormap
from PIL import Image
from wyscout.viz.consts import SPONSOR_LOGO, SPONSOR_TEXT
from wyscout.viz.utils import Arrow
from wyscout.viz.key_passes import plot_arrows

# From https://mplsoccer.readthedocs.io/en/latest/gallery/pitch_plots/plot_kde.html#sphx-glr-gallery-pitch-plots-plot-kde-py


def plot_player_action_map(events: any, passes: List[Arrow], player: any, title: str):
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
    URL = 'https://raw.githubusercontent.com/google/fonts/main/apache/roboto/Roboto%5Bwdth,wght%5D.ttf'
    robotto_regular = FontManager(URL)
    name = f"{player['firstName']} {player['lastName']}"
    axs['title'].text(0, 0.7, name, fontsize=24, color='#000009',
                      fontproperties=robotto_regular.prop,
                      ha='left', va='center')

    axs['title'].text(0, 0.1, title, color='#000009',
                      va='center', ha='left', fontproperties=robotto_regular.prop, fontsize=18)

    axs['endnote'].text(1, 0.5, SPONSOR_TEXT, color='#000009',
                        va='bottom', ha='right', fontproperties=robotto_regular.prop, fontsize=10)

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
