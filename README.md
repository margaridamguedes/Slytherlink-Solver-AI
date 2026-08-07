# Slytherlink-Solver-AI
Slitherlink Solver — IArt 2025/2026

Project developed for the Inteligência Artificial (IArt) course, 2025/2026, Instituto Superior Técnico.

Description

A Python program that solves instances of the Slitherlink puzzle using AI search techniques. Given a grid where each cell may contain a number (0–3) indicating how many of its edges belong to the solution, the program finds the single closed, non-intersecting loop that satisfies all the numeric and topological constraints.

The problem is modeled as a search problem (Problem/Node classes from search.py) and solved with the provided search strategy depth-first tree search, using a custom heuristic to guide the informed searches.

Input format

The program reads an instance from standard input: a grid of rows/columns where each value is 0, 1, 2, 3, or . (no constraint).

1 . 3 1 . 3
. . . 3 . .
. 3 . 2 1 .
. 0 2 . 1 .
. . 2 . . .
2 . 2 3 . 3
Output format

The solution is printed to standard output, one line per grid row. Each cell is represented by 4 binary digits — top right bottom left — indicating whether that edge is part of the solution (1) or not (0).

0010 0010 1101 0001 0010 1101
1001 1010 0100 0111 1001 0110
...
Usage
bash
python slitherlink.py < test.txt

Optionally, a SlitherlinkGUI instance (from slitherlink_gui.py) can be used for a visual, interactive representation of the board during development.

Project structure
File	Responsibility
slitherlink.py	Main program: reads the instance, builds the problem, runs the search and prints the solution.
search.py	Provided search algorithms and base Problem/Node classes (not modified).
utils.py	Provided utility functions used by search.py (not modified).
slitherlink_gui.py	Optional GUI for visualizing and debugging the board.

Inside slitherlink.py:

Board — internal representation of the grid (cells, edges, adjacency).
parse_instance — reads a Slitherlink instance from standard input into a Board.
SlytherlinkState — represents a search state (wraps a Board).
Slytherlink — the search problem itself (actions, result, h heuristic for A*).
Dependencies

Only the Python standard library and numpy are used; search.py and utils.py are used as provided, without modification.

Authors

(fill in with group members' names and student numbers)