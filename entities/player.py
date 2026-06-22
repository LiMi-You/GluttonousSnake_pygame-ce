"""
entities/player.py — 贪吃蛇实体

Snake 类封装了蛇的所有数据与行为：
- 蛇身坐标列表（网格坐标系）
- 方向控制（含反向移动防护）
- 移动、增长、自碰检测
- 邻居感知的边框渲染
"""
import pygame
from settings import (
    CELL_SIZE, MARGIN_LEFT, MARGIN_TOP,
    SNAKE_INITIAL, SNAKE_INITIAL_DIRECTION,
    SNAKE_COLOR, SNAKE_BORDER_COLOR, SNAKE_BORDER_WIDTH,
)


class Snake:
    """贪吃蛇实体：管理蛇身数据、方向、移动与渲染"""

    def __init__(self):
        # 蛇身：列表头为蛇头，每个元素为 (grid_x, grid_y)
        self.body: list[tuple[int, int]] = list(SNAKE_INITIAL)

        # 方向管理
        self.current_direction: tuple[int, int] = SNAKE_INITIAL_DIRECTION
        self.next_direction: tuple[int, int] = SNAKE_INITIAL_DIRECTION

        # 是否在本轮移动中吃到了食物（外部设置）
        self.just_ate = False

        # ── 调试标志（由 DebugConfig 控制）──
        self.invincible: bool = False    # 无敌：碰撞不死
        self.god_mode: bool = False      # 上帝模式：不撞墙
        self._speed_multiplier: float = 1.0  # 速度倍率

    # ── 方向控制 ──

    def set_direction(self, dx: int, dy: int):
        """
        尝试设置下一步方向。
        自动忽略反向指令（基于 current_direction 判断，防止穿模）。
        """
        # 禁止反向：新方向不能与当前实际方向相反
        if (dx, dy) == (-self.current_direction[0], -self.current_direction[1]):
            return
        self.next_direction = (dx, dy)

    # ── 移动逻辑 ──

    def move(self) -> tuple[int, int]:
        """
        执行一步移动。
        返回新的蛇头坐标 (grid_x, grid_y)。
        """
        # 1. 正式应用方向
        self.current_direction = self.next_direction

        # 2. 计算新蛇头
        head = self.body[0]
        new_head = (
            head[0] + self.current_direction[0],
            head[1] + self.current_direction[1],
        )

        # 3. 插入新头
        self.body.insert(0, new_head)

        # 4. 如果没吃到食物，移除尾（保持长度不变）
        if not self.just_ate:
            self.body.pop()
        else:
            self.just_ate = False  # 重置标记

        return new_head

    # ── 碰撞检测 ──

    def check_self_collision(self) -> bool:
        """检测蛇头是否撞到自身（蛇头 == 任意身体段）"""
        head = self.body[0]
        return head in self.body[1:]

    def occupies(self, pos: tuple[int, int]) -> bool:
        """检查指定网格坐标是否被蛇身占据"""
        return pos in self.body

    # ── 坐标转换 ──

    @staticmethod
    def grid_to_pixel(grid_x: int, grid_y: int) -> tuple[int, int]:
        """网格坐标 → 像素坐标（格子左上角）"""
        pixel_x = MARGIN_LEFT + grid_x * CELL_SIZE
        pixel_y = MARGIN_TOP + grid_y * CELL_SIZE
        return pixel_x, pixel_y

    # ── 渲染 ──

    def draw(self, screen: pygame.Surface):
        """
        绘制蛇身。
        使用邻居感知算法：只在与相邻蛇身不接触的方向绘制边框，
        这样内部相邻段之间的接缝不可见，视觉上是一个整体。
        """
        body_set = set(self.body)  # O(1) 邻居查找

        for x, y in self.body:
            px, py = self.grid_to_pixel(x, y)
            rect = pygame.Rect(px - 1, py - 1, CELL_SIZE + 2, CELL_SIZE + 2)

            # 填充蛇身
            pygame.draw.rect(screen, SNAKE_COLOR, rect)

            # 检查四个方向是否有相邻蛇身
            has_up = (x, y - 1) in body_set
            has_down = (x, y + 1) in body_set
            has_left = (x - 1, y) in body_set
            has_right = (x + 1, y) in body_set

            # 只在没有邻居的方向绘制边框
            tl = rect.topleft
            tr = rect.topright
            br = rect.bottomright
            bl = rect.bottomleft

            if not has_up:
                pygame.draw.line(screen, SNAKE_BORDER_COLOR, tl, tr, SNAKE_BORDER_WIDTH)
            if not has_down:
                pygame.draw.line(screen, SNAKE_BORDER_COLOR, bl, br, SNAKE_BORDER_WIDTH)
            if not has_left:
                pygame.draw.line(screen, SNAKE_BORDER_COLOR, tl, bl, SNAKE_BORDER_WIDTH)
            if not has_right:
                pygame.draw.line(screen, SNAKE_BORDER_COLOR, tr, br, SNAKE_BORDER_WIDTH)
