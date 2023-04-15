from typing import List
from pygame.math import Vector2
from pygame.rect import Rect

class AABB(object):
    _lower_bound: Vector2
    _upper_bound: Vector2
    _padding: int = 1
    
    def __init__(self, lower: Vector2, upper: Vector2):
        self._lower_bound = lower
        self._upper_bound = upper
        
    def union(a1: 'AABB', a2: 'AABB') -> 'AABB':
        padding: int = 5
        lower = Vector2(0, 0)
        upper = Vector2(0, 0)
        lower.x = min(a1._lower_bound.x, a2._lower_bound.x) - padding
        lower.y = min(a1._lower_bound.y, a2._lower_bound.y) - padding
        upper.x = max(a1._upper_bound.x, a2._upper_bound.x) + padding
        upper.y = max(a1._upper_bound.y, a2._upper_bound.y) + padding
        return AABB(lower, upper)
    
    def render(self, surface, color: str):
        rect: Rect = Rect(self._lower_bound.x, self._lower_bound.y,
                          self._upper_bound.x - self._lower_bound.x,
                          self._upper_bound.y - self._lower_bound.y)
        print(rect)
        pygame.draw.rect(surface, color, rect, 1)
        
class AABBNode(object):
    _is_leaf: bool
    _bounding_box: AABB
    _left_child: 'AABBNode'
    _right_child: 'AABBNode'
    
    def __init__(self, is_leaf: bool, rect: Rect = None, aabb: AABB = None):
        self._is_leaf = is_leaf
        if is_leaf:
            self._bounding_box = AABB(Vector2(rect.topleft), Vector2(rect.bottomright))
        elif aabb != None:
            self._bounding_box = aabb
        self._left_child = None
        self._right_child = None
        
    def render(self, surface):
        if self._is_leaf:
            self._bounding_box.render(surface, "green")
        else:
            self._bounding_box.render(surface, "brown")
    
class AABBTree(object):
    _nodes: List[AABBNode]
    _root: AABBNode
    
    def __init__(self):
        self._nodes = []
        self._root = None
        
    def insert_node(self, new_node: AABBNode):
        if self._root == None:
            self._root = new_node
            self._nodes.append(new_node)
            return
    
        # otherwise, make a new internal node and put this on right
        internal_node_bb = AABB.union(new_node._bounding_box, self._nodes[-1]._bounding_box)
        internal_node = AABBNode(is_leaf=False, aabb=internal_node_bb)
        internal_node._left_child = self._nodes[-1]
        internal_node._right_child = new_node
        self._nodes.append(internal_node)
        self._nodes.append(new_node)
        
if __name__ == "__main__":
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
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    running = True

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
            curr_circle = Circle((random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT)),
                                (random.randint(-100, 100), random.randint(-100, 100)),
                                (0, 0),# (random.randint(-20, 20), random.randint(-20, 20)),
                                radius, 
                                random.choice(["green", "blue", "yellow", "red", "grey"]))
            circles.append(curr_circle)
            new_node = AABBNode(is_leaf=True, rect=curr_circle.rect)
            aabb_tree.insert_node(new_node)
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
                
        screen.fill("#000000")
        
        for circle in circles:
            circle.render(screen)
            
        for node in aabb_tree._nodes:
            print(node)
            print(node._bounding_box._lower_bound, node._bounding_box._upper_bound)
            node.render(screen)

        pygame.display.flip()

        # convert dt to seconds by dividing by 1000
        dt = clock.tick(75) / 1000
        
    pygame.quit()