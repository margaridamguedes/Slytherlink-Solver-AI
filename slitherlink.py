#!/usr/bin/python3
# slitherlink.py: Template para implementação do projeto de Inteligência Artificial 2025/2026.
# Devem alterar as classes e funções neste ficheiro de acordo com as instruções do enunciado.
# Além das funções e classes sugeridas, podem acrescentar outras que considerem pertinentes.

# Grupo 63:
# 114497 Margarida Mendes Guedes
# 114295 Carolina Mendes Pires Cardoso Matias

import random, copy
from sys import stdin
from collections import defaultdict, deque

import utils
from utils import *

from search import (
    Problem,
    Node,
    astar_search,
    breadth_first_tree_search,
    depth_first_tree_search,
    greedy_search,
    recursive_best_first_search,
)


class SlitherlinkState:
    state_id = 0

    def __init__(self, board):
        self.board = board
        self.id = SlitherlinkState.state_id
        SlitherlinkState.state_id += 1

    def __lt__(self, other):
        return self.id < other.id


class Board:

    def __init__(self, grid, h_edges=None, v_edges=None, edges_0=None, changed_edges=None, valid=True):
        self.grid = grid
        self.rows = len(grid)
        self.columns = len(grid[0]) if self.rows > 0 else 0

        self.valid = valid
        self.edges_0 = edges_0 if edges_0 is not None else set()
        self.changed_edges = changed_edges if changed_edges is not None else set()

        if h_edges is None or v_edges is None:
            self.h_edges = [[0 for _ in range(self.columns)] for _ in range(self.rows + 1)]
            self.v_edges = [[0 for _ in range(self.columns + 1)] for _ in range(self.rows)]
            self.initialize_board()
        else:
            self.h_edges = h_edges
            self.v_edges = v_edges

    def initialize_board(self):
        for row in range(self.rows + 1):
            for col in range(self.columns):
                self.edges_0.add(("h", row, col))

        for row in range(self.rows):
            for col in range(self.columns + 1):
                self.edges_0.add(("v", row, col))

        self.preprocess_corners()
        self.preprocess_zeros()
        self.propagate_all()

    def copy(self):
        cloned = Board.__new__(Board)
        cloned.grid = self.grid
        cloned.rows = self.rows
        cloned.columns = self.columns
        cloned.h_edges = [row[:] for row in self.h_edges]
        cloned.v_edges = [row[:] for row in self.v_edges]
        cloned.edges_0 = self.edges_0.copy()
        cloned.changed_edges = set()
        cloned.valid = self.valid
        return cloned

    def adjacent_cell(self, cell: tuple) -> list:
        row, col = cell
        adjacent = []

        if row > 0:
            adjacent.append((row - 1, col))
        if col + 1 < self.columns:
            adjacent.append((row, col + 1))
        if row + 1 < self.rows:
            adjacent.append((row + 1, col))
        if col > 0:
            adjacent.append((row, col - 1))

        return adjacent

    def get_cell_edges(self, row: int, column: int) -> list:
        return [
            ("h", row, column),
            ("h", row + 1, column),
            ("v", row, column),
            ("v", row, column + 1),
        ]

    def get_active_edges(self, row: int, column: int) -> int:
        return (
            (1 if self.h_edges[row][column] == 1 else 0) +
            (1 if self.h_edges[row + 1][column] == 1 else 0) +
            (1 if self.v_edges[row][column] == 1 else 0) +
            (1 if self.v_edges[row][column + 1] == 1 else 0)
        )

    def get_inactive_edges(self, row: int, column: int) -> int:
        return (
            (1 if self.h_edges[row][column] == 2 else 0) +
            (1 if self.h_edges[row + 1][column] == 2 else 0) +
            (1 if self.v_edges[row][column] == 2 else 0) +
            (1 if self.v_edges[row][column + 1] == 2 else 0)
        )

    def get_edge(self, etype: str, row: int, col: int) -> int:
        if etype == "h":
            return self.h_edges[row][col]
        return self.v_edges[row][col]

    def edge_in_bounds(self, etype: str, row: int, col: int) -> bool:
        if etype == "h":
            return 0 <= row <= self.rows and 0 <= col < self.columns
        return 0 <= row < self.rows and 0 <= col <= self.columns

    def edge_vertices(self, etype: str, row: int, col: int):
        if etype == "h":
            return [(row, col), (row, col + 1)]
        return [(row, col), (row + 1, col)]

    def edge_cells(self, etype: str, row: int, col: int):
        cells = []

        if etype == "h":
            if row > 0:
                cells.append((row - 1, col))
            if row < self.rows:
                cells.append((row, col))
        else:
            if col > 0:
                cells.append((row, col - 1))
            if col < self.columns:
                cells.append((row, col))

        return cells

    def get_vertex_edges(self, vertex):
        row, col = vertex
        edges = []
        edge_state_0 = 0
        edge_state_1 = 0

        possible_edges = [
            ("h", row, col - 1),
            ("h", row, col),
            ("v", row - 1, col),
            ("v", row, col),
        ]

        for etype, r, c in possible_edges:
            if self.edge_in_bounds(etype, r, c):
                edges.append((etype, r, c))
                value = self.get_edge(etype, r, c)

                if value == 0:
                    edge_state_0 += 1
                elif value == 1:
                    edge_state_1 += 1

        return edges, edge_state_0, edge_state_1

    def cell_counts(self, row: int, col: int):
        edge_state_1 = 0
        edge_state_0 = 0
        edge_state_2 = 0

        values = (
            self.h_edges[row][col],
            self.h_edges[row + 1][col],
            self.v_edges[row][col],
            self.v_edges[row][col + 1],
        )

        for value in values:
            if value == 1:
                edge_state_1 += 1
            elif value == 0:
                edge_state_0 += 1
            else:
                edge_state_2 += 1

        return edge_state_1, edge_state_0, edge_state_2

    def conclusions_from_cells(self, cells) -> list:

        conclusions = []

        for row, col in cells:
            value = self.grid[row][col]
            edge_state_1, edge_state_0, _ = self.cell_counts(row, col)

            if value == -1:
                if edge_state_1 > 3:
                    self.valid = False
                    return None

                if edge_state_1 == 3:
                    for edge in self.get_cell_edges(row, col):
                        if self.get_edge(*edge) == 0:
                            conclusions.append((edge, 2))

            else:
                if edge_state_1 > value:
                    self.valid = False
                    return None

                if edge_state_1 + edge_state_0 < value:
                    self.valid = False
                    return None

                if edge_state_1 == value:
                    for edge in self.get_cell_edges(row, col):
                        if self.get_edge(*edge) == 0:
                            conclusions.append((edge, 2))

                elif edge_state_1 + edge_state_0 == value:
                    for edge in self.get_cell_edges(row, col):
                        if self.get_edge(*edge) == 0:
                            conclusions.append((edge, 1))

        return conclusions

    def conclusions_from_vertex(self, vertex: tuple):
        edges, edge_state_0, edge_state_1 = self.get_vertex_edges(vertex)

        if edge_state_1 > 2:
            return None

        if edge_state_1 == 2:
            return [(edge, 2) for edge in edges if self.get_edge(*edge) == 0]

        if edge_state_1 == 1:
            if edge_state_0 == 0:
                return None

            if edge_state_0 == 1:
                return [(edge, 1) for edge in edges if self.get_edge(*edge) == 0]

        if edge_state_1 == 0 and edge_state_0 == 1:
            return [(edge, 2) for edge in edges if self.get_edge(*edge) == 0]

        return []

    def set_edge(self, etype: str, row: int, col: int, state: int):

        if not self.valid:
            return False

        if state not in (1, 2):
            self.valid = False
            return False

        if not self.edge_in_bounds(etype, row, col):
            self.valid = False
            return False

        queue = deque()
        queue.append(((etype, row, col), state))
        inserted_active_edge = False

        while queue and self.valid:
            (etype, row, col), state = queue.popleft()

            if not self.edge_in_bounds(etype, row, col):
                self.valid = False
                return False

            current = self.get_edge(etype, row, col)

            if current == state:
                continue

            if current != 0:
                self.valid = False
                return False

            if state == 1 and not self.is_move_valid(etype, row, col, 1):
                self.valid = False
                return False

            if etype == "h":
                self.h_edges[row][col] = state
            else:
                self.v_edges[row][col] = state

            if state == 1:
                inserted_active_edge = True

            self.edges_0.discard((etype, row, col))
            self.changed_edges.add((etype, row, col))

            cells = self.edge_cells(etype, row, col)
            vertexes = self.edge_vertices(etype, row, col)

            conclusions = self.conclusions_from_cells(cells)

            if conclusions is None:
                self.valid = False
                return False

            for new_edge, new_state in conclusions:
                current_value = self.get_edge(*new_edge)

                if current_value == 0:
                    queue.append((new_edge, new_state))
                elif current_value != new_state:
                    self.valid = False
                    return False

            for vertex in vertexes:
                conclusions = self.conclusions_from_vertex(vertex)

                if conclusions is None:
                    self.valid = False
                    return False

                for new_edge, new_state in conclusions:
                    current_value = self.get_edge(*new_edge)

                    if current_value == 0:
                        queue.append((new_edge, new_state))
                    elif current_value != new_state:
                        self.valid = False
                        return False

        if self.valid and inserted_active_edge and self.has_premature_closed_loop():
            self.valid = False
            return False

        return self.valid

    def propagate_all(self):
        changed = True

        while changed and self.valid:
            changed = False
            conclusions = []

            for row in range(self.rows):
                for col in range(self.columns):
                    result = self.conclusions_from_cells([(row, col)])

                    if result is None:
                        self.valid = False
                        return False

                    conclusions.extend(result)

            for row in range(self.rows + 1):
                for col in range(self.columns + 1):
                    result = self.conclusions_from_vertex((row, col))

                    if result is None:
                        self.valid = False
                        return False

                    conclusions.extend(result)

            for edge, state in conclusions:
                current = self.get_edge(*edge)

                if current == 0:
                    if not self.set_edge(edge[0], edge[1], edge[2], state):
                        return False

                    changed = True

                elif current != state:
                    self.valid = False
                    return False

        return self.valid

    def preprocess_corners(self):

        if self.rows == 0 or self.columns == 0:
            return

        last_r = self.rows - 1
        last_c = self.columns - 1

        corner_edges = {
            (0, 0): [("h", 0, 0), ("v", 0, 0)],
            (0, last_c): [("h", 0, last_c), ("v", 0, self.columns)],
            (last_r, 0): [("h", self.rows, 0), ("v", last_r, 0)],
            (last_r, last_c): [("h", self.rows, last_c), ("v", last_r, self.columns)],
        }

        corner_two_edges = {
            (0, 0): [("h", 0, 1), ("v", 1, 0)],
            (0, last_c): [("h", 0, last_c - 1), ("v", 1, self.columns)],
            (last_r, 0): [("h", self.rows, 1), ("v", last_r - 1, 0)],
            (last_r, last_c): [("h", self.rows, last_c - 1), ("v", last_r - 1, self.columns)],
        }

        for row, col in corner_edges:
            value = self.grid[row][col]

            if value == 1:
                for edge in corner_edges[(row, col)]:
                    if self.edge_in_bounds(edge[0], edge[1], edge[2]):
                        self.set_edge(edge[0], edge[1], edge[2], 2)

            elif value == 2:
                for edge in corner_two_edges[(row, col)]:
                    if self.edge_in_bounds(edge[0], edge[1], edge[2]):
                        self.set_edge(edge[0], edge[1], edge[2], 1)

            elif value == 3:
                for edge in corner_edges[(row, col)]:
                    if self.edge_in_bounds(edge[0], edge[1], edge[2]):
                        self.set_edge(edge[0], edge[1], edge[2], 1)

    def preprocess_zeros(self):

        for row in range(self.rows):
            for col in range(self.columns):
                value = self.grid[row][col]

                if value == 0:
                    for etype, _, _ in self.get_cell_edges(row, col):
                        if self.edge_in_bounds(etype, row, col):
                            self.set_edge(etype, row, col, 2)

                if value != 3:
                    continue

    def is_move_valid(self, etype, row, col, state):
        if not self.edge_in_bounds(etype, row, col):
            return False

        current = self.get_edge(etype, row, col)

        if current == state:
            return True

        if current != 0:
            return False

        if state == 1:
            for vertex in self.edge_vertices(etype, row, col):
                _, _, edge_state_1 = self.get_vertex_edges(vertex)

                if edge_state_1 + 1 > 2:
                    return False

        return True

    def is_board_valid(self):
        if not self.valid:
            return False

        if not self.changed_edges:
            return True

        cells_to_check = set()
        vertexes_to_check = set()

        for etype, row, col in self.changed_edges:
            for cell in self.edge_cells(etype, row, col):
                cells_to_check.add(cell)
            for vertex in self.edge_vertices(etype, row, col):
                vertexes_to_check.add(vertex)

        self.changed_edges.clear()

        for row, col in cells_to_check:
            value = self.grid[row][col]
            edge_state_1, edge_state_0, _ = self.cell_counts(row, col)

            if value == -1:
                if edge_state_1 > 3:
                    return False
            else:
                if edge_state_1 > value or edge_state_1 + edge_state_0 < value:
                    return False

        for vertex in vertexes_to_check:
            _, edge_state_0, edge_state_1 = self.get_vertex_edges(vertex)

            if edge_state_1 > 2:
                return False

            if edge_state_1 == 1 and edge_state_0 == 0:
                return False

        return True

    def adjacency_1(self):
        adj = defaultdict(list)
        total_1 = 0

        for row in range(self.rows + 1):
            for col in range(self.columns):
                if self.h_edges[row][col] == 1:
                    total_1 += 1
                    v1 = (row, col)
                    v2 = (row, col + 1)
                    adj[v1].append(v2)
                    adj[v2].append(v1)

        for row in range(self.rows):
            for col in range(self.columns + 1):
                if self.v_edges[row][col] == 1:
                    total_1 += 1
                    v1 = (row, col)
                    v2 = (row + 1, col)
                    adj[v1].append(v2)
                    adj[v2].append(v1)

        return adj, total_1

    def all_clues_satisfied(self):
        for row in range(self.rows):
            for col in range(self.columns):
                value = self.grid[row][col]
                top = self.h_edges[row][col]
                bottom = self.h_edges[row + 1][col]
                left = self.v_edges[row][col]
                right = self.v_edges[row][col + 1]
                active = (1 if top == 1 else 0) + (1 if bottom == 1 else 0) + (1 if left == 1 else 0) + (1 if right == 1 else 0)

                if value != -1:
                    if active != value:
                        return False
                elif active > 3:
                    return False

        return True

    def has_premature_closed_loop(self):

        graph, total_edges = self.adjacency_1()

        if total_edges == 0:
            return False

        visited = set()

        for start in graph:
            if start in visited:
                continue

            stack = [start]
            component_vertices = set()
            degree_sum = 0
            is_closed_loop = True

            while stack:
                vertex = stack.pop()

                if vertex in component_vertices:
                    continue

                component_vertices.add(vertex)
                visited.add(vertex)

                degree = len(graph[vertex])
                degree_sum += degree

                if degree != 2:
                    is_closed_loop = False

                for neighbour in graph[vertex]:
                    if neighbour not in component_vertices:
                        stack.append(neighbour)

            if is_closed_loop:
                component_edges = degree_sum // 2

                if component_edges != total_edges:
                    return True

                if not self.all_clues_satisfied():
                    return True

        return False

    def choose_edge(self):

        if not self.edges_0:
            return None

        best_edge = None
        best_key = None

        for edge in self.edges_0:
            etype, row, col = edge

            has_vertex_with_one = False
            touches_numbered_cell = False
            best_cell_unknowns = 5
            cell_almost_forced = False

            for vertex in self.edge_vertices(etype, row, col):
                _, _, edge_state_1 = self.get_vertex_edges(vertex)
                if edge_state_1 == 1:
                    has_vertex_with_one = True

            for cell_row, cell_col in self.edge_cells(etype, row, col):
                value = self.grid[cell_row][cell_col]
                if value != -1:
                    touches_numbered_cell = True
                    edge_state_1, edge_state_0, _ = self.cell_counts(cell_row, cell_col)
                    if edge_state_0 < best_cell_unknowns:
                        best_cell_unknowns = edge_state_0

                    missing = value - edge_state_1
                    if missing == 1 or missing == edge_state_0 - 1:
                        cell_almost_forced = True

            if cell_almost_forced:
                priority = 0
            elif has_vertex_with_one:
                priority = 1
            elif touches_numbered_cell:
                priority = 2
            else:
                priority = 3

            key = (priority, best_cell_unknowns, edge)

            if best_key is None or key < best_key:
                best_key = key
                best_edge = edge

        return best_edge

    def print(self):
        rows = []

        for row in range(self.rows):
            output_row = []

            for col in range(self.columns):
                top = "1" if self.h_edges[row][col] == 1 else "0"
                right = "1" if self.v_edges[row][col + 1] == 1 else "0"
                bottom = "1" if self.h_edges[row + 1][col] == 1 else "0"
                left = "1" if self.v_edges[row][col] == 1 else "0"
                output_row.append(top + right + bottom + left)

            rows.append("\t".join(output_row))

        return "\n".join(rows)

    def print_instance(self):
        return self.print()

    @staticmethod
    def parse_instance():
        grid = []

        for line in stdin:
            parts = line.strip().split()

            if parts:
                grid.append([int(x) if x != "." else -1 for x in parts])

        return Board(grid)


