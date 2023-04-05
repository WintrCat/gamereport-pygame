import pickle
import chess
import pygame
from time import sleep

import board
import engine
import inputlib
import args

pygame.init()

# initialise window and graphics
win = pygame.display.set_mode((960, 640))

pygame.display.set_caption("WintrCat's Game Report")
pygame.display.set_icon(pygame.image.load("assets/icon.png"))

font: pygame.font.Font = pygame.font.SysFont("Arial", 24)
smallerFont: pygame.font.Font = pygame.font.SysFont("Arial", 10)

# setup virtual board for rendering
renderBoard = chess.Board()
renderBoardFlipped = False

# parse command line arguments
# analysis thread only started if savefile was NOT specified
# thread starts in args module
args.parseArguments()

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

                    # save analysis
                    if (
                        (inputlib.is_mouse_over(900, 950, 595, 640) and inputlib.is_mouse_down(0))
                        or
                        (inputlib.is_key_down(pygame.K_LCTRL) and inputlib.is_key_down(pygame.K_s))
                    ):
                        pickle.dump(engine.get_analysis_results(), open("save.asys", "wb"))

                except:
                    pass

            # flip board button (analysis doesn't have to be complete)
            if inputlib.is_mouse_over(850, 900, 595, 640) and inputlib.is_mouse_down(0):
                renderBoardFlipped = not renderBoardFlipped

    # render background
    pygame.draw.rect(win, pygame.Color(41,41,41), pygame.Rect(0, 0, 960, 640))

    # render board, pieces & move classification & arrows
    board.render(win, renderBoard, renderBoardFlipped)

    # render analysis loading bar or eval bar depending on analysis completion
    progress = engine.get_analysis_progress()
    pygame.draw.rect(win, "#1b1b1b", pygame.Rect(650, 10, 300, 50))
    
    if engine.get_analysis_results().complete:
        pygame.draw.rect(win, "#0c0c0c", pygame.Rect(654, 14, 292, 42))

        evaluation = engine.get_analysis_results().evals[len(renderBoard.move_stack)]

        # calc length of white portion of eval bar and draw it
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

        # render played move and classification text
        if len(renderBoard.move_stack) > 0:
            classificationText = "unknown"
            currentClassification = engine.get_analysis_results().classifications[len(renderBoard.move_stack) - 1]

            if currentClassification == "forced":
                classificationText = "forced"
            elif currentClassification == "blunder":
                classificationText = "a blunder"
            elif currentClassification == "mistake":
                classificationText = "a mistake"
            elif currentClassification == "inaccuracy":
                classificationText = "an inaccuracy"
            elif currentClassification == "good":
                classificationText = "good"
            elif currentClassification == "excellent":
                classificationText = "excellent"
            elif currentClassification == "best":
                classificationText = "best"
            elif currentClassification == "book":
                classificationText = "book theory"

            win.blit(
                font.render(
                    engine.get_analysis_results().sanMoves[len(renderBoard.move_stack) - 1] + " is " + classificationText, 
                    True, 
                    board.classificationColours[currentClassification]
                ), (650, 84)
            )

        # render top engine moves text
        for i, move in enumerate(engine.get_analysis_results().topMoves[len(renderBoard.move_stack)]):
            # get polarity string because '+' not included
            centipawnPolarity = ""
            if move["Centipawn"] != None and move["Centipawn"] > 0:
                centipawnPolarity = "+"

            # get SAN from UCI
            moveSan = renderBoard.san(chess.Move.from_uci(move["Move"]))

            win.blit(
                font.render(
                    f"{moveSan} > {centipawnPolarity}{(move['Centipawn'] / 100) if move['Centipawn'] != None else 'M' + str(abs(move['Mate']))}",
                    True,
                    "#ffffff"
                ), (650, 108 + i * 24)
            )

        # render save button (only exists when analysis is complete)
        win.blit(
            pygame.image.load("assets/save.png"),
            (900, 595)
        )

        # render opening name
        openings = engine.get_analysis_results().openings
        win.blit(
            smallerFont.render(
                openings[min(len(renderBoard.move_stack) - 1, len(openings) - 1)] 
                if len(renderBoard.move_stack) > 0 
                else "Starting Position",
                True,
                "#ffffff"
            ), (650, 580)
        )
            
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