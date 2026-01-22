import pygame

pygame.init()

CELL = 40
W, H = 11, 17

screen = pygame.display.set_mode((W * CELL, H * CELL))
pygame.display.set_caption("Escape Room")
clock = pygame.time.Clock()

running = True
while running:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

    screen.fill((0, 0, 0))
    pygame.display.flip()
    clock.tick(60)

pygame.quit()