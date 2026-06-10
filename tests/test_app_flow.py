import os
import random
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from Board import Board
from constants import (
    BACK_BUTTON_RECT,
    BG_COLOR,
    BOARD_SIZE,
    GAME_HEIGHT,
    GAME_WIDTH,
    HINT_FEEDBACK_DURATION_MS,
    HINT_PENALTY_SECONDS,
    HINT_BUTTON_RECT,
    LEADERBOARD_PANEL_WIDTH,
    RIGHT_PANEL_X,
    RULES_BOX_RECT,
    SIDE_PANEL_WIDTH,
    UI_BORDER_WIDTH,
)
from sudoku import (
    DIFFICULTY_OPTIONS,
    LoadingAnimation,
    add_leaderboard_entry,
    apply_number_input,
    back_button_contains,
    difficulty_hover_color,
    difficulty_option_draw_rect,
    difficulty_from_click,
    elapsed_with_hint_penalty,
    freeze_elapsed_seconds,
    format_score_time,
    format_time,
    hint_feedback_alpha,
    hints_enabled_for_difficulty,
    hint_button_contains,
    number_from_key,
    reset_gameplay_state_values,
    timer_border_segments,
    update_difficulty_hover_progress,
    visible_leaderboard_entries,
)


class AppFlowTests(unittest.TestCase):
    def test_loading_animation_fills_all_cells_then_completes(self):
        random.seed(0)
        animation = LoadingAnimation()

        self.assertFalse(animation.is_complete())
        self.assertEqual(animation.visible_cell_count, 0)
        self.assertNotEqual(animation.cell_order, [(row, col) for row in range(9) for col in range(9)])

        for _ in range(81):
            animation.advance()

        self.assertTrue(animation.is_complete())
        self.assertEqual(animation.visible_cell_count, 81)

    def test_difficulty_clicks_use_existing_removed_cell_rules(self):
        for option in DIFFICULTY_OPTIONS:
            x = BOARD_SIZE // 2
            y = option.center[1]

            selected = difficulty_from_click(x, y)

            self.assertEqual(selected, option.name)

        self.assertIsNone(difficulty_from_click(-1, -1))

    def test_difficulty_hover_styles_use_requested_colors_and_subtle_scale(self):
        expected_colors = {
            "easy": (45, 160, 80),
            "medium": (218, 178, 0),
            "hard": (205, 55, 55),
        }

        for option in DIFFICULTY_OPTIONS:
            normal_rect = difficulty_option_draw_rect(option, 0)
            hovered_rect = difficulty_option_draw_rect(option, 1)

            self.assertEqual(difficulty_hover_color(option.name), expected_colors[option.name])
            self.assertEqual(normal_rect, option.rect)
            self.assertGreater(hovered_rect[2], normal_rect[2])
            self.assertGreater(hovered_rect[3], normal_rect[3])
            self.assertLessEqual(hovered_rect[2] / normal_rect[2], 1.08)
            self.assertGreaterEqual(hovered_rect[2] / normal_rect[2], 1.04)

    def test_difficulty_hover_progress_eases_toward_hovered_option(self):
        progress = {option.name: 0 for option in DIFFICULTY_OPTIONS}
        easy = DIFFICULTY_OPTIONS[0]

        progress = update_difficulty_hover_progress(progress, easy.center)

        self.assertGreater(progress["easy"], 0)
        self.assertLess(progress["easy"], 1)
        self.assertEqual(progress["medium"], 0)
        self.assertEqual(progress["hard"], 0)
        self.assertGreater(difficulty_option_draw_rect(easy, progress["easy"])[2], easy.width)

    def test_timer_top_border_closes_between_panel_lines_with_ui_width(self):
        self.assertEqual(timer_border_segments(), [((SIDE_PANEL_WIDTH, 0), (RIGHT_PANEL_X, 0), UI_BORDER_WIDTH)])

    def test_empty_key_unicode_is_not_treated_as_number(self):
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_LEFT, unicode="")

        self.assertIsNone(number_from_key(event))

    def test_timer_format_is_minutes_and_seconds(self):
        self.assertEqual(format_time(0), "Time: 00:00")
        self.assertEqual(format_time(65), "Time: 01:05")

    def test_gameplay_surface_has_left_panel_without_resizing_board(self):
        self.assertEqual(GAME_WIDTH, SIDE_PANEL_WIDTH + BOARD_SIZE + LEADERBOARD_PANEL_WIDTH)
        self.assertEqual(GAME_HEIGHT, BOARD_SIZE + 50)
        self.assertEqual(RIGHT_PANEL_X, SIDE_PANEL_WIDTH + BOARD_SIZE)

    def test_hint_button_click_region_is_left_of_board(self):
        x, y, width, height = HINT_BUTTON_RECT

        self.assertLess(x + width, SIDE_PANEL_WIDTH)
        self.assertTrue(hint_button_contains(x + width / 2, y + height / 2))
        self.assertFalse(hint_button_contains(SIDE_PANEL_WIDTH + 1, y + height / 2))

    def test_back_button_sits_above_hint_without_panel_overlap(self):
        back_x, back_y, back_width, back_height = BACK_BUTTON_RECT
        hint_x, hint_y, hint_width, _ = HINT_BUTTON_RECT
        rules_x, rules_y, _, _ = RULES_BOX_RECT

        self.assertEqual(back_x, hint_x)
        self.assertEqual(back_width, hint_width)
        self.assertLess(back_y + back_height, hint_y)
        self.assertLess(back_x + back_width, SIDE_PANEL_WIDTH)
        self.assertLess(back_y + back_height, rules_y)
        self.assertTrue(back_button_contains(back_x + back_width / 2, back_y + back_height / 2))
        self.assertFalse(back_button_contains(SIDE_PANEL_WIDTH + 1, back_y + back_height / 2))
        self.assertFalse(back_button_contains(rules_x, rules_y))

    def test_back_to_difficulty_resets_active_game_state_without_leaderboard(self):
        leaderboard = [{"name": "Denny", "seconds": 90}]

        reset_values = reset_gameplay_state_values()

        self.assertEqual(reset_values["state"], "difficulty")
        self.assertIsNone(reset_values["board"])
        self.assertIsNone(reset_values["game_start_ticks"])
        self.assertIsNone(reset_values["completed_elapsed_seconds"])
        self.assertIsNone(reset_values["current_difficulty"])
        self.assertEqual(reset_values["hint_penalty_seconds"], 0)
        self.assertIsNone(reset_values["hint_feedback_start_ticks"])
        self.assertEqual(reset_values["player_name"], "")
        self.assertEqual(leaderboard, [{"name": "Denny", "seconds": 90}])

    def test_hint_penalty_adds_fifteen_seconds_to_active_time(self):
        self.assertEqual(HINT_PENALTY_SECONDS, 15)
        self.assertEqual(elapsed_with_hint_penalty(120, 0), 120)
        self.assertEqual(elapsed_with_hint_penalty(120, 15), 135)
        self.assertEqual(elapsed_with_hint_penalty(120, 30), 150)

    def test_number_input_commits_final_correct_cell_for_immediate_win_check(self):
        screen = pygame.Surface((1, 1))
        board = Board(BOARD_SIZE, BOARD_SIZE, screen, "easy")
        board.board = [row[:] for row in board.solution]
        board.original_board = [row[:] for row in board.solution]
        for row in range(9):
            for col in range(9):
                board.cells[row][col].set_cell_value(board.solution[row][col])
                board.cells[row][col].set_sketched_value(0)
                board.cells[row][col].fixed = True

        row, col = 0, 0
        board.board[row][col] = 0
        board.original_board[row][col] = 0
        board.cells[row][col].set_cell_value(0)
        board.cells[row][col].fixed = False
        board.select(row, col)

        self.assertTrue(apply_number_input(board, board.solution[row][col]))

        self.assertEqual(board.board[row][col], board.solution[row][col])
        self.assertEqual(board.cells[row][col].sketched_value, 0)
        self.assertTrue(board.is_full())
        self.assertTrue(board.check_board())

    def test_freeze_elapsed_time_reuses_completed_time_after_win(self):
        frozen_time = freeze_elapsed_seconds(None, 1_000, 136_000, 15)

        self.assertEqual(frozen_time, 150)
        self.assertEqual(freeze_elapsed_seconds(frozen_time, 1_000, 999_000, 45), 150)

    def test_hint_feedback_alpha_fades_then_disappears(self):
        start_ticks = 5_000

        self.assertEqual(hint_feedback_alpha(start_ticks, start_ticks), 255)
        self.assertLess(hint_feedback_alpha(start_ticks, start_ticks + HINT_FEEDBACK_DURATION_MS // 2), 255)
        self.assertEqual(hint_feedback_alpha(start_ticks, start_ticks + HINT_FEEDBACK_DURATION_MS), 0)
        self.assertEqual(hint_feedback_alpha(None, start_ticks), 0)

    def test_hints_are_disabled_only_for_hard_difficulty(self):
        self.assertTrue(hints_enabled_for_difficulty("easy"))
        self.assertTrue(hints_enabled_for_difficulty("medium"))
        self.assertFalse(hints_enabled_for_difficulty("hard"))

    def test_score_times_format_for_leaderboard(self):
        self.assertEqual(format_score_time(0), "00:00")
        self.assertEqual(format_score_time(65), "01:05")
        self.assertEqual(format_score_time(3661), "01:01:01")

    def test_leaderboard_sorts_fastest_and_visible_list_has_five_slots(self):
        entries = []
        entries = add_leaderboard_entry(entries, "Denny", 222)
        entries = add_leaderboard_entry(entries, "Alex", 180)
        entries = add_leaderboard_entry(entries, "Sam", 240)
        entries = add_leaderboard_entry(entries, "Jo", 120)
        entries = add_leaderboard_entry(entries, "Rae", 300)
        entries = add_leaderboard_entry(entries, "Lee", 90)

        self.assertEqual([entry["name"] for entry in entries], ["Lee", "Jo", "Alex", "Denny", "Sam", "Rae"])
        self.assertEqual([entry["seconds"] for entry in entries], [90, 120, 180, 222, 240, 300])
        self.assertEqual(
            visible_leaderboard_entries(entries),
            ["1. Lee - 01:30", "2. Jo - 02:00", "3. Alex - 03:00", "4. Denny - 03:42", "5. Sam - 04:00"],
        )
        self.assertEqual(
            visible_leaderboard_entries([]),
            ["1. ---", "2. ---", "3. ---", "4. ---", "5. ---"],
        )

    def test_leaderboard_uses_hint_adjusted_time(self):
        adjusted_time = elapsed_with_hint_penalty(120, 30)
        entries = add_leaderboard_entry([], "Denny", adjusted_time)

        self.assertEqual(entries[0]["seconds"], 150)
        self.assertEqual(visible_leaderboard_entries(entries)[0], "1. Denny - 02:30")

    def test_background_color_is_slightly_beige(self):
        self.assertEqual(BG_COLOR, (252, 248, 235))


if __name__ == "__main__":
    unittest.main()