class Slitherlink(Problem):
    def __init__(self, board: Board, gui=None):
        state = SlitherlinkState(board)
        super().__init__(state)
        self.gui = gui

    def actions(self, state: SlitherlinkState):
        board = state.board

        if not board.is_board_valid():
            return []

        edge = board.choose_edge()

        if edge is None:
            return []

        edge_type, row, col = edge
        actions = []

        actions.append([(edge_type, row, col, 2)])

        if board.is_move_valid(edge_type, row, col, 1):
            actions.append([(edge_type, row, col, 1)])

        return actions

    def result(self, state: SlitherlinkState, action):
        board = state.board
        new_board = board.copy()

        for edge_type, row, col, edge_state in action:
            new_board.set_edge(edge_type, row, col, edge_state)

        return SlitherlinkState(new_board)

    def goal_test(self, state: SlitherlinkState):
        board = state.board

        if not board.valid:
            return False

        if not board.all_clues_satisfied():
            return False

        adj, total_1 = board.adjacency_1()

        if total_1 == 0:
            return False

        for neighbors in adj.values():
            if len(neighbors) != 2:
                return False

        start = next(iter(adj))
        visited = set()
        stack = [start]

        while stack:
            vertex = stack.pop()

            if vertex in visited:
                continue

            visited.add(vertex)

            for next_vertex in adj[vertex]:
                if next_vertex not in visited:
                    stack.append(next_vertex)

        return len(visited) == len(adj)

    def h(self, node: Node):
        return 0


if __name__ == "__main__":
    board = Board.parse_instance()
    problem = Slitherlink(board)

    goal_node = depth_first_tree_search(problem)

    if goal_node is not None:
        print(goal_node.state.board.print())