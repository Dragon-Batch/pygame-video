from .Vector2 import Vector2
from typing import Union
import pygame

class Character:
    def __init__(self, symbol: str, surface: pygame.Surface):
        self.symbol = symbol
        self.size = Vector2(surface.get_size())
        self.surface = surface
        self.rect = surface.get_rect()

class Font:
    def __init__(
        self,
        font_name: str,
        font_size: int,
        foreground_color: pygame.Color = pygame.Color(255, 255, 255),
        background_color: pygame.Color = pygame.Color(0, 0, 0),
        bold: bool = False,
        italic: bool = False,
        antialias: bool = True,
        colorkey_foreground: bool = False,
        colorkey_background: bool = True,
    ):
        self.foreground_color = foreground_color
        self.background_color = background_color

        self.colorkey_foreground = colorkey_foreground
        self.colorkey_background = colorkey_background

        self.bold = bold
        self.italic = italic
        self.antialias = antialias

        self.font_name = font_name
        self.font_size = font_size

        self.FONT = pygame.font.SysFont(font_name, font_size, bold, italic)
        # this characters dict is a dict of all the characters that have been generated
        self.characters: dict[str, Character] = {}

        # we are generating the space character here so we can get the font height
        self.generate_character(" ")
        self.font_height = self.characters.get(" ").size.y

    def generate_character(self, symbol: str):
        try: surface = self.FONT.render(symbol, self.antialias, self.foreground_color, self.background_color)
        except: surface = self.FONT.render(" ", self.antialias, self.foreground_color, self.background_color)

        char = Character(symbol, surface)
        self.characters[symbol] = char

    def create_rows_from_text(self, text: str, width: int = -1, xstart: int = None):
        if xstart is None:
            xstart = 0

        text_rows: list[list[Character]] = [[]]
        current_position = Vector2(xstart, 0)

        for symbol in text:
            if not symbol in self.characters:
                self.generate_character(symbol)

            char = self.characters.get(symbol)

            if width != -1:
                if current_position.x + char.rect.w >= width:
                    if symbol not in ["\r", "\n"]:
                        text_rows.append([])
                    current_position.x = 0
                    current_position.y += self.font_height

            if symbol in ["\r", "\n"]:
                text_rows.append([])
                current_position.x = 0
                current_position.y += self.font_height

            else:
                text_rows[-1].append(char)
                current_position.x += char.rect.w

        return text_rows

    def get_size_from_rows(self, rows: list[list[Character]], width: int = -1):
        largest_size = 0

        for collum in rows:
            collum_size = sum([char.rect.width for char in collum])
            if collum_size > largest_size:
                largest_size = collum_size

        return Vector2(
            min(width, largest_size) if not width == -1 else largest_size,
            len(rows) * self.font_height
        )

    def render_max_size(self, text: str, size: Vector2, start: Vector2 = None):
        if start is None:
            start = Vector2

        text_rows: list[list[Character]] = self.create_rows_from_text(text, size.x, start.x)

        total_font_size = self.get_size_from_rows(text_rows, size.x)

        current_position = start
        output_surface = pygame.Surface(size + start)

        if self.colorkey_foreground:
            output_surface.set_colorkey(self.foreground_color)

        if self.colorkey_background:
            output_surface.set_colorkey(self.background_color)

        for i, row in enumerate(text_rows):
            for char in row:
                output_surface.blit(char.surface, current_position)
                current_position.x += char.rect.w

            if i < len(text_rows) - 1:
                current_position.x = 0
                current_position.y += self.font_height

        return output_surface, current_position

    def render_max_width(self, text: str, width: int = -1, start: Vector2 = None):
        if start is None:
            start = Vector2(0, 0)

        text_rows: list[list[Character]] = self.create_rows_from_text(text, width, start.x)

        total_font_size = self.get_size_from_rows(text_rows, width)
        total_font_size += start
        current_position = start
        output_surface = pygame.Surface(total_font_size)

        if self.colorkey_foreground:
            output_surface.set_colorkey(self.foreground_color)

        if self.colorkey_background:
            output_surface.set_colorkey(self.background_color)

        for i, row in enumerate(text_rows):
            for char in row:
                output_surface.blit(char.surface, current_position)
                current_position.x += char.rect.w

            if i < len(text_rows) - 1:
                current_position.x = 0
                current_position.y += self.font_height

        return output_surface, current_position