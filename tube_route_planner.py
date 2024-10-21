#!/usr/bin/env python
'''
Route Planning for London Undergound

Use Dijkstra's Algorithm to find shortest weighted path where paths must take account of line
transfer penalties and geographical distances.

See data at https://commons.wikimedia.org/wiki/London_Underground_geographic_maps
'''

from __future__ import annotations  # for self-referential type hints
from typing import Any, Self, Sequence  # more type hints
from collections import defaultdict as ddict  # data structure to store adjacency list
from math import radians, sqrt, cos, inf  # converting spherical (latitude, longitude)
from queue import PriorityQueue  # data structure for Dijkstra's Algorithm
import csv  # module for parsing and extracting CSV files
import os  # extract current python file directory


class ImportCSV():
  'Import data from CSV files and store into data structures.'
  
  def lines(file_path: str) -> dict[int, dict[str, str]]:
    '''
    Import London Underground Lines
  
    CSV format:
    "line","name","colour","stripe"
    1,"Bakerloo Line","ab6612",NULL
    '''
    # Get directory of current python file
    dir_path = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(sys.argv[0])))
    full_path = os.path.join(dir_path, file_path)

    results = {}
    with open(full_path) as csv_file:
      reader = csv.DictReader(csv_file)  # by default DictReader does not read line1 of fieldnames
      line, name, colour, stripe = reader.fieldnames
      for row in reader:
        # results[int(row[line])] = (row[name], row[colour], row[stripe])  # dict[int, tuple(str)]
        results[int(row[line])] = {name: row[name], colour: row[colour], stripe: row[stripe]}
    return results

  def stations(file_path: str) -> dict[int, dict[str, Any]]:
    '''
    Import London Underground Stations
  
    CSV format:
    "id","latitude","longitude","name","display_name","zone","total_lines","rail"
    1,51.5028,-0.2801,"Acton Town","Acton<br />Town",3,2,0
    '''
    # Get directory of current python file
    dir_path = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(sys.argv[0])))
    full_path = os.path.join(dir_path, file_path)

    results = {}
    with open(full_path) as csv_file:
      reader = csv.DictReader(csv_file)  # by default DictReader does not read line1 of fieldnames
      id, lat, lon, name, dname, zone, lines, rail = reader.fieldnames
      for r in reader:  # for row in reader object
        # results[int(row[line])] = (float(r[lat]), float(r[lon]), r[name], float(r[zone]),
        # int(r[lines]), int(r[rail]))  # dict[int, tuple(Any)]
        results[int(r[id])] = {'lat': float(r[lat]), 'lon': float(r[lon]), name: r[name],
                               zone: float(r[zone]), 'lines': int(r[lines]), rail: int(r[rail])}
    return results

  def routes(file_path: str) -> dict[int, dict[int, int]]:
    '''
    Import London Underground Routes as Undirected Edges
  
    CSV format:
    "station1","station2","line"
    11,163,1
    '''
    # Get directory of current python file
    dir_path = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(sys.argv[0])))
    full_path = os.path.join(dir_path, file_path)
  
    results = ddict(dict)
    with open(full_path) as csv_file:
      reader = csv.DictReader(csv_file)  # by default DictReader does not read line1 of fieldnames
      station1, station2, line = reader.fieldnames
      for row in reader:
        results[int(row[station1])][int(row[station2])] = int(row[line])
        results[int(row[station2])][int(row[station1])] = int(row[line])
    return dict(results)


def dist_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
  '''
  Calculate distance between two points given GPS coordinates (latitude, longitude) in decimal
  degrees. Since distance between stations are small, assume equirectangular approximation
  (Pythagoras' Theorem) instead of haversine formula. Assume mean Earth radius = 6371 km.

  See https://www.movable-type.co.uk/scripts/latlong.html
  :param: latitude is horizontal and longitude is vertical (and negative means west/south)
  :return: distance in kilometers
  '''
  x = radians(lon2 - lon1) * cos(0.5 * (radians(lat2 + lat1)))
  y = radians(lat2 - lat1)
  d = 6371 * sqrt(x*x + y*y)
  return d


