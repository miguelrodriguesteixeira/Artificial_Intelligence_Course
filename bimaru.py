# 103449 Miguel Alexandre Rodrigues Teixeira
# bimaru.py: Projeto de Inteligência Artificial 2022/2023.

import copy
import sys

from search import (
    Problem,
    Node,
    depth_first_tree_search,
    astar_search
)

MAX_LENGTH = 10
VERT = True
HORIZ = False
HINT = 0
HINT_OVERLAP = 1
SHIP_PRIO = 2
SHIP_NO_PRIO = 3
count = 0
hint_num = 0
astar_flag = True


class BimaruState:
    state_id = 0

    def __init__(self, board):
        self.board = board
        self.id = BimaruState.state_id
        BimaruState.state_id += 1

    def __lt__(self, other):
        return self.id < other.id


def can_change_cell(value):
    return value not in ('T', 'B', 'M', 'W', 'L', 'R', 'C')


class Board:
    """Representação interna de um tabuleiro de Bimaru."""

    def __init__(self, board, rows, columns, hints):
        self.board = board  # Matriz
        self.rows = rows  # Lista  com numero de peças de barco por linha
        self.columns = columns  # Lista  com numero de peças de barco por coluna
        self.hints = hints
        self.ships = [4, 3, 2, 1]
        self.cells_left_row = [10] * MAX_LENGTH
        self.cells_left_col = [10] * MAX_LENGTH
        self.lastpos = (0, 0)
        self.wrong = False

    def get_value(self, row: int, col: int) -> str:
        """Devolve o valor na respetiva posição do tabuleiro."""
        return self.board[row][col] if 0 <= row < len(self.board) and 0 <= col < len(self.board[0]) else None

    def adjacent_vertical_values(self, row: int, col: int) -> (str, str):
        """Devolve os valores imediatamente acima e abaixo,
        respectivamente."""
        above = self.get_value(row - 1, col) if row - 1 >= 0 else None
        below = self.get_value(row + 1, col) if row + 1 < len(self.board) else None
        return above, below

    def adjacent_horizontal_values(self, row: int, col: int) -> (str, str):
        """Devolve os valores imediatamente à esquerda e à direita,
        respectivamente."""
        left = self.get_value(row, col - 1) if col - 1 >= 0 else None
        right = self.get_value(row, col + 1) if col + 1 < len(self.board[0]) else None
        return left, right

    def adjacent_diagonal_values(self, row: int, col: int) -> (str, str, str, str):
        """Devolve os valores imediatamente nas diagonais, respetivamente."""
        lt = self.get_value(row - 1, col - 1) if row - 1 >= 0 and col - 1 >= 0 else None
        rt = self.get_value(row - 1, col + 1) if row - 1 >= 0 and col + 1 < len(self.board[0]) else None
        lb = self.get_value(row + 1, col - 1) if row + 1 < len(self.board) and col - 1 >= 0 else None
        rb = self.get_value(row + 1, col + 1) if row + 1 < len(self.board) and col + 1 < len(self.board[0]) else None
        return lt, rt, lb, rb

    @staticmethod
    def parse_instance():
        """Lê o test do standard input (stdin) que é passado como argumento
        e retorna uma instância da classe Board.

        Por exemplo:
            $ python3 bimaru.py < input_T01

            > from sys import stdin
            > line = stdin.readline().split()
        """
        global hint_num, astar_flag
        matrix = [[None for _ in range(MAX_LENGTH)] for _ in range(MAX_LENGTH)]
        rows = list(map(int, sys.stdin.readline().split()[1:]))
        columns = list(map(int, sys.stdin.readline().split()[1:]))
        astar_flag = any(num >= 4 for num in rows[:5])
        num_hints = int(sys.stdin.readline().strip())
        hints = []
        hint_num = num_hints
        for _ in range(num_hints):
            hint = input().strip().split()[1:]
            row, col, value = int(hint[0]), int(hint[1]), hint[2]
            hints.append((row, col, value))
        board = Board(matrix, rows, columns, hints)
        board.fill_board_water()
        return board

    def __str__(self):
        """Imprime a grelha atual"""
        matrix = ""
        for i in range(MAX_LENGTH):
            matrix += str(self.columns[i]) + " "
        matrix += "\n"
        for r in range(10):
            for c in range(10):
                value = self.get_value(r, c)
                matrix += self.get_value(r, c) + " " if value else "- "
            matrix += str(self.rows[r])
            matrix += "\n"
        # matrix = matrix[:-1]
        return matrix

    def print_solution(self):
        matrix = ""
        for r in range(MAX_LENGTH):
            for c in range(MAX_LENGTH):
                value = self.get_value(r, c)
                matrix += self.get_value(r, c) if value else "-"
            matrix += "\n"
        matrix = matrix[:-1]
        print(matrix)

    def add_water_sides(self, row, col, is_vertical):
        if is_vertical:
            if col + 1 <= 9:
                self.change_cell(row, col + 1, '.')
            if col - 1 >= 0:
                self.change_cell(row, col - 1, '.')
        else:
            if row - 1 >= 0:
                self.change_cell(row - 1, col, '.')
            if row + 1 <= 9:
                self.change_cell(row + 1, col, '.')

    def add_water_ends(self, row, col, is_vertical, direction):  # -1 up left 1 down right
        if is_vertical:
            self.add_water_sides(row, col, is_vertical)
            row += direction
            if not 0 <= row <= 9:
                return
        else:
            self.add_water_sides(row, col, is_vertical)
            col += direction
            if not 0 <= col <= 9:
                return
        self.change_cell(row, col, '.')
        self.add_water_sides(row, col, is_vertical)

    def surround_piece(self, row, col):
        self.add_water_ends(row, col, True, -1)
        self.add_water_ends(row, col, True, 1)
        self.add_water_ends(row, col, False, -1)
        self.add_water_ends(row, col, False, 1)

    def col_has_ship(self, col):
        return self.columns[col] != 0

    def row_has_ship(self, row):
        return self.rows[row] != 0

    def fill_board_water(self):
        for i in range(MAX_LENGTH):
            if not self.row_has_ship(i) and self.cells_left_row != 0:
                self.fill_row_water(i)
            if not self.col_has_ship(i) and self.cells_left_col != 0:
                self.fill_col_water(i)

    def decrease_piece_count(self, row, col):
        self.rows[row] -= 1
        self.columns[col] -= 1

    def place_ship(self, ship):
        for i in range(MAX_LENGTH):
            if self.rows[i] > self.cells_left_row[i] or self.columns[i] > self.cells_left_col[i]:
                self.wrong = True
                return False
        row, col, length, is_vertical = ship[:4]
        if length == 1:
            self.change_cell(row, col, "c")
            self.decrease_piece_count(row, col)
            self.surround_piece(row, col)
            self.ships[length - 1] -= 1
            if self.ships[length - 1] < 0:
                self.wrong = True
                return False
            self.fill_board_water()
            self.place_guaranteed_ships()
            return True
        length -= 2
        if is_vertical:
            # Place First Piece
            self.change_cell(row, col, "t")
            self.decrease_piece_count(row, col)
            self.add_water_ends(row, col, is_vertical, -1)

            # Middle Pieces
            for i in range(1, length + 1):
                self.add_water_sides(row + i, col, is_vertical)
                self.change_cell(row + i, col, "m")
                self.decrease_piece_count(row + i, col)

            # Last Piece
            self.change_cell(row + length + 1, col, "b")
            self.decrease_piece_count(row + length + 1, col)
            self.add_water_ends(row + length + 1, col, is_vertical, 1)

        else:
            self.change_cell(row, col, "l")
            self.add_water_ends(row, col, is_vertical, -1)
            self.decrease_piece_count(row, col)

            for i in range(1, length + 1):
                self.change_cell(row, col + i, "m")
                self.add_water_sides(row, col + i, is_vertical)
                self.decrease_piece_count(row, col + i)

            self.change_cell(row, col + length + 1, "r")
            self.decrease_piece_count(row, col + length + 1)
            self.add_water_ends(row, col + length + 1, is_vertical, 1)
        self.ships[length + 2 - 1] -= 1
        if self.ships[length + 2 - 1] < 0:
            self.wrong = True
            return False
        self.fill_board_water()
        self.place_guaranteed_ships()
        return True

    def change_cell(self, row, col, value):
        if can_change_cell(self.get_value(row, col)):
            if self.get_value(row, col) is None:
                self.decrease_cell_left(row, col)
            self.board[row][col] = value

    def fill_row_water(self, row):
        for col in range(len(self.board[row])):
            cell = self.board[row][col]
            if cell is None:
                self.change_cell(row, col, '.')
        self.cells_left_row[row] = 0

    def fill_col_water(self, col):
        for row_i, row in enumerate(self.board):
            cell = row[col]
            if cell is None:
                self.change_cell(row_i, col, '.')
        self.cells_left_col[col] = 0

    def decrease_cell_left(self, row, col, amount=1):
        self.cells_left_row[row] -= amount
        self.cells_left_col[col] -= amount

    def is_cell_empty(self, row, col):
        return self.get_value(row, col) is None

    def can_fit_row(self, length, row):
        return self.rows[row] - length >= 0

    def can_fit_col(self, length, col):
        return self.columns[col] - length >= 0

    def can_place_ship(self, ship):
        row, col, length, is_vertical = ship[:4]
        if is_vertical is None:
            if not self.can_fit_col(length, col):
                return False
            if not self.can_fit_row(length, row) or not self.check_adjacencies((row, col)):
                return False

        elif is_vertical:
            if row + length > MAX_LENGTH:
                return False
            if self.can_fit_col(length, col):
                for i in range(row, row + length):
                    if not self.can_fit_row(1, i) or not self.check_adjacencies((i, col)):
                        return False
            else:
                return False
        elif not is_vertical:
            if col + length > MAX_LENGTH:
                return False
            if self.can_fit_row(length, row):
                for i in range(col, col + length):
                    if not self.can_fit_col(1, i) or not self.check_adjacencies((row, i)):
                        return False
            else:
                return False
        return True

    def check_adjacencies(self, pos):
        row, col = pos
        if self.get_value(row, col) in ["T", "B", "L", "R", "M", "W", "C"]:
            return False
        vertical = self.adjacent_vertical_values(row, col)
        horizontal = self.adjacent_horizontal_values(row, col)
        diagonal = self.adjacent_diagonal_values(row, col)
        for values in vertical, horizontal, diagonal:
            for value in values:
                if value is not None and value.upper() in ["T", "B", "L", "R", "M", "C"]:
                    return False
        return True

    def build_ship_row_consecutive(self, row, col):
        length = 1
        for i in range(col + 1, MAX_LENGTH):
            if self.is_cell_empty(row, i):
                length += 1
            else:
                break
            if length > 4:
                return []  # is too long for row wrong board
        if length > 1:
            ship = (row, col, length, HORIZ, SHIP_PRIO)
            return [ship]
        return None

    def build_ship_col_consecutive(self, row, col):
        length = 1
        for i in range(row + 1, MAX_LENGTH):
            if self.is_cell_empty(i, col):
                length += 1
            else:
                break
            if length > 4:
                return []  # ship is too long for row wrong board
        if length > 1:
            ship = (row, col, length, VERT, SHIP_PRIO)
            return [ship]
        return None

    def add_ship(self, row, col, ship_len, direction, actions, ship_type):
        ship = (row, col, ship_len, direction, ship_type)
        if self.can_place_ship(ship):
            actions.append(ship)

    def get_actions_with_prio(self, row, col, is_vertical):
        ships = []
        for ship_len, amount in enumerate(self.ships):
            if amount == 0:
                continue
            ship_len += 1
            if ship_len < 1:
                continue
            if ship_len == 1:
                self.add_ship(row, col, ship_len, None, ships, SHIP_PRIO)
                continue
            if is_vertical:
                for row_vert in range(row - ship_len + 1, row + 1):
                    if row_vert < 0:
                        continue
                    self.add_ship(row_vert, col, ship_len, VERT, ships, SHIP_PRIO)
            elif not is_vertical:
                for col_vert in range(col - ship_len + 1, col + 1):
                    if col_vert < 0:
                        continue
                    self.add_ship(row, col_vert, ship_len, HORIZ, ships, SHIP_PRIO)
        return ships

    def overlap_value(self, row, col, value):
        self.board[row][col] = value

    def find_empty_space(self, fixed_coord, current_coord, is_vertical):

        if is_vertical:
            for i in range(current_coord, MAX_LENGTH):
                if self.is_cell_empty(i, fixed_coord):
                    return i
            return None
        else:
            for i in range(current_coord, MAX_LENGTH):
                if self.is_cell_empty(fixed_coord, i):
                    return i
            return None

    def place_guaranteed_ships(self):
        ship_placed = False
        for i in range(MAX_LENGTH):
            row, col = 0, 0
            if self.wrong:
                return
            if self.rows[i] == self.cells_left_row[i] != 0:
                while col < MAX_LENGTH:
                    col = self.find_empty_space(i, col, HORIZ)
                    if col is None:
                        break
                    ship = self.build_ship_row_consecutive(i, col)
                    if ship is None:
                        col += 2
                    elif not ship:
                        self.wrong = True
                        return
                    else:
                        ship = ship[0]
                        ship_placed = self.place_ship(ship)
                        col += ship[2] + 1
            if self.columns[i] == self.cells_left_col[i] != 0:
                while row < MAX_LENGTH:
                    cenas = self.find_empty_space(i, row, VERT)
                    row = cenas
                    if row is None:
                        break
                    ship = self.build_ship_col_consecutive(row, i)
                    if ship is None:
                        row += 2
                    elif not ship:
                        self.wrong = True
                        return
                    else:
                        ship = ship[0]
                        ship_placed = self.place_ship(ship)
                        row += ship[2] + 1

    def find_next_guaranteed_ship(self, fixed_coord, is_vertical):
        current_cord = self.find_empty_space(fixed_coord, 0, is_vertical)
        if is_vertical:
            possible_action = self.build_ship_col_consecutive(current_cord, fixed_coord)
            if possible_action is not None:
                return possible_action
            else:
                return self.get_actions_with_prio(current_cord, fixed_coord, HORIZ)
        else:
            possible_action = self.build_ship_row_consecutive(fixed_coord, current_cord)
            if possible_action is not None:
                return possible_action
            else:
                return self.get_actions_with_prio(fixed_coord, current_cord, VERT)


