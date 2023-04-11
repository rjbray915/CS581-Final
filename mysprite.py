from pygame.math import Vector2
from pygame import draw
from pygame import Rect
from pygame import math
from pygame.sprite import Sprite

class MySprite(Sprite):
    _pos: Vector2
    _vel: Vector2
    _acc: Vector2
    
    def __init__(self, pos_init: tuple, vel_init: tuple, acc_init: tuple, radius: int = 40):
        # parent constructor
        Sprite.__init__(self)
        
        self._pos = Vector2(pos_init[0], pos_init[1])
        self._vel = Vector2(vel_init[0], vel_init[1])
        self._acc = Vector2(acc_init[0], acc_init[1])
        self._radius = radius
        
        # bounding box
        self._bbox = Rect(self._pos.x - self._radius, 
                          self._pos.y - self._radius,
                          self._radius * 2,
                          self._radius * 2)
        
    def on_tick(self, dt):
        self._pos += self._vel * dt
        self._vel += self._acc * dt
        
        # move bounding box
        self._bbox.left = self._pos.x - self._radius
        self._bbox.top = self._pos.y - self._radius
        
    def reflect(self, ref_vel):
        norm_vel = ref_vel - self._vel
        self._vel = self._vel.reflect(norm_vel)
        
    def render(self, surface):
        '''
        used on each render, implemented by child class
        
        Args:
            surface (pygame.Surface): surface to render onto
            
        return: None
        '''
        pass