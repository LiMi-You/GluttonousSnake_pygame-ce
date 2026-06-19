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
from items import ItemManager, ItemInstance
from utils import StatsManager
from debug import DebugProbe


class GameScreen(Scene):
    """贪吃蛇游戏场景"""

    def __init__(self, screen: pygame.Surface, debug_probe: DebugProbe | None = None):
        super().__init__(screen)

        # ── 调试探针 ──
        self.debug_probe = debug_probe or DebugProbe()
        self._register_probe_collectors()

        # ── 游戏实体 ──
        self.snake = Snake()
        self.item_manager = ItemManager()
        self.stats = StatsManager()
        self.npc_manager = NPCManager(item_manager=self.item_manager)

        # ── 移动计时器（使用 get_ticks 差值，不依赖外部传 delta）──
        self._last_tick: int = 0          # 上一帧的绝对毫秒时间戳
        self._move_accumulator: int = 0   # 移动时间累加器（毫秒）

        # ── 游戏状态 ──
        self.game_over_flag: bool = False
        self.game_over_start_tick: int = 0  # 游戏结束时的时间戳
        self.GAME_OVER_DELAY: int = 1500    # 死亡后可操作的最小等待（毫秒）

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
            npc_list = []
            for i, npc in enumerate(self.npc_manager.npcs):
                npc_list.append({
                    "index": i,
                    "type": npc.npc_type.npc_id,
                    "state": npc.spawn_state.name,
                    "length": len(npc.body),
                    "head": npc.head,
                    "direction": npc.current_direction,
                    "move_accumulator": npc._move_accumulator,
                })
            return {
                "alive_count": self.npc_manager.alive_count,
                "total_count": self.npc_manager.total_count,
                "list": npc_list,
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
        self.npc_manager.update(
            self.snake.body,
            self.item_manager.active_items,
            delta_ms,
        )

        # 正常游戏：累加时间并驱动步进
        self._move_accumulator += delta_ms
        while self._move_accumulator >= MOVE_INTERVAL:
            self._move_accumulator -= MOVE_INTERVAL
            self._game_step()
            if self.game_over_flag:
                break  # 游戏结束则停止步进

        # ── 同步蛇长到统计模块 ──
        self.stats.set_snake_length(len(self.snake.body))

        # ── 驱动探针收集 ──
        self.debug_probe.tick()

    def _game_step(self):
        """执行一步游戏逻辑：预判碰撞 → 移动蛇 → 检测道具"""
        # 0. 预计算新蛇头位置（不移动，仅预测）
        head = self.snake.body[0]
        dx, dy = self.snake.next_direction
        new_head = (head[0] + dx, head[1] + dy)

        # 1. 撞墙检测（移动前）
        if (new_head[0] < 0 or new_head[0] >= GRID_WIDTH or
                new_head[1] < 0 or new_head[1] >= GRID_HEIGHT):
            self._trigger_game_over()
            return

        # 2. 撞自身检测（移动前，预判）
        check_body = self.snake.body[1:] if self.snake.just_ate else self.snake.body[1:-1]
        if new_head in check_body:
            self._trigger_game_over()
            return

        # 3. 撞NPC检测（移动前，预判）
        for npc in self.npc_manager.npcs:
            if npc.is_alive and new_head in npc.body:
                self._trigger_game_over()
                return

        # 4. 移动蛇
        new_head = self.snake.move()

        # 5. 检测是否碰撞到道具
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
        # 触发分数滚动动画
        self._score_anim_from = self._score_display
        self._score_target = self.stats.get_score()
        self._score_anim_start = pygame.time.get_ticks()
        self._score_animating = True

    def _trigger_game_over(self):
        """触发游戏结束"""
        self.game_over_flag = True
        self.game_over_start_tick = pygame.time.get_ticks()

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
