import torch
import numpy as np
from model import Linear_QNet
from battlefield import generate_data, generate_enemies, Unit


model = Linear_QNet(8, 256, 4)
model.load_state_dict(torch.load('./model.pth'))
model.eval()

from battlefield import BattlefieldAI, Pos

def get_state(game, unit):
    point_l = Pos(unit.pos.x - 1, unit.pos.y)
    point_r = Pos(unit.pos.x + 1, unit.pos.y)
    point_u = Pos(unit.pos.x, unit.pos.y - 1)
    point_d = Pos(unit.pos.x, unit.pos.y + 1)
    enemy = list(filter(lambda enemy: enemy.health > 0, game.enemies))[0]

    bm_w_r = game.battlemap[point_r.x][point_r.y] if not game.is_collision(unit, point_r) else -1
    bm_w_l = game.battlemap[point_l.x][point_l.y] if not game.is_collision(unit, point_l) else -1
    bm_w_u = game.battlemap[point_u.x][point_u.y] if not game.is_collision(unit, point_u) else -1
    bm_w_d = game.battlemap[point_d.x][point_d.y] if not game.is_collision(unit, point_d) else -1

    bm_w_min = min([bm_w_r, bm_w_l, bm_w_u, bm_w_d])

    state = [

        bm_w_r == bm_w_min and bm_w_r != -1,
        bm_w_l == bm_w_min and bm_w_l != -1,
        bm_w_u == bm_w_min and bm_w_u != -1,
        bm_w_d == bm_w_min and bm_w_d != -1,

        enemy.pos.x < unit.pos.x,  # food left
        enemy.pos.x > unit.pos.x,  # food right
        enemy.pos.y < unit.pos.y,  # food up
        enemy.pos.y > unit.pos.y,  # food down
    ]

    return np.array(state, dtype=float)

def play():
    n = 80

    battlemap, _, _ = generate_data(n)
    enemies, _ = generate_enemies(n)
    allies = [Unit(30, 10, Pos(0, 0)), Unit(100, 5, Pos(n-3, n-3)), Unit(300, 10, Pos(0, n-3)), Unit(300, 20, Pos(n-3, 0))]
    battle = BattlefieldAI(n, battlemap, enemies, [])

    for i, allie in enumerate(allies):
        battle.allies = allies[:i]

        while(len(list(filter(lambda allie: allie.health > 0, battle.allies)))):

            for allie in battle.allies:
                state = get_state(battle, allie)

                pred = model(torch.tensor(state, dtype=torch.float))

                max_value = max(pred)
                pred_ = [1 if value == max_value else 0 for value in pred]

                reward, done, score = battle.play_step(pred_, allie)
            battle.tick_clock()

if __name__ == '__main__':
    play()