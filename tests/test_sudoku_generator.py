import subprocess
import sys
import unittest
import random

from sudoku_generator import SudokuGenerator, generate_sudoku


def nonzero_values(values):
    return [value for value in values if value != 0]


class SudokuGeneratorTests(unittest.TestCase):
    def assert_valid_partial_board(self, board):
        self.assertEqual(len(board), 9)
        for row in board:
            self.assertEqual(len(row), 9)
            self.assertTrue(all(0 <= value <= 9 for value in row))
            filled = nonzero_values(row)
            self.assertEqual(len(filled), len(set(filled)))

        for col in range(9):
            filled = nonzero_values(board[row][col] for row in range(9))
            self.assertEqual(len(filled), len(set(filled)))

        for box_row in range(0, 9, 3):
            for box_col in range(0, 9, 3):
                values = [
                    board[row][col]
                    for row in range(box_row, box_row + 3)
                    for col in range(box_col, box_col + 3)
                ]
                filled = nonzero_values(values)
                self.assertEqual(len(filled), len(set(filled)))

    def test_generate_sudoku_returns_valid_puzzle_with_requested_removed_cells(self):
        board = generate_sudoku(9, 30)

        self.assert_valid_partial_board(board)
        self.assertEqual(sum(value == 0 for row in board for value in row), 30)

    def test_generate_sudoku_can_use_independent_rngs_for_different_puzzles(self):
        first = generate_sudoku(9, 30, rng=random.Random(1))
        second = generate_sudoku(9, 30, rng=random.Random(2))

        self.assert_valid_partial_board(first)
        self.assert_valid_partial_board(second)
        self.assertNotEqual(first, second)

    def test_fill_values_varies_complete_solution_with_different_rngs(self):
        first = SudokuGenerator(9, 0, rng=random.Random(1))
        second = SudokuGenerator(9, 0, rng=random.Random(2))

        first.fill_values()
        second.fill_values()

        self.assert_valid_partial_board(first.get_board)
        self.assert_valid_partial_board(second.get_board)
        self.assertNotEqual(first.get_board, second.get_board)

    def test_is_valid_rejects_row_column_and_box_duplicates(self):
        generator = SudokuGenerator(9, 0)
        generator.board[0][0] = 5
        generator.board[1][1] = 6
        generator.board[4][4] = 7

        self.assertFalse(generator.is_valid(0, 3, 5))
        self.assertFalse(generator.is_valid(3, 0, 5))
        self.assertFalse(generator.is_valid(2, 2, 6))
        self.assertTrue(generator.is_valid(0, 3, 8))

    def test_remove_cells_removes_exact_count(self):
        generator = SudokuGenerator(9, 12)
        generator.fill_values()

        generator.remove_cells()

        self.assertEqual(sum(value == 0 for row in generator.board for value in row), 12)
        self.assert_valid_partial_board(generator.board)

    def test_importing_generator_has_no_stdout_side_effects(self):
        result = subprocess.run(
            [sys.executable, "-c", "import sudoku_generator"],
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
