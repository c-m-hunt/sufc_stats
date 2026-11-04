# sufc-stats

Southend United statistics and visualisations built on the Wyscout API: shot maps, heat maps,
xG charts, player scouting maps and season-on-season comparisons, in Jupyter notebooks backed by
a small Python package.

## Setup

```
uv sync                       # installs the wyscout package (editable) and its dependencies
docker compose up -d          # a local Mongo that caches every API response
```

Put your Wyscout API credentials in `notebooks/.env`:

```
CLIENT_ID=...
CLIENT_SECRET=...
```

The cache matters: a season of match events is a few hundred requests, and everything in the
notebooks is cached for hours or days after the first run. Error responses (a match whose data
isn't published yet) are never cached.

## The package

`wyscout` is split into layers, each of which only depends on the one below:

| layer | what it does |
|---|---|
| `wyscout.api`, `wyscout.match`, `wyscout.team`, `wyscout.competitions` | raw API calls, cached in Mongo |
| `wyscout.data` | turns API responses into events, locations and DataFrames - `filters` (predicates over events), `match`, `season`, `player`, `goalkeeping`, `tracking` |
| `wyscout.league_table` | rebuilds league tables at any date and tracks a team's position match by match |
| `wyscout.viz` | draws things it is handed, never fetches - `event_map` is the general multi-pitch chart, plus `shots`, `heat_map`, `arrows`, `match`, `player`, `team`, `season` |
| `wyscout.reports` | one function per chart, taking Wyscout ids - `match`, `team`, `season`, `player`. This is what the notebooks call |
| `wyscout.ids` | the ids of teams, competitions, seasons and a few players |

So a report is a few lines of data + viz, and both halves can be used on their own - build an
`EventPanel` from any events you like and hand it to `plot_event_maps`, or take the DataFrames
from `wyscout.data.season` into your own charts.

## Notebooks

All in `notebooks/`, all on Southend United data, every cell annotated.

**Showcase - Match**, **Showcase - Team and Season**, **Showcase - Player** - every report
function with its variations, the arguments that change each one, and the data layer beneath.
Start here.

| notebook | what it covers |
|---|---|
| `season.ipynb` | the current season: results, attempts, xG, a player's influence, comparison with last season and the gap to the top |
| `matchday.ipynb` | one match in detail |
| `SUFC Attack.ipynb` | scouting maps for players, at Southend and at other clubs |
| `SUFC Summary.ipynb` | the squad, appearances and output |
| `Southend vs Boreham Wood.ipynb` | Southend against the league leaders, side by side: title race, tale of the tape, style radar, attempts for and against, xG by situation, average positions, territory, duels by zone, chance creation, pressing, strikers, goal timing, game state and passing style. Change `RIVAL` to compare with another club |
| `Goalkeepers.ipynb` | every National League keeper in 2025/26 - shot stopping by distance, xG and placement, distribution by length - with Collin Andeng-Ndi picked out |
| `misc.ipynb` | finding ids, possession share, video lengths, month of birth |
| `Fantasy Squads.ipynb` | Premier League players matched to Fantasy Premier League, exported for a Ludwig model |

To re-run every notebook with a clean kernel and save the outputs:

```
uv run python scripts/run_notebooks.py            # all of them
uv run python scripts/run_notebooks.py season     # by name prefix
```

`scripts/goals_by_xg.py` prints the season's goals, lowest xG first.
