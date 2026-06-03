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
from items import ItemManager, ItemInstance
from utils import StatsManager


class GameScreen(Scene):
    """贪吃蛇游戏场景"""

    def __init__(self, screen: pygame.Surface):
        super().__init__(screen)

        # ── 游戏实体 ──
        self.snake = Snake()
        self.item_manager = ItemManager()
        self.stats = StatsManager()

        # ── 移动计时器（使用 get_ticks 差值，不依赖外部传 delta）──
        self._last_tick: int = 0          # 上一帧的绝对毫秒时间戳
        self._move_accumulator: int = 0   # 移动时间累加器（毫秒）

        # ── 游戏状态 ──
        self.game_over_flag: bool = False
        self.game_over_start_tick: int = 0  # 游戏结束时的时间戳
        self.GAME_OVER_DELAY: int = 1500    # 死亡后可操作的最小等待（毫秒）

        # ── 字体 ──
        self.score_font = pygame.font.Font("assets/fonts/SmileySans-Oblique.ttf", 24)
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

    # ── 场景生命周期 ──

    def on_enter(self):
        """进入游戏场景时初始化/重置游戏状态"""
        print("🟢 进入 GAME（贪吃蛇）")
        self._reset_game()

    def on_exit(self):
        """离开游戏场景时的清理"""
        print("🔴 离开 GAME")

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
                return "LOBBY"
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

        # 游戏结束：不做移动更新
        if self.game_over_flag:
            return

        # ── 更新道具管理器（生成新道具）──
        self.item_manager.update(self.snake.body, delta_ms)

        # 正常游戏：累加时间并驱动步进
        self._move_accumulator += delta_ms
        while self._move_accumulator >= MOVE_INTERVAL:
            self._move_accumulator -= MOVE_INTERVAL
            self._game_step()
            if self.game_over_flag:
                break  # 游戏结束则停止步进

        # ── 同步蛇长到统计模块 ──
        self.stats.set_snake_length(len(self.snake.body))

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

        # 3. 移动蛇
        new_head = self.snake.move()

        # 4. 检测是否碰撞到道具
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

        # 5. 分数
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
        """绘制场上所有道具（使用预加载的图片）"""
        for item in self.item_manager.active_items:
            # 计算网格中心像素坐标
            px, py = self.snake.grid_to_pixel(item.grid_x, item.grid_y)
            cx = px + CELL_SIZE // 2
            cy = py + CELL_SIZE // 2

            img = self._item_images.get(item.item_id)
            if img:
                # 有图片：居中绘制，尺寸为 ITEM_RENDER_SIZE
                rect = img.get_rect(center=(cx, cy))
                screen.blit(img, rect)
            else:
                # 无图片时用纯色圆点兜底
                color = item.defn.color
                pygame.draw.circle(screen, color, (cx, cy), ITEM_RENDER_SIZE // 2)

    def _draw_score(self, screen: pygame.Surface):
        """绘制当前分数和蛇长"""
        score_text = self.score_font.render(
            f"得分：{self.stats.get_score()}  长度：{self.stats.get_snake_length()}",
            True, (255, 255, 255),
        )
        screen.blit(score_text, (MARGIN_LEFT, MARGIN_TOP - 36))

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
        hint_text = self.score_font.render(
            f"最终得分：{stats['score']}  最大连击：{stats['max_combo']} — 按任意键返回大厅",
            True, (200, 200, 200),
        )
        hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
        screen.blit(hint_text, hint_rect)
