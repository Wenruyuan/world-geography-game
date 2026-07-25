/**
 * 世界地理战略推演游戏 - 前端逻辑
 */

// ==================== 全局状态 ====================
let gameState = null;       // 当前游戏状态
let gameId = null;          // 游戏ID
let selectedCity = null;    // 当前选中的城市ID
let inspectedCity = null;   // 当前查看的城市（NPC查看连线用）
let cityDataMap = {};       // 城市数据映射
let planningPlayer = 'player_a';   // 当前正在规划的玩家（前端状态）
let gameMode = "pvp";     // pvp or pve
let projectedA = {};        // 蓝方的即时增援投影
let projectedB = {};        // 红方的即时增援投影

// 获取当前方投影
function currentProjections() {
    return planningPlayer === 'player_a' ? projectedA : projectedB;
}

// 同步城市数据（state 变化后必须调用）
function syncCityData() {
    if (!gameState) return;
    gameState.cities.forEach(c => { cityDataMap[c.id] = c; });
}

// 获取某城市的"可见兵力" = 实际兵力 + 当前方的投影增援
function getCityDisplayArmy(cityId) {
    const city = cityDataMap[cityId];
    if (!city) return 0;
    const proj = currentProjections();
    return Math.max(0, city.army + (proj[cityId] || 0));
}

// 应用即时增援投影（当前方）
function applyProjectedReinforce(srcId, dstId, amt) {
    const proj = currentProjections();
    proj[srcId] = (proj[srcId] || 0) - amt;
    proj[dstId] = (proj[dstId] || 0) + amt;
}

function togglePlanningPlayer() {
    planningPlayer = planningPlayer === 'player_a' ? 'player_b' : 'player_a';
    updatePlanningUI();
    selectedCity = null;
    renderMap();
    renderActionQueue();
    renderPlayerInfo();
    updateActionPanel();
}

function updatePlanningUI() {
    const btn = document.getElementById('planning-toggle');
    if (planningPlayer === 'player_a') {
        btn.textContent = '蓝方';
        btn.className = 'btn btn-sm btn-primary';
    } else {
        btn.textContent = '红方';
        btn.className = 'btn btn-sm btn-secondary';
    }
}

