import pygame
from razine import Pos, GameMap, build_walkable

pygame.init()

CELL = 40
W, H = 11, 17

screen = pygame.display.set_mode((W * CELL, H * CELL))
pygame.display.set_caption("Escape Room")
clock = pygame.time.Clock()

COLOR_WALK = (255, 255, 255)
COLOR_WALL = (55, 55, 55)
GRID_COLOR = (0, 0, 0)

walkable = build_walkable()
game_map = GameMap(W, H, walkable)

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
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
