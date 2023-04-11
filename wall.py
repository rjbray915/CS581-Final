from pygame.math import Vector2
from pygame import draw
from pygame import Rect
from pygame import math
from pygame.sprite import Sprite

class Wall(Sprite):
    _pos: Vector2
    _vel: Vector2
    _acc: Vector2
    
    def __init__(self, pos_init: tuple, vel_init: tuple, acc_init: tuple, width: int, height: int,
                 reflect_vect_tup: tuple):
        # parent constructor
        Sprite.__init__(self)
        
        self._pos = Vector2(pos_init[0], pos_init[1])
        self._vel = Vector2(vel_init[0], vel_init[1])
        self._acc = Vector2(acc_init[0], acc_init[1])
        self._width = width
        self._height = height
        self._norm_vect: Vector2 = Vector2(reflect_vect_tup[0], reflect_vect_tup[1])
        
        # bounding box
        self.rect = Rect(self._pos.x - self._width / 2, 
                          self._pos.y - self._height / 2,
                          self._width,
                          self._height)
        
    def on_tick(self, dt):
        self._pos += self._vel * dt
        self._vel += self._acc * dt
        
        # move bounding box
        self.rect.left = self._pos.x - self._radius
        self.rect.top = self._pos.y - self._radius
        
    def reflect(self, ref, dt):
        self._pos -= self._vel * dt
        norm_vel = ref._vel - self._vel
        self._vel = self._vel.reflect(norm_vel)
        norm_acc = ref._acc - self._acc
        self._acc = self._acc.reflect(norm_acc)
        
    def render(self, surface):
        draw.rect(surface, "red", self.rect, 1)