// ==================== API 调用 ====================
const API = {
    async newGame() {
        const res = await fetch('/api/new-game', { method: 'POST' });
        return res.json();
    },
    async getState() {
        const res = await fetch(`/api/game/${gameId}/state`);
        return res.json();
    },
    async getValidTargets(cityId) {
        const res = await fetch(`/api/game/${gameId}/valid-targets/${cityId}`);
        return res.json();
    },
    async addAction(player, fromCity, toCity, army) {
        const res = await fetch(`/api/game/${gameId}/add-action`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ player, from_city: fromCity, to_city: toCity, army }),
        });
        return res.json();
    },
    async removeAction(index) {
        const res = await fetch(`/api/game/${gameId}/remove-action`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ index }),
        });
        return res.json();
    },
    async clearActions() {
        const res = await fetch(`/api/game/${gameId}/clear-actions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
        });
        return res.json();
    },
    async endTurn() {
        const res = await fetch(`/api/game/${gameId}/end-turn`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
        });
        return res.json();
    },
};

// ==================== 游戏启动 ====================
async function startGame(mode = "pvp") {
    gameMode = mode;
    const result = await API.newGame();
    gameId = result.game_id;
    gameState = result.state;
    syncCityData();
    projectedA = {};
    projectedB = {};
    planningPlayer = 'player_a';
    updatePlanningUI();

    // 重置地图
    mapInitialized = false;
    const svg = document.getElementById('game-map');
    if (svg) { svg.innerHTML = ''; svg.setAttribute('viewBox', '0 0 1800 1000'); }

    // 切换到游戏界面
    document.getElementById('start-screen').classList.remove('active');
    document.getElementById('game-screen').classList.add('active');

    renderAll();
}

async function restartGame() {
    document.getElementById('game-over-modal').classList.add('hidden');
    document.getElementById('game-screen').classList.remove('active');
    document.getElementById('start-screen').classList.add('active');
    selectedCity = null;
    gameState = null;
    gameId = null;
}

// ==================== 渲染 ====================
function renderAll() {
    if (!gameState) return;
    renderMap();
    renderPlayerInfo();
    renderActionQueue();
    renderBattleLog();
    updateCurrentPlayer();
    updateActionPanel();
}


// --- 玩家信息 ---
function renderPlayerInfo() {
    const pa = gameState.player_a;
    const pb = gameState.player_b;

    document.getElementById('pa-cities').textContent = pa.cities_count;
    document.getElementById('pa-troops').textContent = pa.total_troops;
    document.getElementById('pa-actions').textContent = pa.actions_remaining;

    document.getElementById('pb-cities').textContent = pb.cities_count;
    document.getElementById('pb-troops').textContent = pb.total_troops;
    document.getElementById('pb-actions').textContent = pb.actions_remaining;

    // 活跃状态
    const aCard = document.getElementById('player-a-card');
    const bCard = document.getElementById('player-b-card');
    aCard.classList.remove('active', 'player-a-active');
    bCard.classList.remove('active', 'player-b-active');

    if (planningPlayer === 'player_a') {
        aCard.classList.add('active', 'player-a-active');
    } else {
        bCard.classList.add('active', 'player-b-active');
    }
}

// --- 行动队列（只显示当前规划方的行动，对方行动隐藏）---
function renderActionQueue() {
    const list = document.getElementById('action-queue-list');
    const allActions = gameState.pending_actions || [];
    const myActions = allActions.filter(a => a.player === planningPlayer);
    const otherActions = allActions.filter(a => a.player !== planningPlayer);

    // 更新标题
    const title = document.querySelector('.queue-title');
    if (title) {
        const playerName = planningPlayer === 'player_a' ? '蓝方' : '红方';
        title.textContent = `行动队列（${playerName}）${otherActions.length > 0 ? ' — 对方已规划 ' + otherActions.length + ' 步' : ''}`;
    }

    if (myActions.length === 0) {
        list.innerHTML = '<div class="queue-empty">暂无行动</div>';
        return;
    }

    list.innerHTML = myActions.map((action) => {
        const realIndex = allActions.findIndex(a => a === action);
        const from = cityDataMap[action.from_city];
        const to = cityDataMap[action.to_city];
        const typeLabel = action.type === 'attack' ? '⚔' : '↗';
        return `
            <div class="queue-item fade-in">
                <span>${typeLabel} ${from ? from.name : '?'} <span class="arrow">→</span> ${to ? to.name : '?'} (${action.army}兵)</span>
                <button class="remove-btn" onclick="removeAction(${realIndex})" title="移除">✕</button>
            </div>
        `;
    }).join('');
}

// --- 战斗日志 ---
function renderBattleLog() {
    const log = document.getElementById('battle-log');
    const entries = gameState.action_log || [];

    log.innerHTML = entries.map(entry => {
        let cls = 'log-entry';
        if (entry.type === 'system') cls += ' system';
        else if (entry.type === 'attack') cls += ' attack';
        else if (entry.type === 'move') cls += ' move';
        else if (entry.type === 'capture') cls += ' capture';
        else if (entry.type === 'reinforce') cls += ' system';
        return `<div class="${cls}">${entry.message}</div>`;
    }).join('');

    log.scrollTop = log.scrollHeight;
}

// --- 当前玩家 ---
function updateCurrentPlayer() {
    const turnNum = document.getElementById('turn-number');
    turnNum.textContent = gameState.turn;

    if (gameState.game_over) {
        const winnerName = gameState.winner === 'player_a' ? '蓝方' : (gameState.winner === 'player_b' ? '红方' : '平局');
        showGameOver(winnerName);
    }
}

// --- 行动面板 ---
function updateActionPanel() {
    const form = document.getElementById('action-form');
    const hint = document.getElementById('action-hint');

    if (selectedCity) {
        const city = cityDataMap[selectedCity];
        const isOwned = city && city.owner === planningPlayer;
        const isChain = city && (gameState.pending_actions || []).some(a =>
            a.player === planningPlayer && a.to_city === selectedCity && a.type === 'attack'
        );

        if (isOwned || isChain) {
            form.classList.remove('hidden');
            hint.classList.add('hidden');
            const label = isChain ? `${city.name}（连锁规划）` : city.name;
            document.getElementById('selected-city-name').textContent = label;

            // 更新目标选择
            updateTargetSelect(selectedCity);

            // 滑块上限
            const slider = document.getElementById('army-slider');
            slider.min = 1;
            if (isChain) {
                // 连锁：不限制兵力上限，实际可用兵力取决于结算时前置攻击的剩余
                slider.max = 999;
            } else {
                slider.max = isOwned ? getCityDisplayArmy(city.id) : slider.max;
            }
            slider.value = Math.min(Math.max(1, parseInt(slider.value) || 1), slider.max);
            onSliderChange();
        } else {
            form.classList.add('hidden');
            hint.classList.remove('hidden');
        }
    } else {
        form.classList.add('hidden');
        hint.classList.remove('hidden');
        hint.textContent = '点击你的城市（或规划攻占的城市）开始行动';
    }
}

async function updateTargetSelect(cityId) {
    const targets = await API.getValidTargets(cityId);
    const select = document.getElementById('target-select');

    select.innerHTML = '<option value="">请选择目标</option>';
    targets.forEach(t => {
        const ownerLabels = {
            'player_a': '蓝', 'player_b': '红',
            'npc': 'NPC', 'unassigned': '无'
        };
        const isAttack = t.owner !== planningPlayer;
        const atkCost = isAttack ? Math.ceil(t.army * 1.5) : 0;
        let label;
        if (isAttack) {
            label = `${t.name}（${ownerLabels[t.owner]} ${t.army}兵 → 需${atkCost}兵攻占）`;
        } else {
            label = `${t.name}（友方 ${t.army}兵，可增援）`;
        }
        const opt = document.createElement('option');
        opt.value = t.id;
        opt.textContent = label;
        if (!t.can_attack && !t.can_move) {
            opt.disabled = true;
            opt.textContent = label + ' ✗';
        }
        select.appendChild(opt);
    });
}

// ==================== 事件处理 ====================
function onCityClick(cityId) {
    if (gameState.game_over) return;

    const city = cityDataMap[cityId];
    if (!city) return;

    // 点击已选中的城市 → 取消选中
    if (selectedCity === cityId) {
        selectedCity = null;
        renderMap();
        updateActionPanel();
        return;
    }

    // 点击正在查看连线的城市 → 取消查看
    if (inspectedCity === cityId) {
        inspectedCity = null;
        renderMap();
        return;
    }

    // 检查是否可以选此城市：本人拥有 OR 有 pending 攻击指向此城（连锁）
    const canSelect = city.owner === planningPlayer
        || (gameState.pending_actions || []).some(a =>
            a.player === planningPlayer && a.to_city === cityId && a.type === 'attack'
        );

    // 如果点击的是可选的 → 选为起点
    if (canSelect) {
        selectedCity = cityId;
        inspectedCity = null;
        renderMap();
        updateActionPanel();
    }
    // 不可选的 → 查看连线（NPC / 敌方城市）
    else {
        inspectedCity = cityId;
        selectedCity = null;
        renderMap();
        updateActionPanel();
    }
}

function onTargetChange() {
    const targetId = document.getElementById('target-select').value;
    if (!targetId || !selectedCity) return;

    const src = cityDataMap[selectedCity];
    const target = cityDataMap[targetId];
    if (!src || !target) return;

    const isAttack = target.owner !== planningPlayer;
    const atkCost = isAttack ? Math.ceil(target.army * 1.5) : 1;

    // 判断是否为连锁攻击（起点城市有 pending 攻击指向它 → 即将被攻占）
    const isChainSrc = (gameState.pending_actions || []).some(a =>
        a.player === planningPlayer && a.to_city === selectedCity && a.type === 'attack'
    );

    const slider = document.getElementById('army-slider');
    slider.min = 1;
    slider.max = isChainSrc ? 999 : getCityDisplayArmy(selectedCity);
    // 连锁攻击：保持 updateActionPanel 设置的宽松上限，不覆盖

    if (isAttack) {
        slider.value = Math.min(Math.max(atkCost, parseInt(slider.value) || atkCost), slider.max);
    } else {
        const halfTroops = Math.max(1, Math.floor(src.army / 2));
        slider.value = Math.min(isChainSrc ? atkCost : halfTroops, slider.max);
    }
    onSliderChange();
}

function onSliderChange() {
    const slider = document.getElementById('army-slider');
    const value = parseInt(slider.value);
    const hint = document.getElementById('attack-hint');
    document.getElementById('army-value').textContent = value;

    const targetId = document.getElementById('target-select').value;
    if (targetId) {
        const target = cityDataMap[targetId];
        if (target && target.owner !== planningPlayer) {
            // 攻击模式
            const atkCost = Math.ceil(target.army * 1.5);
            if (value >= atkCost) {
                hint.textContent = `可攻占（需${atkCost}，敌${target.army}兵）`;
                hint.className = 'attack-hint can-attack';
            } else {
                hint.textContent = `兵力不足（需${atkCost}）`;
                hint.className = 'attack-hint cannot-attack';
            }
        } else if (target) {
            // 增援模式
            hint.textContent = `向友方城市增援兵力（最少 1 兵）`;
            hint.className = 'attack-hint can-attack';
        }
    } else {
        hint.textContent = '';
        hint.className = 'attack-hint';
    }
}

async function submitAction() {
    if (!selectedCity) return;

    const targetId = document.getElementById('target-select').value;
    if (!targetId) {
        alert('请选择目标城市');
        return;
    }

    const army = parseInt(document.getElementById('army-slider').value);
    const player = planningPlayer;
    const dst = cityDataMap[targetId];
    const isMove = dst && dst.owner === player;

    const result = await API.addAction(player, selectedCity, targetId, army);
    if (result.success) {
        gameState = result.state;
        syncCityData();
        // 增援：前端立即投影兵力变化（仅当前方可见，结算时以后端为准）
        if (isMove) {
            applyProjectedReinforce(selectedCity, targetId, army);
        }
        selectedCity = null;
        renderAll();
    } else {
        alert(result.message || '行动失败');
    }
}

async function removeAction(index) {
    const result = await API.removeAction(index);
    if (result.success) {
        gameState = result.state;
        syncCityData();
        // 如果是已投影的增援，撤销投影
        const removed = gameState.pending_actions[index];  // 已经不在了，用之前的数据
        renderAll();
    }
}

async function clearActions() {
    // 清空当前规划玩家的行动和投影
    const res = await fetch(`/api/game/${gameId}/clear-actions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ player: planningPlayer }),
    });
    const data = await res.json();
    if (data.state) {
        gameState = data.state;
        syncCityData();
        if (planningPlayer === 'player_a') projectedA = {};
        else projectedB = {};
        renderAll();
    }
}

