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
parser.add_argument("min_radius", help="minimum radius of circles", type=int)
parser.add_argument("max_radius", help="maximum radius of circles", type=int)
parser.add_argument("spacing", help="spacing of circles", type=int)
args = parser.parse_args()
num_spawn = int(args.num_spawn)
min_radius = int(args.min_radius)
max_radius = int(args.max_radius)
spacing = int(args.spacing)

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT)) # flags=pygame.NOFRAME
pygame.display.set_caption('Combinations')
clock = pygame.time.Clock()
running = True
paused = False

# timing code
sum_dt = 0
first_thirty = True

# random seed
random.seed(581)

# fps counter
font = pygame.font.SysFont("dejavusansmono", 18)
def update_fps():
    fps = str(int(clock.get_fps())) # averages the last 10 calls to Clock.tick()
    fps_text = font.render(fps, 1, pygame.Color("coral"))
    return fps_text

def render_text(text: str):
    return font.render(text, 1, pygame.Color("coral"))

# circle spawning
# calculate number that we can spawn with the radius + spacing
# radius = 5
# spacing = 20
num_width = int(SCREEN_WIDTH / (max_radius * 2 + spacing))
num_height = int(SCREEN_HEIGHT / (max_radius * 2 + spacing))
if(num_spawn > num_width * num_height):
    print("too many circles, not enough room!")
    exit()

# spawn circles
circles: List[Circle] = []
curr_x = spacing
curr_y = spacing
for i in range(num_height):
    curr_y += max_radius

    for j in range(num_width):
        if i * num_width + j >= num_spawn:
            break

        curr_x += max_radius
        circles.append(Circle((curr_x, curr_y),
                            (random.randint(-100, 100), random.randint(-100, 100)),
                            (0, 0),# (random.randint(-20, 20), random.randint(-20, 20)),
                            random.randint(min_radius, max_radius), # can experiment with random radius -- random.randint(1, radius)
                            random.choice(["green", "blue", "yellow", "red", "grey"])))
        curr_x += max_radius + spacing

    # reset pos
    curr_x = spacing
    curr_y += max_radius + spacing

# walls
# WALL_WIDTH = 50
# walls: List[Wall] = []
# walls.append(Wall((WALL_WIDTH/2, SCREEN_HEIGHT/2), (0, 0), (0, 0), WALL_WIDTH, SCREEN_HEIGHT, (1, 0)))                      # left
# walls.append(Wall((SCREEN_WIDTH/2, WALL_WIDTH/2), (0, 0), (0, 0), SCREEN_WIDTH, WALL_WIDTH, (0, -1)))                       # top
# walls.append(Wall(((SCREEN_WIDTH - WALL_WIDTH/2), SCREEN_HEIGHT / 2), (0, 0), (0, 0), WALL_WIDTH, SCREEN_HEIGHT, (-1, 0)))  # right
# walls.append(Wall((SCREEN_WIDTH/2, (SCREEN_HEIGHT - WALL_WIDTH/2)), (0, 0), (0, 0), SCREEN_WIDTH, WALL_WIDTH, (0, 1)))      # bottom

# get combinations
circle_combos = list(itertools.combinations(range(len(circles)), 2))

total_time = 0
num_checks = 0
total_frames = 0
frames_checks = 0
avg_frames_render = None
avg_checks_render = None

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                running = False
            if event.key == pygame.K_p:
                paused = not paused

    # convert dt to seconds by dividing by 1000
    dt = clock.tick() / 1000
            
    screen.fill("#000000")
    
    if paused:
        continue

    for circle in circles:
        circle.on_tick(dt)
    
        # for wall in walls:      
        #     #check if colliding
        #     if pygame.sprite.collide_rect(circles[i], wall):
        #         circles[i].reflect_wall(wall, dt)
        #     wall.render(screen)
            
    for combo in circle_combos:
        # check if bounding box is colliding
        # if pygame.sprite.collide_rect(circles[combo[0]], circles[combo[1]]):
            # precise calculation for circles
        num_checks += 1
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

    time_diff = 30
    curr_fps = clock.get_fps()
    fps_surface = update_fps()
    total_time += dt
    total_frames += curr_fps
    frames_checks += 1
    # avg fps and checks every 1s
    if total_time >= time_diff:
        avg_framerate = total_frames / frames_checks
        avg_checks = num_checks / frames_checks
        
        avg_check_str = "{:<12}{:10.1f}".format("Avg Checks:", avg_checks)
        avg_frames_str = "{:<12}{:10.1f}".format("Avg FPS:", avg_framerate)
        avg_checks_render = render_text(avg_check_str)
        avg_frames_render = render_text(avg_frames_str)

        total_time = 0
        total_frames = 0
        frames_checks = 0
        num_checks = 0

        if first_thirty:
                first_thirty = False
                print("reached1", sum_dt)
        else:
            paused = True
            print("reached2", sum_dt)

    # fps rect
    s = pygame.Surface((250, 70), pygame.SRCALPHA)
    s.fill((0, 0, 0, 128))
    screen.blit(s, (0, 0))
    fps_text = "{:<12}{:10d}".format("Cur FPS:", int(curr_fps))
    screen.blit(render_text(fps_text), (5, 10))
    if avg_frames_render:
        screen.blit(avg_frames_render, (5, 30))
    if avg_checks_render:
        screen.blit(avg_checks_render, (5, 50))
    pygame.display.flip()
    
pygame.quit()