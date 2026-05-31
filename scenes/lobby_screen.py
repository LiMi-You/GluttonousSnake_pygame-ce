"""
scenes/lobby_screen.py — 大厅/主入口场景

玩家在这里选择进入游戏或其他功能。
"""
import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, COLORS
from scenes.base_scene import Scene


class LobbyScreen(Scene):
    """大厅场景：提供开始游戏入口"""

    def __init__(self, screen: pygame.Surface):
        super().__init__(screen)

        # ── 标题 ──
        self.title_font = pygame.font.Font("assets/fonts/SmileySans-Oblique.ttf", 40)
        self.title_surface = self.title_font.render(
            "贪 吃 蛇", True, (36, 128, 103),
        )
        self.title_rect = self.title_surface.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3),
        )

        # ── 副标题 ──
        self.subtitle_font = pygame.font.Font("assets/fonts/SmileySans-Oblique.ttf", 22)
        self.subtitle_surface = self.subtitle_font.render(
            "Gluttonous Snake — 经典贪吃蛇", True, (120, 120, 140),
        )
        self.subtitle_rect = self.subtitle_surface.get_rect(
            center=(SCREEN_WIDTH // 2, self.title_rect.bottom + 20),
        )

        # ── 开始游戏按钮 ──
        self.btn_font = pygame.font.Font("assets/fonts/SmileySans-Oblique.ttf", 28)
        self.btn_rect = pygame.Rect(0, 0, 260, 60)
        self.btn_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40)

        # 按钮文字（预渲染两套：普通态 / 悬停态）
        self._make_btn_text()

    def _make_btn_text(self):
        """构建按钮文字 Surface（普通 & 高亮两套）"""
        self.btn_text_normal = self.btn_font.render(
            "开始游戏", True, COLORS["white"],
        )
        self.btn_text_hover = self.btn_font.render(
            "▶  开始游戏", True, (255, 220, 100),
        )
        self.btn_text_rect = self.btn_text_normal.get_rect(
            center=self.btn_rect.center,
        )

    # ── 生命周期 ──

    def on_enter(self):
        print("🟢 进入 LOBBY（大厅）")

    def on_exit(self):
        print("🔴 离开 LOBBY")

    # ── 输入处理 ──

    def handle_input(self, input_state: dict) -> str | None:
        """
        处理输入：
        - CONFIRM（键盘 Enter/Space）→ 进入游戏
        - 鼠标点击按钮 → 进入游戏
        """
        # 键盘确认
        if "CONFIRM" in input_state["context"]:
            return "GAME"

        # 鼠标点击按钮
        if pygame.mouse.get_pressed()[0]:
            if self.btn_rect.collidepoint(pygame.mouse.get_pos()):
                return "GAME"

        return None

    # ── 更新 ──

    def update(self):
        """大厅无需帧更新逻辑"""
        pass

    # ── 渲染 ──

    def draw(self, screen: pygame.Surface):
        """绘制大厅界面"""
        # 背景
        super().draw(screen)

        # 标题
        screen.blit(self.title_surface, self.title_rect)
        screen.blit(self.subtitle_surface, self.subtitle_rect)

        # ── 按钮（含悬停效果）──
        mouse_pos = pygame.mouse.get_pos()
        hovered = self.btn_rect.collidepoint(mouse_pos)

        # 按钮背景
        btn_bg_color = (50, 150, 120) if hovered else (60, 120, 100)
        pygame.draw.rect(screen, btn_bg_color, self.btn_rect, border_radius=12)
        pygame.draw.rect(screen, COLORS["white"], self.btn_rect, width=2, border_radius=12)

        # 按钮文字
        btn_text = self.btn_text_hover if hovered else self.btn_text_normal
        screen.blit(btn_text, btn_text.get_rect(center=self.btn_rect.center))