async function confirmTurn() {
    if (gameState.game_over) return;

    // 结算前清空双方投影
    projectedA = {};
    projectedB = {};

    const result = await (gameMode === "pve" ? aiTurn() : API.endTurn());
    gameState = result.state;
    syncCityData();
    selectedCity = null;

    // 详细结算日志
    if (result.action_results) {
        result.action_results.forEach(r => {
            const playerName = (r.player === 'player_a') ? '蓝' : (r.player === 'npc' ? 'NPC' : '红');
            const sim = r.simultaneous ? '【同时攻击】' : '';
            if (r.detail) {
                // 有详细结算公式，直接展示
                const emoji = r.captured ? '✓' : '✗';
                gameState.action_log.push({
                    type: r.captured ? 'capture' : 'attack',
                    message: `${sim}[${playerName}] ${r.from} → ${r.to}: ${emoji} ${r.detail}`
                });
            } else if (r.type === 'capture') {
                gameState.action_log.push({
                    type: 'capture',
                    message: `${sim}[${playerName}] ${r.from} → ${r.to}: 攻占成功（消耗${r.attack_cost}兵，原守${r.defender_before}兵，剩余${r.remaining}兵）`
                });
            } else if (r.type === 'attack') {
                gameState.action_log.push({
                    type: 'attack',
                    message: `${sim}[${playerName}] ${r.from} → ${r.to}: 攻击未果（消耗${r.attack_cost}兵，敌剩${r.remaining}兵）`
                });
            } else if (r.type === 'move') {
                gameState.action_log.push({
                    type: 'move',
                    message: `[${playerName}] ${r.from} → ${r.to}: 增援${r.army}兵`
                });
            } else if (r.type === 'skipped') {
                gameState.action_log.push({
                    type: 'system',
                    message: `[跳过] ${r.message}`
                });
            }
        });
    }

    renderAll();
}

