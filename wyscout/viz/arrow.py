from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass

from wyscout.viz.consts import COLOUR_1


@dataclass
class Arrow:
    start: Tuple[float, float]
    end: Tuple[float, float]
    color: str
    edgecolor: str
    width: float


@dataclass
class ArrowOptions:
    color: str = COLOUR_1
    width: int = 2
    edgecolor: str = None
    highlighted_width: int = 4
    highlighted_color: str = 'red'
    highlight: Callable[[Dict[str, Any]], bool] = lambda event: False


def pass_event_to_arrow(event: Dict[str, Any], highlight_players: List[int], options: ArrowOptions = ArrowOptions()) -> Arrow:
    color = options.highlighted_color if event["player"]["id"] in highlight_players else options.color
    width = options.width
    edgecolor = options.edgecolor or options.color
    if options.highlight(event):
        color = options.highlighted_color
    return Arrow(
        start=(event["location"]["x"], event["location"]["y"]),
        end=(event["pass"]["endLocation"]["x"],
             event["pass"]["endLocation"]["y"]),
        color=color,
        width=width,
        edgecolor=edgecolor
    )


def is_goal_pass(event: Dict[str, Any]) -> bool:
    return ("possession" in event
            and "attack" in event["possession"]
            and event["possession"]["attack"]
            and event["possession"]["attack"]["withGoal"])


def is_first_half(event: Dict[str, Any]) -> bool:
    return event["matchPeriod"] == "1H"
