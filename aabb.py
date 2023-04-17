from typing import List
import sys
from pygame.math import Vector2
from pygame.rect import Rect

class AABB(object):
    _lower_bound: Vector2
    _upper_bound: Vector2
    _padding: int = 1
    
    def __init__(self, lower: Vector2, upper: Vector2):
        self._lower_bound = lower
        self._upper_bound = upper
        width = self._upper_bound.x - self._lower_bound.x
        height = self._upper_bound.y - self._lower_bound.y
        self._cost = width * height #2 * width + 2 * height
        
    def union(a1: 'AABB',
     a2: 'AABB') -> 'AABB':
        padding: int = 25
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
        pygame.draw.rect(surface, color, rect, 1)
        
class AABBNode(object):
    _is_leaf: bool
    _bounding_box: AABB
    _left_child: 'AABBNode'
    _right_child: 'AABBNode'
    _parent: 'AABBNode'
    _indx: int
    
    def __init__(self, is_leaf: bool, indx: int, rect: Rect = None, aabb: AABB = None):
        self._is_leaf = is_leaf
        self._indx = indx
        if is_leaf:
            self._bounding_box = AABB(Vector2(rect.topleft), Vector2(rect.bottomright))
        elif aabb != None:
            self._bounding_box = aabb
        else:
            self._bounding_box = None
        self._left_child = None
        self._right_child = None
        self._parent = None
        
    def cost(self):
        '''recursive helper for cost function'''
        return self.cost_recursive(self)
    
    def find_best_cost(self, curr_node: 'AABBNode', new_node: 'AABBNode'):
        '''recursive cost function based on bounding box costs'''
        # base case
        if curr_node._is_leaf:
            new_aabb = AABB.union(curr_node._bounding_box, new_node._bounding_box)
            return (new_aabb, curr_node)

        left_node: AABBNode = None
        right_node: AABBNode = None
        left_aabb: AABB = None
        right_aabb: AABB = None
        left_cost = sys.maxsize
        right_cost = sys.maxsize
        if curr_node._left_child:
            left_aabb, left_node = self.find_best_cost(curr_node._left_child, new_node)
            left_cost = left_aabb._cost
        if curr_node._right_child:
            right_aabb, right_node = self.find_best_cost(curr_node._right_child, new_node)
            right_cost = right_aabb._cost
        return (left_aabb, left_node) if left_cost < right_cost else (right_aabb, right_node)
        
    def cost_recursive(self, curr_node: 'AABBNode'):
        '''recursive cost function based on bounding box costs'''
        left_cost = 0
        right_cost = 0
        if curr_node._left_child and not curr_node._left_child._is_leaf:
            left_cost = self.cost_recursive(curr_node._left_child)
        if curr_node._right_child and not curr_node._right_child._is_leaf:
            right_cost = self.cost_recursive(curr_node._right_child)
        return curr_node._bounding_box._cost + left_cost + right_cost
        
    def render(self, surface, color):
        if self._bounding_box == None:
            return
        
        if self._is_leaf:
            self._bounding_box.render(surface, pygame.Color(0, 255, 0))
            surface.blit(cost_font.render(str(int(self._indx)), 1, pygame.Color("coral")), (self._bounding_box._lower_bound.x + 5, self._bounding_box._lower_bound.y + 5))
        else:
            self._bounding_box.render(surface, color)
            surface.blit(cost_font.render(str(int(self.cost())), 1, pygame.Color("coral")), (self._bounding_box._lower_bound.x + 5, self._bounding_box._lower_bound.y + 5))
    
