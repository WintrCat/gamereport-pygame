import pygame
import chess
import engine
pygame.init()

coordFont: pygame.font.Font = pygame.font.SysFont("Arial", 16, bold=True)

alphabet = list("abcdefgh")

pieceMap = {
    "r": "blackrook",
    "n": "blackknight",
    "b": "blackbishop",
    "q": "blackqueen",
    "k": "blackking",
    "p": "blackpawn",
    "R": "whiterook",
    "N": "whiteknight",
    "B": "whitebishop",
    "Q": "whitequeen",
    "K": "whiteking",
    "P": "whitepawn",
}

classificationColours = {
    "brilliant": pygame.Color(27, 172, 167),
    "great": pygame.Color(92, 139, 176),
    "best": pygame.Color(151, 188, 74),
    "excellent": pygame.Color(151, 188, 74),
    "good": pygame.Color(151, 175, 138),
    "inaccuracy": pygame.Color(246, 193, 69),
    "mistake": pygame.Color(228, 142, 42),
    "blunder": pygame.Color(202, 52, 49),
    "forced": pygame.Color(151, 175, 138),
    "book": pygame.Color(168, 136, 101)
}

def reverse_list(arr: list):
    listcopy = arr.copy()
    listcopy.reverse()
    return listcopy

def flip_fen(fen: str) -> str:
    flipped_fen = ""
    for row in reverse_list(fen.split(" ")[0].split("/")):
        flipped_fen += "".join(reverse_list(list(row))) + "/"
    return flipped_fen[:-1]

# r4rk1/p3ppbp/2n3p1/8/3q2n1/N1N5/PPQ2PPP/R1B1K2R
def render(win: pygame.Surface, renderBoard: chess.Board, flipped: bool):
    fen = renderBoard.fen()

    # render board
    for y in range(8):
        for x in range(8):
            colour = "#c0a582" if (x + y) % 2 == 0 else "#7f5c41"
            pygame.draw.rect(win, colour, pygame.Rect(x * 80, y * 80, 80, 80))

    # render co-ordinates
    for y in range(8):
        num = (y + 1) if flipped else 8 - y
        colour = ["#7f5c41", "#c0a582"][y % 2]
        win.blit(coordFont.render(str(num), True, colour), (3, y * 80 + 3))
    for x in range(8):
        letter = alphabet[7 - x] if flipped else alphabet[x]
        colour = ["#c0a582", "#7f5c41"][x % 2]
        win.blit(coordFont.render(letter, True, colour), (x * 80 + 67, 621))

    # flip fen if desired
    if flipped:
        fen = flip_fen(fen)

    # if analysis complete, render classification highlight
    currentClassification = None
    currentMoveSquares = [None, None]
    if engine.get_results().complete and len(renderBoard.move_stack) > 0:
        # fetch current classification and move squares
        currentClassification = engine.get_results().classifications[len(renderBoard.move_stack) - 1]
        currentMoveSquares[0] = renderBoard.move_stack[-1].from_square
        currentMoveSquares[1] = renderBoard.move_stack[-1].to_square

        # make translucent surface and highlight both squares
        highlightSurface = pygame.Surface((640, 640))
        highlightSurface.set_colorkey((0, 0, 0))
        highlightSurface.set_alpha(175)
        for i in range(2):
            pygame.draw.rect(highlightSurface, classificationColours[currentClassification], pygame.Rect(
                ((7 - (currentMoveSquares[i] % 8)) * 80) if flipped else (currentMoveSquares[i] % 8) * 80, 
                ((currentMoveSquares[i] // 8) * 80) if flipped else ((63 - currentMoveSquares[i]) // 8) * 80, 
                80,
                80
            ))
        win.blit(highlightSurface, (0, 0))

    # render pieces
    x = 0
    y = 0
    for fenc in list(fen.split(" ")[0]):
        if fenc == "/":
            y += 1
            x = 0
        elif fenc.isdigit():
            x += int(fenc)
        else:
            win.blit(pygame.image.load(f"assets/{pieceMap[fenc]}.png"), (x * 80, y * 80))
            x += 1

    # draw classification icon onto piece
    if currentClassification != None:
        win.blit(
            pygame.image.load(f"assets/{currentClassification}.png"),
            (
                ((7 - (currentMoveSquares[1] % 8)) * 80 + 58) if flipped else (currentMoveSquares[1] % 8) * 80 + 58, 
                ((currentMoveSquares[1] // 8) * 80 - 10) if flipped else ((63 - currentMoveSquares[1]) // 8) * 80 - 10, 
            )
        )

def play_move_sound(renderBoard: chess.Board):
    if len(renderBoard.move_stack) == 0: return

    if renderBoard.is_checkmate():
        pygame.mixer.Sound("assets/checkmate.wav").play()
    elif renderBoard.is_check():
        pygame.mixer.Sound("assets/check.wav").play()
    elif "x" in engine.get_results().sans[len(renderBoard.move_stack) - 1]:
        pygame.mixer.Sound("assets/capture.wav").play()
    else:
        pygame.mixer.Sound("assets/normal.wav").play()
