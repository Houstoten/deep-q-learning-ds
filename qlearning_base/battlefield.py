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
    battlemap = np.array([np.random.uniform(low=0, high=1 - i / n, size=(n,)) for i in range(n)])
    enemies, enemymap = generate_enemies(n)

    return (battlemap, enemies, enemymap)

def generate_enemies(n):
    enemymap = np.array([np.random.permutation([1 * np.random.uniform(low=0.4, high=1)] * math.ceil(1) + [0] * math.floor(n - 1)) for i in range(n)])
    enemies = np.array([Enemy(enemymap[x][y], Pos(x, y)) for [x, y] in np.transpose((enemymap > 0).nonzero())]);
    return enemies, enemymap


# window = pygame.display.set_mode((510,510))
active = True
n = 20
scale = 500 / n

WHITE = (255, 255, 255)
RED = (200,0,0)
BLUE1 = (0, 0, 255)
BLUE2 = (0, 100, 255)
BLACK = (0,0,0)

class BattlefieldAI:
    def __init__(self,  w=500, h=500):
        self.w = w
        self.h = h

        battlemap, enemies, enemymap = generate_data(n) 
        self.battlemap = battlemap
        # self.friendly_unit = Unit(100, 10, Pos(40, 40))
        # init display
        self.display = pygame.display.set_mode((self.w, self.h))
        pygame.display.set_caption('Battlefield')
        self.score = 0
        self.clock = pygame.time.Clock()
        self.reset()

    def reset(self):
        self.friendly_unit = Unit(30, 10, Pos(10, 10))
        self.frame_iteration = 0
        self.score = 0
        self.enemies, self.enemymap = generate_enemies(n)

    def play_step(self, action):
        self.frame_iteration += 1
        # 1. collect user input
        self._move(action) # update the head

        if self.is_collision():
            game_over = True
            reward = -10
            return reward, game_over, self.score

        pos_decay = self.battlemap[self.friendly_unit.pos.x][self.friendly_unit.pos.y]
        self.friendly_unit.health -= 2 * pos_decay
        
        # 3. check if game over
        reward = 0
        game_over = False
        if self.friendly_unit.health < 0:
            game_over = True
            reward = -10
            return reward, game_over, self.score

        # 4. check enemy or just move
        index, enemy = next(
            ((index, enemy) for (index, enemy) in enumerate(self.enemies) if enemy.pos.x == self.friendly_unit.pos.x and enemy.pos.y == self.friendly_unit.pos.y and enemy.health > 0),
            (None, None)
        )

        if enemy is not None:
            enemy.health = 0
            self.enemies[index] = enemy

            self.score += 1
            reward = 100
        else:
            reward = -10

        self._update_ui()
        self.clock.tick(100)

        # 6. return game over and score
        print("Health: ", self.friendly_unit.health, " Score: ", self.score, end = "\r")
        return reward, game_over, self.score


    def is_collision(self, pt=None):
        if pt is None:
            pt = self.friendly_unit.pos
        # hits boundary
        if pt.x * scale >= self.w or pt.x < 0 or pt.y * scale >= self.h or pt.y < 0:
            return True

        return False


    def _update_ui(self):
        self.display.fill(BLACK)

        for enemy in self.enemies:
            if enemy.health > 0: pygame.draw.rect(window, (255, 1 / (255 * enemy.threat), 255 * enemy.threat), pygame.Rect(enemy.pos.x * scale, enemy.pos.y * scale, scale, scale))

        pygame.draw.rect(window, (0,0,255), pygame.Rect(self.friendly_unit.pos.x * scale, self.friendly_unit.pos.y * scale, scale, scale))

        # text = font.render("Health: " + str(self.friendly_unit.health), True, WHITE)
        # self.display.blit(text, [0, 0])

        pygame.display.flip()

    def _move(self, action):
        x = self.friendly_unit.pos.x
        y = self.friendly_unit.pos.y

        if np.array_equal(action, [1, 0, 0, 0]):
            x += 1
        elif np.array_equal(action, [0, 1, 0, 0]):
            y += 1
        elif np.array_equal(action, [0, 0, 1, 0]):
            x -= 1
        else: 
            y -= 1

        if not self.is_collision(Pos(x, y)): self.friendly_unit.pos = Pos(x, y)
