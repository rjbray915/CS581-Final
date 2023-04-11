import pygame
import os
from typing import List
import random

from circle import Circle
from wall import Wall

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()
running = True

# test circle
circles: List[Circle] = []
for i in range(100):
    circles.append(Circle((random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT)),
                          (random.randint(-100, 100), random.randint(-100, 100)),
                          (random.randint(-100, 100), random.randint(-100, 100)),
                          10, 
                          random.choice(["green", "blue", "yellow", "red"])))
# circles.append(Circle((100, 100), (200, 200), (0, 20)))
# circles.append(Circle((1000, 100), (-200, 200), (-20, 20), 40, "green"))
# circles.append(Circle((500, 500), (50, 50), (10, 10), 40, "yellow"))

# walls
WALL_WIDTH = 5
walls: List[Wall] = []
walls.append(Wall((WALL_WIDTH / 2, SCREEN_HEIGHT / 2), (0,0), (0,0), WALL_WIDTH, SCREEN_HEIGHT, (1, 0)))                     # left
walls.append(Wall((SCREEN_WIDTH / 2, WALL_WIDTH / 2), (0,0), (0,0), SCREEN_WIDTH, WALL_WIDTH, (0, -1)))          # top
walls.append(Wall(((SCREEN_WIDTH-WALL_WIDTH / 2), SCREEN_HEIGHT / 2), (0,0), (0,0), WALL_WIDTH, SCREEN_HEIGHT, (-1, 0)))  # right
walls.append(Wall((SCREEN_WIDTH / 2, (SCREEN_HEIGHT-WALL_WIDTH / 2)), (0,0), (0,0), SCREEN_WIDTH, WALL_WIDTH, (0, 1)))       # bottom

# init at 0.1 to avoid divide by 0
dt: float = 0.1

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
                print("COLLIDE")
                circles[i].reflect_wall(wall, dt)
            wall.render(screen)
            
        for j in range(len(circles)):
            if j != i:
                if pygame.sprite.collide_rect(circles[i], circles[j]):
                    circles[i].reflect_obj(circles[j], dt)
        
        circles[i].render(screen)
    pygame.display.flip()

    dt = clock.tick(60) / 1000
    
pygame.quit()