from typing import List
from pygame.math import Vector2
from pygame.rect import Rect

class AABB(object):
    _lower_bound: Vector2
    _upper_bound: Vector2
    
    def __init__(self, rect: Rect):
        self._lower_bound = Vector2(rect.bottomleft)
        self._upper_bound = Vector2(rect.bottomright)
        
class AABBNode(object):
    _is_leaf: bool
    _bounding_box: AABB
    _left_child: 'AABBNode'
    _right_child: 'AABBNode'
    
    def __init__(self, is_leaf: bool, rect: Rect = None):
        self._is_leaf = is_leaf
        if is_leaf:
            self._bounding_box = AABB(rect)
        self._left_child = None
        self._right_child = None
    
class AABBTree(object):
    _nodes: List[AABBNode]
    _root: AABBNode
    
    def __init__(self):
        nodes = []
        root = None
        
    # def insert_node(self, new_node: AABBNode):
        