### Quick visualization script
import math
import random
from time import sleep

import pysicktim.pysicktim.pysicktim as pysicktim
from easydict import EasyDict as edict
import logging
from pprint import pprint
import os, sys
import pygame
from pygame.locals import *
import numpy as np

logging.basicConfig(level=logging.DEBUG)

log = logging.getLogger(__name__)

lidar = pysicktim.LiDAR()


### PYGAME

pygame.init()

WIDTH = 512
HEIGHT = 512

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Lidar Visualisation')
pygame.mouse.set_visible(0)
background = pygame.Surface(screen.get_size())
background = background.convert()
background.fill((250, 250, 250))

if pygame.font:
    font = pygame.font.Font(None, 36)
    text = font.render("Lidar test", 1, (10, 10, 10))
    textpos = text.get_rect(centerx=background.get_width()/2)
    background.blit(text, textpos)

screen.blit(background, (0, 0))


def mainloop():
    import random
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                print("quit")
                return
            elif event.type == KEYDOWN and event.key == K_ESCAPE:
                print("quit")
                return

        background.fill((250, 250, 250))

        if pygame.font:
            font = pygame.font.Font(None, 36)
            text = font.render("Lidar test", 1, (10, 10, 10))
            textpos = text.get_rect(centerx=background.get_width() / 2)
            background.blit(text, textpos)

            font = pygame.font.Font(None, 16)
            text = font.render(lidar.info(), 1, (10, 10, 10))
            textpos = text.get_rect(centerx=background.get_width() / 2)
            background.blit(text, (0,50))

        screen.blit(background, (0, 0))

        scan = lidar.scan()
        # degrees = np.arange(-45,225, 0.3333)
        # log.debug(f"degrees len = {len(degrees)} measurements len = {len(scan.distances)}")
        degrees = [scan.dist_start_ang+i*scan.dist_angle_res for i in range(len(scan.distances))]
        assert len(scan.distances) == len(degrees)
        for dist, deg in zip(scan.distances, degrees):
            SIZE = 10
            startpoint = (WIDTH // 2, HEIGHT // 2)
            endpoint = (startpoint[0] + dist * SIZE * math.sin(np.deg2rad(deg)),
                        startpoint[0] + dist * SIZE * math.cos(np.deg2rad(deg)))
            pygame.draw.line(screen, (10, 10, 10), startpoint, endpoint, 1)
        pygame.display.flip()



lidar.open()
mainloop()
lidar.close()

