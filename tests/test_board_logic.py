import os
import random
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from Board import Board
from constants import BOARD_SIZE, DIFFICULTY_REMOVED_CELLS


class BoardLogicTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.display.set_mode((1, 1))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_place_number_only_accepts_generated_solution_value(self):
        board = Board(BOARD_SIZE, BOARD_SIZE, self.screen, 1)
        row, col = board.find_empty()
        correct_value = board.solution[row][col]
        wrong_value = 1 if correct_value != 1 else 2

        board.select(row, col)

        self.assertFalse(board.place_number(wrong_value))
        self.assertEqual(board.board[row][col], 0)
        self.assertTrue(board.place_number(correct_value))
        self.assertEqual(board.board[row][col], correct_value)

    def test_click_select_sketch_and_clear_update_real_cells(self):
        board = Board(BOARD_SIZE, BOARD_SIZE, self.screen, 1)
        row, col = board.find_empty()
        x = col * (BOARD_SIZE / 9) + 1
        y = row * (BOARD_SIZE / 9) + 1

        self.assertEqual(board.click(x, y), (row, col))
        board.select(row, col)
        board.sketch(board.solution[row][col])

        self.assertEqual(board.selected, (row, col))
        self.assertTrue(board.cells[row][col].selected)
        self.assertEqual(board.cells[row][col].sketched_value, board.solution[row][col])

        board.clear()

        self.assertEqual(board.board[row][col], 0)
        self.assertEqual(board.cells[row][col].value, 0)
        self.assertEqual(board.cells[row][col].sketched_value, 0)

    def test_click_accounts_for_gameplay_offsets(self):
        board = Board(BOARD_SIZE, BOARD_SIZE, self.screen, 1, y_offset=50, x_offset=200)
        row, col = board.find_empty()
        x = 200 + col * (BOARD_SIZE / 9) + 1
        y = 50 + row * (BOARD_SIZE / 9) + 1

        self.assertEqual(board.click(x, y), (row, col))
        self.assertIsNone(board.click(199, y))
        self.assertIsNone(board.click(x, 49))

    def test_reveal_hint_fills_solution_value_marks_red_and_locks_cell(self):
        board = Board(BOARD_SIZE, BOARD_SIZE, self.screen, "easy", rng=random.Random(4))
        empty_count = sum(value == 0 for row in board.board for value in row)

        row, col = board.reveal_hint(rng=random.Random(1))
        value = board.solution[row][col]

        self.assertEqual(board.board[row][col], value)
        self.assertEqual(board.cells[row][col].value, value)
        self.assertEqual(board.cells[row][col].sketched_value, 0)
        self.assertTrue(board.cells[row][col].is_hint)
        self.assertEqual(sum(value == 0 for row in board.board for value in row), empty_count - 1)

        board.select(row, col)
        board.clear()
        self.assertEqual(board.board[row][col], value)
        board.sketch(1 if value != 1 else 2)
        self.assertEqual(board.cells[row][col].sketched_value, 0)
        self.assertFalse(board.place_number(1 if value != 1 else 2))
        self.assertEqual(board.board[row][col], value)

    def test_reveal_hint_returns_none_when_no_empty_cells_remain(self):
        board = Board(BOARD_SIZE, BOARD_SIZE, self.screen, 0)

        self.assertIsNone(board.reveal_hint())
        self.assertFalse(any(cell.is_hint for row in board.cells for cell in row))

    def test_check_board_requires_full_valid_sudoku_solution(self):
        board = Board(BOARD_SIZE, BOARD_SIZE, self.screen, 0)

        self.assertTrue(board.check_board())

        board.board[0][0] = board.board[0][1]
        self.assertFalse(board.check_board())

        board.board = [row[:] for row in board.solution]
        board.board[8][8] = 0
        self.assertFalse(board.check_board())

    def test_valid_move_rejects_duplicates_in_row_column_and_box(self):
        board = Board(BOARD_SIZE, BOARD_SIZE, self.screen, 0)
        row, col = 0, 0
        correct_value = board.solution[row][col]
        row_duplicate = board.board[row][1]
        column_duplicate = board.board[1][col]
        box_duplicate = board.board[1][1]

        board.original_board[row][col] = 0
        board.board[row][col] = 0
        board.cells[row][col].set_cell_value(0)

        self.assertFalse(board.is_valid_move(row, col, row_duplicate))
        self.assertFalse(board.is_valid_move(row, col, column_duplicate))
        self.assertFalse(board.is_valid_move(row, col, box_duplicate))
        self.assertTrue(board.is_valid_move(row, col, correct_value))

        board.board[row][col] = correct_value
        self.assertTrue(board.is_valid_move(row, col, correct_value))

    def test_valid_move_rejects_duplicates_in_each_three_by_three_box(self):
        board = Board(BOARD_SIZE, BOARD_SIZE, self.screen, 0)

        for box_start_row in (0, 3, 6):
            for box_start_col in (0, 3, 6):
                board.board = [[0 for _ in range(9)] for _ in range(9)]
                row = box_start_row
                col = box_start_col
                duplicate_row = box_start_row + 1
                duplicate_col = box_start_col + 1
                board.board[duplicate_row][duplicate_col] = 5

                self.assertFalse(board.is_valid_move(row, col, 5))
                self.assertTrue(board.is_valid_move(row, col, 6))

    def test_valid_move_rejects_duplicate_visible_sketched_values(self):
        board = Board(BOARD_SIZE, BOARD_SIZE, self.screen, 0)
        board.board = [[0 for _ in range(9)] for _ in range(9)]
        board.original_board = [[0 for _ in range(9)] for _ in range(9)]
        for row in board.cells:
            for cell in row:
                cell.set_cell_value(0)
                cell.set_sketched_value(0)

        duplicate_cases = (
            ((0, 0), (0, 4), "row"),
            ((0, 0), (4, 0), "column"),
            ((0, 0), (1, 1), "box"),
            ((4, 4), (3, 5), "middle box"),
            ((8, 8), (6, 6), "bottom-right box"),
        )

        for (row, col), (duplicate_row, duplicate_col), label in duplicate_cases:
            with self.subTest(label=label):
                for cell_row in board.cells:
                    for cell in cell_row:
                        cell.set_sketched_value(0)

                board.cells[duplicate_row][duplicate_col].set_sketched_value(5)

                self.assertFalse(board.is_valid_move(row, col, 5))
                self.assertTrue(board.is_valid_move(row, col, 6))

    def test_sketch_and_place_number_leave_duplicate_moves_unchanged(self):
        board = Board(BOARD_SIZE, BOARD_SIZE, self.screen, 0)
        row, col = 0, 0
        duplicate_value = board.board[row][1]
        correct_value = board.solution[row][col]

        board.original_board[row][col] = 0
        board.board[row][col] = 0
        board.cells[row][col].set_cell_value(0)
        board.select(row, col)

        board.sketch(duplicate_value)
        self.assertEqual(board.cells[row][col].sketched_value, 0)

        board.cells[row][col].set_sketched_value(correct_value)
        board.board[row][1] = correct_value

        self.assertFalse(board.place_number(correct_value))
        self.assertEqual(board.board[row][col], 0)
        self.assertEqual(board.cells[row][col].value, 0)

    def test_difficulties_use_distinct_starting_clue_counts(self):
        expected_clues = {"easy": 51, "medium": 41, "hard": 31}

        for difficulty, expected in expected_clues.items():
            board = Board(BOARD_SIZE, BOARD_SIZE, self.screen, difficulty)
            clues = sum(value != 0 for row in board.original_board for value in row)

            self.assertEqual(clues, expected)
            self.assertEqual(81 - clues, DIFFICULTY_REMOVED_CELLS[difficulty])

    def test_same_difficulty_generates_different_starting_boards_with_different_random_seeds(self):
        first = Board(BOARD_SIZE, BOARD_SIZE, self.screen, "easy", rng=random.Random(1)).original_board
        second = Board(BOARD_SIZE, BOARD_SIZE, self.screen, "easy", rng=random.Random(2)).original_board

        self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
