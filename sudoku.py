import asyncio
from dataclasses import dataclass
import json
import random
import pygame
from constants import *
from Board import Board
from Cell import Cell
from sudoku_generator import SudokuGenerator
# ==================== main file ==================== #


STATE_LOADING = "loading"
STATE_DIFFICULTY = "difficulty"
STATE_PLAYING = "playing"
STATE_WIN = "win"
LEADERBOARD_STORAGE_KEY = "group77_sudoku_leaderboard"
MEMORY_LEADERBOARD = []


@dataclass(frozen=True)
class DifficultyOption:
    name: str
    label: str
    x: int
    y: int
    width: int
    height: int

    @property
    def rect(self):
        return (self.x, self.y, self.width, self.height)

    @property
    def center(self):
        return (self.x + self.width / 2, self.y + self.height / 2)

    def contains(self, x, y):
        return self.x <= x <= self.x + self.width and self.y <= y <= self.y + self.height


DIFFICULTY_OPTIONS = (
    DifficultyOption("easy", "Easy", BOARD_SIZE // 2 - 120, 300, 240, 55),
    DifficultyOption("medium", "Medium", BOARD_SIZE // 2 - 120, 375, 240, 55),
    DifficultyOption("hard", "Hard", BOARD_SIZE // 2 - 120, 450, 240, 55),
)
DIFFICULTY_HOVER_COLORS = {
    "easy": (45, 160, 80),
    "medium": (218, 178, 0),
    "hard": (205, 55, 55),
}
DIFFICULTY_HOVER_SCALE = 1.06
DIFFICULTY_HOVER_EASING = 0.2

RULES_LINES = (
    "Sudoku Rules",
    "- Fill every cell with 1-9.",
    "- Each row must contain 1-9 once.",
    "- Each column must contain 1-9 once.",
    "- Each 3x3 box must contain 1-9 once.",
    "- No duplicates are allowed.",
)


class LoadingAnimation:
    def __init__(self):
        generator = SudokuGenerator(9, 0)
        generator.fill_values()
        self.board = [row[:] for row in generator.get_board]
        self.cell_order = [(row, col) for row in range(9) for col in range(9)]
        random.shuffle(self.cell_order)
        self.visible_cell_count = 0

    def advance(self):
        if self.visible_cell_count < 81:
            self.visible_cell_count += 1

    def is_complete(self):
        return self.visible_cell_count >= 81


def number_from_key(event):
    """Returns the pressed number key as an int, or None for non-number keys."""
    unicode_value = getattr(event, "unicode", "")
    if unicode_value and unicode_value in "123456789":
        return int(unicode_value)
    if pygame.K_KP1 <= event.key <= pygame.K_KP9:
        return event.key - pygame.K_KP0
    return None


def format_time(total_seconds):
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"Time: {minutes:02}:{seconds:02}"


def format_score_time(total_seconds):
    total_seconds = max(0, int(total_seconds))
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    if hours:
        return f"{hours:02}:{minutes:02}:{seconds:02}"
    return f"{minutes:02}:{seconds:02}"


def elapsed_with_hint_penalty(base_elapsed_seconds, hint_penalty_seconds):
    return int(base_elapsed_seconds) + int(hint_penalty_seconds)


def freeze_elapsed_seconds(completed_elapsed_seconds, game_start_ticks, current_ticks, hint_penalty_seconds):
    if completed_elapsed_seconds is not None:
        return completed_elapsed_seconds
    base_elapsed_seconds = (current_ticks - game_start_ticks) // 1000
    return elapsed_with_hint_penalty(base_elapsed_seconds, hint_penalty_seconds)


def hint_feedback_alpha(start_ticks, current_ticks):
    if start_ticks is None:
        return 0
    elapsed_ticks = current_ticks - start_ticks
    if elapsed_ticks < 0:
        elapsed_ticks = 0
    if elapsed_ticks >= HINT_FEEDBACK_DURATION_MS:
        return 0
    remaining = 1 - (elapsed_ticks / HINT_FEEDBACK_DURATION_MS)
    return max(0, min(255, round(255 * remaining)))


def apply_number_input(board, value):
    if board is None or board.selected is None:
        return False
    if board.place_number(value):
        return True

    row, col = board.selected
    before_sketch = board.cells[row][col].sketched_value
    board.sketch(value)
    return board.cells[row][col].sketched_value != before_sketch


def reset_gameplay_state_values():
    return {
        "board": None,
        "game_start_ticks": None,
        "completed_elapsed_seconds": None,
        "current_difficulty": None,
        "hint_penalty_seconds": 0,
        "hint_feedback_start_ticks": None,
        "player_name": "",
        "state": STATE_DIFFICULTY,
    }


def hints_enabled_for_difficulty(difficulty):
    return str(difficulty).lower() != "hard"


def clean_player_name(name):
    cleaned = name.strip()
    if cleaned == "":
        return "Player"
    return cleaned[:18]


def sort_leaderboard(entries):
    clean_entries = []
    for entry in entries:
        try:
            name = clean_player_name(str(entry["name"]))
            seconds = int(entry["seconds"])
        except (KeyError, TypeError, ValueError):
            continue
        if seconds >= 0:
            clean_entries.append({"name": name, "seconds": seconds})
    return sorted(clean_entries, key=lambda entry: entry["seconds"])


def add_leaderboard_entry(entries, name, seconds):
    updated_entries = list(entries)
    updated_entries.append({"name": clean_player_name(name), "seconds": int(seconds)})
    return sort_leaderboard(updated_entries)


def visible_leaderboard_entries(entries):
    sorted_entries = sort_leaderboard(entries)
    visible_entries = []
    for index in range(5):
        if index < len(sorted_entries):
            entry = sorted_entries[index]
            visible_entries.append(f"{index + 1}. {entry['name']} - {format_score_time(entry['seconds'])}")
        else:
            visible_entries.append(f"{index + 1}. ---")
    return visible_entries


def get_browser_local_storage():
    try:
        import platform

        if getattr(platform, "is_browser", False):
            return platform.window.localStorage
    except Exception:
        pass
    return None


def load_leaderboard():
    storage = get_browser_local_storage()
    if storage is None:
        return sort_leaderboard(MEMORY_LEADERBOARD)

    try:
        raw_entries = storage.getItem(LEADERBOARD_STORAGE_KEY)
        if not raw_entries:
            return []
        return sort_leaderboard(json.loads(raw_entries))
    except Exception:
        return []


def save_leaderboard(entries):
    global MEMORY_LEADERBOARD
    sorted_entries = sort_leaderboard(entries)
    storage = get_browser_local_storage()
    if storage is None:
        MEMORY_LEADERBOARD = sorted_entries
        return

    try:
        storage.setItem(LEADERBOARD_STORAGE_KEY, json.dumps(sorted_entries))
    except Exception:
        MEMORY_LEADERBOARD = sorted_entries


async def wait_for_browser_preloader():
    """Waits for the HTML Sudoku preloader when running under pygbag."""
    try:
        import platform

        if not getattr(platform, "is_browser", False):
            return False

        while not platform.window.sudokuPreloaderComplete:
            await asyncio.sleep(0.05)
        return True
    except Exception:
        return False


def hide_browser_preloader():
    try:
        import platform

        if getattr(platform, "is_browser", False):
            preloader = platform.window.document.getElementById("sudoku-preloader")
            if preloader:
                preloader.style.display = "none"
    except Exception:
        pass


def difficulty_from_click(x, y):
    for option in DIFFICULTY_OPTIONS:
        if option.contains(x, y):
            return option.name
    return None


def difficulty_hover_color(difficulty):
    return DIFFICULTY_HOVER_COLORS[str(difficulty).lower()]


def difficulty_option_draw_rect(option, hover_progress):
    hover_progress = max(0, min(1, float(hover_progress)))
    scale = 1 + (DIFFICULTY_HOVER_SCALE - 1) * hover_progress
    width = round(option.width * scale)
    height = round(option.height * scale)
    center_x, center_y = option.center
    return (
        round(center_x - width / 2),
        round(center_y - height / 2),
        width,
        height,
    )


def update_difficulty_hover_progress(progress, mouse_pos):
    updated_progress = {}
    for option in DIFFICULTY_OPTIONS:
        target = 1 if option.contains(*mouse_pos) else 0
        current = float(progress.get(option.name, 0))
        eased = current + (target - current) * DIFFICULTY_HOVER_EASING
        if abs(eased - target) < 0.01:
            eased = target
        updated_progress[option.name] = max(0, min(1, eased))
    return updated_progress


def hint_button_contains(x, y):
    button_x, button_y, button_width, button_height = HINT_BUTTON_RECT
    return button_x <= x <= button_x + button_width and button_y <= y <= button_y + button_height


def back_button_contains(x, y):
    button_x, button_y, button_width, button_height = BACK_BUTTON_RECT
    return button_x <= x <= button_x + button_width and button_y <= y <= button_y + button_height


def point_in_rect(point, rect):
    x, y = point
    rect_x, rect_y, rect_width, rect_height = rect
    return rect_x <= x <= rect_x + rect_width and rect_y <= y <= rect_y + rect_height


def draw_wrapped_text(surface, text, font, color, x, y, max_width, line_spacing=4):
    words = text.split()
    lines = []
    current = ""

    for word in words:
        candidate = word if current == "" else f"{current} {word}"
        if font.size(candidate)[0] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    for line in lines:
        rendered = font.render(line, True, color)
        surface.blit(rendered, (x, y))
        y += rendered.get_height() + line_spacing

    return y


def draw_grid(surface):
    for index in range(10):
        width = 4 if index % 3 == 0 else 1
        position = index * BLOCK_SIZE
        pygame.draw.line(surface, BLACK, (position, 0), (position, BOARD_SIZE), width)
        pygame.draw.line(surface, BLACK, (0, position), (BOARD_SIZE, position), width)


def draw_loading_screen(surface, animation):
    surface.fill(BG_COLOR)

    for index in range(animation.visible_cell_count):
        row, col = animation.cell_order[index]
        value = animation.board[row][col]
        Cell(value, row, col, surface, True).draw()

    draw_grid(surface)


def draw_difficulty_prompt(surface, hover_progress=None):
    title_font = pygame.font.Font(None, NUM_FONT)
    option_font = pygame.font.Font(None, SKETCH_FONT)
    hover_progress = hover_progress or {option.name: 0 for option in DIFFICULTY_OPTIONS}
    surface.fill(BG_COLOR)

    title = title_font.render("Select Difficulty", True, BLACK)
    title_rect = title.get_rect(center=(BOARD_SIZE / 2, 220))
    surface.blit(title, title_rect)

    for option in DIFFICULTY_OPTIONS:
        progress = hover_progress.get(option.name, 0)
        color = difficulty_hover_color(option.name) if progress > 0 else BLACK
        rect = difficulty_option_draw_rect(option, progress)
        pygame.draw.rect(surface, color, rect, 2)
        label = option_font.render(option.label, True, color)
        label_rect = label.get_rect(center=option.center)
        surface.blit(label, label_rect)


def timer_border_segments():
    return [((BOARD_X_OFFSET, 0), (RIGHT_PANEL_X, 0), UI_BORDER_WIDTH)]


def draw_timer_border(surface):
    for start, end, width in timer_border_segments():
        pygame.draw.line(surface, BLACK, start, end, width)


def draw_timer(surface, elapsed_seconds):
    draw_timer_border(surface)
    timer_font = pygame.font.Font(None, TIMER_FONT)
    timer = timer_font.render(format_time(elapsed_seconds), True, BLACK)
    timer_rect = timer.get_rect(center=(BOARD_X_OFFSET + BOARD_SIZE / 2, TIMER_HEIGHT / 2))
    surface.blit(timer, timer_rect)


def draw_hint_feedback(surface, alpha):
    if alpha <= 0:
        return

    feedback_font = pygame.font.Font(None, TIMER_FONT)
    text = feedback_font.render(f"+{HINT_PENALTY_SECONDS}", True, RED)
    text.set_alpha(alpha)
    button_x, button_y, button_width, button_height = HINT_BUTTON_RECT
    text_rect = text.get_rect(center=(button_x + button_width / 2, button_y + button_height + 12))
    surface.blit(text, text_rect)


def draw_button(surface, rect, label, font):
    x, y, width, height = rect
    pygame.draw.rect(surface, BLACK, rect, 2)
    rendered_label = font.render(label, True, BLACK)
    label_rect = rendered_label.get_rect(center=(x + width / 2, y + height / 2))
    surface.blit(rendered_label, label_rect)


def draw_left_panel(surface, hints_enabled=True, back_enabled=True):
    button_font = pygame.font.Font(None, SKETCH_FONT)
    rules_title_font = pygame.font.Font(None, TIMER_FONT)
    rules_font = pygame.font.Font(None, RULES_FONT)
    rules_x, rules_y, rules_width, rules_height = RULES_BOX_RECT

    pygame.draw.line(surface, BLACK, (SIDE_PANEL_WIDTH, 0), (SIDE_PANEL_WIDTH, GAME_HEIGHT), UI_BORDER_WIDTH)
    if back_enabled:
        draw_button(surface, BACK_BUTTON_RECT, "Back", button_font)
    if hints_enabled:
        draw_button(surface, HINT_BUTTON_RECT, "Hint", button_font)

    pygame.draw.rect(surface, BLACK, RULES_BOX_RECT, 2)
    rules_y += 14
    title = rules_title_font.render(RULES_LINES[0], True, BLACK)
    surface.blit(title, (rules_x + 12, rules_y))
    rules_y += title.get_height() + 14

    for line in RULES_LINES[1:]:
        rules_y = draw_wrapped_text(surface, line, rules_font, BLACK, rules_x + 12, rules_y, rules_width - 24, 3)
        rules_y += 7


def draw_leaderboard_panel(surface, leaderboard):
    title_font = pygame.font.Font(None, TIMER_FONT)
    entry_font = pygame.font.Font(None, RULES_FONT)
    box_x, box_y, box_width, box_height = LEADERBOARD_BOX_RECT

    pygame.draw.line(surface, BLACK, (RIGHT_PANEL_X, 0), (RIGHT_PANEL_X, GAME_HEIGHT), UI_BORDER_WIDTH)
    pygame.draw.rect(surface, BLACK, LEADERBOARD_BOX_RECT, 2)

    title = title_font.render("Leaderboard", True, BLACK)
    surface.blit(title, (box_x + 12, box_y + 14))

    y = box_y + 58
    for line in visible_leaderboard_entries(leaderboard):
        y = draw_wrapped_text(surface, line, entry_font, BLACK, box_x + 12, y, box_width - 24, 2)
        y += 6


def draw_win_screen(surface, elapsed_seconds, player_name):
    overlay = pygame.Surface((GAME_WIDTH, GAME_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 85))
    surface.blit(overlay, (0, 0))

    modal_font = pygame.font.Font(None, SKETCH_FONT)
    text_font = pygame.font.Font(None, TIMER_FONT)
    input_font = pygame.font.Font(None, RULES_FONT)
    modal_x, modal_y, modal_width, modal_height = WIN_MODAL_RECT

    pygame.draw.rect(surface, BG_COLOR, WIN_MODAL_RECT)
    pygame.draw.rect(surface, BLACK, WIN_MODAL_RECT, 2)

    title = modal_font.render("Puzzle Complete", True, BLACK)
    title_rect = title.get_rect(center=(modal_x + modal_width / 2, modal_y + 42))
    surface.blit(title, title_rect)

    time_label = text_font.render(f"Time: {format_score_time(elapsed_seconds)}", True, BLACK)
    time_rect = time_label.get_rect(center=(modal_x + modal_width / 2, modal_y + 82))
    surface.blit(time_label, time_rect)

    prompt = input_font.render("Name:", True, BLACK)
    surface.blit(prompt, (NAME_INPUT_RECT[0], NAME_INPUT_RECT[1] - 26))
    pygame.draw.rect(surface, BLACK, NAME_INPUT_RECT, 2)

    name_text = input_font.render(player_name, True, BLACK)
    surface.blit(name_text, (NAME_INPUT_RECT[0] + 8, NAME_INPUT_RECT[1] + 9))

    pygame.draw.rect(surface, BLACK, WIN_SUBMIT_BUTTON_RECT, 2)
    submit = input_font.render("Submit", True, BLACK)
    submit_rect = submit.get_rect(center=(
        WIN_SUBMIT_BUTTON_RECT[0] + WIN_SUBMIT_BUTTON_RECT[2] / 2,
        WIN_SUBMIT_BUTTON_RECT[1] + WIN_SUBMIT_BUTTON_RECT[3] / 2,
    ))
    surface.blit(submit, submit_rect)


def draw_game(surface, board, elapsed_seconds, leaderboard=(), hints_enabled=True, hint_feedback_alpha_value=0, back_enabled=True):
    surface.fill(BG_COLOR)
    draw_left_panel(surface, hints_enabled, back_enabled)
    draw_hint_feedback(surface, hint_feedback_alpha_value)
    draw_leaderboard_panel(surface, leaderboard)
    draw_timer(surface, elapsed_seconds)
    board.draw()


async def main():
    used_browser_preloader = await wait_for_browser_preloader()
    pygame.init()
    surface = pygame.display.set_mode((BOARD_SIZE, BOARD_SIZE))
    pygame.display.set_caption("Sudoku")
    clock = pygame.time.Clock()
    loading_animation = LoadingAnimation()
    loading_frame_delay = 2
    frame_count = 0
    state = STATE_DIFFICULTY if used_browser_preloader else STATE_LOADING
    board = None
    game_start_ticks = None
    completed_elapsed_seconds = None
    current_difficulty = None
    hint_penalty_seconds = 0
    hint_feedback_start_ticks = None
    player_name = ""
    leaderboard = load_leaderboard()
    difficulty_hover_progress = {option.name: 0 for option in DIFFICULTY_OPTIONS}

    if used_browser_preloader:
        draw_difficulty_prompt(surface, difficulty_hover_progress)
        pygame.display.update()
        hide_browser_preloader()

    def start_game(difficulty):
        nonlocal board, game_start_ticks, completed_elapsed_seconds, current_difficulty, hint_penalty_seconds, hint_feedback_start_ticks, player_name, state, surface
        surface = pygame.display.set_mode((GAME_WIDTH, GAME_HEIGHT))
        board = Board(BOARD_SIZE, BOARD_SIZE, surface, difficulty, TIMER_HEIGHT, x_offset=BOARD_X_OFFSET)
        game_start_ticks = pygame.time.get_ticks()
        completed_elapsed_seconds = None
        current_difficulty = difficulty
        hint_penalty_seconds = 0
        hint_feedback_start_ticks = None
        player_name = ""
        state = STATE_PLAYING
        pygame.display.set_caption(f"Sudoku - {difficulty.title()}")

    def finish_if_complete():
        nonlocal completed_elapsed_seconds, state
        if board is not None and board.is_full() and board.check_board():
            completed_elapsed_seconds = freeze_elapsed_seconds(
                completed_elapsed_seconds,
                game_start_ticks,
                pygame.time.get_ticks(),
                hint_penalty_seconds,
            )
            state = STATE_WIN
            pygame.display.set_caption("Sudoku - Complete")

    def return_to_difficulty_selection():
        nonlocal board, game_start_ticks, completed_elapsed_seconds, current_difficulty, hint_penalty_seconds, hint_feedback_start_ticks, player_name, state, surface
        reset_values = reset_gameplay_state_values()
        board = reset_values["board"]
        game_start_ticks = reset_values["game_start_ticks"]
        completed_elapsed_seconds = reset_values["completed_elapsed_seconds"]
        current_difficulty = reset_values["current_difficulty"]
        hint_penalty_seconds = reset_values["hint_penalty_seconds"]
        hint_feedback_start_ticks = reset_values["hint_feedback_start_ticks"]
        player_name = reset_values["player_name"]
        state = reset_values["state"]
        surface = pygame.display.set_mode((BOARD_SIZE, BOARD_SIZE))
        pygame.display.set_caption("Sudoku")

    def submit_win_name():
        nonlocal leaderboard
        if current_difficulty is None or completed_elapsed_seconds is None:
            return
        leaderboard = add_leaderboard_entry(leaderboard, player_name, completed_elapsed_seconds)
        save_leaderboard(leaderboard)
        start_game(current_difficulty)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:  # just closes the game with x
                running = False
            elif state == STATE_DIFFICULTY and event.type == pygame.MOUSEBUTTONDOWN:
                difficulty = difficulty_from_click(*event.pos)
                if difficulty is not None:
                    start_game(difficulty)
            elif state == STATE_DIFFICULTY and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_e:
                    start_game("easy")
                elif event.key == pygame.K_m:
                    start_game("medium")
                elif event.key == pygame.K_h:
                    start_game("hard")
            elif state == STATE_WIN:
                if event.type == pygame.MOUSEBUTTONDOWN and point_in_rect(event.pos, WIN_SUBMIT_BUTTON_RECT):
                    submit_win_name()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_BACKSPACE:
                        player_name = player_name[:-1]
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        submit_win_name()
                    else:
                        typed = getattr(event, "unicode", "")
                        if typed.isprintable() and len(player_name) < 18:
                            player_name += typed
            elif state != STATE_PLAYING:
                continue
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if back_button_contains(*event.pos):
                    return_to_difficulty_selection()
                    continue

                if hints_enabled_for_difficulty(current_difficulty) and hint_button_contains(*event.pos):
                    if board.reveal_hint() is not None:
                        hint_penalty_seconds += HINT_PENALTY_SECONDS
                        hint_feedback_start_ticks = pygame.time.get_ticks()
                    finish_if_complete()
                    continue

                clicked = board.click(*event.pos)
                if clicked is not None:
                    board.select(*clicked)
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_BACKSPACE, pygame.K_DELETE):
                    board.clear()
                    finish_if_complete()
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if board.selected is not None:
                        row, col = board.selected
                        value = board.cells[row][col].sketched_value
                        if value != 0:
                            board.place_number(value)
                        finish_if_complete()
                else:
                    value = number_from_key(event)
                    if value is not None:
                        apply_number_input(board, value)
                        finish_if_complete()

        if state == STATE_LOADING:
            if frame_count % loading_frame_delay == 0:
                loading_animation.advance()
            frame_count += 1
            draw_loading_screen(surface, loading_animation)
            if loading_animation.is_complete():
                state = STATE_DIFFICULTY
        elif state == STATE_DIFFICULTY:
            difficulty_hover_progress = update_difficulty_hover_progress(
                difficulty_hover_progress,
                pygame.mouse.get_pos(),
            )
            draw_difficulty_prompt(surface, difficulty_hover_progress)
        elif board is not None:
            if completed_elapsed_seconds is None:
                base_elapsed_seconds = (pygame.time.get_ticks() - game_start_ticks) // 1000
                elapsed_seconds = elapsed_with_hint_penalty(base_elapsed_seconds, hint_penalty_seconds)
            else:
                elapsed_seconds = completed_elapsed_seconds
            feedback_alpha = hint_feedback_alpha(hint_feedback_start_ticks, pygame.time.get_ticks())
            draw_game(
                surface,
                board,
                elapsed_seconds,
                leaderboard,
                hints_enabled_for_difficulty(current_difficulty),
                feedback_alpha,
                state == STATE_PLAYING,
            )
            if state == STATE_WIN:
                draw_win_screen(surface, elapsed_seconds, player_name)

        pygame.display.update()
        clock.tick(60)
        await asyncio.sleep(0)

    pygame.quit()  # closes game if running is False


if __name__ == "__main__":
    asyncio.run(main())