// ==================== 游戏结束 ====================

async function aiTurn() {
    const res = await fetch(`/api/game/${gameId}/ai-turn`, { method: "POST" });
    return res.json();
}

function showGameOver(winnerName) {
    const modal = document.getElementById('game-over-modal');
    const title = document.getElementById('game-over-title');
    const message = document.getElementById('game-over-message');

    if (!winnerName) {
        const winner = gameState.winner;
        winnerName = winner === 'player_a' ? '蓝方' : (winner === 'player_b' ? '红方' : '平局');
    }
    if (winnerName === '蓝方') {
        title.textContent = '蓝方胜利！';
        message.textContent = '蓝方成功占领了更多城市，取得了战略优势。';
    } else if (winnerName === '红方') {
        title.textContent = '红方胜利！';
        message.textContent = '红方成功占领了更多城市，取得了战略优势。';
    } else {
        title.textContent = '游戏结束';
        message.textContent = '回合数已达上限，双方平局。';
    }

    modal.classList.remove('hidden');
}

// ==================== 面板折叠 ====================
function toggleLeftPanel() { document.querySelector('.left-panel').classList.toggle('collapsed'); }
function toggleRightPanel() { document.querySelector('.right-panel').classList.toggle('collapsed'); }
function toggleTopBar() { document.querySelector('.top-bar').classList.toggle('collapsed'); }
function toggleBottomBar() { document.querySelector('.bottom-bar').classList.toggle('collapsed'); }

// ==================== 工具函数 ====================
function createSvgEl(tag, attrs) {
    const el = document.createElementNS('http://www.w3.org/2000/svg', tag);
    for (const [key, val] of Object.entries(attrs)) {
        el.setAttribute(key, val);
    }
    return el;
}
