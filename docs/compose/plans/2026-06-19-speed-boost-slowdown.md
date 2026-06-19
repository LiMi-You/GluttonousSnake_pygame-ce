# Speed Boost / Slowdown Props + BuffManager Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use compose:subagent (recommended) or compose:execute to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement speed boost and slowdown props with a standalone BuffManager to handle timed player speed effects.

**Architecture:** New `items/buff_manager.py` manages all active buffs. `GameScreen` integrates it for speed multiplier on move interval. Two new item definitions added to `item_defs.py`.

**Tech Stack:** Python, pygame-ce

---

### Task 1: Create BuffManager

**Covers:** Buff system core — manages timed speed effects on the player

**Files:**
- Create: `items/buff_manager.py`

- [ ] **Step 1: Create `items/buff_manager.py`**

```python
"""
items/buff_manager.py — Buff/Debuff 管理器

管理玩家身上的时效性状态（加速、减速等）。
支持：添加、更新（倒计时）、过期移除、查询当前速度系数。
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Buff:
    """单个 Buff 实例"""
    buff_id: str            # 唯一标识（如 "speed_boost"）
    duration_ms: int        # 总持续时间（毫秒）
    remaining_ms: int       # 剩余时间（毫秒）
    speed_mult: float       # 速度系数（<1 = 加速, >1 = 减速, 1.0 = 无效果）


class BuffManager:
    """
    Buff 管理器 — 追踪玩家身上的所有活跃 buff。

    速度类 buff 规则：
    - 同 ID buff 重复拾取 → 刷新持续时间（不叠加系数）
    - 加速/减速互斥 → 后拾取的覆盖先拾取的（取最后生效）
    """

    def __init__(self):
        self.active_buffs: list[Buff] = []

    def reset(self):
        """游戏重置时清空所有 buff"""
        self.active_buffs.clear()

    def add_buff(self, buff_id: str, duration_ms: int, speed_mult: float):
        """
        添加一个 buff。

        如果同 ID buff 已存在 → 刷新持续时间。
        如果是速度类 buff（speed_mult != 1.0）→ 移除之前的速度类 buff（互斥）。
        """
        if speed_mult != 1.0:
            self.active_buffs = [
                b for b in self.active_buffs
                if b.speed_mult == 1.0  # 保留非速度类 buff
            ]

        existing = next((b for b in self.active_buffs if b.buff_id == buff_id), None)
        if existing:
            existing.remaining_ms = duration_ms
        else:
            self.active_buffs.append(
                Buff(
                    buff_id=buff_id,
                    duration_ms=duration_ms,
                    remaining_ms=duration_ms,
                    speed_mult=speed_mult,
                )
            )

    def update(self, dt_ms: int):
        """每帧调用，递减所有 buff 的剩余时间，到期自动移除"""
        for buff in self.active_buffs:
            buff.remaining_ms -= dt_ms
        self.active_buffs = [b for b in self.active_buffs if b.remaining_ms > 0]

    def get_speed_multiplier(self) -> float:
        """
        返回当前速度系数。
        无 buff → 1.0；有速度 buff → 返回该 buff 的 speed_mult。
        """
        for buff in self.active_buffs:
            if buff.speed_mult != 1.0:
                return buff.speed_mult
        return 1.0

    def has_buff(self, buff_id: str) -> bool:
        """检查指定 buff 是否活跃"""
        return any(b.buff_id == buff_id for b in self.active_buffs)

    def get_active_buffs_info(self) -> list[dict]:
        """返回活跃 buff 信息列表（供探针使用）"""
        return [
            {
                "id": b.buff_id,
                "remaining_ms": b.remaining_ms,
                "duration_ms": b.duration_ms,
                "speed_mult": b.speed_mult,
            }
            for b in self.active_buffs
        ]
```

- [ ] **Step 2: Update `items/__init__.py` to export BuffManager**

```python
# 在现有导出中添加
from .buff_manager import BuffManager
```

- [ ] **Step 3: Commit**

```bash
git add items/buff_manager.py items/__init__.py
git commit -m "feat: add BuffManager for timed speed effects"
```

---

### Task 2: Add Speed Boost & Slowdown Item Definitions

**Covers:** Item definitions for the two new props

**Files:**
- Modify: `items/item_defs.py`

