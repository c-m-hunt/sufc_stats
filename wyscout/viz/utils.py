"""Headers, footers and small text helpers shared by the pitch charts."""

from typing import Any
from urllib.request import urlopen

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from mplsoccer import add_image
from PIL import Image

from wyscout.viz.consts import APP_FONT, SPONSOR_TEXT

TEXT_COLOUR = "#000009"


def load_image(source: str | Image.Image) -> Image.Image:
    """A PIL image from a URL, a local path or an image already loaded."""
    if isinstance(source, Image.Image):
        return source
    if source.startswith("http"):
        return Image.open(urlopen(source))
    return Image.open(source)


def add_footer(fig: Figure, ax: plt.Axes, font_size: float = 10, scale_img: float = 1.5) -> None:
    if not SPONSOR_TEXT:
        return

    ax.text(
        1,
        0.5,
        SPONSOR_TEXT,
        color=TEXT_COLOUR,
        va="bottom",
        ha="right",
        fontproperties=APP_FONT.prop,
        fontsize=font_size,
    )


def add_header(
    fig: Figure,
    ax: plt.Axes,
    title: str,
    subtitle: str | list[str] | None = None,
    imgs: list[Any] | None = None,
    font_size: float = 20,
    subtitle_font_size: float = 10,
    subtitle_start_pos: float = 0.4,
    scale_img: float = 1.3,
    img_rel_x_pos: float = 0.15,
    img_rel_y_pos: float = 0,
    title_pos=(0, 0.9),
    title_ha: str = "left",
    title_va: str = "center",
    subtitle_gap: float = 0.25,
    img_gap: float = 0.11,
) -> None:
    """Title, optional subtitle lines and images (badges, player photos) top right."""
    if title:
        ax.text(
            title_pos[0],
            title_pos[1],
            title,
            color=TEXT_COLOUR,
            va=title_va,
            ha=title_ha,
            fontproperties=APP_FONT.prop,
            fontsize=font_size,
            weight="bold",
        )

    if subtitle:
        lines = [subtitle] if isinstance(subtitle, str) else subtitle
        for i, line in enumerate(lines):
            ax.text(
                0,
                subtitle_start_pos - i * subtitle_gap,
                line,
                color=TEXT_COLOUR,
                va=title_va,
                ha=title_ha,
                fontproperties=APP_FONT.prop,
                fontsize=subtitle_font_size,
            )

    for i, img in enumerate(imgs or []):
        add_image(
            load_image(img),
            fig,
            interpolation="hanning",
            left=ax.get_position().x1 - img_rel_x_pos - i * img_gap,
            bottom=ax.get_position().y0 - img_rel_y_pos,
            height=ax.get_position().height * scale_img,
        )


def add_stat_lines(
    ax: plt.Axes,
    stats: dict[str, Any],
    x: float = 5,
    y: float = 70,
    step: float = 2.5,
    fontsize: float = 12,
) -> None:
    """Write "label: value" lines down the pitch, floats to two decimals."""
    for i, (label, value) in enumerate(stats.items()):
        if isinstance(value, float):
            value = f"{value:.2f}"
        ax.text(
            x,
            y - i * step,
            f"{label}: {value}",
            ha="left",
            va="center",
            fontsize=fontsize,
            fontproperties=APP_FONT.prop,
        )


def panel_title(ax: plt.Axes, text: str, fontsize: float, y: float = 103) -> None:
    """A centred caption above one pitch."""
    if text:
        ax.text(50, y, text, ha="center", va="center", fontsize=fontsize, fontproperties=APP_FONT.prop)
