import pygame
from time import sleep

import board
import engine

pygame.init()

# initialise window
win = pygame.display.set_mode((960, 640))

pygame.display.set_caption("WintrCat's Game Report")
pygame.display.set_icon(pygame.image.load("assets/icon.png"))

# begin analysis of pgn in new thread
engine.startAnalysisThread()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()

    # render background
    pygame.draw.rect(win, pygame.Color(41,41,41), pygame.Rect(0, 0, 960, 640))

    # render board
    board.render(win, engine.get_fen())

    pygame.display.update()
    sleep(0.05)