- [ ] **Step 1: Add two new item definitions to `ITEM_DEFS` dict in `items/item_defs.py`**

Add after the `"lucky_patrol_food"` entry (line 69):

```python
    "speed_boost": ItemDef(
        item_id="speed_boost",
        name="加速道具",
        category=CAT_BUFF,
        grid_w=1,
        grid_h=1,
        base_weight=20,
        max_on_screen=1,
        color=(0, 200, 255),
        score_value=500,
        image_key="speed_boost.png",
    ),
    "slow_down": ItemDef(
        item_id="slow_down",
        name="减速道具",
        category=CAT_DEBUFF,
        grid_w=1,
        grid_h=1,
        base_weight=20,
        max_on_screen=1,
        color=(200, 100, 255),
        score_value=300,
        image_key="slow_down.png",
    ),
```

- [ ] **Step 2: Commit**

```bash
git add items/item_defs.py
git commit -m "feat: add speed_boost and slow_down item definitions"
```

---

### Task 3: Integrate BuffManager into GameScreen

**Covers:** GameScreen integration — buff lifecycle, speed multiplier, item pickup

**Files:**
- Modify: `scenes/game_screen.py`

- [ ] **Step 1: Add BuffManager import at top of `scenes/game_screen.py`**

Change line 21:
```python
from items import ItemManager, ItemInstance
```
to:
```python
from items import ItemManager, ItemInstance, BuffManager
```

- [ ] **Step 2: Create BuffManager instance in `GameScreen.__init__`**

After line 39 (`self.stats = StatsManager()`), add:
```python
        self.buff_manager = BuffManager()
```

- [ ] **Step 3: Reset BuffManager in `_reset_game()`**

After line 265 (`self.stats.start_timer()`), add:
```python
        self.buff_manager.reset()
```

- [ ] **Step 4: Add buff duration constants at class level**

After line 49 (`self.GAME_OVER_DELAY: int = 1500`), add:
```python
        # ── Buff 持续时间 ──
        BUFF_SPEED_BOOST_DURATION = 5000   # 加速：5秒
        BUFF_SLOW_DOWN_DURATION = 10000    # 减速：10秒
        BUFF_SPEED_BOOST_MULT = 0.5        # 加速系数（×2速）
        BUFF_SLOW_DOWN_MULT = 1.5          # 减速系数（×0.67速）
        self.BUFF_SPEED_BOOST_DURATION = BUFF_SPEED_BOOST_DURATION
        self.BUFF_SLOW_DOWN_DURATION = BUFF_SLOW_DOWN_DURATION
        self.BUFF_SPEED_BOOST_MULT = BUFF_SPEED_BOOST_MULT
        self.BUFF_SLOW_DOWN_MULT = BUFF_SLOW_DOWN_MULT
```

- [ ] **Step 5: Update `_apply_item_effect()` to handle speed props**

Replace the `_apply_item_effect` method (lines 412-422) with:

```python
    def _apply_item_effect(self, item: ItemInstance):
        """应用道具效果"""
        self.stats.add_score(item.defn.score_value)
        self.stats.on_item_collected(item.item_id)
        self.snake.just_ate = True
        self.item_manager.remove_item(item)

        # ── 速度类 buff 处理 ──
        if item.item_id == "speed_boost":
            self.buff_manager.add_buff(
                "speed_boost",
                self.BUFF_SPEED_BOOST_DURATION,
                self.BUFF_SPEED_BOOST_MULT,
            )
        elif item.item_id == "slow_down":
            self.buff_manager.add_buff(
                "slow_down",
                self.BUFF_SLOW_DOWN_DURATION,
                self.BUFF_SLOW_DOWN_MULT,
            )

        # 触发分数滚动动画
        self._score_anim_from = self._score_display
        self._score_target = self.stats.get_score()
        self._score_anim_start = pygame.time.get_ticks()
        self._score_animating = True
```

- [ ] **Step 6: Update `update()` to drive buff timer and apply speed multiplier**

In the `update()` method, after line 334 (`delta_ms = now - self._last_tick`), add:
```python
        # ── 更新 buff 计时器 ──
        self.buff_manager.update(delta_ms)
```

