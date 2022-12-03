from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Arrow:
    start: Tuple[float, float]
    end: Tuple[float, float]
    color: str
    width: float


@dataclass
class ArrowOptions:
    color: str = "blue"
    width: int = 2
    highlighted_width: int = 4
    highlighted_color: str = 'red'


def pass_event_to_arrow(event: Dict[str, Any], highlight_players: List[int], options: ArrowOptions = ArrowOptions()) -> Arrow:
    color = options.highlighted_color if event["player"]["id"] in highlight_players else options.color
    width = options.width
    if ("possession" in event and
        "attack" in event["possession"] and
        event["possession"]["attack"] and
            event["possession"]["attack"]["withGoal"]):
        # width = options.highlighted_width
        color = options.highlighted_color
    return Arrow(
        start=(event["location"]["x"], event["location"]["y"]),
        end=(event["pass"]["endLocation"]["x"],
             event["pass"]["endLocation"]["y"]),
        color=color,
        width=width
    )
