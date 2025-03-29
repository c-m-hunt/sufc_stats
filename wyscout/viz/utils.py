from datetime import datetime
from typing import List
from urllib.request import Request, urlopen

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from mplsoccer import add_image
from PIL import Image

from wyscout.team import get_team_details
from wyscout.viz.consts import APP_FONT, SPONSOR_LOGO, SPONSOR_TEXT


def get_sponsor_logo():
    req = Request(
        SPONSOR_LOGO,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"},
    )
    im = Image.open(urlopen(req))
    width, height = im.size
    left = 0
    top = height / 5
    right = width
    bottom = height - top
    imCropped = im.crop((left, top, right, bottom))
    return imCropped

def add_footer(fig, ax, font_size=10, scale_img=1.5):
    ax.text(
        1,
        0.5,
        SPONSOR_TEXT,
        color="#000009",
        va="bottom",
        ha="right",
        fontproperties=APP_FONT.prop,
        fontsize=font_size,
    )

    add_image(
        get_sponsor_logo(),
        fig,
        interpolation="hanning",
        # set the left, bottom and height to align with the title
        left=ax.get_position().x0,
        bottom=ax.get_position().y0,
        height=ax.get_position().height * scale_img,
    )


def add_header(
    fig: Figure,
    ax: plt.Axes,
    title: str,
    subtitle: List[str] = None,
    imgs: List[Image.Image] = None,
    font_size=20,
    subtitle_font_size=10,
    subtitle_start_pos=0.4,
    scale_img=1.3,
    img_rel_x_pos=0.15,
    img_rel_y_pos=0,
    title_pos=(0, 0.9),
    title_ha="left",
    title_va="center",
):
    if title:
        ax.text(
            title_pos[0],
            title_pos[1],
            title,
            color="#000009",
            va=title_va,
            ha=title_ha,
            fontproperties=APP_FONT.prop,
            fontsize=font_size,
            weight="bold",
        )

    if subtitle:
        height = 0.4
        for s in subtitle:
            ax.text(
                0,
                subtitle_start_pos,
                s,
                color="#000009",
                va=title_va,
                ha=title_ha,
                fontproperties=APP_FONT.prop,
                fontsize=subtitle_font_size,
            )
            height -= 0.25

    if imgs:
        rel_start_pos = img_rel_x_pos
        move_img = 0.1
        for img in imgs:
            add_image(
                img,
                fig,
                interpolation="hanning",
                # set the left, bottom and height to align with the title
                left=ax.get_position().x1 - rel_start_pos,
                bottom=ax.get_position().y0 - img_rel_y_pos,
                height=ax.get_position().height * scale_img,
            )
            rel_start_pos += move_img


def format_match_details(
    match_detail, team_id, fmt_str="{opposition} ({venue}) {match_date_formatted}"
) -> str:
    format_in = "%B %d, %Y at %H:%M:%S %p"
    match_date = datetime.strptime(match_detail["date"].split(" GMT")[0], format_in)
    format_out = "%d %b, %Y"
    match_date_formatted = match_date.strftime(format_out)

    venue = ""
    opposition = ""

    f = 0
    a = 0
    result = "D"
    if match_detail["winner"] == team_id:
        result = "W"
    elif match_detail["winner"] != 0:
        result = "L"

    for t in match_detail["teamsData"].values():
        if t["teamId"] == team_id:
            venue = t["side"][0]
            f = t["score"]
        else:
            opposition_detail = get_team_details(t["teamId"])
            opposition = opposition_detail["name"]
            a = t["score"]

    score = f"{f}-{a}"

    return fmt_str.format(
        opposition=opposition,
        venue=venue,
        match_date_formatted=match_date_formatted,
        result=result,
        score=score,
    )