def graph_dijkstra(g: dict[int, dict], start: int, end: int) -> tuple[dict[str, float], list[int]]:
  '''
  Use priorityqueue (min heap) for Dijkstra's algorithm to traverse graph, g, and find shortest
  weighted path. Assume a transfer penalty and use geographical distance for edge weights.

  :param: g is adjacency list of london underground routes
  :param: start = starting station, end = ending station
  :return: dictionary of shortest edge distances, list vertices for shortest path
  '''
  # Initialize local variables for storing info about shortest weighted path
  dist = {v: inf for v in g}  # store min dist path to vertex from start
  prev = {v: None for v in g}  # store previous vertex with min edge dist
  pq = PriorityQueue()  # priority queue or min heap data structure
  penalty = 1.33  # assume transfer penalty is an extra 0.33 distance stop

  # Start Dijkstra's Algorithm
  dist[start] = 0  # set distance from start to start as 0
  pq.put((0, start))  # enqueque
  while not pq.empty():
    length, node = pq.get()  # dequeue
    for neighbor in routes[node]:  # routes is module scoped variable
      d_km = dist_km(stations[node]['lat'], stations[node]['lon'],
                     stations[neighbor]['lat'], stations[neighbor]['lon'])

      # Check if previous node exists and if line transfer from current node to neighbor
      if (prev_n := prev.get(node, None)) and g[prev_n][node] != g[node][neighbor]:
        new_dist = length + d_km * penalty  # issue transfer penalty
      else:
        new_dist = length + d_km

      # If new distance is new minimum path then update variables and add to pqueue
      if new_dist < dist[neighbor]:
        dist[neighbor] = new_dist
        prev[neighbor] = node
        pq.put((new_dist, neighbor))

  # Reconstruct Path
  path = [end]
  while path[-1] in prev:
    path.append(prev[path[-1]])
  path.pop()  # the last append at the start_vertex adds None so remove it

  # Return dictionary of min distances and shortest path as list
  return dist, list(reversed(path))


def directions(routes: dict[int, dict], path: list[int]) -> dict[tuple[int, int], list[int]]:
  '''
  Formats shortest unweighted path and prints out directions: one train per line towards next stop
  and finishing at final stop before transfer or end. List number of stops and if 1 stop combine
  next stop and final stop. Color train lines

  "Train Line" to "Final Stop if Next Stop is Final Stop"
  "Next Train Line" towards "Next Stop" to "Final Stop" ("Number of Stops")

  :param: routes is adjacency list of london underground routes
  :param: path is shortest unweighted path from Dijkstra's algorithm
  :return: dictionary of transfers and number of stops
  '''
  directions = ddict(list)
  transfer_number = 0  # mark transfer number, useful when there are revisited lines
  line_id = routes[path[0]][path[1]]  # NOTE routes is module scoped variable
  transfer = (transfer_number, line_id)  # use as key for directions
  for i in range(len(path) - 1):
    current_stop, next_stop = path[i], path[i + 1]
    if (next_line := routes[current_stop][next_stop]) == line_id:  # check if next line is transfer
      directions[transfer].append(next_stop)
    else:
      transfer_number += 1
      line_id = next_line
      transfer = (transfer_number, line_id)  # update transfer
      directions[transfer].append(next_stop)
  return dict(directions)


# Require 2 user arguments for start and end vertex for Dijkstra's Algorithm to calculate
# shortest weighted path between two stations in the London Underground.
if __name__ == '__main__':
  import sys  # extract command line arguments
  from colors import color  # ANSI color for text aka foregorund (fg) or background (bg)

  # Store london underground data into dictionaries of dictionaries
  lines = ImportCSV.lines(r'datasets/lines.csv')
  stations = ImportCSV.stations(r'datasets/stations.csv')
  routes = ImportCSV.routes(r'datasets/routes.csv')

  # Get user input and check if 2 arguments given and if names are valid
  try:
    start_vertex, end_vertex = sys.argv[1], sys.argv[2]  # recall sys.argv stores input as str
    station_names = {station['name']: id for id, station in stations.items()}  # ordered set
    # check if station name is valid
    start_id = station_names[start_vertex]
    end_id = station_names[end_vertex]
    # check if start is end_vertex
    if start_vertex == end_vertex:
      print(f'start_vertex is same as end_vertex')
      sys.exit()
  except IndexError:
    print(f'Error {sys.argv[0]} expects 2 command line arguments: start_vertex & end_vertex!')
    sys.exit()
  except KeyError:
    print(f'Error station name(s) do not exist! See valid names below:\n{tuple(station_names)} ')
    sys.exit()

  # Dijkstra's Algorithm to calc shortest weighted path between two stations
  distances, path = graph_dijkstra(routes, start_id, end_id)

  # Create Dictionary where key is every transfer along path
  transfers = directions(routes, path)

  # Print Out from `Transfers` in Readable Format with Colors
  for transfer, line in transfers:
    color_bg = '#' + lines[line]['colour']  # format string to hex color by prepending '#'
    name = lines[line]['name']  # get name of line
    if len(stops := transfers[(transfer, line)]) > 1:  # if next stop is not final stop
      print(color(name, bg=color_bg), f"towards {stations[stops[0]]['name']}", end=' ')
      print(f"to {stations[stops[-1]]['name']} ({len(stops)} stops)")
    else:
      print(color(name, bg=color_bg), f"to {stations[stops[-1]]['name']}")
