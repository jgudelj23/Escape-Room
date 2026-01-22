from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar, Iterable

@dataclass(frozen=True, slots=True)
class Pos:
    x: int
    y: int

@dataclass(frozen=True, slots=True)
class Tile:
    walkable: bool

WALL = Tile(False)
FLOOR = Tile(True)

class MapBuilder:
    def __init__(self, w: int, h: int):
        self.w, self.h = w, h
        self.walkable: set[Pos] = set()

    def add(self, p: Pos) -> None:
        if 0 <= p.x < self.w and 0 <= p.y < self.h:
            self.walkable.add(p)

    def add_cells(self, *cells: Pos):
        for c in cells:
            self.add(c)
        return self

    def add_vertical(self, x: int, y0: int, y1: int):
        for y in range(y0, y1 + 1):
            self.add(Pos(x, y))
        return self

    def add_horizontal(self, y: int, x0: int, x1: int):
        for x in range(x0, x1 + 1):
            self.add(Pos(x, y))
        return self

class GameMap:
    def __init__(self, w: int, h: int, walkable: set[Pos]):
        self.w, self.h = w, h
        self.walkable = walkable

    def tile_at(self, p: Pos) -> Tile:
        return FLOOR if p in self.walkable else WALL

    def in_bounds(self, p: Pos) -> bool:
        return 0 <= p.x < self.w and 0 <= p.y < self.h
def build_walkable() -> set[Pos]:
    W, H = 11, 17
    b = MapBuilder(W, H)

    b.add_vertical(5, 0, 2)
    b.add_horizontal(3, 2, 7)
    b.add_vertical(2, 3, 7)
    b.add_vertical(7, 3, 5)
    b.add_vertical(6, 5, 7)
    b.add_horizontal(5, 6, 9)
    b.add_vertical(9, 5, 12)

    b.add_horizontal(7, 0, 4)
    b.add_vertical(0, 7, 10)
    b.add_vertical(4, 7, 10)
    b.add_cells(Pos(6, 7), Pos(9, 7))

    b.add_vertical(3, 10, 13)
    b.add_horizontal(12, 3, 5)
    b.add_vertical(5, 12, 13)

    b.add_horizontal(12, 7, 10)
    b.add_vertical(10, 12, 15)
    b.add_vertical(7, 12, 16)
    b.add_horizontal(15, 7, 10)

    return b.walkable
class Feature:
    sprite_key: ClassVar[str] = ""
    def __init__(self, pos: Pos):
        self.pos = pos

class Player(Feature):   sprite_key = "igrac"
class Door(Feature):     sprite_key = "vrata"
class Key(Feature):      sprite_key = "kljuc"
class Axe(Feature):      sprite_key = "sjekira"
class Terminal(Feature): sprite_key = "terminal"
class Bars(Feature):     sprite_key = "resetke"
class Paper(Feature):    sprite_key = "papir"
class Exit(Feature):     sprite_key = "zastava"
class Tree(Feature):     sprite_key = "drvo"
