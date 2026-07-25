"""
世界地理战略推演游戏 - 核心引擎
World Geography Strategic Simulation Game - Core Engine
"""

import math
import random
import uuid
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from enum import Enum


# ==================== 常量配置 ====================
ATTACK_MULTIPLIER = 1.5
INITIAL_TROOPS = 10
MAX_ACTIONS_PER_TURN = 3
MAX_TURNS = 150

# 资源丰富城市：被玩家占领后每回合额外+2兵
RESOURCE_CITIES = {'riyadh', 'tehran', 'kabul', 'yekaterinburg', 'tashkent', 'novosibirsk', 'baikal'}


# ==================== 城市数据（74个世界城市，含经纬度用于地球仪）====================
# lng=-180~180, lat=-90~90（负=南/西）
CITIES_DATA = [
    {"id": "reykjavik", "name": "冰岛", "x": 80, "y": 80},
    {"id": "london", "name": "伦敦", "x": 200, "y": 160},
    {"id": "stockholm", "name": "北欧", "x": 380, "y": 130},
    {"id": "stpetersburg", "name": "圣彼得堡", "x": 560, "y": 130},
    {"id": "berlin", "name": "柏林", "x": 200, "y": 280},
    {"id": "warsaw", "name": "波兰", "x": 380, "y": 280},
    {"id": "kiev", "name": "基辅", "x": 540, "y": 280},
    {"id": "moscow", "name": "莫斯科", "x": 700, "y": 260},
    {"id": "yekaterinburg", "name": "叶卡捷琳堡", "x": 880, "y": 260},
    {"id": "paris", "name": "巴黎", "x": 100, "y": 380},
    {"id": "vienna", "name": "奥地利", "x": 360, "y": 390},
    {"id": "madrid", "name": "西班牙", "x": 60, "y": 500},
    {"id": "athens", "name": "希腊", "x": 460, "y": 480},
    {"id": "istanbul", "name": "土耳其", "x": 480, "y": 580},
    {"id": "riyadh", "name": "沙特阿拉伯", "x": 380, "y": 680},
    {"id": "tehran", "name": "伊朗", "x": 540, "y": 680},
    {"id": "pakistan", "name": "巴基斯坦", "x": 560, "y": 780},
    {"id": "delhi", "name": "新德里", "x": 560, "y": 880},
    {"id": "bangladesh", "name": "孟加拉", "x": 720, "y": 880},
    {"id": "nagpur", "name": "那格浦尔", "x": 560, "y": 980},
    {"id": "hyderabad", "name": "海得拉巴", "x": 560, "y": 1080},
    {"id": "colombo", "name": "科伦坡", "x": 560, "y": 1200},
    {"id": "nafrica", "name": "北非", "x": 320, "y": 800},
    {"id": "cafrica", "name": "中非", "x": 320, "y": 940},
    {"id": "capetown", "name": "好望角", "x": 260, "y": 1300},
    {"id": "tashkent", "name": "塔什干", "x": 780, "y": 440},
    {"id": "kabul", "name": "阿富汗", "x": 700, "y": 680},
    {"id": "lhasa", "name": "拉萨", "x": 880, "y": 700},
    {"id": "urumqi", "name": "乌鲁木齐", "x": 960, "y": 580},
        {"id": "vientiane", "name": "万象", "x": 900, "y": 920},
    {"id": "phnompenh", "name": "金边", "x": 720, "y": 1320},
    {"id": "singapore", "name": "新加坡", "x": 720, "y": 1450},
    {"id": "jakarta", "name": "雅加达", "x": 880, "y": 1500},
    {"id": "brunei", "name": "文莱", "x": 900, "y": 1350},
    {"id": "dili", "name": "帝力", "x": 1050, "y": 1500},
    {"id": "manila", "name": "马尼拉", "x": 1200, "y": 1280},
    {"id": "oymyakon", "name": "奥伊米亚康", "x": 1080, "y": 60},
    {"id": "bering", "name": "白令海峡", "x": 1300, "y": 60},
    {"id": "novosibirsk", "name": "新西伯利亚", "x": 1080, "y": 160},
    {"id": "baikal", "name": "贝加尔湖", "x": 1260, "y": 160},
    {"id": "vladivostok", "name": "海参崴", "x": 1420, "y": 160},
    {"id": "haerbin", "name": "哈尔滨", "x": 1260, "y": 300},
    {"id": "japan", "name": "日本", "x": 1680, "y": 200},
    {"id": "beijing", "name": "北京", "x": 1100, "y": 400},
    {"id": "lianyungang", "name": "连云港", "x": 1260, "y": 400},
    {"id": "shandong", "name": "山东", "x": 1260, "y": 530},
    {"id": "xian", "name": "西安", "x": 1100, "y": 520},
    {"id": "nanjing", "name": "南京", "x": 1420, "y": 540},
    {"id": "wuhan", "name": "武汉", "x": 1100, "y": 660},
    {"id": "fuzhou", "name": "福建", "x": 1550, "y": 720},
    {"id": "taiwan", "name": "台湾", "x": 1580, "y": 820},
    {"id": "kunming", "name": "昆明", "x": 1100, "y": 820},
    {"id": "hongkong", "name": "香港", "x": 1420, "y": 820},
    {"id": "hekou", "name": "河口", "x": 1100, "y": 960},
    {"id": "alaska", "name": "阿拉斯加", "x": 1680, "y": 60},
    {"id": "greenland", "name": "格陵兰", "x": 2340, "y": 160},
    {"id": "edmonton", "name": "埃德蒙顿", "x": 1820, "y": 160},
    {"id": "winnipeg", "name": "温尼伯", "x": 2020, "y": 160},
    {"id": "ottawa", "name": "渥太华", "x": 2220, "y": 160},
    {"id": "vancouver", "name": "温哥华", "x": 1820, "y": 300},
    {"id": "honolulu", "name": "檀香山", "x": 1660, "y": 610},
    {"id": "sanfrancisco", "name": "旧金山", "x": 2020, "y": 400},
    {"id": "chicago", "name": "芝加哥", "x": 2220, "y": 400},
    {"id": "newyork", "name": "纽约", "x": 2220, "y": 520},
    {"id": "losangeles", "name": "洛杉矶", "x": 1820, "y": 560},
    {"id": "neworleans", "name": "新奥尔良", "x": 2020, "y": 520},
    {"id": "miami", "name": "迈阿密", "x": 2220, "y": 640},
    {"id": "amazon", "name": "亚马孙", "x": 2020, "y": 800},
    {"id": "brazil", "name": "巴西", "x": 2020, "y": 920},
    {"id": "riodejaneiro", "name": "里约热内卢", "x": 2220, "y": 920},
    {"id": "argentina", "name": "阿根廷", "x": 2020, "y": 1040},
    {"id": "santiago", "name": "圣地亚哥", "x": 1820, "y": 1040},
    {"id": "neau", "name": "东北澳", "x": 1820, "y": 1200},
    {"id": "swau", "name": "西南澳", "x": 1400, "y": 1500},
    {"id": "lanzhou", "name": "兰州", "x": 960, "y": 660},
]














