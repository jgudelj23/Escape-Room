import random
import pygame
from pathlib import Path
from collections import deque

from razine import (
    Pos, GameMap, build_walkable, build_level,
    Feature, Door, Key, Axe, Paper, Tree, Exit, Terminal, Bars
)

pygame.init()

CELL = 40
W, H = 11, 17
SECRET_CODE = "2004"

COLOR_WALK = (255, 255, 255)
COLOR_WALL = (55, 55, 55)
GRID_COLOR = (0, 0, 0)

MODE_PLAY, MODE_PAPER, MODE_CODE, MODE_EXIT = "play", "paper", "code", "exit"
AUTO_STEP_MS = 70
AUTO_CODE_STEP_MS = 260
DIRS4 = [(-1, 0), (1, 0), (0, -1), (0, 1)]
INF = 10**9

screen = pygame.display.set_mode((W * CELL, H * CELL))
pygame.display.set_caption("Escape Room")
clock = pygame.time.Clock()

class Popup:
    def __init__(self):
        self.text = ""
        self.until = 0
        self.font = pygame.font.SysFont(None, 26)

    def show(self, text: str, ms: int = 1700):
        self.text = text
        self.until = pygame.time.get_ticks() + ms

    def draw(self, surf: pygame.Surface):
        if not (self.text and pygame.time.get_ticks() < self.until):
            return
        pad = 12
        txt = self.font.render(self.text, True, (255, 255, 255))
        w, h = txt.get_width() + pad * 2, txt.get_height() + pad * 2
        x, y = (surf.get_width() - w) // 2, 10
        r = pygame.Rect(x, y, w, h)
        pygame.draw.rect(surf, (20, 20, 20), r, border_radius=10)
        pygame.draw.rect(surf, (255, 255, 255), r, 2, border_radius=10)
        surf.blit(txt, (x + pad, y + pad))

popup = Popup()

_fonts = {}
def F(size: int):
    if size not in _fonts:
        _fonts[size] = pygame.font.SysFont(None, size)
    return _fonts[size]

asset_dir = Path(__file__).parent / "slike"

def load_sprite(name: str):
    fp = asset_dir / f"{name}.png"
    if not fp.exists():
        return None
    img = pygame.image.load(str(fp)).convert_alpha()
    return pygame.transform.smoothscale(img, (CELL, CELL))

def scale_sprite(surf, wc, hc):
    return None if surf is None else pygame.transform.smoothscale(surf, (CELL * wc, CELL * hc))

sprites = {k: load_sprite(k) for k in (
    "igrac", "vrata", "kljuc", "sjekira", "terminal", "resetke",
    "papir", "zastava", "drvo", "voda", "most"
)}

paper_original = None
pp = asset_dir / "papir.png"
if pp.exists():
    paper_original = pygame.image.load(str(pp)).convert_alpha()

def blit_cell(key: str, p: Pos):
    spr = sprites.get(key)
    if spr:
        screen.blit(spr, (p.x * CELL, p.y * CELL))

walkable = build_walkable()
game_map = GameMap(W, H, walkable)
player, features, sea, start_pos = build_level()

sea_big = scale_sprite(sprites.get("voda"), sea.width_cells, sea.height_cells)
bridge_big = scale_sprite(sprites.get("most"), sea.width_cells, sea.height_cells)

feat_at = {f.pos: f for f in features}
def remove_feature(f: Feature):
    if f in features:
        features.remove(f)
        feat_at.pop(f.pos, None)

has_key = has_axe = has_wood = has_paper = False
bridge_built = terminal_unlocked = False
mode = MODE_PLAY
code_input = ""

exit_start_ms = 0
confetti = []
game_finished = False

graf = {}
for p in walkable:
    graf[p] = [Pos(p.x + dx, p.y + dy) for dx, dy in DIRS4 if Pos(p.x + dx, p.y + dy) in walkable]

def try_collect():
    global has_paper, mode
    if game_finished:
        return
    f = feat_at.get(player.pos)
    if isinstance(f, Paper):
        has_paper = True
        remove_feature(f)
        mode = MODE_PAPER

def draw_dim(alpha=190):
    s = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    s.fill((0, 0, 0, alpha))
    screen.blit(s, (0, 0))

def draw_tiles():
    for y in range(H):
        for x in range(W):
            p = Pos(x, y)
            color = COLOR_WALK if game_map.tile_at(p).walkable else COLOR_WALL
            r = pygame.Rect(x * CELL, y * CELL, CELL, CELL)
            pygame.draw.rect(screen, color, r)
            pygame.draw.rect(screen, GRID_COLOR, r, 1)

def draw_paper():
    draw_dim()
    sw, sh = screen.get_size()
    if paper_original is None:
        screen.blit(F(26).render("papir.png nije pronađen", True, (255, 255, 255)), (20, 20))
        return
    iw, ih = paper_original.get_size()
    sc = min((sw * 0.92) / iw, (sh * 0.92) / ih)
    nw, nh = int(iw * sc), int(ih * sc)
    big = pygame.transform.scale(paper_original, (nw, nh))
    screen.blit(big, ((sw - nw) // 2, (sh - nh) // 2))
    screen.blit(F(26).render("SPACE/ENTER/ESC za zatvoriti", True, (255, 255, 255)), (20, sh - 30))

def move(dx: int, dy: int):
    if mode != MODE_PLAY or game_finished:
        return
    np = Pos(player.pos.x + dx, player.pos.y + dy)
    if not game_map.in_bounds(np):
        return
    if not game_map.tile_at(np).walkable:
        return
    player.pos = np
    try_collect()

try_collect()

running = True
while running:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
            break

        if e.type != pygame.KEYDOWN:
            continue

        if e.key == pygame.K_ESCAPE:
            if mode == MODE_PAPER:
                mode = MODE_PLAY
            else:
                running = False
            continue

        if game_finished:
            continue

        if mode == MODE_PAPER:
            if e.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
                mode = MODE_PLAY
            continue

        if mode == MODE_PLAY:
            if e.key in (pygame.K_w, pygame.K_UP):
                move(0, -1)
            elif e.key in (pygame.K_s, pygame.K_DOWN):
                move(0, 1)
            elif e.key in (pygame.K_a, pygame.K_LEFT):
                move(-1, 0)
            elif e.key in (pygame.K_d, pygame.K_RIGHT):
                move(1, 0)

    draw_tiles()

    img = bridge_big if bridge_built else sea_big
    if img:
        screen.blit(img, (sea.top_left.x * CELL, sea.top_left.y * CELL))

    for f in features:
        blit_cell(f.sprite_key, f.pos)
    blit_cell("igrac", player.pos)

    if mode == MODE_PAPER:
        draw_paper()

    popup.draw(screen)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
