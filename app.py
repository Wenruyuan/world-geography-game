"""
世界地理战略推演游戏 - Flask 后端
"""

from flask import Flask, render_template, jsonify, request
from game_engine import GameEngine, Action, Owner, ATTACK_MULTIPLIER
from ai_player import plan_ai_actions

app = Flask(__name__)

# 游戏实例存储（内存中）
games: dict = {}


def _get_game(game_id: str):
    game = games.get(game_id)
    if not game:
        return None, jsonify({"error": "游戏不存在"}), 404
    return game, None


# ==================== 页面路由 ====================

@app.route("/")
def index():
    return render_template("index.html")


# ==================== API 路由 ====================

@app.route("/api/new-game", methods=["POST"])
def new_game():
    """创建新游戏"""
    game = GameEngine()
    game.setup_game()
    games[game.id] = game
    return jsonify({"game_id": game.id, "state": game.get_state()})


@app.route("/api/game/<game_id>/state")
def get_state(game_id):
    """获取游戏状态"""
    game, err = _get_game(game_id)
    if err:
        return err
    return jsonify(game.get_state())


@app.route("/api/game/<game_id>/valid-targets/<city_id>")
def get_valid_targets(game_id, city_id):
    """获取某城市的有效目标"""
    game, err = _get_game(game_id)
    if err:
        return err
    return jsonify(game.get_valid_targets(city_id))


@app.route("/api/game/<game_id>/add-action", methods=["POST"])
def add_action(game_id):
    """添加行动。增援立即结算（更新兵力），攻击保留等统一结算"""
    game, err = _get_game(game_id)
    if err:
        return err

    data = request.json
    try:
        player = Owner(data["player"])
        from_city_id = data["from_city"]
        to_city_id = data["to_city"]
        army = int(data["army"])

        # 查询目标城市的当前所有者（区分攻击/移动的关键）
        target_city = game.cities.get(to_city_id)
        if not target_city:
            return jsonify({"success": False, "message": "目标城市不存在"})

        action = Action(
            player=player,
            from_city=from_city_id,
            to_city=to_city_id,
            army=army,
            target_owner=target_city.owner.value,
        )
    except (KeyError, ValueError) as e:
        return jsonify({"error": f"参数错误: {e}"}), 400

    valid, msg = game.validate_action(action)
    if not valid:
        return jsonify({"success": False, "message": msg})

    # 所有行动（增援+攻击）都加入队列，等统一结算
    game.pending_actions.append(action)
    return jsonify({"success": True, "message": msg, "state": game.get_state()})


@app.route("/api/game/<game_id>/remove-action", methods=["POST"])
def remove_action(game_id):
    """移除待执行行动"""
    game, err = _get_game(game_id)
    if err:
        return err

    data = request.json
    idx = int(data.get("index", -1))
    if 0 <= idx < len(game.pending_actions):
        game.pending_actions.pop(idx)
        return jsonify({"success": True, "state": game.get_state()})
    return jsonify({"success": False, "message": "行动索引无效"})


@app.route("/api/game/<game_id>/clear-actions", methods=["POST"])
def clear_actions(game_id):
    """清除行动。可选参数 player 指定只清除某玩家的行动。"""
    game, err = _get_game(game_id)
    if err:
        return err
    data = request.json or {}
    player_filter = data.get("player")

    if player_filter:
        try:
            p = Owner(player_filter)
            game.pending_actions = [a for a in game.pending_actions if a.player != p]
        except ValueError:
            pass
    else:
        game.clear_pending_actions()
    return jsonify({"success": True, "state": game.get_state()})


@app.route("/api/game/<game_id>/end-turn", methods=["POST"])
def end_turn(game_id):
    """结束当前回合"""
    game, err = _get_game(game_id)
    if err:
        return err

    result = game.end_turn()
    result["state"] = game.get_state()
    return jsonify(result)


@app.route("/api/game/<game_id>/ai-turn", methods=["POST"])
def ai_turn(game_id):
    """AI 自动规划 player_b 行动并结算"""
    game, err = _get_game(game_id)
    if err:
        return err
    actions = plan_ai_actions(game)
    for a in actions:
        game.pending_actions.append(a)
    result = game.end_turn()
    result["state"] = game.get_state()
    return jsonify(result)


# ==================== 启动 ====================

if __name__ == "__main__":
    print("=" * 50)
    print("  世界地理战略推演游戏")
    print("  打开浏览器访问: http://127.0.0.1:5000")
    print("=" * 50)
    app.run(debug=True, host="0.0.0.0", port=5000)
