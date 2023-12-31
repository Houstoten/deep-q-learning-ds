import torch
import random
import numpy as np
from collections import deque
from battlefield_train import Direction, BattlefieldAI, Pos
from model import Linear_QNet, QTrainer
from functools import reduce
from helper import plot

MAX_MEMORY = 100_000
BATCH_SIZE = 1000
LR = 0.001

class Agent:

    def __init__(self):
        self.n_games = 0
        self.epsilon = 0 # randomness
        self.gamma = 0.9 # discount rate
        self.memory = deque(maxlen=MAX_MEMORY) # popleft()
        self.model = Linear_QNet(12, 256, 4)
        self.trainer = QTrainer(self.model, lr=LR, gamma=self.gamma)


    def get_state(self, game):
        unit = game.friendly_unit
        point_l = Pos(unit.pos.x - 1, unit.pos.y)
        point_r = Pos(unit.pos.x + 1, unit.pos.y)
        point_u = Pos(unit.pos.x, unit.pos.y - 1)
        point_d = Pos(unit.pos.x, unit.pos.y + 1)


        sq_radius = 15
        enemies = sorted(list(filter(lambda enemy: enemy.health > 0 and abs(enemy.pos.x - unit.pos.x) < sq_radius and abs(enemy.pos.y - unit.pos.y) < sq_radius, game.enemies)), key=lambda e: e.health)

        # acc_x = [0, 0]
        # for enemy in game.enemies:
        #     acc_x = [acc_x[0] + enemy.health, acc_x[1]] if enemy.pos.x < game.friendly_unit.pos.x else [acc_x[0], acc_x[1] + enemy.health]

        # acc_y = [0, 0]
        # for enemy in game.enemies:
        #     acc_y = [acc_y[0] + enemy.health, acc_y[1]] if enemy.pos.y < game.friendly_unit.pos.y else [acc_y[0], acc_y[1] + enemy.health]

        bm_w_r = game.battlemap[point_r.x][point_r.y] if not game.is_collision(point_r) else -1
        bm_w_l = game.battlemap[point_l.x][point_l.y] if not game.is_collision(point_l) else -1
        bm_w_u = game.battlemap[point_u.x][point_u.y] if not game.is_collision(point_u) else -1
        bm_w_d = game.battlemap[point_d.x][point_d.y] if not game.is_collision(point_d) else -1

        bm_w_min = min([bm_w_r, bm_w_l, bm_w_u, bm_w_d])

        state = [
            (game.is_collision(point_r)),
            (game.is_collision(point_l)),
            (game.is_collision(point_u)),
            (game.is_collision(point_d)),

            bm_w_r == bm_w_min and bm_w_r != -1,
            bm_w_l == bm_w_min and bm_w_l != -1,
            bm_w_u == bm_w_min and bm_w_u != -1,
            bm_w_d == bm_w_min and bm_w_d != -1,

#####
            # (game.battlemap[point_r.x][point_r.y] > 0.5 if not  game.is_collision(point_r) else 0),
            # (game.battlemap[point_l.x][point_l.y] > 0.5 if not  game.is_collision(point_l) else 0),
            # (game.battlemap[point_u.x][point_u.y] > 0.5 if not  game.is_collision(point_u) else 0),
            # (game.battlemap[point_d.x][point_d.y] > 0.5 if not  game.is_collision(point_d) else 0),

            # (game.enemymap[point_r.x][point_r.y]*10 < game.friendly_unit.health if not game.is_collision(point_r) else 0),
            # (game.enemymap[point_l.x][point_l.y]*10 < game.friendly_unit.health if not  game.is_collision(point_l) else 0),
            # (game.enemymap[point_u.x][point_u.y]*10 < game.friendly_unit.health if not  game.is_collision(point_u) else 0),
            # (game.enemymap[point_d.x][point_d.y]*10 < game.friendly_unit.health if not  game.is_collision(point_d) else 0),
#####

            # Danger bottom
            # (dir_l and game.is_collision(point_r)) or 
            # (dir_r and game.is_collision(point_l)) or 
            # (dir_d and game.is_collision(point_u)) or 
            # (dir_u and game.is_collision(point_d)),

            # # Danger right
            # (dir_u and game.is_collision(point_r)) or 
            # (dir_d and game.is_collision(point_l)) or 
            # (dir_l and game.is_collision(point_u)) or 
            # (dir_r and game.is_collision(point_d)),

            # # Danger left
            # (dir_d and game.is_collision(point_r)) or 
            # (dir_u and game.is_collision(point_l)) or 
            # (dir_r and game.is_collision(point_u)) or 
            # (dir_l and game.is_collision(point_d)),

            
            # Move direction
            # dir_l,
            # dir_r,
            # dir_u,
            # dir_d, 

            # Enemy health location fraction
            # acc_x[0] > acc_x[1],
            # acc_x[0] < acc_x[1],
            # acc_y[0] > acc_y[1],
            # acc_y[0] < acc_y[1],

            # acc_x[0] / max(np.sum(acc_x), 1),
            # acc_x[1] / max(np.sum(acc_x), 1),
            # acc_y[0] / max(np.sum(acc_y), 1),
            # acc_y[1] / max(np.sum(acc_y), 1),

            enemies[0].pos.x < unit.pos.x if len(enemies) > 0 else 0,  # food left
            enemies[0].pos.x > unit.pos.x if len(enemies) > 0 else 0,  # food right
            enemies[0].pos.y < unit.pos.y if len(enemies) > 0 else 0,  # food up
            enemies[0].pos.y > unit.pos.y if len(enemies) > 0 else 0,  # food down
           ]

        return np.array(state, dtype=float)

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done)) # popleft if MAX_MEMORY is reached

    def train_long_memory(self):
        if len(self.memory) > BATCH_SIZE:
            mini_sample = random.sample(self.memory, BATCH_SIZE) # list of tuples
        else:
            mini_sample = self.memory

        states, actions, rewards, next_states, dones = zip(*mini_sample)
        self.trainer.train_step(states, actions, rewards, next_states, dones)
        #for state, action, reward, nexrt_state, done in mini_sample:
        #    self.trainer.train_step(state, action, reward, next_state, done)

    def train_short_memory(self, state, action, reward, next_state, done):
        self.trainer.train_step(state, action, reward, next_state, done)

    def get_action(self, state):
        # random moves: tradeoff exploration / exploitation
        self.epsilon = 80 - self.n_games
        final_move = [0,0,0,0]
        if random.randint(0, 200) < self.epsilon:
            move = random.randint(0, 2)
            final_move[move] = 1
        else:
            state0 = torch.tensor(state, dtype=torch.float)
            prediction = self.model(state0)
            move = torch.argmax(prediction).item()
            final_move[move] = 1

        return final_move


def train():
    plot_scores = []
    plot_mean_scores = []
    total_score = 0
    record = 0
    agent = Agent()
    game = BattlefieldAI()
    while True:
        # get old state
        state_old = agent.get_state(game)

        # get move
        final_move = agent.get_action(state_old)

        # perform move and get new state
        reward, done, score = game.play_step(final_move)
        state_new = agent.get_state(game)

        # train short memory
        agent.train_short_memory(state_old, final_move, reward, state_new, done)

        # remember
        agent.remember(state_old, final_move, reward, state_new, done)

        if done:
            # train long memory, plot result
            game.reset()
            agent.n_games += 1
            agent.train_long_memory()

            if score > record:
                record = score
                agent.model.save()

            print('\nGame', agent.n_games, 'Score', score, 'Record:', record)

            plot_scores.append(score)
            total_score += score
            mean_score = total_score / agent.n_games
            plot_mean_scores.append(mean_score)
            plot(plot_scores, plot_mean_scores)


if __name__ == '__main__':
    train()