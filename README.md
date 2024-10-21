# Route Planning for the Tube

Used Dijkstra's Algorithm to find shortest weighted path where paths must take account of line transfer penalties and geographical distances.

See data at https://commons.wikimedia.org/wiki/London_Underground_geographic_maps

Python 3.12

Note: Install ansicolors module for different tube line colors.

## CLI Example
Script takes two command line arguments [1] "Station A" and [2] "Station B"

**Input**


`python -m tube_route_planner.py "Paddington" "Charing Cross"`

Then it will output what `line` to take, toward the `next_stop` to the `final_stop` on the line with how many `stops`, and followed by the `transfer` if it exits on the next line.

**Output**

`Bakerloo Line` towards `Edgware Road (B)` to `Charing Cross` (`7` stops)
