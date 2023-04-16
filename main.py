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
parser.add_argument("radius", help="radius of circles", type=int)
parser.add_argument("spacing", help="spacing of circles", type=int)
args = parser.parse_args()
num_spawn = int(args.num_spawn)
radius = int(args.radius)
spacing = int(args.spacing)

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT)) # flags=pygame.NOFRAME
clock = pygame.time.Clock()
running = True

# fps counter
font = pygame.font.SysFont("dejavusansmono", 18)
def update_fps():
	fps = str(int(clock.get_fps())) # averages the last 10 calls to Clock.tick()
	fps_text = font.render(fps, 1, pygame.Color("coral"))
	return fps_text

# circle spawning
# calculate number that we can spawn with the radius + spacing
# radius = 5
# spacing = 20
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
                            (random.randint(-100, 100), random.randint(-100, 100)),
                            (0, 0),# (random.randint(-20, 20), random.randint(-20, 20)),
                            radius, 
                            random.choice(["green", "blue", "yellow", "red", "grey"])))
        curr_x += radius + spacing

    # reset pos
    curr_x = spacing
    curr_y += radius + spacing

# walls
# WALL_WIDTH = 50
# walls: List[Wall] = []
# walls.append(Wall((WALL_WIDTH/2, SCREEN_HEIGHT/2), (0, 0), (0, 0), WALL_WIDTH, SCREEN_HEIGHT, (1, 0)))                      # left
# walls.append(Wall((SCREEN_WIDTH/2, WALL_WIDTH/2), (0, 0), (0, 0), SCREEN_WIDTH, WALL_WIDTH, (0, -1)))                       # top
# walls.append(Wall(((SCREEN_WIDTH - WALL_WIDTH/2), SCREEN_HEIGHT / 2), (0, 0), (0, 0), WALL_WIDTH, SCREEN_HEIGHT, (-1, 0)))  # right
# walls.append(Wall((SCREEN_WIDTH/2, (SCREEN_HEIGHT - WALL_WIDTH/2)), (0, 0), (0, 0), SCREEN_WIDTH, WALL_WIDTH, (0, 1)))      # bottom

# get combinations
circle_combos = list(itertools.combinations(range(len(circles)), 2))

while running:
    # convert dt to seconds by dividing by 1000
    dt = clock.tick() / 1000

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                running = False
            
    screen.fill("#000000")

    for i in range(len(circles)):
        circles[i].on_tick(dt)
    
        # for wall in walls:      
        #     #check if colliding
        #     if pygame.sprite.collide_rect(circles[i], wall):
        #         circles[i].reflect_wall(wall, dt)
        #     wall.render(screen)
            
    for combo in circle_combos:
        # check if bounding box is colliding
        # if pygame.sprite.collide_rect(circles[combo[0]], circles[combo[1]]):
            # precise calculation for circles
        if circles[combo[0]].is_colliding_circle(circles[combo[1]]):
            circles[combo[0]].reflect_obj(circles[combo[1]], dt)
    
    for circle in circles:
        if circle._pos.x - circle._radius < 0:
            circle._pos.x = circle._radius
            circle._vel.x = -circle._vel.x
        if circle._pos.x + circle._radius > SCREEN_WIDTH-1:
            circle._pos.x = SCREEN_WIDTH-1 - circle._radius
            circle._vel.x = -circle._vel.x
        if circle._pos.y - circle._radius < 0:
            circle._pos.y = circle._radius
            circle._vel.y = -circle._vel.y
        if circle._pos.y + circle._radius > SCREEN_HEIGHT-1:
            circle._pos.y = SCREEN_HEIGHT-1 - circle._radius
            circle._vel.y = -circle._vel.y

        circle.render(screen)

    screen.blit(update_fps(), (5, 10))
    pygame.display.flip()
    
pygame.quit()