class Bimaru(Problem):
    def __init__(self, board: Board):
        """O construtor especifica o estado inicial."""
        super().__init__(BimaruState(board))
        self.count = 0

    def actions(self, state: BimaruState):
        """Retorna uma lista de ações que podem ser executadas a
        partir do estado passado como argumento."""
        board = state.board
        if board.wrong:
            return []
        actions = []
        for i in range(MAX_LENGTH):
            if board.rows[i] > board.cells_left_row[i] or board.columns[i] > board.cells_left_col[i]:
                return []

        if board.hints:
            return self.hint_actions(board)

        for i in range(MAX_LENGTH):
            if board.rows[i] == board.cells_left_row[i] != 0:
                return board.find_next_guaranteed_ship(i, HORIZ)
            if board.columns[i] == board.cells_left_col[i] != 0:
                return board.find_next_guaranteed_ship(i, VERT)

        row = board.lastpos[0]
        col = board.lastpos[1]
        for row in range(row, MAX_LENGTH):
            for col in range(col, MAX_LENGTH):
                if board.is_cell_empty(row, col):
                    for ship_len, amount in enumerate(board.ships):
                        if amount == 0:
                            continue
                        ship_len += 1
                        if ship_len < 1:
                            continue
                        if ship_len == 1:
                            board.add_ship(row, col, ship_len, None, actions, SHIP_NO_PRIO)
                            continue
                        board.add_ship(row, col, ship_len, VERT, actions, SHIP_NO_PRIO)
                        board.add_ship(row, col, ship_len, HORIZ, actions, SHIP_NO_PRIO)
            col = 0
        return actions

    def hint_actions(self,
                     board):
        actions = []
        adjust_coords = {
            'T': (0, 0, VERT),
            'B': (-1, 0, VERT),
            'L': (0, 0, HORIZ),
            'R': (0, -1, HORIZ),
            'C': (0, 0, None)
        }
        hint = board.hints[0]
        row, col, value = hint
        if value == "M":
            for ship_len, amount in enumerate(board.ships[2:], start=2):
                if amount == 0:
                    continue
                board.add_ship(row - ship_len + 1, col, ship_len + 1, VERT, actions, HINT)
                board.add_ship(row, col - ship_len + 1, ship_len + 1, HORIZ, actions, HINT)
                if ship_len > 2:
                    board.add_ship(row - ship_len + 2, col, ship_len + 1, VERT, actions, HINT)
                    board.add_ship(row, col - ship_len - 2, ship_len + 1, HORIZ, actions, HINT)
        elif value == 'W':
            return [(row, col, value, None, HINT_OVERLAP)]
        else:
            if value == 'C':
                ships = board.ships[:1]
                start = 0
            else:
                ships = board.ships[1:]
                start = 1
            for ship_len, amount in enumerate(ships, start):
                if amount == 0:
                    continue
                setup = adjust_coords[value]
                board.add_ship(row + setup[0] * ship_len, col + setup[1] * ship_len, ship_len + 1, setup[2], actions,
                               HINT)
            if not actions:
                if board.get_value(row, col) is not None and board.get_value(row, col).upper() == value:
                    actions.append((row, col, value, None, HINT_OVERLAP))
        return actions

    def result(self, state: BimaruState, action):
        """Retorna o estado resultante de executar a 'action' sobre
        'state' passado como argumento. A ação a executar deve ser uma
        das presentes na lista obtida pela execução de
        self.actions(state)."""
        new_board = copy.deepcopy(state.board)
        if action[4] == HINT_OVERLAP:
            if action[2] == 'W' and new_board.get_value(action[0], action[1]) is None:
                new_board.decrease_cell_left(action[0], action[1])
            new_board.overlap_value(action[0], action[1], action[2])
            new_board.hints.pop(0)

        else:
            new_board.place_ship(action)  # por os ships na new board

            if action[4] == HINT:
                row, col, val = new_board.hints.pop(0)
                new_board.overlap_value(row, col, val)
            elif action[4] == SHIP_NO_PRIO:
                new_board.lastpos = (action[0], action[1])

        new_state = BimaruState(new_board)

        return new_state  # criar o estado updated

    def goal_test(self, state: BimaruState):
        """Retorna True se e só se o estado passado como argumento é
        um estado objetivo. Deve verificar se todas as posições do tabuleiro
        estão preenchidas de acordo com as regras do problema."""
        board = state.board
        return all(ship_amount == 0 for ship_amount in board.ships)

    def h(self, node: Node):
        """Função heuristica utilizada para a procura A*."""
        board = node.state.board

        cells_left = sum(board.cells_left_row) + sum(board.cells_left_col)

        unplaced_ships = (sum(board.rows) + sum(board.columns)) * 10

        heuristic = cells_left + unplaced_ships

        return heuristic


if __name__ == "__main__":
    board1 = Board.parse_instance()
    bimaru = Bimaru(board1)
    if hint_num == 3:
        sol = astar_search(bimaru)
    else:
        sol = depth_first_tree_search(bimaru)
    if sol is None:
        print("There is no solution available. Better luck next time :)")
    else:
        sol.state.board.print_solution()
    pass
