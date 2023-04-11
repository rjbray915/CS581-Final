from pygame.math import Vector2
from pygame import draw
from pygame import Rect
from pygame import math
from pygame.sprite import Sprite

class Circle(Sprite):
    _pos: Vector2
    _vel: Vector2
    _acc: Vector2
    
    def __init__(self, pos_init: tuple, vel_init: tuple, acc_init: tuple, radius: int = 40, color: str = "blue"):
        # parent constructor
        Sprite.__init__(self)
        
        self._pos = Vector2(pos_init[0], pos_init[1])
        self._vel = Vector2(vel_init[0], vel_init[1])
        self._acc = Vector2(acc_init[0], acc_init[1])
        self._radius = radius
        self._color = color
        
        # bounding box
        self.rect = Rect(self._pos.x - self._radius, 
                          self._pos.y - self._radius,
                          self._radius * 2,
                          self._radius * 2)
        
    def on_tick(self, dt):
        self._prev_pos = self._pos
        self._pos += self._vel * dt
        self._vel += self._acc * dt
        
        # move bounding box
        self.rect.centerx = self._pos.x
        self.rect.centery = self._pos.y
        
    def reflect_wall(self, ref, dt):
        # walls using their norm vect
        self._pos = self._prev_pos
        self._vel = self._vel.reflect(ref._norm_vect)
        self._acc = self._acc.reflect(ref._norm_vect)
        
    def reflect_obj(self, ref, dt):
        my_vel = self._vel.copy()
        ref_vel = ref._vel.copy()
        my_acc = self._acc.copy()
        ref_acc = ref._acc.copy()
        
        #objects by calculating their norm vects
        norm_vel = ref_vel - my_vel
        norm_acc = ref_acc - my_acc
        self._vel = self._vel.reflect(norm_vel)
        self._acc = self._acc.reflect(norm_acc)
        
        norm_vel = my_vel - ref_vel
        norm_acc = my_vel - ref_acc
        ref._vel = ref._vel.reflect(norm_vel)
        ref._acc = ref._acc.reflect(norm_acc)
        
    def render(self, surface):
        draw.circle(surface, self._color, self._pos, 40)
        draw.rect(surface, "red", self.rect, 1)