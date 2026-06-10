import random
import pygame
from Cell import *
from sudoku_generator import *
from constants import *


class Board:
    def __init__(self, width, height, screen, difficulty, y_offset=0, rng=None, x_offset=0):
        """
        Constructor for the Board class.
        screen is a window from PyGame.
        difficulty is a variable to indicate if the user chose easy medium, or hard.
        """
        self.width = width
        self.height = height
        self.screen = screen
        self.y_offset = y_offset
        self.x_offset = x_offset
        self.duplicate_entry_blocking_enabled = self._duplicate_entry_blocking_enabled(difficulty)
        difficulty = self._difficulty_to_removed_cells(difficulty)
        generator = SudokuGenerator(9, difficulty, rng)
        generator.fill_values()
        self.solution = [row[:] for row in generator.get_board]
        generator.remove_cells()
        self.board = [row[:] for row in generator.get_board]
        self.original_board = [row[:] for row in self.board]
        self.selected = None
        self.cells = [
            [
                Cell(self.board[row][col], row, col, screen, self.original_board[row][col] != 0, y_offset, x_offset)
                for col in range(9)
            ]
            for row in range(9)
        ]

    def _difficulty_to_removed_cells(self, difficulty):
        if isinstance(difficulty, str):
            difficulty = difficulty.lower()
            if difficulty == "easy":
                return DIFFICULTY_REMOVED_CELLS["easy"]
            if difficulty == "medium":
                return DIFFICULTY_REMOVED_CELLS["medium"]
            if difficulty == "hard":
                return DIFFICULTY_REMOVED_CELLS["hard"]
        return int(difficulty)

    def _duplicate_entry_blocking_enabled(self, difficulty):
        if isinstance(difficulty, str):
            return difficulty.lower() not in ("medium", "hard")
        return True

    def select(self, row, col):
        """Marks a cell as selected."""
        if not (0 <= row < 9 and 0 <= col < 9):
            return

        for board_row in self.cells:
            for cell in board_row:
                cell.selected = False

        self.selected = (row, col)
        self.cells[row][col].selected = True

    def click(self, x, y):
        """Returns the row and column clicked on the board."""
        board_x = x - self.x_offset
        board_y = y - self.y_offset
        if board_x < 0 or board_x >= self.width or board_y < 0 or board_y >= self.height:
            return None
        return int(board_y // BLOCK_SIZE), int(board_x // BLOCK_SIZE)

    def clear(self):
        """Clears the selected cell if it was not part of the original puzzle."""
        if self.selected is None:
            return

        row, col = self.selected
        if self.original_board[row][col] == 0 and not self.cells[row][col].is_hint:
            self.board[row][col] = 0
            self.cells[row][col].set_cell_value(0)
            self.cells[row][col].set_sketched_value(0)

    def sketch(self, value):
        """Stores a temporary value in the selected editable cell."""
        if self.selected is None:
            return

        row, col = self.selected
        if (
            self.original_board[row][col] == 0
            and not self.cells[row][col].is_hint
            and self.board[row][col] == 0
            and self.is_valid_move(row, col, value)
        ):
            self.cells[row][col].set_sketched_value(value)

    def place_number(self, value):
        """Places a number in the selected editable cell."""
        if self.selected is None:
            return False

        row, col = self.selected
        if self.original_board[row][col] != 0 or self.cells[row][col].is_hint:
            return False

        if not self.is_valid_move(row, col, value):
            return False

        if self.duplicate_entry_blocking_enabled and self.solution[row][col] != value:
            return False

        self.board[row][col] = value
        self.cells[row][col].set_cell_value(value)
        self.cells[row][col].set_sketched_value(0)
        return True

    def reveal_hint(self, rng=None):
        """Reveals one random empty cell using the generated solution."""
        empty_cells = [
            (row, col)
            for row in range(9)
            for col in range(9)
            if self.board[row][col] == 0
        ]
        if not empty_cells:
            return None

        chooser = rng or random
        row, col = chooser.choice(empty_cells)
        value = self.solution[row][col]
        self.board[row][col] = value
        self.cells[row][col].set_cell_value(value)
        self.cells[row][col].set_sketched_value(0)
        self.cells[row][col].is_hint = True
        self.cells[row][col].fixed = True
        self._clear_duplicate_peer_sketches(row, col, value)
        return row, col

    def _clear_duplicate_peer_sketches(self, row, col, value):
        peers = {(row, check_col) for check_col in range(9)}
        peers.update((check_row, col) for check_row in range(9))
        box_start_row = (row // 3) * 3
        box_start_col = (col // 3) * 3
        peers.update(
            (check_row, check_col)
            for check_row in range(box_start_row, box_start_row + 3)
            for check_col in range(box_start_col, box_start_col + 3)
        )
        peers.discard((row, col))

        for check_row, check_col in peers:
            if self.cells[check_row][check_col].sketched_value == value:
                self.cells[check_row][check_col].set_sketched_value(0)

    def _visible_value_at(self, row, col):
        """Returns the finalized value or the visible sketched value for a cell."""
        if self.board[row][col] != 0:
            return self.board[row][col]
        return self.cells[row][col].sketched_value

    def is_valid_move(self, row, col, value):
        """Returns False when value breaks row, column, or 3x3 box rules."""
        if not (0 <= row < 9 and 0 <= col < 9):
            return False
        if value < 1 or value > 9:
            return False
        if not self.duplicate_entry_blocking_enabled:
            return True

        for check_col in range(9):
            if check_col != col and self._visible_value_at(row, check_col) == value:
                return False

        for check_row in range(9):
            if check_row != row and self._visible_value_at(check_row, col) == value:
                return False

        box_start_row = (row // 3) * 3
        box_start_col = (col // 3) * 3
        for check_row in range(box_start_row, box_start_row + 3):
            for check_col in range(box_start_col, box_start_col + 3):
                if (check_row, check_col) != (row, col) and self._visible_value_at(check_row, check_col) == value:
                    return False

        return True

    def reset_to_original(self):
        """Restores the board to the original generated puzzle."""
        self.board = [row[:] for row in self.original_board]
        for row in range(9):
            for col in range(9):
                self.cells[row][col].set_cell_value(self.original_board[row][col])
                self.cells[row][col].set_sketched_value(0)
                self.cells[row][col].is_hint = False
                self.cells[row][col].fixed = self.original_board[row][col] != 0

    def is_full(self):
        """Returns True when every board cell has a value."""
        return all(value != 0 for row in self.board for value in row)

    def find_empty(self):
        """Returns the first empty cell, or None when the board is full."""
        for row in range(9):
            for col in range(9):
                if self.board[row][col] == 0:
                    return row, col
        return None

    def check_board(self):
        """Returns True when the board is full, valid, and matches the solution."""
        required_digits = set(range(1, 10))
        if not self.is_full():
            return False

        for row in self.board:
            if set(row) != required_digits:
                return False

        for col in range(9):
            if {self.board[row][col] for row in range(9)} != required_digits:
                return False

        for box_start_row in range(0, 9, 3):
            for box_start_col in range(0, 9, 3):
                box_values = {
                    self.board[row][col]
                    for row in range(box_start_row, box_start_row + 3)
                    for col in range(box_start_col, box_start_col + 3)
                }
                if box_values != required_digits:
                    return False

        return self.board == self.solution

    def draw(self):
        """
        Draws an outline of the Sudoku grid, with bold lines to delineate the 3x3 boxes.
        Draws every cell on this board.
        """
        for row in self.cells:
            for cell in row:
                cell.draw()

        for index in range(10):
            width = 4 if index % 3 == 0 else 1
            x_position = index * BLOCK_SIZE + self.x_offset
            y_position = index * BLOCK_SIZE + self.y_offset
            pygame.draw.line(self.screen, BLACK, (x_position, self.y_offset), (x_position, self.height + self.y_offset), width)
            pygame.draw.line(self.screen, BLACK, (self.x_offset, y_position), (self.width + self.x_offset, y_position), width)
