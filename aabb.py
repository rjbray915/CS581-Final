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
        
    def union(a1: 'AABB', a2: 'AABB') -> 'AABB':
        padding: int = 50 # seems to do worse with less padding
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
    
    def find_best_cost(self, curr_node: 'AABBNode', new_node: 'AABBNode', curr_cost: int):
        '''recursive cost function based on bounding box costs'''
        new_aabb = AABB.union(curr_node._bounding_box, new_node._bounding_box)
        new_cost = new_aabb._cost
        # base case
        if curr_node._is_leaf:
            return (new_aabb, curr_node, new_cost)

        left_node: AABBNode = None
        right_node: AABBNode = None
        left_aabb: AABB = None
        right_aabb: AABB = None

        left_aabb, left_node, left_cost = self.find_best_cost(curr_node._left_child, new_node, curr_cost)
        right_aabb, right_node, right_cost = self.find_best_cost(curr_node._right_child, new_node, curr_cost)
        curr_cost = curr_node.cost()
        
        if curr_cost < left_cost and curr_cost < right_cost:
            return (new_aabb, curr_node, curr_cost + new_cost)
        else:
            return (left_aabb, left_node, left_cost + new_cost) if left_cost < right_cost else (right_aabb, right_node, right_cost + new_cost)
        
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
            #surface.blit(cost_font.render(str(int(self._indx)), 1, pygame.Color("coral")), (self._bounding_box._lower_bound.x, self._bounding_box._lower_bound.y))
        else:
            self._bounding_box.render(surface, color)
            #surface.blit(cost_font.render(str(int(self.cost())), 1, pygame.Color("coral")), (self._bounding_box._lower_bound.x + 5, self._bounding_box._lower_bound.y + 5))
    
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
        best_node: AABBNode = self.find_best_node(self._root, new_node) # self.find_best_node_heuristic(self._root, new_node)
        # internal_node_bb = AABB.union(new_node._bounding_box, best_node._bounding_box)
        internal_node = AABBNode(False, -1)
        old_node = best_node._parent
        internal_node._parent = old_node
        
        # this is not the root node
        if old_node != None:
            if old_node._left_child == best_node:
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
        #print(curr_node._indx)
        # if this is a leaf, return
        if not curr_node._left_child and not curr_node._right_child:
            return curr_node
        
        # go down the rabbit hole  
        _, best_node, _ = curr_node.find_best_cost(curr_node, new_node, 0)
        return best_node

    def find_best_node_heuristic(self, curr_node: AABBNode, new_node: AABBNode) -> AABBNode:
        # if this is a leaf, return
        if not curr_node._left_child and not curr_node._right_child:
            return curr_node
        
        # estimate costs
        left_cost = curr_node._left_child._bounding_box._cost + AABB.union(curr_node._left_child._bounding_box, new_node._bounding_box)._cost
        right_cost = curr_node._right_child._bounding_box._cost + AABB.union(curr_node._right_child._bounding_box, new_node._bounding_box)._cost
        curr_cost = curr_node._bounding_box._cost + AABB.union(curr_node._bounding_box, new_node._bounding_box)._cost

        if curr_cost < left_cost and curr_cost < right_cost:
            return curr_node
        else:
            return self.find_best_node_heuristic(curr_node._left_child, new_node) if left_cost < right_cost else self.find_best_node_heuristic(curr_node._right_child, new_node)

    def update_tree(self, circles):
        #circles.sort(key=lambda c: (c._pos.x, c._pos.y))

        new_tree = AABBTree()
        for i, circle in enumerate(circles):
            new_node = AABBNode(is_leaf=True, indx=i, rect=circle.rect)
            new_tree.insert_node(new_node)

        return new_tree

    def render_tree(self, screen, color):
        for node in self._nodes:
            # print(node)
            # print(node._bounding_box._lower_bound, node._bounding_box._upper_bound)
            node.render(screen, color)
            color.g = (color.g + 30) % 255

    # Thanks ChatGPT :-)
    def delete_leaf_node(self, node: AABBNode):
        if node._parent is None:
            # Node is the root of the tree.
            self._root = None
        else:
            # Node is not the root of the tree.
            parent = node._parent
            sibling = parent._left_child if parent._right_child == node else parent._right_child
            grandparent = parent._parent
            
            if grandparent is None:
                # Node's parent is the root of the tree.
                self._root = sibling
                sibling._parent = None
            else:
                # Node's parent is not the root of the tree.
                if grandparent._left_child == parent:
                    grandparent._left_child = sibling
                else:
                    grandparent._right_child = sibling
                sibling._parent = grandparent
            
                # Walk back up the tree, updating bounding boxes.
                curr_node = sibling._parent
                while curr_node is not None:
                    curr_node._bounding_box = AABB.union(curr_node._left_child._bounding_box, curr_node._right_child._bounding_box)
                    curr_node = curr_node._parent

            # remove this overwritten internal parent node
            self._nodes.remove(parent)
                
        # Remove the node from the list of nodes.
        self._nodes.remove(node)

    # DOES NOT WORK
    def update_node(self, node: AABBNode, new_aabb: AABB):
        node._bounding_box = new_aabb
        # Walk back up the tree, updating bounding boxes.
        curr_node = node._parent
        while curr_node is not None:
            curr_node._bounding_box = AABB.union(curr_node._left_child._bounding_box, curr_node._right_child._bounding_box)
            curr_node = curr_node._parent
        
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
                                random.randint(radius, radius), 
                                random.choice(["green", "blue", "yellow", "red", "grey"]))
            new_node = AABBNode(is_leaf=True, indx=len(circles), rect=curr_circle.rect)
            circles.append(curr_circle)
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

        for circle in circles:
            circle.on_tick(dt)

        nodes_to_redraw = []
        for node in aabb_tree._nodes:
            if node._is_leaf and node._parent:
                circle = circles[node._indx]
                rect1 = circle.rect
                # redraw tree if any part of the circle has left its immediate parent's bounding box
                rect2 = node._parent._bounding_box
                overlapping = not (rect1.x + rect1.w - 2*circle._radius < rect2._lower_bound.x or rect1.x + 2*circle._radius > rect2._upper_bound.x or rect1.y + rect1.h - 2*circle._radius < rect2._lower_bound.y or rect1.y + 2*circle._radius > rect2._upper_bound.y)
                #overlapping = not (rect1.x + rect1.w - circle._vel.x < rect2._lower_bound.x or rect1.x + circle._vel.x > rect2._upper_bound.x or rect1.y + rect1.h - circle._vel.y < rect2._lower_bound.y or rect1.y + circle._vel.y > rect2._upper_bound.y)
                if not overlapping:
                    #nodes_to_redraw.append(node)
                    aabb_tree = aabb_tree.update_tree(circles)
                    break
        
        # for node in nodes_to_redraw:
        #     new_node = AABBNode(is_leaf=True, indx=node._indx, rect=circles[node._indx].rect)
        #     aabb_tree.delete_leaf_node(node)
        #     aabb_tree.insert_node(new_node)

            # new_rect = circles[node._indx].rect
            # aabb_tree.update_node(node, AABB(Vector2(new_rect.topleft), Vector2(new_rect.bottomright)))

        # determine which AABBs can collide
        #circle_combos = []
        for i, circle in enumerate(circles):
            stack = [aabb_tree._root]
            rect1 = circle.rect
            while len(stack) > 0:
                top = stack.pop()
                if top._is_leaf and top._indx != i:
                    # handle collision
                    if circle.is_colliding_circle(circles[top._indx]):
                        #circle_combos.append((circle, circles[top._indx]))
                        circle.reflect_obj(circles[top._indx], dt)
                else:
                    if top._left_child:
                        rect2 = top._left_child._bounding_box
                        overlapping = not (rect1.x + rect1.w < rect2._lower_bound.x or rect1.x > rect2._upper_bound.x or rect1.y + rect1.h < rect2._lower_bound.y or rect1.y > rect2._upper_bound.y)
                        if overlapping:
                            stack.append(top._left_child)
                    if top._right_child:
                        rect2 = top._right_child._bounding_box
                        overlapping = not (rect1.x + rect1.w < rect2._lower_bound.x or rect1.x > rect2._upper_bound.x or rect1.y + rect1.h < rect2._lower_bound.y or rect1.y > rect2._upper_bound.y)
                        if overlapping:
                            stack.append(top._right_child)

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

        screen.blit(update_fps(), (5, 10))
        pygame.display.flip()
        
    pygame.quit()