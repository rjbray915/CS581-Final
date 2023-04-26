import pygame
import os
from typing import List
import random
import itertools
import argparse
from pygame.math import Vector2

from circle import Circle
from wall import Wall
from aabb import AABB, AABBNode, AABBTree

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
pygame.display.set_caption('AABB Tree w/ Optimized Bounding Boxes')
global_screen = screen
clock = pygame.time.Clock()
running = True
paused = False

# fps counter
font = pygame.font.SysFont("dejavusansmono", 18)
def update_fps():
    fps = str(int(clock.get_fps())) # averages the last 10 calls to Clock.tick()
    fps_text = font.render(fps, 1, pygame.Color("coral"))
    return fps_text

def render_text(text: str):
    return font.render(text, 1, pygame.Color("coral"))

cost_font = pygame.font.SysFont("dejavusansmono", 12)

# circle spawning
# calculate number that we can spawn with the radius + spacing
num_width = int(SCREEN_WIDTH / (max_radius * 2 + spacing))
num_height = int(SCREEN_HEIGHT / (max_radius * 2 + spacing))
if(num_spawn > num_width * num_height):
    print("too many circles, not enough room!")
    exit()

# spawn circles
circles: List[Circle] = []
curr_x = spacing
curr_y = spacing
aabb_tree = AABBTree()
for i in range(num_height):
    curr_y += max_radius

    for j in range(num_width):
        if i * num_width + j >= num_spawn:
            break

        curr_x += max_radius
        curr_circle = Circle((curr_x, curr_y),
                            (random.randint(-100, 100), random.randint(-100, 100)),
                            (0, 0),# (random.randint(-20, 20), random.randint(-20, 20)),
                            random.randint(min_radius, max_radius),  # can experiment with random radius -- random.randint(1, radius)
                            random.choice(["green", "blue", "yellow", "red", "grey"]))
        new_node = AABBNode(is_leaf=True, indx=len(circles), rect=curr_circle.rect)
        circles.append(curr_circle)
        aabb_tree.insert_from_root(new_node)
        curr_x += max_radius + spacing

    # reset pos
    curr_x = spacing
    curr_y += max_radius + spacing
    
total_time = 0
num_checks = 0
total_frames = 0
frames_checks = 0
reinsertions = 0
avg_frames_render = None
avg_checks_render = None
avg_reinserts_render = None

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

    nodes_to_redraw = []
    for node in aabb_tree._nodes:
        if node._is_leaf and node._parent:
            circle = circles[node._indx]
            rect1 = circle.rect

            # redraw node if any part of the circle has left its immediate parent's bounding box
            rect2 = node._parent._bounding_box
            not_overlapping = rect1.x + rect1.w - 2*circle._radius < rect2._lower_bound.x or rect1.x + 2*circle._radius > rect2._upper_bound.x or rect1.y + rect1.h - 2*circle._radius < rect2._lower_bound.y or rect1.y + 2*circle._radius > rect2._upper_bound.y
            if not_overlapping:
                nodes_to_redraw.append(node)
            else:
                # always update at least the leaf bounding box but don't change its parent by walking up!!!
                # otherwise it will never redraw because it keeps changing the bounds
                node._bounding_box = AABB(Vector2(rect1.topleft), Vector2(rect1.bottomright))
    
    for node in nodes_to_redraw:
        new_node = AABBNode(is_leaf=True, indx=node._indx, rect=circles[node._indx].rect)
        aabb_tree.delete_leaf_node(node)
        aabb_tree.insert_from_root(new_node)

    # determine which AABBs can collide
    for i, circle in enumerate(circles):
        stack = [aabb_tree._root]
        rect1 = circle.rect
        while len(stack) > 0:
            top = stack.pop()
            num_checks += 1
            if top._is_leaf:
                # handle collision
                if top._indx != i and circle.is_colliding_circle(circles[top._indx]):
                    circle.reflect_obj(circles[top._indx], dt)
            else:
                rect2 = top._left_child._bounding_box
                overlapping = not (rect1.x + rect1.w < rect2._lower_bound.x or rect1.x > rect2._upper_bound.x or rect1.y + rect1.h < rect2._lower_bound.y or rect1.y > rect2._upper_bound.y)
                if overlapping:
                    stack.append(top._left_child)
                
                rect2 = top._right_child._bounding_box
                overlapping = not (rect1.x + rect1.w < rect2._lower_bound.x or rect1.x > rect2._upper_bound.x or rect1.y + rect1.h < rect2._lower_bound.y or rect1.y > rect2._upper_bound.y)
                if overlapping:
                    stack.append(top._right_child)
    
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
    
    #aabb_tree = aabb_tree.update_tree(circles)
    aabb_tree.render_tree(screen, pygame.Color(255, 0, 0)) # has little to no effect on framerate
    #aabb_tree.print_levels()

    curr_fps = clock.get_fps()
    fps_surface = update_fps()
    total_time += dt
    total_frames += curr_fps
    frames_checks += 1
    reinsertions += len(nodes_to_redraw)
    # avg fps and checks every 1s
    if total_time >= 1:
        avg_framerate = total_frames / frames_checks
        avg_checks = num_checks / frames_checks
        reinsertions /= frames_checks
        
        avg_check_str = "{:<12}{:10.1f}".format("Avg Checks:", avg_checks)
        avg_frames_str = "{:<12}{:10.1f}".format("Avg FPS:", avg_framerate)
        avg_reinserts_str = "{:<12}{:9.1f}".format("Reinsertions:", reinsertions)
        avg_checks_render = render_text(avg_check_str)
        avg_frames_render = render_text(avg_frames_str)
        avg_reinserts_render = render_text(avg_reinserts_str)

        total_time = 0
        total_frames = 0
        frames_checks = 0
        num_checks = 0
        reinsertions = 0

    # fps rect
    s = pygame.Surface((250, 90), pygame.SRCALPHA)
    s.fill((0, 0, 0, 128))
    screen.blit(s, (0, 0))
    fps_text = "{:<12}{:10d}".format("Cur FPS:", int(curr_fps))
    screen.blit(render_text(fps_text), (5, 10))
    if avg_frames_render:
        screen.blit(avg_frames_render, (5, 30))
    if avg_checks_render:
        screen.blit(avg_checks_render, (5, 50))
    if avg_reinserts_render:
        screen.blit(avg_reinserts_render, (5, 70))
    pygame.display.flip()
    
pygame.quit()