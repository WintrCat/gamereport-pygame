import pygame

def is_mouse_over(x1: int, x2: int, y1: int, y2: int) -> bool:
    pos = pygame.mouse.get_pos()
    return pos[0] >= x1 and pos[0] < x2 and pos[1] >= y1 and pos[1] < y2

def is_mouse_down(button: int) -> bool:
    return pygame.mouse.get_pressed()[button]

def is_key_down(key: int) -> bool:
    return pygame.key.get_pressed()[key]