"""
scenes/game_screen.py — 贪吃蛇游戏主场景

集成框架输入系统（InputManager）与蛇实体（Snake），
实现完整的贪吃蛇游戏循环：移动、道具、碰撞、渲染。
"""
import pygame
from typing import Optional

from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    CELL_SIZE, GRID_WIDTH, GRID_HEIGHT,
    MARGIN_LEFT, MARGIN_TOP,
    MOVE_INTERVAL,
    ITEM_RENDER_SIZE, GRID_LINE_COLOR, GRID_LINE_WIDTH,
    GAME_BG_COLOR, GAME_BG_LAYERS,
)
from scenes.base_scene import Scene
from entities.player import Snake
from entities.npc import NPCManager
from items import ItemManager, ItemInstance, BuffManager
from items.event_bus import EventBus
from utils import StatsManager
from debug import DebugProbe


class GameScreen(Scene):
    """贪吃蛇游戏场景"""

    def __init__(self, screen: pygame.Surface, debug_probe: DebugProbe | None = None,
                 debug_config=None):
        super().__init__(screen)

        # ── 调试探针 ──
        self.debug_probe = debug_probe or DebugProbe()
        self.debug_config = debug_config
        self._register_probe_collectors()

        # ── 游戏实体 ──
        self.snake = Snake()
        self.event_bus = EventBus()
        self.item_manager = ItemManager(event_bus=self.event_bus)
        self.stats = StatsManager()
        self.buff_manager = BuffManager()
        self.npc_manager = NPCManager(item_manager=self.item_manager, event_bus=self.event_bus)

        # ── 移动计时器（使用 get_ticks 差值，不依赖外部传 delta）──
        self._last_tick: int = 0          # 上一帧的绝对毫秒时间戳
        self._move_accumulator: int = 0   # 移动时间累加器（毫秒）

        # ── 游戏状态 ──
        self.game_over_flag: bool = False
        self.game_over_start_tick: int = 0  # 游戏结束时的时间戳
        self.GAME_OVER_DELAY: int = 1500    # 死亡后可操作的最小等待（毫秒）

        # ── Buff 持续时间（从 debug_config 读取，无配置则用默认值）──
        if self.debug_config and hasattr(self.debug_config, 'buff'):
            bc = self.debug_config.buff
            self.BUFF_SPEED_BOOST_DURATION = bc.speed_boost_duration
            self.BUFF_SLOW_DOWN_DURATION = bc.slow_down_duration
            self.BUFF_CLEAR_DURATION = bc.clear_mode_duration
        else:
            self.BUFF_SPEED_BOOST_DURATION = 5000
            self.BUFF_SLOW_DOWN_DURATION = 10000
            self.BUFF_CLEAR_DURATION = 5000
        self.BUFF_SPEED_BOOST_MULT = 0.5
        self.BUFF_SLOW_DOWN_MULT = 1.5

        # ── 分数滚动动画 ──
        SCORE_ANIM_DURATION = 2000          # 固定 2 秒
        self._score_display: int = 0        # 当前显示值（滚动中）
        self._score_anim_from: int = 0      # 动画起始值
        self._score_target: int = 0         # 目标真实分数
        self._score_anim_start: int = 0     # 动画开始时刻
        self._score_animating: bool = False
        self.SCORE_ANIM_DURATION: int = SCORE_ANIM_DURATION

        # ── 字体 ──
        self.score_font = pygame.font.Font("assets/fonts/DS-DIGIB.TTF", 58)
        self.score_font_over = pygame.font.Font("assets/fonts/SmileySans-Oblique.ttf", 24)
        self.game_over_font = pygame.font.Font("assets/fonts/SmileySans-Oblique.ttf", 48)

        # ── 加载背景图层 ──
        self.bg_layers: list[pygame.Surface] = []
        self._load_backgrounds()

        # ── 预加载道具图片 ──
        self._item_images: dict[str, pygame.Surface | None] = {}
        self._load_item_images()

    # ── 资源加载 ──

    def _load_backgrounds(self):
        """加载并缓存游戏背景图层，缩放至屏幕尺寸"""
        for filename in GAME_BG_LAYERS:
            try:
                img = pygame.image.load(f"assets/images/{filename}").convert_alpha()
                img = pygame.transform.scale(img, (SCREEN_WIDTH, SCREEN_HEIGHT))
                self.bg_layers.append(img)
            except FileNotFoundError:
                print(f"⚠️ 背景图缺失: assets/images/{filename}，跳过")

    def _load_item_images(self):
        """预加载道具图片，统一缩放到 ITEM_RENDER_SIZE"""
        from items.item_defs import ITEM_DEFS
        for item_id, defn in ITEM_DEFS.items():
            if defn.image_key:
                try:
                    img = pygame.image.load(f"assets/images/{defn.image_key}").convert_alpha()
                    img = pygame.transform.scale(img, (ITEM_RENDER_SIZE, ITEM_RENDER_SIZE))
                    self._item_images[item_id] = img
                except FileNotFoundError:
                    print(f"⚠️ 道具图片缺失: assets/images/{defn.image_key}，使用纯色替代")
                    self._item_images[item_id] = None

    # ── 探针注册 ──

    def _register_probe_collectors(self):
        """注册探针数据收集回调"""
        probe = self.debug_probe

        def collect_snake():
            DIR_MAP = {(0, -1): "UP", (0, 1): "DOWN", (-1, 0): "LEFT", (1, 0): "RIGHT"}
            return {
                "head": self.snake.body[0],
                "current_direction": self.snake.current_direction,
                "next_direction": self.snake.next_direction,
                "length": len(self.snake.body),
                "move_accumulator": self._move_accumulator,
                "just_ate": self.snake.just_ate,
                "body_preview": self.snake.body[:5],
            }

        def collect_npcs():
            mgr = self.npc_manager
            npc_list = []
            by_type: dict[str, int] = {}
            for i, npc in enumerate(mgr.npcs):
                type_id = npc.npc_type.npc_id
                by_type[type_id] = by_type.get(type_id, 0) + 1
                npc_list.append({
                    "index": i,
                    "type": type_id,
                    "state": npc.spawn_state.name,
                    "length": len(npc.body),
                    "head": npc.head,
                    "direction": npc.current_direction,
                    "move_accumulator": npc._move_accumulator,
                    "move_interval_ms": npc.move_interval_ms,
                    "target_length": npc.target_length,
                    "unfold_remaining": npc.unfold_remaining,
                    "can_pickup": npc.npc_type.can_pickup,
                    "has_drops": npc.npc_type.has_drops,
                })
            return {
                "alive_count": mgr.alive_count,
                "total_count": mgr.total_count,
                "list": npc_list,
                "by_type": by_type,
                "spawn_enabled": mgr.spawn_enabled,
                "spawn_timer": mgr._spawn_timer,
                "next_spawn_interval": mgr._next_spawn_interval,
                "max_npcs": mgr.max_npcs,
                "frozen": mgr.frozen,
                "speed_multiplier": mgr.speed_multiplier,
                "initial_spawn_count": mgr.initial_spawn_count,
                "spawn_interval_min": mgr.spawn_interval_min,
                "spawn_interval_max": mgr.spawn_interval_max,
            }

        def collect_items():
            mgr = self.item_manager
            by_type: dict[str, int] = {}
            moving_items = []
            for item in mgr.active_items:
                by_type[item.item_id] = by_type.get(item.item_id, 0) + 1
                if item.defn.is_moving and not item.picked:
                    moving_items.append({
                        "id": item.item_id,
                        "fx": item.fx,
                        "fy": item.fy,
                        "dir": item.move_dir,
                    })
            return {
                "total": len(mgr.active_items),
                "spawn_accumulator": mgr._spawn_accumulator,
                "by_type": by_type,
                "moving_items": moving_items,
                "active_buffs": self.buff_manager.get_active_buffs_info(),
                "speed_mult": self.buff_manager.get_speed_multiplier(),
            }

        def collect_collision():
            occupied: set = set(self.snake.body)
            for npc in self.npc_manager.npcs:
                if npc.is_alive:
                    for cell in npc.body:
                        occupied.add(cell)
            for item in self.item_manager.active_items:
                for cell in item.occupied_cells:
                    occupied.add(cell)
            return {
                "occupied_cells": len(occupied),
            }

        def collect_stats():
            return self.stats.get_all_stats()

        def collect_weights():
            from items.difficulty_phases import (
                get_active_phases, get_allowed_categories,
                merge_multipliers, get_allowed_item_ids,
            )
            from items.weight_calculator import (
                calc_screen_count_modifier, calc_length_modifier,
                calc_score_modifier,
            )
            from items.item_defs import ITEM_DEFS
            from settings import PHASE_EARLY_MAX_SCORE

            score = self.stats.get_score()
            snake_len = len(self.snake.body)

            # 当前阶段
            active_phases = get_active_phases(score, snake_len)
            phase_names = []
            for p in active_phases:
                name = f"score>={p.min_score}"
                if p.min_length > 0:
                    name += f" len>={p.min_length}"
                phase_names.append(name)

            allowed_cats = get_allowed_categories(active_phases)
            merged_mult = merge_multipliers(active_phases)
            allowed_ids = get_allowed_item_ids(allowed_cats)

            # 场上计数
            current_counts: dict[str, int] = {}
            for item in self.item_manager.active_items:
                current_counts[item.item_id] = current_counts.get(item.item_id, 0) + 1

            # 计算每个道具的详细权重
            weight_details = []
            for item_id in allowed_ids:
                defn = ITEM_DEFS.get(item_id)
                if defn is None:
                    continue
                base_w = defn.base_weight
                count_mod = calc_screen_count_modifier(
                    current_counts.get(item_id, 0), defn.max_on_screen
                )
                len_mod = calc_length_modifier(defn.category, snake_len)
                score_mod = calc_score_modifier(defn.category, score, PHASE_EARLY_MAX_SCORE)
                cat_mult = merged_mult.get(defn.category, 1.0)
                final_w = base_w * count_mod * len_mod * score_mod * cat_mult
                weight_details.append({
                    "id": item_id,
                    "base": base_w,
                    "count_mod": count_mod,
                    "len_mod": len_mod,
                    "score_mod": score_mod,
                    "cat_mult": cat_mult,
                    "final": int(round(final_w)),
                    "on_screen": current_counts.get(item_id, 0),
                    "max": defn.max_on_screen,
                })

            return {
                "score": score,
                "snake_len": snake_len,
                "active_phases": phase_names,
                "allowed_cats": list(allowed_cats),
                "merged_mult": merged_mult,
                "weight_details": weight_details,
            }

        probe.register("snake", collect_snake)
        probe.register("npcs", collect_npcs)
        probe.register("items", collect_items)
        probe.register("collision", collect_collision)
        probe.register("stats", collect_stats)
        probe.register("weights", collect_weights)

    # ── 场景生命周期 ──

    def on_enter(self):
        """进入游戏场景时初始化/重置游戏状态"""
        print("🟢 进入 GAME（贪吃蛇）")
        pygame.mixer.music.load("assets/sounds/game_music.mp3")
        pygame.mixer.music.play(-1, 0, 0)
        self._reset_game()

    def on_exit(self):
        """离开游戏场景时的清理"""
        print("🔴 离开 GAME")
        pygame.mixer.music.fadeout(500)
        pygame.mixer.music.unload()

    def _reset_game(self):
        """重置游戏到初始状态"""
        self.snake = Snake()
        self.item_manager.reset()
        self.stats.reset()
        self.stats.start_timer()
        self.buff_manager.reset()
        self._last_tick = pygame.time.get_ticks()
        self._move_accumulator = 0
        self.game_over_flag = False
        self.game_over_start_tick = 0
        # ── 分数动画重置 ──
        self._score_display = 0
        self._score_anim_from = 0
        self._score_target = 0
        self._score_anim_start = 0
        self._score_animating = False
        # ── 事件总线 ──
        self.event_bus.reset()
        # ── NPC系统 ──
        self.npc_manager.reset()
        self.npc_manager.init_spawn(self.snake.body)

    # ── 输入处理 ──

    def _map_action_to_direction(self, action: str) -> tuple[int, int] | None:
        """将框架为方标准化动作映射向向量"""
        mapping = {
            "MOVE_UP":    (0, -1),
            "MOVE_DOWN":  (0, 1),
            "MOVE_LEFT":  (-1, 0),
            "MOVE_RIGHT": (1, 0),
        }
        return mapping.get(action)

    def handle_input(self, input_state: dict) -> Optional[str]:
        """
        处理框架传入的标准化输入。
        - 方向动作 → 设置蛇的下一步方向
        - GLOBAL_QUIT → 返回 LOBBY
        """
        # 全局快捷键：ESC → 退出覆盖层（由 SceneManager 拦截），这里做兜底
        if "GLOBAL_QUIT" in input_state["global"]:
            # SceneManager 会先拦截弹出覆盖层，如果用户确认退出，
            # 则通过 return False 退出程序。这里不需要额外处理。
            pass

        # 游戏结束状态下：任意 CONFIRM 或点击 → 返回大厅
        if self.game_over_flag:
            if "CONFIRM" in input_state["context"] or pygame.mouse.get_pressed()[0]:
                return "START"
            return None

        # 正常游戏：方向输入
        for action in input_state["context"]:
            direction = self._map_action_to_direction(action)
            if direction:
                self.snake.set_direction(*direction)

        return None

    # ── 帧更新 ──

    def update(self):
        """
        每帧逻辑更新。
        使用 pygame.time.get_ticks() 计算帧间时间差，
        驱动基于计时器的蛇移动（不依赖外部 clock 传参）。
        """
        now = pygame.time.get_ticks()

        # 首帧初始化时间基准
        if self._last_tick == 0:
            self._last_tick = now
            return

        delta_ms = now - self._last_tick
        self._last_tick = now

        # ── 更新 buff 计时器 ──
        self.buff_manager.update(delta_ms)

        # ── 分数滚动动画（游戏结束时也要驱动，确保归位）──
        if self._score_animating:
            elapsed = now - self._score_anim_start
            t = min(elapsed / self.SCORE_ANIM_DURATION, 1.0)
            self._score_display = int(self._score_anim_from + (self._score_target - self._score_anim_from) * t)
            if t >= 1.0:
                self._score_display = self._score_target
                self._score_animating = False

        # 游戏结束：不做移动更新
        if self.game_over_flag:
            return

        # ── 更新道具管理器（生成新道具，传入游戏状态供权重引擎使用）──
        self.item_manager.update(
            self.snake.body, delta_ms,
            score=self.stats.get_score(),
            snake_length=len(self.snake.body),
        )

        # ── 更新NPC管理器（AI决策 + 移动 + 碰撞）──
        obstacle_cells = self._collect_obstacle_cells()
        self.npc_manager.update(
            self.snake.body,
            self.item_manager.active_items,
            delta_ms,
            obstacles=obstacle_cells,
        )

        # 正常游戏：累加时间并驱动步进
        self._move_accumulator += delta_ms
        effective_interval = MOVE_INTERVAL * self.buff_manager.get_speed_multiplier()
        # 玩家 debug 速度倍率
        if self.snake._speed_multiplier != 1.0:
            effective_interval = int(effective_interval / self.snake._speed_multiplier)
        while self._move_accumulator >= effective_interval:
            self._move_accumulator -= effective_interval
            self._game_step()
            if self.game_over_flag:
                break  # 游戏结束则停止步进

        # ── 同步蛇长到统计模块 ──
        self.stats.set_snake_length(len(self.snake.body))

        # ── 驱动探针收集 ──
        self.debug_probe.tick()

    def _game_step(self):
        """执行一步游戏逻辑：预判碰撞 → 移动蛇 → 检测道具"""
        # 0. 处理待增长队列（清场后蛇增长）
        if self.event_bus.consume_growth():
            self.snake.just_ate = True

        # 0.5 处理待加分数
        pending_score = self.event_bus.consume_score()
        if pending_score > 0:
            self.stats.add_score(pending_score)
            self._score_anim_from = self._score_display
            self._score_target = self.stats.get_score()
            self._score_anim_start = pygame.time.get_ticks()
            self._score_animating = True

        # 1. 预计算新蛇头位置（不移动，仅预测）
        head = self.snake.body[0]
        dx, dy = self.snake.next_direction
        new_head = (head[0] + dx, head[1] + dy)

        # 1. 撞墙检测（移动前）— 墙壁永远致命（除非 god_mode）
        if (new_head[0] < 0 or new_head[0] >= GRID_WIDTH or
                new_head[1] < 0 or new_head[1] >= GRID_HEIGHT):
            self.debug_probe.record_collision("player", "wall", new_head)
            if not self.snake.god_mode:
                self._trigger_game_over()
                return
            # god_mode: 将蛇拉回边界内
            new_head = (
                max(0, min(GRID_WIDTH - 1, new_head[0])),
                max(0, min(GRID_HEIGHT - 1, new_head[1])),
            )

        # 2. 撞自身检测（移动前，预判）
        check_body = self.snake.body[1:] if self.snake.just_ate else self.snake.body[1:-1]
        if new_head in check_body:
            self.debug_probe.record_collision("player", "self", new_head)
            if not self.snake.invincible:
                self._trigger_game_over()
                return

        # 3. 撞障碍物检测
        clear_mode = self.buff_manager.has_clear_mode()
        obstacle_hit = self._find_obstacle_at(new_head)
        if obstacle_hit:
            self.debug_probe.record_collision("player", f"obstacle:{obstacle_hit.item_id}", new_head)
            if clear_mode or self.snake.invincible:
                self.item_manager.remove_item(obstacle_hit)
            else:
                self._trigger_game_over()
                return

        # 4. 撞NPC检测
        npc_hit = self._find_npc_at(new_head)
        if npc_hit:
            self.debug_probe.record_collision("player", f"npc:{npc_hit.npc_type.npc_id}", new_head)
            if clear_mode or self.snake.invincible:
                npc_hit.kill()
            else:
                self._trigger_game_over()
                return

        # 5. 移动蛇
        new_head = self.snake.move()

        # 6. 检测是否碰撞到道具
        collected = self.item_manager.check_collision(new_head)
        if collected:
            self._apply_item_effect(collected)
        else:
            self.snake.just_ate = False

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
        elif item.item_id == "lucky_clear_block":
            self.buff_manager.add_buff(
                "lucky_clear_block",
                self.BUFF_CLEAR_DURATION,
                clear_mode=True,
            )
        elif item.item_id == "unique_bouncing_lucky_prop":
            self._execute_full_clear(item.defn.score_value)

        # 触发分数滚动动画
        self._score_anim_from = self._score_display
        self._score_target = self.stats.get_score()
        self._score_anim_start = pygame.time.get_ticks()
        self._score_animating = True

    def _execute_full_clear(self, bonus_score: int):
        """执行全场清除：清NPC+清道具+奖励"""
        # 1. 开始清场锁
        self.event_bus.start_clear()

        # 2. 杀死所有NPC（它们会正常掉落道具）
        for npc in self.npc_manager.npcs:
            if npc.is_alive:
                npc.kill()

        # 3. 清理死亡NPC（触发掉落）
        self.npc_manager._cleanup_dead()

        # 4. 清除所有道具（包括刚掉落的）
        self.item_manager.active_items.clear()

        # 5. 计算奖励：分数 + 蛇增长（按NPC数量）
        npc_count = len(self.npc_manager.npcs)
        growth_segments = max(1, npc_count // 2)  # 增长节数 = NPC数/2，最少1节

        # 6. 完成清场
        self.event_bus.finish_clear(bonus_score, growth_segments)

    def _trigger_game_over(self):
        """触发游戏结束"""
        self.game_over_flag = True
        self.game_over_start_tick = pygame.time.get_ticks()

    def _collect_obstacle_cells(self) -> set[tuple[int, int]]:
        """收集场上所有障碍物占据的格子"""
        cells: set[tuple[int, int]] = set()
        for item in self.item_manager.active_items:
            if item.defn.category == "obstacle" and not item.picked:
                for cell in item.occupied_cells:
                    cells.add(cell)
        return cells

    def _find_obstacle_at(self, pos: tuple[int, int]) -> 'ItemInstance | None':
        """查找指定位置的障碍物道具实例"""
        for item in self.item_manager.active_items:
            if item.defn.category == "obstacle" and not item.picked:
                if item.contains(pos[0], pos[1]):
                    return item
        return None

    def _find_npc_at(self, pos: tuple[int, int]) -> 'NPCSnake | None':
        """查找指定位置的NPC蛇实例"""
        for npc in self.npc_manager.npcs:
            if npc.is_alive and pos in npc.body:
                return npc
        return None

    # ── 渲染 ──

    def draw(self, screen: pygame.Surface):
        """绘制游戏画面：背景 → 网格 → 食物 → 蛇 → UI"""
        # 0. 清屏
        screen.fill(GAME_BG_COLOR)

        # 1. 背景图层
        for layer in self.bg_layers:
            screen.blit(layer, (0, 0))

        # 2. 网格线
        self._draw_grid(screen)

        # 3. 道具
        if not self.game_over_flag:
            self._draw_items(screen)

        # 4. 蛇
        self.snake.draw(screen)

        # 5. NPC蛇
        self.npc_manager.draw(screen)

        # 6. 分数
        self._draw_score(screen)

        # 6. 游戏结束提示
        if self.game_over_flag:
            self._draw_game_over(screen)

    def _draw_grid(self, screen: pygame.Surface):
        """绘制网格线（棋盘风格边框）"""
        for x in range(GRID_WIDTH):
            for y in range(GRID_HEIGHT):
                rect = pygame.Rect(
                    MARGIN_LEFT + x * CELL_SIZE,
                    MARGIN_TOP + y * CELL_SIZE,
                    CELL_SIZE + 2,
                    CELL_SIZE + 2,
                )
                pygame.draw.rect(
                    screen, GRID_LINE_COLOR, rect,
                    width=GRID_LINE_WIDTH, border_radius=4,
                )

    def _draw_items(self, screen: pygame.Surface):
        """绘制场上所有道具（使用预加载的图片，移动道具平滑渲染）"""
        for item in self.item_manager.active_items:
            # 使用小数格坐标 (fx, fy) 计算平滑像素位置
            px = MARGIN_LEFT + item.fx * CELL_SIZE - CELL_SIZE // 2
            py = MARGIN_TOP + item.fy * CELL_SIZE - CELL_SIZE // 2
            cx = px + CELL_SIZE // 2
            cy = py + CELL_SIZE // 2

            img = self._item_images.get(item.item_id)
            if img:
                rect = img.get_rect(center=(cx, cy))
                screen.blit(img, rect)
            else:
                color = item.defn.color
                pygame.draw.circle(screen, color, (cx, cy), ITEM_RENDER_SIZE // 2)

    def _draw_score(self, screen: pygame.Surface):
        """绘制当前分数（滚动动画 + 零填充数码管风格）"""
        score_text = self.score_font.render(
            f"SCORE:{self._score_display:015d}",
            True, (34, 219, 228),
        )
        screen.blit(score_text, (333, 28))

    def _draw_game_over(self, screen: pygame.Surface):
        """绘制游戏结束提示"""
        # 半透明遮罩
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))

        # 游戏结束文字
        go_text = self.game_over_font.render("游戏结束", True, (255, 80, 80))
        go_rect = go_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
        screen.blit(go_text, go_rect)

        # 提示文字
        stats = self.stats.get_all_stats()
        hint_text = self.score_font_over.render(
            f"最终得分：{stats['score']}  最大连击：{stats['max_combo']} — 按任意键返回大厅",
            True, (200, 200, 200),
        )
        hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
        screen.blit(hint_text, hint_rect)