class AABBTree(object):
    _nodes: List[AABBNode]
    _root: AABBNode
    
    def __init__(self):
        self._nodes = []
        self._root = None
        
    def insert_node(self, new_node: AABBNode):
        self._nodes.append(new_node)

        if self._root == None:
            self._root = new_node
            return
    
        # otherwise, make a new internal node and put this on right
        best_node: AABBNode = self.find_best_node(self._root, new_node)
        # internal_node_bb = AABB.union(new_node._bounding_box, best_node._bounding_box)
        internal_node = AABBNode(False, len(self._nodes))
        old_node = best_node._parent
        internal_node._parent = old_node
        
        # this is not the root node
        if old_node != None:
            if old_node._left_child._indx == best_node._indx:
                old_node._left_child = internal_node
            else:
                old_node._right_child = internal_node
        else:
            self._root = internal_node
        
        # set children correctly and append
        internal_node._left_child = best_node
        internal_node._right_child = new_node
        best_node._parent = internal_node
        new_node._parent = internal_node
        self._nodes.append(internal_node)
        
        # walk back up the tree to refit all the AABBs
        curr_node = internal_node
        while(curr_node != None):
            curr_node._bounding_box = AABB.union(curr_node._left_child._bounding_box, curr_node._right_child._bounding_box)
            curr_node = curr_node._parent
        
    def find_best_node(self, curr_node: AABBNode, new_node: AABBNode) -> AABBNode:
        print(curr_node._indx)
        # if this is a leaf, return
        if not curr_node._left_child and not curr_node._right_child:
            return curr_node
        
        # go down the rabbit hole
        left_node: AABBNode = None
        right_node: AABBNode = None
        left_aabb: AABB = None
        right_aabb: AABB = None
        left_cost = sys.maxsize
        right_cost = sys.maxsize
        if curr_node._left_child:
            #left_cost = AABB.union(curr_node._left_child._bounding_box, new_node._bounding_box)._cost
            left_aabb, left_node = curr_node._left_child.find_best_cost(curr_node._left_child, new_node)
            left_cost = left_aabb._cost
        if curr_node._right_child:
            #right_cost = AABB.union(curr_node._right_child._bounding_box, new_node._bounding_box)._cost
            right_aabb, right_node = curr_node._right_child.find_best_cost(curr_node._right_child, new_node)
            right_cost = right_aabb._cost
        
        if left_cost < right_cost:
            return left_node
        else:
            return right_node
            
        # left_cost = sys.maxsize if not curr_node._left_child else curr_node._left_child.cost()
        # right_cost = sys.maxsize if not curr_node._right_child else curr_node._right_child.cost()
        # if left_cost < right_cost:
        #     return self.find_best_node(curr_node._left_child, new_node)
        # else:
        #     return self.find_best_node(curr_node._right_child, new_node)

    def update_tree(self, circles):
        #circles.sort(key=lambda c: (c._pos.x, c._pos.y))

        new_tree = AABBTree()
        for circle in circles:
            new_node = AABBNode(is_leaf=True, indx=len(new_tree._nodes), rect=circle.rect)
            new_tree.insert_node(new_node)

        return new_tree

    def render_tree(self, screen, color):
        for node in self._nodes:
            # print(node)
            # print(node._bounding_box._lower_bound, node._bounding_box._upper_bound)
            node.render(screen, color)
            color.g = (color.g + 30) % 255
        
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
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT)) # flags=pygame.NOFRAME
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
                                radius, 
                                random.choice(["green", "blue", "yellow", "red", "grey"]))
            circles.append(curr_circle)
            new_node = AABBNode(is_leaf=True, indx=len(aabb_tree._nodes), rect=curr_circle.rect)
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
                if event.key == pygame.K_p:
                    paused = not paused

        if paused:
            continue

        # convert dt to seconds by dividing by 1000
        dt = clock.tick() / 1000
                
        screen.fill("#000000")

        for i in range(len(circles)):
            circles[i].on_tick(dt)
        
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
        
        aabb_tree = aabb_tree.update_tree(circles)
        aabb_tree.render_tree(screen, pygame.Color(255, 0, 0))

        screen.blit(update_fps(), (5, 10))
        pygame.display.flip()
        
    pygame.quit()