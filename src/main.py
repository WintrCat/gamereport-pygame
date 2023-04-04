import chess
import pygame
from time import sleep

import board
import engine
import inputlib

pygame.init()

# initialise window and graphics
win = pygame.display.set_mode((960, 640))

pygame.display.set_caption("WintrCat's Game Report")
pygame.display.set_icon(pygame.image.load("assets/icon.png"))

font: pygame.font.Font = pygame.font.SysFont("Arial", 24)

# setup virtual board for rendering
renderBoard = chess.Board()
renderBoardFlipped = False

# begin analysis of pgn in new thread
engine.startAnalysisThread()

# main loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            exit()

        # CHECK FOR MOUSE PRESSES and KEY PRESSES
        if event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.KEYDOWN:
            if engine.get_analysis_results().complete:
                try:
                    # back to start
                    if (
                        (inputlib.is_mouse_over(650, 700, 595, 640) and inputlib.is_mouse_down(0))
                        or
                        inputlib.is_key_down(pygame.K_DOWN)
                    ):
                        renderBoard.reset()
                    
                    # back one move
                    if (
                        inputlib.is_mouse_over(700, 750, 595, 640) and inputlib.is_mouse_down(0)
                        or
                        inputlib.is_key_down(pygame.K_LEFT)
                    ):
                        renderBoard.pop()
                        board.play_move_sound(renderBoard)

                    # forward one move
                    if (
                        inputlib.is_mouse_over(750, 800, 595, 640) and inputlib.is_mouse_down(0)
                        or
                        inputlib.is_key_down(pygame.K_RIGHT)
                    ):
                        renderBoard.push_uci(
                            engine.get_analysis_results().board.move_stack[len(renderBoard.move_stack)].uci()
                        )
                        board.play_move_sound(renderBoard)

                    # go to end
                    if (
                        inputlib.is_mouse_over(800, 850, 595, 640) and inputlib.is_mouse_down(0)
                        or
                        inputlib.is_key_down(pygame.K_UP)
                    ):
                        renderBoard.reset()
                        for move in engine.get_analysis_results().board.move_stack:
                            renderBoard.push_uci(move.uci())
                except IndexError as err:
                    print(err)

            # flip board button (analysis doesn't have to be complete)
            if inputlib.is_mouse_over(850, 900, 595, 640) and inputlib.is_mouse_down(0):
                renderBoardFlipped = not renderBoardFlipped

    # render background
    pygame.draw.rect(win, pygame.Color(41,41,41), pygame.Rect(0, 0, 960, 640))

    # render board, pieces & move classification & arrows
    board.render(win, renderBoard, renderBoardFlipped)

    if engine.get_analysis_results().complete and len(renderBoard.move_stack) > 0:
        __import__("os", "system").system("cls")
        print(engine.get_analysis_results().classifications[len(renderBoard.move_stack) - 1])
        print(engine.get_analysis_results().evals[len(renderBoard.move_stack)])
        print(engine.get_analysis_results().topMoves[len(renderBoard.move_stack)])
        print(engine.get_analysis_results().topMoves[48])

    # render analysis loading bar or eval bar depending on analysis completion
    progress = engine.get_analysis_progress()
    pygame.draw.rect(win, "#1b1b1b", pygame.Rect(650, 10, 300, 50))
    
    if engine.get_analysis_results().complete:
        pygame.draw.rect(win, "#0c0c0c", pygame.Rect(654, 14, 292, 42))

        evaluation = engine.get_analysis_results().evals[len(renderBoard.move_stack)]

        # calc length of white portion of eval bar
        evalLength = 0
        if evaluation["type"] == "cp":
            evalLength = min(292, evaluation["value"] * 0.122 + 146)
        elif renderBoard.is_checkmate():
            if len(renderBoard.move_stack) % 2 == 0:
                evalLength = 0
            else:
                evalLength = 292
        else:
            evalLength = 0 if evaluation["value"] < 0 else 292
        pygame.draw.rect(win, "#f5f5f5", pygame.Rect(654, 14, evalLength, 42))

        # draw text for evaluation value
        if evaluation["type"] == "cp":
            evaluationString = None
            if evaluation["value"] > 0:
                evaluationString = "+" + str(evaluation["value"] / 100)
            elif evaluation["value"] == 0:
                evaluationString = "0.00"
            else:
                evaluationString = str(evaluation["value"] / 100)
            win.blit(font.render(evaluationString, True, "#ffffff"), (650, 60))
        elif renderBoard.is_checkmate():
            win.blit(font.render("Checkmate", True, "#ffffff"), (650, 60))
        else:
            win.blit(font.render("Mate in " + str(abs(evaluation["value"])), True, "#ffffff"), (650, 60))
    else:
        pygame.draw.rect(win, "#2cff4f", pygame.Rect(654, 14, (progress[0] / progress[1]) * 292, 42))
        if progress[2]:
            win.blit(font.render(f"Analysing {progress[0]}/{progress[1]} moves...", True, "#ffffff"), (650, 60))
        else:
            win.blit(font.render(f"Initializing Analysis...", True, "#ffffff"), (650, 60))

    # render move traversal & flip board button
    win.blit(pygame.image.load("assets/backToStart.png"), (650, 595))
    win.blit(pygame.image.load("assets/back.png"), (700, 595))
    win.blit(pygame.image.load("assets/next.png"), (750, 595))
    win.blit(pygame.image.load("assets/goToEnd.png"), (800, 595))
    win.blit(pygame.image.load("assets/flip.png"), (850, 595))

    # update display and wait for next frame
    pygame.display.update()
    sleep(0.05)