In the `_game_step()` call section (lines 365-369), replace:
```python
        while self._move_accumulator >= MOVE_INTERVAL:
```
with:
```python
        effective_interval = MOVE_INTERVAL * self.buff_manager.get_speed_multiplier()
        while self._move_accumulator >= effective_interval:
```

- [ ] **Step 7: Commit**

```bash
git add scenes/game_screen.py
git commit -m "feat: integrate BuffManager into GameScreen for speed effects"
```

---

### Task 4: Update Probe Data Collection

**Covers:** Debug probe shows active buff state

**Files:**
- Modify: `scenes/game_screen.py` (in `_register_probe_collectors`)

- [ ] **Step 1: Add buff data collection to `collect_items()` in `_register_probe_collectors`**

In the `collect_items` function (around line 134), add after the `moving_items` section:

```python
            # buff 状态
            buff_info = self.buff_manager.get_active_buffs_info()
            return {
                "total": len(mgr.active_items),
                "spawn_accumulator": mgr._spawn_accumulator,
                "by_type": by_type,
                "moving_items": moving_items,
                "active_buffs": buff_info,
                "speed_mult": self.buff_manager.get_speed_multiplier(),
            }
```

- [ ] **Step 2: Update `_format_items()` in `probe_panel.py` to display buff info**

In `debug/probe_panel.py`, in the `_format_items` method, after the moving items section (around line 266), add:

```python
        # buff 状态
        buffs = data.get("active_buffs", [])
        speed_mult = data.get("speed_mult", 1.0)
        if buffs:
            lines.append(("─ Buffs", "─", CLR_KEY))
            for b in buffs:
                remaining_s = b.get("remaining_ms", 0) / 1000
                mult = b.get("speed_mult", 1.0)
                effect = "FAST" if mult < 1.0 else "SLOW" if mult > 1.0 else "NONE"
                lines.append((
                    f"  {b.get('id', '?')}",
                    f"{remaining_s:.1f}s ({effect} x{mult})",
                    CLR_ACCENT if mult != 1.0 else CLR_VALUE,
                ))
            lines.append(("  SpeedMult", f"x{speed_mult}", CLR_ACCENT))
```

- [ ] **Step 3: Commit**

```bash
git add scenes/game_screen.py debug/probe_panel.py
git commit -m "feat: add buff state to debug probe display"
```

---

### Task 5: Create Placeholder Images

**Covers:** Asset placeholders for the two new props

**Files:**
- Create: `assets/images/speed_boost.png`
- Create: `assets/images/slow_down.png`

- [ ] **Step 1: Create placeholder images**

Since the project uses pygame-ce, create simple colored circle placeholders. These can be replaced with proper art later.

Run this Python script to generate the placeholders:

```python
# Save as tools/gen_placeholders.py and run once
import pygame
import os

pygame.init()

def create_placeholder(filename, color, size=64):
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    center = size // 2
    pygame.draw.circle(surface, color, (center, center), size // 2 - 4)
    pygame.draw.circle(surface, (255, 255, 255), (center, center), size // 2 - 4, 2)
    pygame.image.save(surface, filename)
    print(f"Created {filename}")

os.makedirs("assets/images", exist_ok=True)
create_placeholder("assets/images/speed_boost.png", (0, 200, 255))
create_placeholder("assets/images/slow_down.png", (200, 100, 255))

pygame.quit()
```

- [ ] **Step 2: Commit**

```bash
git add assets/images/speed_boost.png assets/images/slow_down.png
git commit -m "feat: add placeholder images for speed boost and slowdown props"
```

---

### Task 6: Manual Verification

**Covers:** End-to-end testing of the feature

- [ ] **Step 1: Run the game and verify**

```bash
python main.py
```

Verification checklist:
1. Game starts normally
2. Speed boost prop (cyan circle) appears on screen
3. Slowdown prop (purple circle) appears on screen
4. Picking up speed boost: snake moves faster for ~5 seconds
5. Picking up slowdown: snake moves slower for ~10 seconds
6. Picking up speed boost while slowed: speed effect switches to fast
7. Picking up slowdown while fast: speed effect switches to slow
8. Debug probe (F1) shows active buff info
9. Buff expires correctly and speed returns to normal

- [ ] **Step 2: Commit any final fixes**

```bash
git add -A
git commit -m "fix: final adjustments for speed boost/slowdown props"
```
