from typing import List
import sys
from pygame.math import Vector2
from pygame.rect import Rect

import pygame
import os
from typing import List
import random
import itertools
import argparse

from circle import Circle
from wall import Wall

from aabbtree import AABB
from aabbtree import AABBTree

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

cost_font = pygame.font.SysFont("dejavusansmono", 12)

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
aabb_tree = AABBTree()
for i in range(num_height):
    curr_y += radius

    for j in range(num_width):
        if i * num_width + j >= num_spawn:
            break

        curr_x += radius
        curr_circle = Circle((curr_x, curr_y),
                            (random.randint(-100, 100), random.randint(-100, 100)),
                            (0, 0),# (random.randint(-20, 20), random.randint(-20, 20)),
                            random.randint(radius, radius),  # can experiment with random radius -- random.randint(1, radius)
                            random.choice(["green", "blue", "yellow", "red", "grey"]))
        new_node = AABB([(curr_circle.rect.topleft, curr_circle.rect.topright), (curr_circle.rect.bottomleft, curr_circle.rect.bottomright)])
        circles.append(curr_circle)
        aabb_tree.add(new_node, str(i))
        curr_x += radius + spacing

    # reset pos
    curr_x = spacing
    curr_y += radius + spacing
    
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
            not_overlapping = rect1.x + rect1.w - 2*circle._radius - 1 < rect2._lower_bound.x or rect1.x + 2*circle._radius + 1 > rect2._upper_bound.x or rect1.y + rect1.h - 2*circle._radius - 1 < rect2._lower_bound.y or rect1.y + 2*circle._radius + 1 > rect2._upper_bound.y
            #overlapping = not (rect1.x + rect1.w - circle._vel.x < rect2._lower_bound.x or rect1.x + circle._vel.x > rect2._upper_bound.x or rect1.y + rect1.h - circle._vel.y < rect2._lower_bound.y or rect1.y + circle._vel.y > rect2._upper_bound.y)
            if not_overlapping:
                nodes_to_redraw.append(node)
                # aabb_tree = aabb_tree.update_tree(circles)
                # break

                # new_node = AABBNode(is_leaf=True, indx=node._indx, rect=circle.rect)
                # aabb_tree.delete_leaf_node(node)
                # aabb_tree.insert_node(new_node)
            else:
                # always update at least the leaf bounding box but don't change its parent by walking up!!!
                # otherwise it will never redraw because it keeps changing the bounds
                node._bounding_box = AABB(Vector2(rect1.topleft), Vector2(rect1.bottomright))
    
    for node in nodes_to_redraw:
        new_node = AABBNode(is_leaf=True, indx=node._indx, rect=circles[node._indx].rect)
        aabb_tree.delete_leaf_node(node)
        aabb_tree.insert_node(new_node)

        # new_rect = circles[node._indx].rect
        # aabb_tree.update_node(node, AABB(Vector2(new_rect.topleft), Vector2(new_rect.bottomright)))

    # determine which AABBs can collide
    #circle_combos = []
    for i, circle in enumerate(circles):
        num_checks = 0
        stack = [aabb_tree._root]
        rect1 = circle.rect
        while len(stack) > 0:
            top = stack.pop()
            num_checks += 1
            if top._is_leaf:
                # handle collision
                if top._indx != i and circle.is_colliding_circle(circles[top._indx]):
                    #circle_combos.append((circle, circles[top._indx]))
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

        print(num_checks)

    # for combo in circle_combos:
    #     if combo[0].is_colliding_circle(combo[1]):
    #         combo[0].reflect_obj(combo[1], dt)
    
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

    # for node in aabb_tree._nodes:
    #     print(node._indx)

    screen.blit(update_fps(), (5, 10))
    pygame.display.flip()
    
pygame.quit()