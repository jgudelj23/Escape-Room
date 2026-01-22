from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class Pos:
    x: int
    y: int

@dataclass(frozen=True, slots=True)
class Tile:
    walkable: bool

WALL = Tile(False)
FLOOR = Tile(True)
