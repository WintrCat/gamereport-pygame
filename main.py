import pygame
from time import sleep

import board
import engine

pygame.init()

# initialise window and graphics
win = pygame.display.set_mode((960, 640))

pygame.display.set_caption("WintrCat's Game Report")
pygame.display.set_icon(pygame.image.load("assets/icon.png"))

font: pygame.font.Font = pygame.font.SysFont("Arial", 24)

# begin analysis of pgn in new thread
engine.startAnalysisThread()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()

    # render background
    pygame.draw.rect(win, pygame.Color(41,41,41), pygame.Rect(0, 0, 960, 640))

    # render board, pieces & move classification
    board.render(win, engine.get_fen())

    # render analysis loading bar
    progress = engine.get_analysis_progress()
    pygame.draw.rect(win, "#1b1b1b", pygame.Rect(650, 10, 300, 50))
    pygame.draw.rect(win, "#2cff4f", pygame.Rect(654, 14, (progress[0] / progress[1]) * 292, 42))
    win.blit(font.render(f"Analysing {progress[0]}/{progress[1]} moves...", True, "#ffffff"), (650, 60))

    pygame.display.update()
    sleep(0.05)