import pygame
from pathlib import Path
from razine import Pos, GameMap, build_walkable, build_level, Key

pygame.init()

CELL = 40
W, H = 11, 17

screen = pygame.display.set_mode((W * CELL, H * CELL))
pygame.display.set_caption("Escape Room")
clock = pygame.time.Clock()

COLOR_WALK = (255, 255, 255)
COLOR_WALL = (55, 55, 55)
GRID_COLOR = (0, 0, 0)

class Popup:
    def __init__(self):
        self.text = ""
        self.until = 0
        self.font = pygame.font.SysFont(None, 26)

    def show(self, text, ms=1700):
        self.text = text
        self.until = pygame.time.get_ticks() + ms

    def draw(self, surf):
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

asset_dir = Path(__file__).parent / "slike"

def load_sprite(name):
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

def blit_cell(key, p: Pos):
    spr = sprites.get(key)
    if spr:
        screen.blit(spr, (p.x * CELL, p.y * CELL))

walkable = build_walkable()
game_map = GameMap(W, H, walkable)
player, features, sea, start_pos = build_level()

sea_big = scale_sprite(sprites.get("voda"), sea.width_cells, sea.height_cells)

has_key = False

def draw_tiles():
    for y in range(H):
        for x in range(W):
            p = Pos(x, y)
            color = COLOR_WALK if game_map.tile_at(p).walkable else COLOR_WALL
            r = pygame.Rect(x * CELL, y * CELL, CELL, CELL)
            pygame.draw.rect(screen, color, r)
            pygame.draw.rect(screen, GRID_COLOR, r, 1)

def try_collect():
    global has_key
    for f in features[:]:
        if f.pos == player.pos and isinstance(f, Key):
            features.remove(f)
            has_key = True
            popup.show("Uzeo si ključ")

def move(dx, dy):
    np = Pos(player.pos.x + dx, player.pos.y + dy)
    if not game_map.in_bounds(np):
        return
    if not game_map.tile_at(np).walkable:
        popup.show("Ne možeš proći")
        return
    player.pos = np
    try_collect()

running = True
while running:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
        elif e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_w, pygame.K_UP):
                move(0, -1)
            elif e.key in (pygame.K_s, pygame.K_DOWN):
                move(0, 1)
            elif e.key in (pygame.K_a, pygame.K_LEFT):
                move(-1, 0)
            elif e.key in (pygame.K_d, pygame.K_RIGHT):
                move(1, 0)

    draw_tiles()

    if sea_big:
        screen.blit(sea_big, (sea.top_left.x * CELL, sea.top_left.y * CELL))

    for f in features:
        blit_cell(f.sprite_key, f.pos)
    blit_cell("igrac", player.pos)

    popup.draw(screen)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
