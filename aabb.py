from typing import List
import sys
from pygame.math import Vector2
from pygame.rect import Rect
from collections import deque

global_screen = None

class AABB(object):
    _lower_bound: Vector2
    _upper_bound: Vector2
    
    def __init__(self, lower: Vector2, upper: Vector2):
        self._lower_bound = lower
        self._upper_bound = upper
        width = self._upper_bound.x - self._lower_bound.x
        height = self._upper_bound.y - self._lower_bound.y
        self._cost = width * height #2 * width + 2 * height
        
    def union(a1: 'AABB', a2: 'AABB') -> 'AABB':
        padding: int = 0 # seems to do worse with less padding or more padding -- 25 is just right?
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

    # inspiration from https://github.com/kip-hart/AABBTree/blob/master/aabbtree.py#L215
    def overlap_volume(self, aabb):
        volume = 1

        min1, max1 = self._lower_bound.x, self._upper_bound.x
        min2, max2 = aabb._lower_bound.x, aabb._upper_bound.x

        overlap_min = max(min1, min2)
        overlap_max = min(max1, max2)
        if overlap_min >= overlap_max:
            return 0

        volume *= overlap_max - overlap_min

        min1, max1 = self._lower_bound.y, self._upper_bound.y
        min2, max2 = aabb._lower_bound.y, aabb._upper_bound.y

        overlap_min = max(min1, min2)
        overlap_max = min(max1, max2)
        if overlap_min >= overlap_max:
            return 0

        volume *= overlap_max - overlap_min

        return volume
        
