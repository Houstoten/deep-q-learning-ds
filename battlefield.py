import pygame
import numpy as np
import math
import random
from enum import Enum
from collections import namedtuple

# font = pygame.font.SysFont('arial', 25)

class Pos:
  def __init__(self, x, y):
    self.x = x
    self.y = y
  def __str__(self):
    return f"x = {self.x}, y is {self.y}"
    
class Enemy:
  def __init__(self, threat, pos):
    self.health = 10 * threat
    self.damage = 10 * threat
    self.threat = threat
    self.pos = pos
  def __str__(self):
    return f"health = {self.health}, pos = {self.pos}"

class Unit:
  def __init__(self, health, damage, pos):
    self.health = health
    self.damage = damage
    self.pos = pos

def generate_data(n):
    battlemap = np.array([np.random.uniform(low=0, high=1, size=(n,)) for i in range(n)])
    enemies, enemymap = generate_enemies(n)

    return (battlemap, enemies, enemymap)

def generate_enemies(n):
    enemymap = np.array([np.random.permutation([1 * np.random.uniform(low=0.4, high=1)] * math.ceil(1) + [0] * math.floor(n - 1)) for i in range(n)])
    enemies = np.array([Enemy(enemymap[x][y], Pos(x, y)) for [x, y] in np.transpose((enemymap > 0).nonzero())]);
    return enemies, enemymap


window = pygame.display.set_mode((510,510))
active = True
# n = 20
# scale = 500 / n

WHITE = (255, 255, 255)
RED = (200,0,0)
BLUE1 = (0, 0, 255)
BLUE2 = (0, 100, 255)
BLACK = (0,0,0)

class Direction(Enum):
    RIGHT = 1
    LEFT = 2
    UP = 3
    DOWN = 4

# friendly_unit = Unit(10, 10, Pos(50, 50))

# battlemap, enemies = generate_data(n) 

# clock = pygame.time.Clock()

# while active:
#    window.fill((0, 0, 0))
#    for event in pygame.event.get():
#       if event.type == pygame.QUIT:
#          active = False

#    pygame.draw.rect(window, (0,0,255), pygame.Rect(friendly_unit.pos.y * scale, friendly_unit.pos.x * scale, scale, scale))

#    for enemy in enemies[:1]:
#         pygame.draw.rect(window, (255, 1 / (255 * enemy.threat), 255 * enemy.threat), pygame.Rect(enemy.pos.y * scale, enemy.pos.x * scale, scale, scale))
# #    pygame.draw.circle(window,red,(circleX,circleY),radius) # DRAW CIRCLE

#    pygame.display.update()
#    pygame.display.flip()
#    clock.tick(10)
# #    friendly_unit.pos.x -= 1
#    friendly_unit.pos.y -= 1


class BattlefieldAI:

    def __init__(self, n, battlemap, enemies, allies, w=500, h=500):
        self.w = w
        self.h = h
        self.n = n
        self.scale = w / n

        # battlemap, enemies, enemymap = generate_data(n) 
        self.battlemap = battlemap
        self.enemies = enemies
        self.allies = allies
        # self.friendly_unit = Unit(100, 10, Pos(40, 40))
        # init display
        self.display = pygame.display.set_mode((self.w, self.h))
        pygame.display.set_caption('Battlefield')
        self.score = 0
        self.clock = pygame.time.Clock()
        self.frame_iteration = 0
        # self.reset()

    def reset(self):
        self.friendly_unit = Unit(300, 10, Pos(10, 10))
        self.frame_iteration = 0
        self.score = 0
        self.enemies, self.enemymap = generate_enemies(self.n)

    def tick_clock(self):
        self._update_ui()
        self.clock.tick(20)

    def play_step(self, action, allie):
        self.frame_iteration += 1
        # 1. collect user input
        self._move(action, allie) # update the head

        pos_decay = self.battlemap[allie.pos.x][allie.pos.y]
        allie.health -= pos_decay / 3
        
        # 3. check if game over
        reward = 0
        game_over = False
        if allie.health < 0:
            game_over = True
            reward = -1
            return reward, game_over, self.score

        # 4. check enemy or just move
        index, result = next(
            ((index, enemy) for (index, enemy) in enumerate(self.enemies) if enemy.pos.x == allie.pos.x and enemy.pos.y == allie.pos.y and enemy.health > 0),
            (None, None)
        )

        if result is not None:
            result.health -= allie.damage
            self.enemies[index] = result
            allie.health -= result.damage
            self.score += 1
            reward = 1
        else:
            reward = -1 -pos_decay

        # 5. update ui and clock

        # temp
        # self._update_ui()
        # self.clock.tick(20)

        # 6. return game over and score
        print("Health: ", allie.health, " Score: ", self.score, end = "\r")
        return reward, game_over, self.score


    def is_collision(self, allie, pt=None):
        if pt is None:
            pt = allie.pos
        # hits boundary
        if pt.x * self.scale >= self.w or pt.x < 0 or pt.y * self.scale >= self.h or pt.y < 0:
            return True

        return False


    def _update_ui(self):
        self.display.fill(BLACK)

        for enemy in self.enemies:
            if enemy.health > 0: pygame.draw.rect(window, (255, 1 / (255 * enemy.threat), 255 * enemy.threat), pygame.Rect(enemy.pos.x * self.scale, enemy.pos.y * self.scale, self.scale, self.scale))

        for allie in self.allies:
            if allie.health > 0: pygame.draw.rect(window, (0,0,255), pygame.Rect(allie.pos.x * self.scale, allie.pos.y * self.scale, self.scale, self.scale))

        pygame.display.flip()

    def _move(self, action, allie):
        x = allie.pos.x
        y = allie.pos.y

        if np.array_equal(action, [1, 0, 0, 0]):
            x += 1
        elif np.array_equal(action, [0, 1, 0, 0]):
            y += 1
        elif np.array_equal(action, [0, 0, 1, 0]):
            x -= 1
        else: 
            y -= 1

        if not self.is_collision(allie, Pos(x, y)): allie.pos = Pos(x, y)
