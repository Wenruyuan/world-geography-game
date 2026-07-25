# world-geography-game
世界地理战略推演游戏——回合制战略博弈，75 城手绘世界地图，双人对战/人机对战，隐藏信息盲下，连锁攻击，1.5× 攻防模型。  World Geography Strategic Simulation — Turn-based strategy game with 75 hand-placed world cities. PvP &amp; PvE modes, fog-of-war planning, chain attacks, reciprocal combat, and a 1.5× defense model.

# 世界地理战略推演

> World Geography Strategic Simulation Game

一款双人/人机回合制战略博弈游戏，融合世界地理与军事推演。75 城手绘世界地图，支持隐藏信息盲下、连锁攻击、对攻相遇等特色机制。

---

## 快速开始

```bash
pip install flask -i https://pypi.tuna.tsinghua.edu.cn/simple
python app.py
```

浏览器打开 `http://127.0.0.1:5000`

---

## 游戏模式

| 模式 | 说明 |
|------|------|
| **双人对战** | 同一设备热座模式，蓝方先规划 → 切换红方规划 → 统一结算 |
| **人机对战** | 人类为蓝方，AI 为红方。AI 难度分三档（随机/打分/模拟） |

---

## 核心机制

### 攻防模型
- **攻击成本** = `ceil(守军 × 1.5)`，即守城方有 1.5 倍防御加成
- 攻击成功条件：`派出兵力 > 有效防御`，且剩余兵力进驻新占城
- 攻击失败：有效防御未被完全击穿，守方残血 = `floor((有效防御 − 派出) / 1.5)`
- 空城（cost=0）：可直接占领，不消耗兵力

### 对攻规则
当蓝方 A 城攻击红方 B 城，同时红方 B 城攻击蓝方 A 城时：
1. 两军 1:1 相遇厮杀
2. 胜方剩余兵力继续攻击目标城
3. 平手则双方攻城失败

### 连锁攻击
同回合内可规划 A→B→C 链路：只要 A→B 派出足够兵力打下 B，剩余兵力自动继续攻打 C。

### 隐藏信息
- 蓝方规划时看不到红方当前回合的操作，反之亦然
- 结算时双方行动同时揭露
- 即时增援仅对己方可见（前端投影，后端结算时统一处理）

### 资源城市
7 个资源城（沙特阿拉伯、伊朗、阿富汗、叶卡捷琳堡、塔什干、新西伯利亚、贝加尔湖）被玩家占领后每回合额外 +2 兵力。

### 海陆连接
- 陆地相邻城市之间实线连接
- 跨海/跨洋城市之间短线+标签标注（如伦敦⇢纽约），不画全段线
- 好望角→西南澳等远洋航线以弧线绕地图外围绕行

---

## 项目结构

```
├── app.py                 # Flask 后端
├── game_engine.py         # 核心游戏引擎（城市/战斗/结算）
├── ai_player.py           # AI 决策模块
├── requirements.txt       # Python 依赖
├── start.bat              # Windows 一键启动
├── templates/
│   └── index.html         # 前端页面
└── static/
    ├── css/style.css      # 样式
    └── js/
        ├── game.js        # 前端主逻辑（状态管理/API/UI）
        └── map2d.js       # 地图渲染（SVG/缩放/连线）
```

---

## 技术栈

| 层 | 技术 |
|----|------|
| 后端 | Python 3 + Flask |
| 前端 | 原生 JavaScript + SVG |
| 存储 | 内存（无数据库依赖） |
| AI | 规则打分 + 简易模拟 |

---
