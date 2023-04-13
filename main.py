import pygame
import os
from typing import List
import random
import itertools
import argparse

from circle import Circle
from wall import Wall

parser = argparse.ArgumentParser()
parser.add_argument("num_spawn", help="num circles to spawn on map", type=int)
args = parser.parse_args()
num_spawn = args.num_spawn

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()
running = True

# circle spawning
# calculate number that we can spawn with the radius + spacing
radius = 5
spacing = 20
num_width = int(SCREEN_WIDTH / (radius * 2 + spacing))
num_height = int(SCREEN_HEIGHT / (radius * 2 + spacing))
if(num_spawn > num_width * num_height):
    print("too many circles, not enough room!")
    exit()

# spawn circles
circles: List[Circle] = []
curr_x = spacing
curr_y = spacing
for i in range(num_height):
    curr_y += radius

    for j in range(num_width):
        if i * num_width + j >= num_spawn:
            break

        curr_x += radius
        circles.append(Circle((curr_x, curr_y),
                            (random.randint(-20, 20), random.randint(-20, 20)),
                            (random.randint(-20, 20), random.randint(-20, 20)),
                            radius, 
                            random.choice(["green", "blue", "yellow", "red", "grey"])))
        curr_x += radius + spacing

    # reset pos
    curr_x = spacing
    curr_y += radius + spacing

# walls
WALL_WIDTH = 5
walls: List[Wall] = []
walls.append(Wall((WALL_WIDTH / 2, SCREEN_HEIGHT / 2), (0,0), (0,0), WALL_WIDTH, SCREEN_HEIGHT, (1, 0)))                     # left
walls.append(Wall((SCREEN_WIDTH / 2, WALL_WIDTH / 2), (0,0), (0,0), SCREEN_WIDTH, WALL_WIDTH, (0, -1)))          # top
walls.append(Wall(((SCREEN_WIDTH-WALL_WIDTH / 2), SCREEN_HEIGHT / 2), (0,0), (0,0), WALL_WIDTH, SCREEN_HEIGHT, (-1, 0)))  # right
walls.append(Wall((SCREEN_WIDTH / 2, (SCREEN_HEIGHT-WALL_WIDTH / 2)), (0,0), (0,0), SCREEN_WIDTH, WALL_WIDTH, (0, 1)))       # bottom

# init at 0.1 to avoid divide by 0
dt: float = 0.1

# get combinations
circle_combos = list(itertools.combinations(range(len(circles)), 2))

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
    screen.fill("#000000")
    
    # convert dt to seconds by dividing by 1
    for i in range(len(circles)):
        circles[i].on_tick(dt)
    
        for wall in walls:      
            #check if colliding
            if pygame.sprite.collide_rect(circles[i], wall):
                circles[i].reflect_wall(wall, dt)
            wall.render(screen)
            
    for combo in circle_combos:
        if pygame.sprite.collide_rect(circles[combo[0]], circles[combo[1]]):
            circles[combo[0]].reflect_obj(circles[combo[1]], dt) 
        # for j in range(len(circles)):
        #     if j != i:
        #         if pygame.sprite.collide_rect(circles[i], circles[j]):
        #             circles[i].reflect_obj(circles[j], dt)
    
    for circle in circles:
        circle.render(screen)
    pygame.display.flip()

    dt = clock.tick(60) / 1000
    
pygame.quit()