class AABBNode(object):
    _is_leaf: bool
    _bounding_box: AABB
    _left_child: 'AABBNode'
    _right_child: 'AABBNode'
    _parent: 'AABBNode'
    _indx: int
    _cost: int
    
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
        self._cost = 0
        
    def cost(self):
        '''recursive helper for cost function'''
        self._cost = self.cost_recursive(self)
        return self._cost

    def cost_recursive(self, curr_node: 'AABBNode'):
        '''recursive cost function based on bounding box costs'''
        left_cost = 0
        right_cost = 0
        if curr_node._left_child and not curr_node._left_child._is_leaf:
            left_cost = self.cost_recursive(curr_node._left_child)
        if curr_node._right_child and not curr_node._right_child._is_leaf:
            right_cost = self.cost_recursive(curr_node._right_child)
        return curr_node._bounding_box._cost + left_cost + right_cost
    
    def find_best_cost(self, curr_node: 'AABBNode', new_node: 'AABBNode', curr_cost: int):
        '''recursive cost function based on bounding box costs'''
        new_aabb = AABB.union(curr_node._bounding_box, new_node._bounding_box)
        new_cost = new_aabb._cost # the cost to put the box around all 3 of them is always the same
        # base case
        if curr_node._is_leaf:
            return (curr_node, new_cost)

        left_node: AABBNode = None
        right_node: AABBNode = None

        left_node, left_cost = self.find_best_cost(curr_node._left_child, new_node, curr_cost)
        right_node, right_cost = self.find_best_cost(curr_node._right_child, new_node, curr_cost)
        curr_cost = curr_node.cost()
        
        if curr_cost < left_cost and curr_cost < right_cost:
            return (curr_node, curr_cost + new_cost)
        else:
            return (left_node, left_cost + new_cost) if left_cost < right_cost else (right_node, right_cost + new_cost)

    def trickle_up_cost(self, new_node: 'AABBNode'):
        '''iterative cost function based on all changed bounding box costs'''
        curr_node = self
        curr_aabb = AABB.union(curr_node._bounding_box, new_node._bounding_box)
        cost = curr_aabb._cost
        recursive_cost = self._cost

        while curr_node._parent:
            # consider the cost of replacing the sibling with the new node
            if curr_node._parent._left_child == curr_node:
                curr_aabb = AABB.union(curr_aabb, curr_node._parent._right_child._bounding_box)
            else:
                curr_aabb = AABB.union(curr_aabb, curr_node._parent._left_child._bounding_box)
            cost += curr_aabb._cost
            curr_node = curr_node._parent

        #global_screen.blit(cost_font.render(str(int(cost)), 1, pygame.Color("coral")), (self._bounding_box._lower_bound.x + 5, self._bounding_box._lower_bound.y + 5))

        return cost + recursive_cost
        
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

    def insert_from_root(self, new_node: AABBNode):
        self.insert_node_recursive(self._root, new_node)

    # inspiration from https://github.com/kip-hart/AABBTree/blob/master/aabbtree.py#L340
    def insert_node_recursive(self, curr_node: AABBNode, new_node: AABBNode):
        if self._root is None:
            self._root = new_node
            self._nodes.append(new_node)
            return
        
        if curr_node._is_leaf:
            # base case
            internal_node = AABBNode(False, -1)
            parent = curr_node._parent
            internal_node._parent = parent
            # this is not the root node
            if parent is not None:
                if parent._left_child == curr_node:
                    parent._left_child = internal_node
                else:
                    parent._right_child = internal_node
            else:
                self._root = internal_node

            # set children correctly and append
            internal_node._left_child = curr_node
            internal_node._right_child = new_node
            curr_node._parent = internal_node
            new_node._parent = internal_node
            self._nodes.append(internal_node)
            self._nodes.append(new_node)

            internal_node._bounding_box = AABB.union(internal_node._left_child._bounding_box, internal_node._right_child._bounding_box)
        else:
            new_aabb = new_node._bounding_box
            branch_merge = AABB.union(curr_node._bounding_box, new_aabb)
            left_merge = AABB.union(curr_node._left_child._bounding_box, new_aabb)
            right_merge = AABB.union(curr_node._right_child._bounding_box, new_aabb)

            # Calculate the change in the sum of the bounding volumes
            branch_cost = branch_merge._cost

            left_cost = branch_merge._cost - curr_node._bounding_box._cost
            left_cost += left_merge._cost - curr_node._left_child._bounding_box._cost

            right_cost = branch_merge._cost - curr_node._bounding_box._cost
            right_cost += right_merge._cost - curr_node._right_child._bounding_box._cost

            # Calculate amount of overlap
            branch_olap_cost = curr_node._bounding_box.overlap_volume(new_aabb)
            left_olap_cost = left_merge.overlap_volume(curr_node._right_child._bounding_box)
            right_olap_cost = right_merge.overlap_volume(curr_node._left_child._bounding_box)

            # Calculate total cost
            branch_cost += branch_olap_cost
            left_cost += left_olap_cost
            right_cost += right_olap_cost

            if branch_cost < left_cost and branch_cost < right_cost:
                internal_node = AABBNode(False, -1)
                parent = curr_node._parent
                internal_node._parent = parent
                # this is not the root node
                if parent is not None:
                    if parent._left_child == curr_node:
                        parent._left_child = internal_node
                    else:
                        parent._right_child = internal_node
                else:
                    self._root = internal_node

                # set children correctly and append
                internal_node._left_child = curr_node
                internal_node._right_child = new_node
                curr_node._parent = internal_node
                new_node._parent = internal_node
                self._nodes.append(internal_node)
                self._nodes.append(new_node)

                internal_node._bounding_box = AABB.union(internal_node._left_child._bounding_box, internal_node._right_child._bounding_box)
            elif left_cost < right_cost:
                self.insert_node_recursive(curr_node._left_child, new_node)
            else:
                self.insert_node_recursive(curr_node._right_child, new_node)

            # walks back up the tree for us?
            curr_node._bounding_box = AABB.union(curr_node._left_child._bounding_box, curr_node._right_child._bounding_box)
                    
    def insert_node(self, new_node: AABBNode):
        if self._root is None:
            self._root = new_node
            self._nodes.append(new_node)
            return
    
        # otherwise, make a new internal node and put this on right
        best_node: AABBNode = self.find_best_node(self._root, new_node) # self.find_best_node_itr(new_node) # self.find_best_node(self._root, new_node) # self.find_best_node_heuristic(self._root, new_node)
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
        self._nodes.append(new_node)
        # Help given by Andrew Mueller, The OG Man, and my loving husband. :)
        
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
        best_node, _ = curr_node.find_best_cost(curr_node, new_node, 0) 
        return best_node

    def find_best_node_itr(self, new_node: AABBNode) -> AABBNode:        
        # trickle up stuff -- O(n log n), at most log n for each leaf (n/2 nodes)
        best_node = None
        best_cost = sys.maxsize

        for node in self._nodes:
           node.cost()
        
        for node in self._nodes:
            curr_cost = node.trickle_up_cost(new_node)
            if curr_cost < best_cost:
                best_node = node
                best_cost = curr_cost

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
            new_tree.insert_from_root(new_node)

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

            # remove this overwritten internal parent node (I had to add this)
            self._nodes.remove(parent)
                
        # Remove the node from the list of nodes.
        self._nodes.remove(node)

    def update_node(self, node: AABBNode, new_aabb: AABB):
        node._bounding_box = new_aabb
        # walk back up the tree to refit all the AABBs
        curr_node = node._parent
        while curr_node is not None:
            curr_node._bounding_box = AABB.union(curr_node._left_child._bounding_box, curr_node._right_child._bounding_box)
            curr_node = curr_node._parent

    # Thanks ChatGPT :-)
    # format printed for use with https://www.leetcode-tree-visualizer.com/
    def print_levels(self):
        if not self._root:
            return ''

        queue = [self._root]
        output = []
        all_none = False
        
        while queue and not all_none:
            level_nodes = []
            all_none = True
            for _ in range(len(queue)):
                node = queue.pop(0)
                if node:
                    level_nodes.append(str(node._indx))
                    queue.append(node._left_child)
                    queue.append(node._right_child)
                    all_none = False
                else:
                    level_nodes.append('')
                    queue.extend([None, None])
            
            output.append(','.join(level_nodes))
        
        print(','.join(output))
        
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
            new_node = AABBNode(is_leaf=True, indx=len(circles), rect=curr_circle.rect)
            circles.append(curr_circle)
            aabb_tree.insert_from_root(new_node)
            curr_x += radius + spacing

        # reset pos
        curr_x = spacing
        curr_y += radius + spacing
        
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
            aabb_tree.insert_from_root(new_node)

            # new_rect = circles[node._indx].rect
            # aabb_tree.update_node(node, AABB(Vector2(new_rect.topleft), Vector2(new_rect.bottomright)))

        # determine which AABBs can collide
        #circle_combos = []
        for i, circle in enumerate(circles):
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

            #print(num_checks)

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
        #aabb_tree.print_levels()

        # for node in aabb_tree._nodes:
        #     print(node._indx)

        curr_fps = clock.get_fps()
        fps_surface = update_fps()
        total_time += dt
        total_frames += curr_fps
        frames_checks += 1
        # avg fps and checks every 30s
        if total_time >= 1:
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

        # fps rect
        pygame.draw.rect(screen, "black", Rect(0, 0, 250, 90))
        fps_text = "{:<12}{:10d}".format("Curr FPS:", int(curr_fps))
        screen.blit(render_text(fps_text), (5, 10))
        if avg_frames_render:
            screen.blit(avg_frames_render, (5, 30))
        if avg_checks_render:
            screen.blit(avg_checks_render, (5, 50))
        pygame.display.flip()
        
    pygame.quit()