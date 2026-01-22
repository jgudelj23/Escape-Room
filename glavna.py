import pygame
from pathlib import Path
from razine import Pos, GameMap, build_walkable, build_level

pygame.init()

CELL = 40
W, H = 11, 17

screen = pygame.display.set_mode((W * CELL, H * CELL))
pygame.display.set_caption("Escape Room")
clock = pygame.time.Clock()

COLOR_WALK = (255, 255, 255)
COLOR_WALL = (55, 55, 55)
GRID_COLOR = (0, 0, 0)

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

def draw_tiles():
    for y in range(H):
        for x in range(W):
            p = Pos(x, y)
            color = COLOR_WALK if game_map.tile_at(p).walkable else COLOR_WALL
            r = pygame.Rect(x * CELL, y * CELL, CELL, CELL)
            pygame.draw.rect(screen, color, r)
            pygame.draw.rect(screen, GRID_COLOR, r, 1)

running = True
while running:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

    draw_tiles()

    if sea_big:
        screen.blit(sea_big, (sea.top_left.x * CELL, sea.top_left.y * CELL))

    for f in features:
        blit_cell(f.sprite_key, f.pos)
    blit_cell("igrac", player.pos)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
