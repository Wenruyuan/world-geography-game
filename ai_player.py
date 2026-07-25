"""
人机对战 AI —— 为 player_b 自动规划行动
只读取上一回合结算后的状态，不看玩家当前 pending 行动
"""
import math
import random
from game_engine import GameEngine, Owner, Action, ATTACK_MULTIPLIER, RESOURCE_CITIES

# 难度：0=简单(随机), 1=普通(打分), 2=困难(模拟)
DIFFICULTY = 2


def plan_ai_actions(game: GameEngine) -> list:
    """为 player_b 规划至多 3 个行动，返回 Action 列表"""
    candidates = []
    my_cities = [c for c in game.cities.values() if c.owner == Owner.PLAYER_B]

    for city in my_cities:
        # --- 攻击邻城 ---
        for cid in city.connections:
            target = game.cities[cid]
            cost = game.calc_attack_cost(target.army)
            if city.army < 1:
                continue
            if target.owner == Owner.PLAYER_B:
                continue

            # 基础分 = 打得过的优先
            can_win = city.army > cost
            if target.owner == Owner.NPC:
                # 打NPC：偏好弱城、资源城
                score = 50 + (20 if target.army <= 2 else 0)
                score += (30 if city.army >= cost * 2 else 0)  # 碾压
                score += (40 if target.id in RESOURCE_CITIES else 0)
                army_to_send = min(city.army, max(cost + 5, int(city.army * 0.7)))
            else:
                # 打玩家：更谨慎，只偷袭弱城或空城
                score = 30 if target.army <= 3 else (-10 if not can_win else 10)
                army_to_send = min(city.army, max(cost, int(city.army * 0.8)))
                if target.army == 0:
                    score = 80  # 空城必偷
                    army_to_send = 3

            if DIFFICULTY == 0:
                score = random.randint(0, 100)

            candidates.append({
                'type': 'attack', 'score': score,
                'from': city.id, 'to': cid,
                'army': max(1, army_to_send),
                'can_win': can_win,
            })

        # --- 增援邻城 ---
        for cid in city.connections:
            target = game.cities[cid]
            if target.owner != Owner.PLAYER_B:
                continue
            if city.army < 2:
                continue
            # 往"前线"城（邻敌多的城）增援
            enemy_neighbors = sum(1 for n in target.connections
                                  if game.cities[n].owner != Owner.PLAYER_B)
            my_enemy_neighbors = sum(1 for n in city.connections
                                     if game.cities[n].owner != Owner.PLAYER_B)
            # 从后方往前线送
            if enemy_neighbors > my_enemy_neighbors:
                amt = min(city.army - 1, int(city.army * 0.5))
                score = 20 + enemy_neighbors * 5 - my_enemy_neighbors * 3
                if DIFFICULTY == 0:
                    score = random.randint(0, 100)
                candidates.append({
                    'type': 'move', 'score': score,
                    'from': city.id, 'to': cid,
                    'army': max(1, amt),
                })

    # 按分数排序
    candidates.sort(key=lambda x: x['score'], reverse=True)

    # 困难模式：对 top 候选做简易模拟
    if DIFFICULTY >= 2 and len(candidates) > 3:
        candidates = _simulate_top(game, candidates, 5)

    # 取 top 3，但要去重（同一源城的攻击只取最高分的一个）
    chosen = []
    used_sources = set()
    for c in candidates:
        key = (c['from'], c['type'])
        if key in used_sources:
            continue  # 同城同类行动只取一个
        if len(chosen) >= 3:
            break
        used_sources.add(key)
        chosen.append(c)

    actions = []
    for c in chosen:
        target_city = game.cities[c['to']]
        action = Action(
            player=Owner.PLAYER_B,
            from_city=c['from'],
            to_city=c['to'],
            army=c['army'],
            target_owner=target_city.owner.value,
        )
        valid, _ = game.validate_action(action)
        if valid:
            actions.append(action)

    return actions


def _simulate_top(game, candidates, top_n):
    """简易模拟：对前 N 个候选，估算执行后我方总兵力变化，重排序"""
    scored = []
    for c in candidates[:top_n]:
        # 模拟：如果我执行这个行动，预期的兵力变化
        src = game.cities[c['from']]
        dst = game.cities[c['to']]
        if c['type'] == 'attack':
            cost = game.calc_attack_cost(dst.army)
            committed = min(c['army'], src.army)
            if committed > cost:
                gain = committed - cost  # 攻占后获得的兵力
            else:
                gain = -committed  # 失败损失
        else:
            gain = -c['army']  # 增援失去兵力（但友方获得）
        scored.append((gain, c))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [s[1] for s in scored] + candidates[top_n:]
