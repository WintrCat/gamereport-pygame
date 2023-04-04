import pygame

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

def render(win: pygame.Surface, fen: str):
    for y in range(8):
        for x in range(8):
            colour = "#c0a582" if (x + y) % 2 == 0 else "#7f5c41"
            pygame.draw.rect(win, colour, pygame.Rect(x * 80, y * 80, 80, 80))

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