# ==================== 连接边（无向，弯曲线由前端根据距离自动渲染）====================
EDGES = [
    ("amazon", "brazil"),
    ("athens", "istanbul"),
    ("baikal", "vladivostok"),
    ("bangladesh", "hyderabad"),
    ("bangladesh", "nagpur"),
    ("bangladesh", "vientiane"),
    ("beijing", "shandong"),
    ("beijing", "lianyungang"),
    ("beijing", "xian"),
    ("bering", "alaska"),
    ("alaska", "edmonton"),
    ("edmonton", "vancouver"),
    ("berlin", "paris"),
    ("berlin", "vienna"),
    ("berlin", "warsaw"),
    ("brazil", "argentina"),
    ("brazil", "riodejaneiro"),
    ("brunei", "phnompenh"),
    ("brunei", "dili"),
    ("brunei", "jakarta"),
    ("cafrica", "capetown"),
    ("capetown", "swau"),
    ("chicago", "ottawa"),
    ("chicago", "neworleans"),
    ("chicago", "newyork"),
    ("colombo", "capetown"),
    ("colombo", "singapore"),
    ("colombo", "swau"),
    ("delhi", "bangladesh"),
    ("delhi", "nagpur"),
    ("dili", "manila"),
    ("edmonton", "winnipeg"),
    ("greenland", "ottawa"),
    ("fuzhou", "hongkong"),
    ("fuzhou", "taiwan"),
    ("haerbin", "beijing"),
    ("haerbin", "lianyungang"),
    ("honolulu", "taiwan"),
    ("honolulu", "losangeles"),
    ("honolulu", "sanfrancisco"),
    ("istanbul", "tehran"),
    ("hyderabad", "colombo"),
    ("jakarta", "dili"),
    ("jakarta", "swau"),
    ("japan", "honolulu"),
    ("japan", "lianyungang"),
    ("japan", "taiwan"),
    ("japan", "vancouver"),
    ("kabul", "pakistan"),
    ("kiev", "moscow"),
    ("kunming", "hongkong"),
    ("kunming", "hekou"),
    ("lanzhou", "lhasa"),
    ("lanzhou", "xian"),
    ("lhasa", "pakistan"),
    ("lianyungang", "shandong"),
    ("london", "berlin"),
    ("london", "stockholm"),
    ("losangeles", "neworleans"),
    ("manila", "neau"),
    ("manila", "taiwan"),
    ("miami", "amazon"),
    ("moscow", "yekaterinburg"),
    ("nafrica", "cafrica"),
    ("nagpur", "hyderabad"),
    ("nanjing", "fuzhou"),
    ("nanjing", "hongkong"),
    ("nanjing", "kunming"),
    ("nanjing", "wuhan"),
    ("neau", "argentina"),
    ("neau", "brazil"),
    ("neau", "swau"),
    ("neau", "santiago"),
    ("amazon", "neworleans"),
    ("neworleans", "miami"),
    ("newyork", "miami"),
    ("novosibirsk", "baikal"),
    ("oymyakon", "bering"),
    ("oymyakon", "novosibirsk"),
    ("pakistan", "delhi"),
    ("paris", "athens"),
    ("paris", "madrid"),
    ("paris", "vienna"),
    ("phnompenh", "singapore"),
    ("london", "newyork"),
    ("london", "miami"),
    ("riodejaneiro", "capetown"),
    ("argentina", "capetown"),
    ("reykjavik", "greenland"),
    ("reykjavik", "london"),
    ("riyadh", "nafrica"),
    ("riyadh", "tehran"),
    ("sanfrancisco", "chicago"),
    ("sanfrancisco", "losangeles"),
    ("santiago", "amazon"),
    ("santiago", "brazil"),
    ("shandong", "nanjing"),
    ("shandong", "wuhan"),
    ("singapore", "brunei"),
    ("singapore", "jakarta"),
    ("stockholm", "stpetersburg"),
    ("stpetersburg", "moscow"),
    ("taiwan", "fuzhou"),
    ("taiwan", "neau"),
    ("tashkent", "kabul"),
    ("tashkent", "urumqi"),
    ("tehran", "kabul"),
    ("urumqi", "lanzhou"),
    ("vancouver", "sanfrancisco"),
    ("vancouver", "winnipeg"),
    ("vienna", "athens"),
    ("vienna", "kiev"),
    ("vientiane", "hekou"),
    ("vientiane", "phnompenh"),
    ("vladivostok", "haerbin"),
    ("vladivostok", "japan"),
    ("warsaw", "kiev"),
    ("warsaw", "vienna"),
    ("winnipeg", "chicago"),
    ("winnipeg", "ottawa"),
    ("wuhan", "kunming"),
    ("xian", "shandong"),
    ("xian", "wuhan"),
    ("yekaterinburg", "novosibirsk"),
    ("yekaterinburg", "tashkent"),
]














