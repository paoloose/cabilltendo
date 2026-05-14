#!/usr/bin/env python3
import os
os.environ['SDL_VIDEODRIVER'] = 'kmsdrm'
os.environ['SDL_AUDIODRIVER'] = 'alsa'
from os import path

import pygame
import time

SCRIPT_DIR = path.dirname(path.abspath(__file__))
BOOT_SOUND = os.environ.get('BOOT_SOUND', path.join(SCRIPT_DIR, 'assets', 'boot.ogg'))
LOGO_IMAGE = os.environ.get('LOGO_IMAGE', path.join(SCRIPT_DIR, 'assets', 'console_logo.png'))

def run():
    pygame.init()
    pygame.mouse.set_visible(False)

    has_sound = os.path.isfile(BOOT_SOUND) and os.path.getsize(BOOT_SOUND) > 0
    if has_sound:
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    W, H = screen.get_size()
    pygame.display.set_caption('')

    logo_raw = pygame.image.load(LOGO_IMAGE).convert_alpha()
    scale = min(W / logo_raw.get_width(), H / logo_raw.get_height()) * 0.55
    logo = pygame.transform.smoothscale(
        logo_raw,
        (int(logo_raw.get_width() * scale), int(logo_raw.get_height() * scale)),
    )
    logo_rect = logo.get_rect(center=(W // 2, H // 2))

    if has_sound:
        try:
            pygame.mixer.music.load(BOOT_SOUND)
            pygame.mixer.music.play()
        except Exception:
            pass

    clock = pygame.time.Clock()

    for alpha in range(0, 256, 5):
        screen.fill((0, 0, 0))
        logo.set_alpha(alpha)
        screen.blit(logo, logo_rect)
        pygame.display.flip()
        clock.tick(60)

    hold_start = time.time()
    while time.time() - hold_start < 2.8:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
        screen.fill((0, 0, 0))
        screen.blit(logo, logo_rect)
        pygame.display.flip()
        clock.tick(60)

    for alpha in range(255, -1, -5):
        screen.fill((0, 0, 0))
        logo.set_alpha(alpha)
        screen.blit(logo, logo_rect)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == '__main__':
    run()
