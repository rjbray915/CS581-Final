from pygame.math import Vector2
from pygame import draw
from pygame import Rect
from pygame import math
from pygame.sprite import Sprite
import math

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
        self._mass = self._radius
        
        # bounding box
        self.rect = Rect(self._pos.x - self._radius, 
                          self._pos.y - self._radius,
                          self._radius * 2,
                          self._radius * 2)
        
    def on_tick(self, dt):
        self._prev_pos = self._pos
        self._pos += self._vel * dt + 0.5 * self._acc * dt*dt
        self._vel += self._acc * dt
        
        # move bounding box
        self.rect.centerx = self._pos.x
        self.rect.centery = self._pos.y
        
    def reflect_wall(self, ref, dt):
        # walls using their norm vect
        self._pos = ref._
        self._vel = self._vel.reflect(ref._norm_vect)
        #self._acc = self._acc.reflect(ref._norm_vect)
        
    def elastic_collide(p1, p2, v1, v2, m1, m2):
        mass_term = 2 * m2 / (m1 + m2)
        if p1 == p2:
            p1.x += 0.0001
            p1.y += 0.0001
        dot_term = (Vector2.dot(v1 - v2, p1 - p2) / Vector2.dot(p1 - p2, p1 - p2))
        dot_term *= (p1 - p2)
        return v1 - mass_term * dot_term
    
    def is_colliding_circle(self, ref):
        dist = math.sqrt(math.pow(ref._pos.x - self._pos.x, 2) + math.pow(ref._pos.y - self._pos.y, 2))
        return dist < (self._radius + ref._radius)
        
    def reflect_obj(self, ref, dt):
        # work in progress for "nudging" -- need to change circle collision first
        # let's try nudging based on the angle they currently are
        nudge_total = self._radius + ref._radius
        dist_x = self._pos.x - ref._pos.x
        dist_y = self._pos.y - ref._pos.y
        if (abs(dist_x) > 0):
            ang = math.atan(dist_y / dist_x)
        else:
            ang = 0
        
        nudge_x = abs(nudge_total * math.cos(ang))
        nudge_y = abs(nudge_total * math.sin(ang))
        if self._pos.x < ref._pos.x:
            self._pos.x = ref._pos.x - nudge_x
        else:
            self._pos.x = ref._pos.x + nudge_x
        if self._pos.y < ref._pos.y:
            self._pos.y = ref._pos.y - nudge_y
        else:
            self._pos.y = ref._pos.y + nudge_y
            
        # self._pos = self._prev_pos
        # ref._pos = ref._prev_pos

        my_vel = self._vel.copy()
        ref_vel = ref._vel.copy()
        my_acc = self._acc.copy()
        ref_acc = ref._acc.copy()
        
        self._vel = Circle.elastic_collide(self._pos, ref._pos, my_vel, ref_vel, self._mass, ref._mass)
        #self._acc = Circle.elastic_collide(self._pos, ref._pos, my_acc, ref_acc, self._mass, ref._mass)
        ref._vel = Circle.elastic_collide(ref._pos, self._pos, ref_vel, my_vel, ref._mass, self._mass)
        #ref._acc = Circle.elastic_collide(ref._pos, self._pos, ref_acc, my_acc, ref._mass, self._mass)
        
        # self._pos -= self._vel * dt
        # ref._pos -= ref._vel * dt
        
        # velocity for self
        # my_mass_term = 2 * ref._mass / (self._mass + ref._mass)
        # my_dot_term = (Vector2.dot(self._vel - ref._vel, self._pos - ref._pos) / Vector2.dot(self._pos - ref._pos, self._pos - ref._pos))
        # my_dot_term *= (self._pos - ref._pos)
        # my_vel -= (my_mass_term * my_dot_term)
        # self._vel = my_vel
        
        # #velocity for ref
        # ref_mass_term = 2 * self._mass / (ref._mass + self._mass)
        # ref_dot_term = (Vector2.dot(ref._vel - self._vel, ref._pos - self._pos) / Vector2.dot(ref._pos - self._pos, ref._pos - self._pos))
        # ref_dot_term *= (ref._pos - self._pos)
        # ref_vel -= (ref_mass_term * ref_dot_term)
        # ref._vel = ref_vel
        
        #objects by calculating their norm vects
        # norm_vel = ref_vel - my_vel
        # norm_acc = ref_acc - my_acc
        # self._vel = self._vel.reflect(norm_vel)
        # self._acc = self._acc.reflect(norm_acc)
        
        # norm_vel = my_vel - ref_vel
        # norm_acc = my_vel - ref_acc
        # ref._vel = ref._vel.reflect(norm_vel)
        # ref._acc = ref._acc.reflect(norm_acc)
        
    def render(self, surface):
        draw.circle(surface, self._color, self._pos, self._radius)
        # draw.rect(surface, "red", self.rect, 1)