# ==================== 数据结构（不变）====================

class Owner(Enum):
    UNASSIGNED = "unassigned"
    PLAYER_A = "player_a"
    PLAYER_B = "player_b"
    NPC = "npc"

OWNER_DISPLAY = {
    Owner.UNASSIGNED: {"name": "未分配",   "color": "#666666"},
    Owner.PLAYER_A:   {"name": "蓝方",     "color": "#4A90D9"},
    Owner.PLAYER_B:   {"name": "红方",     "color": "#D94A4A"},
    Owner.NPC:        {"name": "NPC 武装", "color": "#F5A623"},
}

@dataclass
class City:
    id: str
    name: str
    x: float = 0.0
    y: float = 0.0
    connections: List[str] = field(default_factory=list)
    army: int = 0
    owner: Owner = Owner.UNASSIGNED

    @property
    def connection_count(self) -> int:
        return len(self.connections)

    def to_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name,
            "x": self.x, "y": self.y,
            "connections": self.connections,
            "army": self.army, "owner": self.owner.value,
            "connection_count": self.connection_count,
        }

@dataclass
class Action:
    player: Owner
    from_city: str
    to_city: str
    army: int
    target_owner: str = ""

    @property
    def action_type(self) -> str:
        if self.target_owner and self.target_owner != self.player.value:
            return "attack"
        return "move"

    def to_dict(self) -> dict:
        return {
            "player": self.player.value,
            "from_city": self.from_city,
            "to_city": self.to_city,
            "army": self.army,
            "type": self.action_type,
        }

