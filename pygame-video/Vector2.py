from __future__ import annotations
from typing import Iterable, Union
import pygame

class Vector2(pygame.math.Vector2):
    def __init__(self, x: Union[int, float] = None, y: Union[int, float] = None):
        """
        A Vector2 class that inherits from pygame.math.Vector2

        You can create one by passing in two numbers, or a tuple of two numbers.
        """

        if not y == None:
            super().__init__(x, y) # its not a tuple

        elif isinstance(x, tuple):
            super().__init__(x[0], x[1]) # its a tuple

        elif isinstance(x, int) or isinstance(x, float):
            super().__init__(x, x) # its a single number

        elif x is None:
            super().__init__(0, 0)

    def __tuple__(self):
        return (self[0], self[1])

    def __list__(self):
        return [self[0], self[1]]

    def __abs__(self):
        return Vector2(abs(self[0]), abs(self[1]))

    def to_int(self):
        return Vector2(int(self[0]), int(self[1]))

    def copy(self):
        return Vector2(self[0], self[1])

    def __round__(self, i):
        return Vector2(round(self[0], i), round(self[1], i))

    def __imul__(self, other: Union[Vector2, tuple[float, float]]):
        if not isinstance(other, Iterable):
            other = (other, other)
        self[0] *= other[0]
        self[1] *= other[1]
        return Vector2(self[0], self[1])

    def __mul__(self, other: Union[Vector2, tuple[float, float]]):
        if not isinstance(other, Iterable):
            other = (other, other)
        return Vector2(self[0] * other[0], self[1] * other[1])

    def __isub__(self, other: Union[Vector2, tuple[float, float]]):
        if not isinstance(other, Iterable):
            other = (other, other)
        self[0] -= other[0]
        self[1] -= other[1]
        return Vector2(self[0], self[1])

    def __sub__(self, other: Union[Vector2, tuple[float, float]]):
        if not isinstance(other, Iterable):
            other = (other, other)
        return Vector2(self[0] - other[0], self[1] - other[1])

    def __iadd__(self, other: Union[Vector2, tuple[float, float]]):
        if not isinstance(other, Iterable):
            other = (other, other)
        self[0] += other[0]
        self[1] += other[1]
        return Vector2(self[0], self[1])

    def __add__(self, other: Union[Vector2, tuple[float, float]]):
        if not isinstance(other, Iterable):
            other = (other, other)
        return Vector2(self[0] + other[0], self[1] + other[1])

    def __itruediv__(self, other: Union[Vector2, tuple[float, float]]):
        if not isinstance(other, Iterable):
            other = (other, other)
        self[0] /= other[0]
        self[1] /= other[1]
        return Vector2(self[0], self[1])

    def __truediv__(self, other: Union[Vector2, tuple[float, float]]):
        if not isinstance(other, Iterable):
            other = (other, other)
        return Vector2(self[0] / other[0], self[1] / other[1])

    def __ifloordiv__(self, other: Union[Vector2, tuple[float, float]]):
        if not isinstance(other, Iterable):
            other = (other, other)
        self[0] //= other[0]
        self[1] //= other[1]
        return Vector2(self[0], self[1])

    def __floordiv__(self, other: Union[Vector2, tuple[float, float]]):
        if not isinstance(other, Iterable):
            other = (other, other)
        return Vector2(int(self[0] // other[0]), int(self[1] // other[1]))

    def __mod__(self, other: Union[Vector2, tuple[float, float]]):
        if not isinstance(other, Iterable):
            other = (other, other)
        return Vector2(self[0] % other[0], self[1] % other[1])

    def __imod__(self, other: Union[Vector2, tuple[float, float]]):
        if not isinstance(other, Iterable):
            other = (other, other)
        self[0] %= other[0]
        self[1] %= other[1]
        return Vector2(self[0], self[1])

    def __pow__(self, other: Union[Vector2, tuple[float, float]]):
        if not isinstance(other, Iterable):
            other = (other, other)
        return Vector2(self[0] ** other[0], self[1] ** other[1])

    def __ipow__(self, other: Union[Vector2, tuple[float, float]]):
        if not isinstance(other, Iterable):
            other = (other, other)
        self[0] **= other[0]
        self[1] **= other[1]
        return Vector2(self[0], self[1])

    def __lt__(self, other: Union[Vector2, tuple[float, float]]):
        if not isinstance(other, Iterable):
            other = (other, other)
        return self[0] < other[0] and self[1] < other[1]

    def __le__(self, other: Union[Vector2, tuple[float, float]]):
        if not isinstance(other, Iterable):
            other = (other, other)
        return self[0] <= other[0] and self[1] <= other[1]

    def __eq__(self, other: Union[Vector2, tuple[float, float]]):
        if not isinstance(other, Iterable):
            other = (other, other)
        return self[0] == other[0] and self[1] == other[1]

    def __ne__(self, other: Union[Vector2, tuple[float, float]]):
        if not isinstance(other, Iterable):
            other = (other, other)
        return self[0] != other[0] and self[1] != other[1]

    def __ge__(self, other: Union[Vector2, tuple[float, float]]):
        if not isinstance(other, Iterable):
            other = (other, other)
        return self[0] >= other[0] and self[1] >= other[1]

    def __gt__(self, other: Union[Vector2, tuple[float, float]]):
        if not isinstance(other, Iterable):
            other = (other, other)
        return self[0] > other[0] and self[1] > other[1]

    def get_average(values: Iterable[Union[Vector2, tuple[int, int]]]):
        total = Vector2(0, 0)
        for val in values:
            total += val

        return total / Vector2(len(values), len(values))

    def sum(values: Iterable[Union[Vector2, tuple[int, int]]]):
        total = Vector2(0, 0)
        for val in values:
            total += val

        return total