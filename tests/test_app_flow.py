import os
import random
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from constants import (
    BG_COLOR,
    BOARD_SIZE,
    GAME_HEIGHT,
    GAME_WIDTH,
    HINT_PENALTY_SECONDS,
    HINT_BUTTON_RECT,
    LEADERBOARD_PANEL_WIDTH,
    RIGHT_PANEL_X,
    SIDE_PANEL_WIDTH,
)
from sudoku import (
    DIFFICULTY_OPTIONS,
    LoadingAnimation,
    add_leaderboard_entry,
    difficulty_from_click,
    elapsed_with_hint_penalty,
    format_score_time,
    format_time,
    hints_enabled_for_difficulty,
    hint_button_contains,
    number_from_key,
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

    def test_hint_penalty_adds_fifteen_seconds_to_active_time(self):
        self.assertEqual(HINT_PENALTY_SECONDS, 15)
        self.assertEqual(elapsed_with_hint_penalty(120, 0), 120)
        self.assertEqual(elapsed_with_hint_penalty(120, 15), 135)
        self.assertEqual(elapsed_with_hint_penalty(120, 30), 150)

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