@dataclass
class BattleResult:
    attacker: Owner
    defender: Owner
    from_city: str
    to_city: str
    attack_troops: int
    defender_troops_before: int
    success: bool
    remaining_troops: int
    city_captured: bool
    new_owner: Optional[Owner] = None

    def to_dict(self) -> dict:
        return {
            "attacker": self.attacker.value,
            "defender": self.defender.value,
            "from_city": self.from_city,
            "to_city": self.to_city,
            "attack_troops": self.attack_troops,
            "defender_troops_before": self.defender_troops_before,
            "success": self.success,
            "remaining_troops": self.remaining_troops,
            "city_captured": self.city_captured,
            "new_owner": self.new_owner.value if self.new_owner else None,
        }


# ==================== 游戏引擎 ====================

class GameEngine:

    def __init__(self):
        self.id = str(uuid.uuid4())[:8]
        self.cities: Dict[str, City] = {}
        self.turn: int = 1
        self.game_over: bool = False
        self.winner: Optional[Owner] = None
        self.pending_actions: List[Action] = []
        self.action_log: List[dict] = []
        self.battle_results: List[BattleResult] = []
        self._init_cities()

    def _init_cities(self):
        for c in CITIES_DATA:
            self.cities[c["id"]] = City(id=c["id"], name=c["name"], x=c["x"], y=c["y"])
        for a, b in EDGES:
            if a in self.cities and b in self.cities:
                self.cities[a].connections.append(b)
                self.cities[b].connections.append(a)

    def setup_game(self):
        all_ids = list(self.cities.keys())
        random.shuffle(all_ids)
        city_a = self.cities[all_ids[0]]
        city_a.owner = Owner.PLAYER_A
        city_a.army = INITIAL_TROOPS
        city_b = self.cities[all_ids[1]]
        city_b.owner = Owner.PLAYER_B
        city_b.army = INITIAL_TROOPS
        for cid in all_ids[2:]:
            c = self.cities[cid]
            c.owner = Owner.NPC
            c.army = int(c.connection_count * 1.5)
        self.action_log.append({
            "type": "system",
            "message": f"游戏开始！蓝方[{city_a.name}]，红方[{city_b.name}]"
        })

    def reinforce(self):
        gains = {Owner.PLAYER_A: 0, Owner.PLAYER_B: 0}
        for city in self.cities.values():
            if city.owner in gains:
                gain = city.connection_count
                if city.id in RESOURCE_CITIES:
                    gain += 2  # 资源城市额外+2兵
                city.army += gain
                gains[city.owner] += gain
        return gains

    @staticmethod
    def calc_attack_cost(defender_army: int) -> int:
        return math.ceil(defender_army * ATTACK_MULTIPLIER)

    def _pending_incoming(self, city_id: str, player: Owner) -> int:
        total = 0
        for a in self.pending_actions:
            if a.player == player and a.action_type == "move" and a.to_city == city_id:
                total += a.army
        return total

    def get_valid_targets(self, city_id: str) -> List[dict]:
        city = self.cities.get(city_id)
        if not city:
            return []
        targets = []
        for cid in city.connections:
            target = self.cities[cid]
            is_friendly = (target.owner == city.owner)
            if is_friendly:
                cost_needed = 1
            else:
                cost_needed = self.calc_attack_cost(target.army)
            targets.append({
                "id": cid, "name": target.name,
                "owner": target.owner.value, "army": target.army,
                "can_attack": city.army >= 1 and not is_friendly,
                "can_move": city.army >= 1 and is_friendly,
                "cost_needed": cost_needed,
                "is_chain_from": city_id,
            })
        return targets

    def validate_action(self, action: Action) -> tuple:
        if self.game_over:
            return False, "游戏已经结束"
        src = self.cities.get(action.from_city)
        dst = self.cities.get(action.to_city)
        if not src or not dst:
            return False, "城市不存在"
        if src.owner != action.player:
            chain_found = any(
                pa for pa in self.pending_actions
                if pa.to_city == src.id and pa.player == action.player and pa.action_type == "attack"
            )
            if not chain_found:
                return False, f"你不拥有{src.name}（可先规划攻打该城的行动，再以此为起点继续）"
            return True, "连锁行动已添加"
        if dst.id not in src.connections:
            return False, f"{src.name}和{dst.name}不相邻"
        effective_army = src.army + self._pending_incoming(src.id, action.player)
        if action.army < 1:
            return False, "至少派1个兵力"
        if action.army > effective_army:
            return False, f"兵力不足（当前{src.army}，含pending增援后{effective_army}）"
        return True, "合法"

    # -------- 结算 --------
    def resolve_turn(self) -> List[dict]:
        results: List[dict] = []
        actions = list(self.pending_actions)
        if not actions:
            return results
        blue_moves  = [a for a in actions if a.player == Owner.PLAYER_A and a.action_type == "move"]
        red_moves   = [a for a in actions if a.player == Owner.PLAYER_B and a.action_type == "move"]
        blue_attacks = [a for a in actions if a.player == Owner.PLAYER_A and a.action_type == "attack"]
        red_attacks  = [a for a in actions if a.player == Owner.PLAYER_B and a.action_type == "attack"]
        simultaneous_npc: Set[str] = set()
        blue_atk_targets = {a.to_city for a in blue_attacks}
        for a in red_attacks:
            if a.to_city in blue_atk_targets:
                target = self.cities.get(a.to_city)
                if target and target.owner not in (Owner.PLAYER_A, Owner.PLAYER_B):
                    simultaneous_npc.add(a.to_city)
        processed: Set[int] = set()

        def process_move(a: Action):
            if id(a) in processed:
                return
            processed.add(id(a))
            src = self.cities.get(a.from_city)
            dst = self.cities.get(a.to_city)
            if not src or not dst:
                return
            if src.owner != a.player or dst.owner != a.player:
                return
            if src.army < a.army:
                return
            src.army -= a.army
            dst.army += a.army
            results.append({"type": "move", "player": a.player.value, "from": src.name, "to": dst.name, "army": a.army})

        for a in blue_moves: process_move(a)
        for a in red_moves: process_move(a)

        def process_attack(a: Action, is_chain: bool = False):
            if id(a) in processed:
                return
            src = self.cities.get(a.from_city)
            dst = self.cities.get(a.to_city)
            if not src or not dst:
                processed.add(id(a)); return
            if src.owner != a.player:
                return
            processed.add(id(a))
            effective_def = self.calc_attack_cost(dst.army)
            defender_before = dst.army
            if is_chain:
                committed = src.army
            else:
                committed = min(a.army, src.army)
            src.army -= committed
            if committed > effective_def:
                dst.owner = a.player
                dst.army = committed - effective_def
                detail = f"有效防御={defender_before}×1.5={effective_def}，{committed}>{effective_def}攻占成功，剩余={committed}-{effective_def}={dst.army}兵"
                results.append({"type": "capture", "player": a.player.value, "from": src.name, "to": dst.name,
                    "attack_cost": effective_def, "defender_before": defender_before, "remaining": dst.army,
                    "success": True, "captured": True, "detail": detail, "effective_def": effective_def, "committed": committed})
                chain = [ca for ca in actions if ca.from_city == dst.id and ca.action_type == "attack"
                         and ca.player == a.player and id(ca) not in processed]
                for ca in chain:
                    if dst.army > 0:
                        process_attack(ca, is_chain=True)
            else:
                effective_remaining = effective_def - committed
                dst.army = max(0, int(effective_remaining / ATTACK_MULTIPLIER))
                detail = f"有效防御={defender_before}×1.5={effective_def}，{committed}<{effective_def}不足。{effective_def}-{committed}={effective_remaining}，{effective_remaining}÷1.5→{dst.army}兵"
                results.append({"type": "attack", "player": a.player.value, "from": src.name, "to": dst.name,
                    "attack_cost": committed, "defender_before": defender_before, "remaining": dst.army,
                    "success": False, "captured": False, "detail": detail, "effective_def": effective_def, "committed": committed})

        # 检测"对攻"：蓝打红城X，同时红打蓝城Y
        reciprocal = {}  # {蓝action_id: 红action_id}
        for ba in blue_attacks:
            bdst = self.cities.get(ba.to_city)
            if bdst and bdst.owner == Owner.PLAYER_B:
                for ra in red_attacks:
                    rdst = self.cities.get(ra.to_city)
                    if rdst and rdst.owner == Owner.PLAYER_A:
                        reciprocal[id(ba)] = ra
                        reciprocal[id(ra)] = ba

        for a in blue_attacks:
            if a.to_city in simultaneous_npc: continue
            if id(a) in reciprocal: continue
            process_attack(a)
        for a in red_attacks:
            if a.to_city in simultaneous_npc: continue
            if id(a) in reciprocal: continue
            process_attack(a)

        # 处理对攻（相遇1:1厮杀）
        for ba in blue_attacks:
            ra = reciprocal.get(id(ba))
            if not ra or id(ba) in processed: continue
            self._resolve_reciprocal(ba, ra, results)

        for npc_id in simultaneous_npc:
            npc_attacks = [a for a in actions if a.to_city == npc_id and a.action_type == "attack"
                           and a.player in (Owner.PLAYER_A, Owner.PLAYER_B)]
            if len(npc_attacks) >= 2:
                self._resolve_simultaneous_vs_npc(npc_attacks, results)
        self.pending_actions.clear()
        return results

    def _resolve_simultaneous_vs_npc(self, attacks, results):
        dst = self.cities[attacks[0].to_city]
        defender_before = dst.army
        valid = [a for a in attacks if (src := self.cities.get(a.from_city)) and src.owner == a.player and src.army > 0]
        if len(valid) < 2:
            for a in valid:
                self._resolve_single_attack_simple(a, results)
            return
        total_cost = self.calc_attack_cost(dst.army)
        per_player_cost = math.ceil(total_cost / len(valid))
        committed = {}; npc_cost_paid = {}
        for a in valid:
            src = self.cities[a.from_city]
            commit = min(a.army, src.army)
            cost_share = min(commit, per_player_cost)
            src.army -= commit
            committed[a.player] = commit
            npc_cost_paid[a.player] = cost_share
        dst.army -= sum(npc_cost_paid.values())
        if dst.army > 0:
            for a in valid:
                results.append({"type": "attack", "player": a.player.value, "from": self.cities[a.from_city].name,
                    "to": dst.name, "attack_cost": npc_cost_paid[a.player], "defender_before": defender_before,
                    "remaining": 0, "success": False, "captured": False, "simultaneous": True})
            return
        remaining_troops = {a.player: max(0, committed[a.player] - npc_cost_paid[a.player]) for a in valid}
        troops = dict(remaining_troops)
        while len([p for p, t in troops.items() if t > 0]) > 1:
            active = [p for p, t in troops.items() if t > 0]
            min_t = min(troops[p] for p in active)
            for p in active: troops[p] -= min_t
        winner = None
        for p, t in troops.items():
            if t > 0: winner = p; break
        if winner is None:
            dst.army = 0
        else:
            dst.owner = winner
            dst.army = troops[winner]
        for a in valid:
            results.append({"type": "capture" if a.player == winner else "attack", "player": a.player.value,
                "from": self.cities[a.from_city].name, "to": dst.name, "attack_cost": npc_cost_paid[a.player],
                "defender_before": defender_before, "remaining": troops.get(a.player, 0),
                "success": a.player == winner, "captured": a.player == winner, "simultaneous": True})

    def _resolve_reciprocal(self, a1: Action, a2: Action, results: List[dict]):
        """对攻：蓝打红×同时红打蓝 → 两军1:1相遇厮杀 → 胜者攻城"""
        s1 = self.cities[a1.from_city]
        s2 = self.cities[a2.from_city]
        d1 = self.cities[a1.to_city]
        d2 = self.cities[a2.to_city]

        committed1 = min(a1.army, s1.army)
        committed2 = min(a2.army, s2.army)
        s1.army -= committed1
        s2.army -= committed2

        # 1:1 相遇厮杀
        t1, t2 = committed1, committed2
        if t1 > 0 and t2 > 0:
            m = min(t1, t2)
            t1 -= m; t2 -= m

        # 胜者剩余兵力攻击目标城
        # a1(蓝) → d1(红城), a2(红) → d2(蓝城)
        if t1 > t2:
            # 蓝胜 → 蓝攻击 d1(红城)
            effective_def = self.calc_attack_cost(d1.army)
            if t1 > effective_def:
                d1.owner = a1.player
                d1.army = t1 - effective_def
                detail = f"【对攻】蓝{committed1}兵 vs 红{committed2}兵相遇，蓝胜剩{t1}兵，攻击{d1.name}成功"
                results.append({"type":"capture","player":a1.player.value,"from":s1.name,"to":d1.name,
                    "attack_cost":committed1,"defender_before":self.calc_attack_cost(d1.army),
                    "remaining":d1.army,"success":True,"captured":True,"detail":detail})
            else:
                er = max(0, int((effective_def - t1) / ATTACK_MULTIPLIER))
                d1.army = er
                detail = f"【对攻】蓝{committed1}兵 vs 红{committed2}兵相遇，蓝胜剩{t1}兵，攻城不足，{d1.name}残余{er}兵"
                results.append({"type":"attack","player":a1.player.value,"from":s1.name,"to":d1.name,
                    "attack_cost":committed1,"defender_before":self.calc_attack_cost(d1.army),
                    "remaining":er,"success":False,"captured":False,"detail":detail})
        elif t2 > t1:
            # 红胜 → 红攻击 d2(蓝城)
            effective_def = self.calc_attack_cost(d2.army)
            if t2 > effective_def:
                d2.owner = a2.player
                d2.army = t2 - effective_def
                detail = f"【对攻】蓝{committed1}兵 vs 红{committed2}兵相遇，红胜剩{t2}兵，攻击{d2.name}成功"
                results.append({"type":"capture","player":a2.player.value,"from":s2.name,"to":d2.name,
                    "attack_cost":committed2,"defender_before":self.calc_attack_cost(d2.army),
                    "remaining":d2.army,"success":True,"captured":True,"detail":detail})
            else:
                er = max(0, int((effective_def - t2) / ATTACK_MULTIPLIER))
                d2.army = er
                detail = f"【对攻】蓝{committed1}兵 vs 红{committed2}兵相遇，红胜剩{t2}兵，攻城不足，{d2.name}残余{er}兵"
                results.append({"type":"attack","player":a2.player.value,"from":s2.name,"to":d2.name,
                    "attack_cost":committed2,"defender_before":self.calc_attack_cost(d2.army),
                    "remaining":er,"success":False,"captured":False,"detail":detail})
        else:
            # 平手，双方都攻城失败
            detail = f"【对攻】蓝{committed1}兵 vs 红{committed2}兵相遇，同归于尽，双方攻城失败"
            results.append({"type":"attack","player":a1.player.value,"from":s1.name,"to":d1.name,
                "attack_cost":committed1,"defender_before":0,"remaining":0,
                "success":False,"captured":False,"detail":detail})
            results.append({"type":"attack","player":a2.player.value,"from":s2.name,"to":d2.name,
                "attack_cost":committed2,"defender_before":0,"remaining":0,
                "success":False,"captured":False,"detail":detail})

    def _resolve_single_attack_simple(self, action, results):
        src = self.cities[action.from_city]; dst = self.cities[action.to_city]
        effective_def = self.calc_attack_cost(dst.army)
        defender_before = dst.army
        committed = min(action.army, src.army)
        src.army -= committed
        if committed > effective_def:
            dst.owner = action.player; dst.army = committed - effective_def
            detail = f"有效防御={defender_before}×1.5={effective_def}，{committed}>{effective_def}攻占成功，剩余={committed}-{effective_def}={dst.army}兵"
            results.append({"type": "capture", "player": action.player.value, "from": src.name, "to": dst.name,
                "attack_cost": effective_def, "defender_before": defender_before, "remaining": dst.army,
                "success": True, "captured": True, "detail": detail})
        else:
            effective_remaining = effective_def - committed
            dst.army = max(0, int(effective_remaining / ATTACK_MULTIPLIER))
            detail = f"有效防御={defender_before}×1.5={effective_def}，{committed}<{effective_def}不足。{effective_def}-{committed}={effective_remaining}，{effective_remaining}÷1.5→{dst.army}兵"
            results.append({"type": "attack", "player": action.player.value, "from": src.name, "to": dst.name,
                "attack_cost": committed, "defender_before": defender_before, "remaining": dst.army,
                "success": False, "captured": False, "detail": detail})

    def add_pending_action(self, action): return True, "行动已添加"

    def clear_pending_actions(self): self.pending_actions.clear()

    def end_turn(self):
        action_results = self.resolve_turn()
        reinforce_msg = ""
        if not self.game_over:
            gains = self.reinforce()
            parts = []
            if gains[Owner.PLAYER_A]: parts.append(f"蓝方+{gains[Owner.PLAYER_A]}")
            if gains[Owner.PLAYER_B]: parts.append(f"红方+{gains[Owner.PLAYER_B]}")
            if parts:
                self.action_log.append({"type": "reinforce", "message": f"第{self.turn}回合结算 — 增兵：{'，'.join(parts)}"})
        winner, reason = self._check_victory()
        if winner:
            self.game_over = True; self.winner = winner
            self.action_log.append({"type": "system", "message": f"游戏结束！{winner.value} 获胜（{reason}）"})
        self.turn += 1
        if self.turn > MAX_TURNS and not self.game_over:
            self.game_over = True
            a_count = sum(1 for c in self.cities.values() if c.owner == Owner.PLAYER_A)
            b_count = sum(1 for c in self.cities.values() if c.owner == Owner.PLAYER_B)
            self.winner = Owner.PLAYER_A if a_count > b_count else Owner.PLAYER_B
            self.action_log.append({"type": "system", "message": f"达到最大回合数{MAX_TURNS}，游戏结束"})
        return {"action_results": action_results, "turn": self.turn,
                "game_over": self.game_over, "winner": self.winner.value if self.winner else None}

    def _check_victory(self):
        a_cities = [c for c in self.cities.values() if c.owner == Owner.PLAYER_A]
        b_cities = [c for c in self.cities.values() if c.owner == Owner.PLAYER_B]
        if not a_cities: return Owner.PLAYER_B, "蓝方失去所有城市"
        if not b_cities: return Owner.PLAYER_A, "红方失去所有城市"
        return None, None

    def get_player_info(self, player: Owner) -> dict:
        cities = [c for c in self.cities.values() if c.owner == player]
        player_actions = [a for a in self.pending_actions if a.player == player]
        return {
            "cities_count": len(cities), "total_troops": sum(c.army for c in cities),
            "city_ids": [c.id for c in cities],
            "actions_count": len(player_actions),
            "actions_remaining": max(0, MAX_ACTIONS_PER_TURN - len(player_actions)),
        }

    def get_state(self) -> dict:
        a_info = self.get_player_info(Owner.PLAYER_A)
        b_info = self.get_player_info(Owner.PLAYER_B)
        if self.game_over:
            if self.winner == Owner.PLAYER_A:
                a_info["status"], b_info["status"] = "victory", "defeat"
            elif self.winner == Owner.PLAYER_B:
                a_info["status"], b_info["status"] = "defeat", "victory"
            else:
                a_info["status"] = b_info["status"] = "draw"
        else:
            a_info["status"] = b_info["status"] = "planning"
        return {
            "id": self.id, "turn": self.turn,
            "phase": "planning" if not self.game_over else "ended",
            "game_over": self.game_over,
            "winner": self.winner.value if self.winner else None,
            "max_turns": MAX_TURNS, "attack_multiplier": ATTACK_MULTIPLIER,
            "player_a": a_info, "player_b": b_info,
            "cities": [c.to_dict() for c in self.cities.values()],
            "pending_actions": [a.to_dict() for a in self.pending_actions],
            "action_log": self.action_log[-20:],
            "owner_display": {k.value: v for k, v in OWNER_DISPLAY.items()},
        }
