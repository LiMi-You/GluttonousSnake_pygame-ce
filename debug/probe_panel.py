"""
debug/probe_panel.py — 探针 UI 面板（imgui 版）

使用 Dear ImGui 绘制调试面板，支持折叠区块、滚动、实时数据展示、NPC运行时控制、玩家控制。
"""
from __future__ import annotations
import imgui
from typing import Any, TYPE_CHECKING

from .probe_core import DebugProbe
from .debug_config import DebugConfig

if TYPE_CHECKING:
    from entities.npc.npc_manager import NPCManager
    from entities.player import Snake
    from items.item_manager import ItemManager
    from items.buff_manager import BuffManager


class ProbePanel:
    """探针面板（imgui 即时模式）"""

    def __init__(
        self,
        probe: DebugProbe,
        npc_manager: 'NPCManager | None' = None,
        config: DebugConfig | None = None,
    ):
        self.probe = probe
        self.npc_manager = npc_manager
        self.config = config or DebugConfig()
        self._snake: 'Snake | None' = None
        self._item_manager: 'ItemManager | None' = None
        self._buff_manager: 'BuffManager | None' = None
        self._dirty = False

    def set_snake(self, snake: 'Snake'):
        """设置玩家蛇引用（GameScreen 初始化后调用）"""
        self._snake = snake
        self._sync_config_to_snake()

    def set_item_manager(self, item_manager: 'ItemManager'):
        """设置道具管理器引用"""
        self._item_manager = item_manager
        self._sync_config_to_items()

    def set_buff_manager(self, buff_manager: 'BuffManager'):
        """设置Buff管理器引用"""
        self._buff_manager = buff_manager

    def _sync_config_to_snake(self):
        """将 config 值同步到 snake 实例"""
        if not self._snake:
            return
        pc = self.config.player
        self._snake.invincible = pc.invincible
        self._snake.god_mode = pc.god_mode
        self._snake._speed_multiplier = pc.speed_multiplier

    def _sync_config_to_npc(self):
        """将 config 值同步到 npc_manager"""
        if not self.npc_manager:
            return
        nc = self.config.npc
        self.npc_manager.spawn_enabled = nc.spawn_enabled
        self.npc_manager.initial_spawn_count = nc.initial_spawn_count
        self.npc_manager.spawn_interval_min = nc.spawn_interval_min
        self.npc_manager.spawn_interval_max = nc.spawn_interval_max
        self.npc_manager.max_npcs = nc.max_npcs
        self.npc_manager.frozen = nc.frozen
        self.npc_manager.speed_multiplier = nc.speed_multiplier
        self.npc_manager.periodic_spawn_pool = dict(nc.spawn_pool)

    def _sync_config_to_items(self):
        """将 config 值同步到 item_manager"""
        if not self._item_manager:
            return
        ic = self.config.item
        self._item_manager.spawn_interval = ic.spawn_interval
        self._item_manager.max_on_screen = ic.max_on_screen
        self._item_manager.initial_spawn_count = ic.initial_spawn_count
        self._item_manager.move_base_speed = ic.move_base_speed
        self._item_manager._weight_overrides = dict(ic.weight_overrides)
        self._item_manager._enabled_overrides = dict(ic.enabled_overrides)

    def _sync_config_to_phase(self):
        """将 config 值同步到 difficulty_phases"""
        from items.difficulty_phases import set_phase_overrides, DifficultyPhaseOverrides
        pc = self.config.phase
        overrides = DifficultyPhaseOverrides(
            early_max_score=pc.early_max_score,
            early_categories=list(pc.early_categories),
            mid_min_score=pc.mid_min_score,
            mid_categories=list(pc.mid_categories),
            late_min_length=pc.late_min_length,
            late_categories=list(pc.late_categories),
            late_obstacle_mult=pc.late_obstacle_mult,
            late_debuff_mult=pc.late_debuff_mult,
        )
        set_phase_overrides(overrides)

    def _sync_config_to_weight(self):
        """将 config 值同步到 weight_calculator"""
        from items.weight_calculator import (
            set_length_coefficients, set_score_suppress_factor,
        )
        wc = self.config.weight
        set_length_coefficients(wc.length_obstacle_coeff, wc.length_debuff_coeff, wc.length_lucky_coeff)
        set_score_suppress_factor(wc.score_suppress_factor)

    def _mark_dirty(self):
        """标记配置已修改，需要保存"""
        self._dirty = True

    def save_if_needed(self):
        """如果有修改，保存配置"""
        if self._dirty:
            self.config.save()
            self._dirty = False

    def draw(self):
        """绘制探针面板（每帧调用）"""
        if not self.probe.enabled:
            return

        snapshot = self.probe.get_snapshot()

        # ── 窗口 1: 数据展示 ──
        imgui.begin("[F1] DEBUG PROBE", True)

        self._draw_performance(snapshot)
        self._draw_snake(snapshot)
        self._draw_npcs(snapshot)
        self._draw_items(snapshot)
        self._draw_weights(snapshot)
        self._draw_collision(snapshot)
        self._draw_stats(snapshot)

        imgui.end()

        # ── 窗口 2: 玩家控制 ──
        imgui.begin("Player Controls", True)

        self._draw_player_controls(snapshot)

        imgui.end()

        # ── 窗口 3: NPC 控制 ──
        if self.npc_manager:
            imgui.begin("NPC Controls", True)

            self._draw_npc_controls(snapshot)

            imgui.end()

        # ── 窗口 4: Items 控制 ──
        if self._item_manager:
            imgui.begin("Items Controls", True)

            self._draw_items_controls(snapshot)

            imgui.end()

        # 自动保存
        self.save_if_needed()

    # ── Performance ──

    def _draw_performance(self, snap: dict):
        fps = self.probe.get_fps()
        frame_ms = self.probe.get_frame_ms()

        imgui.text(f"FPS:   {fps:.1f}")
        imgui.text(f"Frame: {frame_ms:.1f} ms")
        imgui.text(f"Tick:  {self.probe.tick_count}")
        imgui.separator()

    # ── Player Controls ──

    def _draw_player_controls(self, snap: dict):
        pc = self.config.player

        if imgui.tree_node("Move Config", imgui.TREE_NODE_DEFAULT_OPEN):
            changed, pc.move_interval = imgui.slider_int(
                "Move Interval (ms)", pc.move_interval, 30, 500
            )
            if changed:
                self._mark_dirty()

            changed, pc.speed_multiplier = imgui.slider_float(
                "Speed Multiplier", pc.speed_multiplier, 0.1, 5.0, "%.1f"
            )
            if changed:
                self._mark_dirty()
                self._sync_config_to_snake()

            imgui.tree_pop()

        if imgui.tree_node("Debug Flags"):
            changed, pc.invincible = imgui.checkbox("Invincible", pc.invincible)
            if changed:
                self._mark_dirty()
                self._sync_config_to_snake()

            changed, pc.god_mode = imgui.checkbox("God Mode (No Wall Death)", pc.god_mode)
            if changed:
                self._mark_dirty()
                self._sync_config_to_snake()

            changed, pc.auto_play = imgui.checkbox("Auto Play", pc.auto_play)
            if changed:
                self._mark_dirty()

            imgui.tree_pop()

        # 玩家状态（只读）
        if imgui.tree_node("Status"):
            s = snap.get("snake", {})
            DIR_MAP = {(0, -1): "UP", (0, 1): "DOWN", (-1, 0): "LEFT", (1, 0): "RIGHT"}
            head = s.get("head", (0, 0))
            cur_dir = tuple(s.get("current_direction", (0, 0)))

            imgui.text(f"Head:      {head}")
            imgui.text(f"Dir:       {DIR_MAP.get(cur_dir, str(cur_dir))}")
            imgui.text(f"Length:    {s.get('length', 0)}")
            imgui.text(f"JustAte:   {s.get('just_ate', False)}")

            # 状态标签
            if pc.invincible:
                imgui.text_colored("[INVINCIBLE]", 1.0, 0.8, 0.0)
            if pc.god_mode:
                imgui.text_colored("[GOD MODE]", 0.0, 1.0, 1.0)
            if pc.auto_play:
                imgui.text_colored("[AUTO PLAY]", 0.5, 1.0, 0.5)

            imgui.tree_pop()

    # ── Player Snake ──

    def _draw_snake(self, snap: dict):
        if imgui.tree_node("Player Snake", imgui.TREE_NODE_DEFAULT_OPEN):
            s = snap.get("snake", {})
            DIR_MAP = {(0, -1): "UP", (0, 1): "DOWN", (-1, 0): "LEFT", (1, 0): "RIGHT"}
            head = s.get("head", (0, 0))
            cur_dir = tuple(s.get("current_direction", (0, 0)))
            nxt_dir = tuple(s.get("next_direction", (0, 0)))

            imgui.text(f"Head:      {head}")
            imgui.text(f"Dir(cur):  {DIR_MAP.get(cur_dir, str(cur_dir))}")
            imgui.text(f"Dir(next): {DIR_MAP.get(nxt_dir, str(nxt_dir))}")
            imgui.text(f"Length:    {s.get('length', 0)}")
            imgui.text(f"MoveAcc:   {s.get('move_accumulator', 0)} ms")
            imgui.text(f"JustAte:   {s.get('just_ate', False)}")

            if imgui.tree_node("Body[0:5]"):
                for i, seg in enumerate(s.get("body_preview", [])[:5]):
                    imgui.text(f"  [{i}] {seg}")
                imgui.tree_pop()

            imgui.tree_pop()

    # ── NPC Controls ──

    def _draw_npc_controls(self, snap: dict):
        if not self.npc_manager:
            return

        npc_data = snap.get("npcs", {})
        nc = self.config.npc
        mgr = self.npc_manager

        if imgui.tree_node("Spawn Config", imgui.TREE_NODE_DEFAULT_OPEN):
            changed, nc.spawn_enabled = imgui.checkbox("Spawn Enabled", nc.spawn_enabled)
            if changed:
                self._mark_dirty()
                mgr.spawn_enabled = nc.spawn_enabled

            changed, nc.initial_spawn_count = imgui.slider_int(
                "Initial Count", nc.initial_spawn_count, 0, 10
            )
            if changed:
                self._mark_dirty()
                mgr.initial_spawn_count = nc.initial_spawn_count

            changed, nc.max_npcs = imgui.slider_int(
                "Max NPCs", nc.max_npcs, 1, 20
            )
            if changed:
                self._mark_dirty()
                mgr.max_npcs = nc.max_npcs

            changed, nc.spawn_interval_min = imgui.slider_int(
                "Interval Min (ms)", nc.spawn_interval_min, 1000, 30000
            )
            if changed:
                self._mark_dirty()
                mgr.spawn_interval_min = nc.spawn_interval_min

            changed, nc.spawn_interval_max = imgui.slider_int(
                "Interval Max (ms)", nc.spawn_interval_max, 1000, 30000
            )
            if changed:
                self._mark_dirty()
                mgr.spawn_interval_max = nc.spawn_interval_max

            if nc.spawn_interval_min > nc.spawn_interval_max:
                nc.spawn_interval_max = nc.spawn_interval_min
                mgr.spawn_interval_max = nc.spawn_interval_max

            imgui.tree_pop()

        if imgui.tree_node("Runtime"):
            changed, nc.frozen = imgui.checkbox("Freeze All NPC", nc.frozen)
            if changed:
                self._mark_dirty()
                mgr.frozen = nc.frozen

            changed, nc.speed_multiplier = imgui.slider_float(
                "Speed Multiplier", nc.speed_multiplier, 0.1, 5.0, "%.1f"
            )
            if changed:
                self._mark_dirty()
                mgr.speed_multiplier = nc.speed_multiplier

            imgui.spacing()

            if imgui.button("Kill All NPCs"):
                mgr.debug_kill_all()
            imgui.same_line()
            imgui.text(f"Alive: {npc_data.get('alive_count', 0)}")

            imgui.tree_pop()

        if imgui.tree_node("Spawn Timer"):
            timer = npc_data.get("spawn_timer", 0)
            next_int = npc_data.get("next_spawn_interval", 0)
            progress = timer / next_int if next_int > 0 else 0.0
            imgui.text(f"Timer:      {timer} / {next_int} ms")
            imgui.progress_bar(progress, (0.0, 0.0), f"{progress * 100:.0f}%")
            imgui.tree_pop()

            # ── 手动生成 ──
            if imgui.tree_node("Manual Spawn"):
                for type_id in ["standard", "foraging", "loot", "mythic", "hunter"]:
                    if imgui.button(f"Spawn {type_id}"):
                        if mgr.debug_spawn(type_id, []):
                            pass  # 成功
                imgui.tree_pop()

            # ── 类型配置（只读展示）──
            if imgui.tree_node("Type Configs"):
                self._draw_type_configs()
                imgui.tree_pop()

            # ── 权重池配置 ──
            if imgui.tree_node("Spawn Pool Weights"):
                for type_id in list(nc.spawn_pool.keys()):
                    weight = nc.spawn_pool[type_id]
                    changed, new_val = imgui.slider_int(
                        f"##{type_id}", weight, 0, 100
                    )
                    if changed:
                        nc.spawn_pool[type_id] = new_val
                        mgr.periodic_spawn_pool[type_id] = new_val
                        self._mark_dirty()
                    imgui.same_line()
                    imgui.text(type_id)
                imgui.tree_pop()

    def _draw_type_configs(self):
        """展示各NPC类型的配置参数"""
        from entities.npc.npc_types import NPC_TYPE_DEFS

        for type_id, defn in NPC_TYPE_DEFS.items():
            if imgui.tree_node(f"{type_id}"):
                imgui.text(f"Length:     {defn.min_length} ~ {defn.max_length}")
                imgui.text(f"Move:       {defn.move_interval_ms} ms")
                imgui.text(f"Drops:      {'Yes' if defn.has_drops else 'No'} (x{defn.drop_count})")
                imgui.text(f"Pickup:     {'Yes' if defn.can_pickup else 'No'} ({defn.pickup_chance})")
                imgui.text(f"Strategy:   {defn.nav_strategy.name}")
                imgui.text(f"Color:      RGB{defn.color}")
                imgui.tree_pop()

    # ── Items Controls ──

    def _draw_items_controls(self, snap: dict):
        ic = self.config.item
        pc = self.config.phase
        wc = self.config.weight
        bc = self.config.buff
        mgr = self._item_manager

        # ── 全局生成配置 ──
        if imgui.tree_node("Spawn Config", imgui.TREE_NODE_DEFAULT_OPEN):
            changed, ic.spawn_interval = imgui.slider_int(
                "Spawn Interval (ms)", ic.spawn_interval, 500, 10000
            )
            if changed:
                self._mark_dirty()
                mgr.spawn_interval = ic.spawn_interval

            changed, ic.max_on_screen = imgui.slider_int(
                "Max On Screen", ic.max_on_screen, 10, 200
            )
            if changed:
                self._mark_dirty()
                mgr.max_on_screen = ic.max_on_screen

            changed, ic.initial_spawn_count = imgui.slider_int(
                "Initial Count", ic.initial_spawn_count, 0, 20
            )
            if changed:
                self._mark_dirty()
                mgr.initial_spawn_count = ic.initial_spawn_count

            changed, ic.move_base_speed = imgui.slider_float(
                "Move Base Speed", ic.move_base_speed, 0.01, 0.1, "%.3f"
            )
            if changed:
                self._mark_dirty()
                mgr.move_base_speed = ic.move_base_speed

            imgui.tree_pop()

        # ── 每类型权重 + 开关 ──
        if imgui.tree_node("Item Weights"):
            from items.item_defs import ITEM_DEFS
            for item_id, defn in ITEM_DEFS.items():
                # 开关
                enabled = ic.enabled_overrides.get(item_id, True)
                changed, new_enabled = imgui.checkbox(f"##en_{item_id}", enabled)
                if changed:
                    ic.enabled_overrides[item_id] = new_enabled
                    mgr.set_enabled(item_id, new_enabled)
                    self._mark_dirty()
                imgui.same_line()

                # 权重 slider
                current_w = ic.weight_overrides.get(item_id, defn.base_weight)
                changed, new_w = imgui.slider_int(
                    f"##w_{item_id}", current_w, 0, 200
                )
                if changed:
                    ic.weight_overrides[item_id] = new_w
                    mgr.set_weight_override(item_id, new_w)
                    self._mark_dirty()
                imgui.same_line()
                imgui.text(item_id)

            imgui.tree_pop()

        # ── 难度阶段 ──
        if imgui.tree_node("Difficulty Phases"):
            imgui.text("Early (always active):")
            changed, pc.early_max_score = imgui.slider_int(
                "Early Max Score", pc.early_max_score, 0, 500000
            )
            if changed:
                self._mark_dirty()
                self._sync_config_to_phase()

            # 早期分类 toggle
            for cat in ["basic", "lucky", "buff", "debuff", "obstacle"]:
                active = cat in pc.early_categories
                changed, new_active = imgui.checkbox(f"##early_{cat}", active)
                if changed:
                    if new_active and cat not in pc.early_categories:
                        pc.early_categories.append(cat)
                    elif not new_active and cat in pc.early_categories:
                        pc.early_categories.remove(cat)
                    self._mark_dirty()
                    self._sync_config_to_phase()
                imgui.same_line()
                imgui.text(cat)

            imgui.separator()
            imgui.text("Mid (score >= threshold):")
            changed, pc.mid_min_score = imgui.slider_int(
                "Mid Min Score", pc.mid_min_score, 0, 500000
            )
            if changed:
                self._mark_dirty()
                self._sync_config_to_phase()

            for cat in ["basic", "lucky", "buff", "debuff", "obstacle"]:
                active = cat in pc.mid_categories
                changed, new_active = imgui.checkbox(f"##mid_{cat}", active)
                if changed:
                    if new_active and cat not in pc.mid_categories:
                        pc.mid_categories.append(cat)
                    elif not new_active and cat in pc.mid_categories:
                        pc.mid_categories.remove(cat)
                    self._mark_dirty()
                    self._sync_config_to_phase()
                imgui.same_line()
                imgui.text(cat)

            imgui.separator()
            imgui.text("Late (length >= threshold):")
            changed, pc.late_min_length = imgui.slider_int(
                "Late Min Length", pc.late_min_length, 0, 50
            )
            if changed:
                self._mark_dirty()
                self._sync_config_to_phase()

            for cat in ["basic", "lucky", "buff", "debuff", "obstacle"]:
                active = cat in pc.late_categories
                changed, new_active = imgui.checkbox(f"##late_{cat}", active)
                if changed:
                    if new_active and cat not in pc.late_categories:
                        pc.late_categories.append(cat)
                    elif not new_active and cat in pc.late_categories:
                        pc.late_categories.remove(cat)
                    self._mark_dirty()
                    self._sync_config_to_phase()
                imgui.same_line()
                imgui.text(cat)

            changed, pc.late_obstacle_mult = imgui.slider_float(
                "Late Obstacle Mult", pc.late_obstacle_mult, 0.5, 5.0, "%.1f"
            )
            if changed:
                self._mark_dirty()
                self._sync_config_to_phase()

            changed, pc.late_debuff_mult = imgui.slider_float(
                "Late Debuff Mult", pc.late_debuff_mult, 0.5, 5.0, "%.1f"
            )
            if changed:
                self._mark_dirty()
                self._sync_config_to_phase()

            imgui.tree_pop()

        # ── 权重公式系数 ──
        if imgui.tree_node("Weight Formula"):
            changed, wc.length_obstacle_coeff = imgui.slider_float(
                "Obstacle Length Coeff", wc.length_obstacle_coeff, 0.0, 0.2, "%.3f"
            )
            if changed:
                self._mark_dirty()
                self._sync_config_to_weight()

            changed, wc.length_debuff_coeff = imgui.slider_float(
                "Debuff Length Coeff", wc.length_debuff_coeff, 0.0, 0.2, "%.3f"
            )
            if changed:
                self._mark_dirty()
                self._sync_config_to_weight()

            changed, wc.length_lucky_coeff = imgui.slider_float(
                "Lucky Length Coeff", wc.length_lucky_coeff, -0.1, 0.0, "%.3f"
            )
            if changed:
                self._mark_dirty()
                self._sync_config_to_weight()

            changed, wc.score_suppress_factor = imgui.slider_float(
                "Score Suppress Factor", wc.score_suppress_factor, 0.0, 1.0, "%.2f"
            )
            if changed:
                self._mark_dirty()
                self._sync_config_to_weight()

            imgui.tree_pop()

        # ── Buff 持续时间 ──
        if imgui.tree_node("Buff Duration"):
            changed, bc.speed_boost_duration = imgui.slider_int(
                "Speed Boost (ms)", bc.speed_boost_duration, 1000, 20000
            )
            if changed:
                self._mark_dirty()

            changed, bc.slow_down_duration = imgui.slider_int(
                "Slow Down (ms)", bc.slow_down_duration, 1000, 20000
            )
            if changed:
                self._mark_dirty()

            changed, bc.clear_mode_duration = imgui.slider_int(
                "Clear Mode (ms)", bc.clear_mode_duration, 1000, 20000
            )
            if changed:
                self._mark_dirty()

            imgui.tree_pop()

        # ── 运行时按钮 ──
        if imgui.tree_node("Runtime"):
            if imgui.button("Clear All Items"):
                mgr.active_items.clear()
            imgui.same_line()
            imgui.text(f"On screen: {len(mgr.active_items)}")

            imgui.spacing()

            for item_id in ["score_boost", "lucky_patrol_food", "speed_boost",
                            "slow_down", "common_obstacle", "lucky_clear_block"]:
                if imgui.button(f"Spawn {item_id}"):
                    mgr._spawn_one(item_id)
                imgui.same_line()
            imgui.new_line()

            imgui.tree_pop()

        # ── 只读：场上统计 ──
        if imgui.tree_node("On Screen Stats"):
            items_data = snap.get("items", {})
            by_type = items_data.get("by_type", {})
            for item_id, count in sorted(by_type.items()):
                imgui.text(f"  {item_id}: {count}")
            if not by_type:
                imgui.text("  (empty)")
            imgui.tree_pop()

    # ── NPCs ──

    def _draw_npcs(self, snap: dict):
        data = snap.get("npcs", {})
        alive = data.get("alive_count", 0)
        total = data.get("total_count", 0)
        by_type = data.get("by_type", {})

        type_summary = " ".join(f"{k}:{v}" for k, v in by_type.items()) if by_type else ""
        label = f"NPCs ({alive}/{total}) {type_summary}"

        if imgui.tree_node(label):
            for npc in data.get("list", []):
                state = npc.get("state", "")
                idx = npc.get("index", "?")
                npc_type = npc.get("type", "?")
                header = f"#{idx} {npc_type}"

                if imgui.tree_node(header):
                    imgui.text(f"State:    {state}")
                    imgui.text(f"Length:   {npc.get('length', 0)} / {npc.get('target_length', '?')}")
                    imgui.text(f"Head:     {npc.get('head', (0,0))}")
                    imgui.text(f"Dir:      {npc.get('direction', (0,0))}")
                    imgui.text(f"MoveAcc:  {npc.get('move_accumulator', 0)} ms")
                    imgui.text(f"Interval: {npc.get('move_interval_ms', 150)} ms")
                    imgui.text(f"Unfold:   {npc.get('unfold_remaining', 0)}")
                    imgui.text(f"Pickup:   {npc.get('can_pickup', False)}")
                    imgui.text(f"Drops:    {npc.get('has_drops', False)}")
                    imgui.tree_pop()

            imgui.tree_pop()

    # ── Items ──

    def _draw_items(self, snap: dict):
        data = snap.get("items", {})
        total = data.get("total", 0)

        label = f"Items ({total})"
        if imgui.tree_node(label):
            imgui.text(f"SpawnAcc: {data.get('spawn_accumulator', 0)} ms")

            by_type = data.get("by_type", {})
            if by_type:
                if imgui.tree_node("By Type"):
                    for item_type, count in by_type.items():
                        imgui.text(f"  {item_type}: {count}")
                    imgui.tree_pop()

            moving = data.get("moving_items", [])
            if moving:
                if imgui.tree_node(f"Moving ({len(moving)})"):
                    for m in moving[:10]:
                        imgui.text(
                            f"  {m.get('id', '?')} "
                            f"f({m.get('fx', 0):.1f},{m.get('fy', 0):.1f}) "
                            f"dir={m.get('dir', (0,0))}"
                        )
                    if len(moving) > 10:
                        imgui.text(f"  ... +{len(moving)-10} more")
                    imgui.tree_pop()

            buffs = data.get("active_buffs", [])
            speed_mult = data.get("speed_mult", 1.0)
            if buffs:
                if imgui.tree_node(f"Buffs ({len(buffs)})"):
                    for b in buffs:
                        remaining_s = b.get("remaining_ms", 0) / 1000
                        mult = b.get("speed_mult", 1.0)
                        is_clear = b.get("clear_mode", False)
                        if is_clear:
                            effect = "CLEAR"
                        elif mult < 1.0:
                            effect = "FAST"
                        elif mult > 1.0:
                            effect = "SLOW"
                        else:
                            effect = "NONE"
                        imgui.text(f"  {b.get('id', '?')}: {remaining_s:.1f}s ({effect})")
                    imgui.text(f"  SpeedMult: x{speed_mult}")
                    imgui.tree_pop()

            imgui.tree_pop()

    # ── Weight Calc ──

    def _draw_weights(self, snap: dict):
        data = snap.get("weights", {})
        if imgui.tree_node("Weight Calc"):
            imgui.text(f"Score:    {data.get('score', 0)}")
            imgui.text(f"SnakeLen: {data.get('snake_len', 0)}")

            phases = data.get("active_phases", [])
            imgui.text(f"Phases:   {', '.join(phases) if phases else 'NONE'}")

            cats = data.get("allowed_cats", [])
            imgui.text(f"AllowCats: {', '.join(cats) if cats else 'NONE'}")

            mult = data.get("merged_mult", {})
            if mult:
                if imgui.tree_node("Multipliers"):
                    for cat, m in mult.items():
                        imgui.text(f"  {cat}: x{m}")
                    imgui.tree_pop()

            details = data.get("weight_details", [])
            if details:
                if imgui.tree_node(f"Details ({len(details)})"):
                    for d in details:
                        imgui.text(
                            f"  {d.get('id', '?')}: "
                            f"w={d.get('final', 0)} "
                            f"(base={d.get('base', 0)} "
                            f"x{d.get('count_mod', 0):.2f} "
                            f"x{d.get('len_mod', 0):.2f} "
                            f"x{d.get('score_mod', 0):.2f} "
                            f"x{d.get('cat_mult', 0):.1f}) "
                            f"[{d.get('on_screen', 0)}/{d.get('max', 0)}]"
                        )
                    imgui.tree_pop()
            else:
                imgui.text("  (no allowed items)")

            imgui.tree_pop()

    # ── Collision ──

    def _draw_collision(self, snap: dict):
        data = snap.get("collision", {})
        if imgui.tree_node("Collision"):
            imgui.text(f"Occupied cells: {data.get('occupied_cells', 0)}")

            history = self.probe.get_collision_history()
            if history:
                recent = history[-5:]
                if imgui.tree_node(f"Recent ({len(history)} total)"):
                    for ev in reversed(recent):
                        imgui.text(f"  {ev.subject} -> {ev.target} @{ev.pos}")
                    imgui.tree_pop()
            else:
                imgui.text("Last: NONE")

            imgui.tree_pop()

    # ── Stats ──

    def _draw_stats(self, snap: dict):
        data = snap.get("stats", {})
        score = data.get("score", 0)
        combo = data.get("combo", 0)
        max_combo = data.get("max_combo", 0)
        time_ms = data.get("play_time_ms", 0)
        mins = (time_ms // 1000) // 60
        secs = (time_ms // 1000) % 60

        if imgui.tree_node("Stats"):
            imgui.text(f"Score:    {score}")
            imgui.text(f"Combo:    {combo} (max {max_combo})")
            imgui.text(f"Time:     {mins:02d}:{secs:02d}")
            imgui.text(f"SnakeLen: {data.get('snake_length', 0)}")

            items_collected = data.get("items_collected", {})
            if items_collected:
                if imgui.tree_node("Collected"):
                    for item_id, count in items_collected.items():
                        imgui.text(f"  {item_id}: {count}")
                    imgui.tree_pop()

            imgui.tree_pop()
