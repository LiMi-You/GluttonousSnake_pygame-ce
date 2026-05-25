# quit_overlay.py
"""退出确认覆盖层 - 在原场景上绘制半透明遮罩和确认框，独立可复用"""

import pygame


class QuitOverlay:
    """退出确认覆盖层"""

    def __init__(self, screen_width: int, screen_height: int):
        self.box_width = 1280
        self.box_height = 250

        # 确认框矩形（居中）
        self.box_rect = pygame.Rect(
            0,
            (screen_height - self.box_height) // 2,
            self.box_width,
            self.box_height,
        )

        self.active = False
        # 0 = "是"(退出), 1 = "否"(取消) — 默认选"否"更安全
        self.selected = 1

        # 字体
        self.font_title = pygame.font.Font("assets/fonts/SmileySans-Oblique.ttf", 28)
        self.font_btn = pygame.font.Font(None, 40)

        # 预计算按钮矩形，供 draw 和鼠标检测复用
        self.btn_rects = self._compute_button_rects()

    # ── 按钮几何计算 ──

    def _compute_button_rects(self) -> list[pygame.Rect]:
        """计算"是"/"否"按钮的矩形区域"""
        btn_y = self.box_rect.centery + 30
        btn_w, btn_h = 160, 55
        gap = 40
        total_w = btn_w * 2 + gap
        start_x = self.box_rect.centerx - total_w // 2

        return [
            pygame.Rect(start_x, btn_y, btn_w, btn_h),
            pygame.Rect(start_x + btn_w + gap, btn_y, btn_w, btn_h),
        ]

    # ── 生命周期 ──

    def show(self):
        """显示覆盖层"""
        self.active = True
        self.selected = 1  # 默认选"否"

    def hide(self):
        """隐藏覆盖层"""
        self.active = False

    def toggle(self):
        """切换显示状态"""
        if self.active:
            self.hide()
        else:
            self.show()

    # ── 输入处理 ──

    def handle_input(self, actions: dict) -> bool | None:
        """
        处理输入（键盘 + 鼠标）
        返回: True=确认退出, False=取消, None=继续等待
        """
        if not self.active:
            return None

        # ── 鼠标检测 ──
        mouse_clicked = actions.get("mouse_clicked", False)
        mouse_pos = actions.get("mouse_pos", None)

        if mouse_clicked and mouse_pos:
            for i, rect in enumerate(self.btn_rects):
                if rect.collidepoint(mouse_pos):
                    self.selected = i
                    if i == 0:  # "是" → 退出
                        return True
                    else:  # "否" → 取消
                        self.hide()
                        return False

        # ── 键盘检测 ──

        # ESC → 取消（等同于选"否"）
        if "CANCEL" in actions["context"]:
            self.hide()
            return False

        # 方向键切换选项
        if "NAV_LEFT" in actions["context"]:
            self.selected = 0  # 移到"是"
        elif "NAV_RIGHT" in actions["context"]:
            self.selected = 1  # 移到"否"

        # 确认选择
        if "CONFIRM" in actions["context"]:
            if self.selected == 0:  # "是" → 退出
                return True
            else:  # "否" → 取消
                self.hide()
                return False

        return None

    # ── 绘制 ──

    def draw(self, screen: pygame.Surface):
        """在屏幕上层绘制覆盖层"""
        if not self.active:
            return

        sw, sh = screen.get_width(), screen.get_height()

        # 半透明遮罩
        mask = pygame.Surface((sw, sh))
        mask.set_alpha(160)
        mask.fill((0, 0, 0))
        screen.blit(mask, (0, 0))

        # 确认框背景
        pygame.draw.rect(screen, (40, 40, 60), self.box_rect, border_radius=12)
        pygame.draw.rect(screen, (180, 180, 220), self.box_rect, 3, border_radius=12)

        # ── 标题 ──
        # 确定要退出游戏吗 = Are you sure you want to quit the game?
        title = self.font_title.render("确定要退出游戏吗?", True, (255, 255, 255))
        title_rect = title.get_rect(center=(self.box_rect.centerx, self.box_rect.top + 65))
        screen.blit(title, title_rect)

        # ── 鼠标悬停检测 ──
        mouse_pos = pygame.mouse.get_pos()
        hovered_index = next(
            (i for i, rect in enumerate(self.btn_rects) if rect.collidepoint(mouse_pos)),
            None,
        )
        if not hovered_index == None:
            self.selected = hovered_index
        

        # ── 按钮 ──
        btn_labels = ["  是  ", "  否  "]
        btn_colors = [(200, 60, 60), (80, 160, 80)]  # 红 / 绿

        for i in range(2):
            btn_rect = self.btn_rects[i]
            is_active = i == self.selected or i == hovered_index
            base_color = btn_colors[i]

            if is_active:
                # 活跃（选中/悬停）时更亮
                btn_color = tuple(min(c + 50, 255) for c in base_color)
                border_color = (255, 255, 255)
            else:
                # 非活跃时更暗
                btn_color = tuple(c // 2 for c in base_color)
                border_color = btn_color

            pygame.draw.rect(screen, btn_color, btn_rect, border_radius=8)
            pygame.draw.rect(screen, border_color, btn_rect, 2, border_radius=8)

            btn_surf = self.font_btn.render(btn_labels[i].strip(), True, (255, 255, 255))
            btn_surf_rect = btn_surf.get_rect(center=btn_rect.center)
            screen.blit(btn_surf, btn_surf_rect)

        # ── 底部提示 ──
        hint = pygame.font.Font(None, 24).render(
            "← → 切换选项  Enter/Space 确认  ESC 取消",
            True,
            (160, 160, 180),
        )
        hint_rect = hint.get_rect(center=(self.box_rect.centerx, self.box_rect.bottom - 25))
        screen.blit(hint, hint_rect)
