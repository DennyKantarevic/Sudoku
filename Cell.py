import pygame
from constants import *

class Cell:
    def __init__(self, value, row, col, screen, fixed=False, y_offset=0, x_offset=0):
        """Constructor for the Cell class"""
        self.value = value
        self.row = row
        self.col = col
        self.screen = screen
        self.sketched_value = 0
        self.fixed = fixed
        self.is_hint = False
        self.selected = False
        self.y_offset = y_offset
        self.x_offset = x_offset

    def set_cell_value(self, value):
        """Setter for this cell’s value"""
        self.value = value

    def set_sketched_value(self, value):
        """Setter for this cell’s sketched value"""
        self.sketched_value = value

    def draw(self):
        """
        Draws this cell, along with the value inside it.
        If this cell has a nonzero value, that value is displayed.
        Otherwise, no value is displayed in the cell.
        The cell is outlined red if it is currently selected.
        """
        num_font = pygame.font.Font(None, NUM_FONT)
        sketch_font = pygame.font.Font(None, SKETCH_FONT)
        x = self.col * BLOCK_SIZE + self.x_offset
        y = self.row * BLOCK_SIZE + self.y_offset

        if self.value != 0:
            color = RED if self.is_hint else BLACK
            text = num_font.render(str(self.value), True, color)
            text_rect = text.get_rect(center=(x + BLOCK_SIZE / 2, y + BLOCK_SIZE / 2))
            self.screen.blit(text, text_rect)
        elif self.sketched_value != 0:
            text = sketch_font.render(str(self.sketched_value), True, BLACK)
            text_rect = text.get_rect(topleft=(x + 6, y + 4))
            self.screen.blit(text, text_rect)

        if self.selected:
            pygame.draw.rect(self.screen, RED, (x, y, BLOCK_SIZE, BLOCK_SIZE), 3)
