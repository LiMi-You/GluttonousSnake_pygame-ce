"""pause_menu.py — 暂停菜单覆盖层"""

import pygame
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    PAUSE_MENU_PANEL_WIDTH, PAUSE_MENU_BTN_WIDTH, PAUSE_MENU_BTN_HEIGHT,
    PAUSE_MENU_BTN_GAP, PAUSE_MENU_PADDING_TOP, PAUSE_MENU_PADDING_BOTTOM,
    PAUSE_MENU_MASK_ALPHA, PAUSE_MENU_COLORS,
    PAUSE_MENU_ITEMS,
)


class PauseMenu:
    """暂停菜单覆盖层"""

    def __init__(self):
        self.active: bool = False
        self.selected: int | None = None
        self._input_mode: str = "mouse"
        self._hovered: int | None = None
        self._prev_mouse_pos: tuple[int, int] | None = None

        self.font_title = pygame.font.Font("assets/fonts/SmileySans-Oblique.ttf", 32)
        self.font_btn = pygame.font.Font("assets/fonts/SmileySans-Oblique.ttf", 24)
        self.font_hint = pygame.font.Font("assets/fonts/SmileySans-Oblique.ttf", 14)

        self._compute_layout()
        self.btn_rects: list[pygame.Rect] = []
        self._compute_button_rects()

    def _compute_layout(self):
        title_height = 40
        btn_area_height = len(PAUSE_MENU_ITEMS) * PAUSE_MENU_BTN_HEIGHT + (len(PAUSE_MENU_ITEMS) - 1) * PAUSE_MENU_BTN_GAP
        panel_height = PAUSE_MENU_PADDING_TOP + title_height + btn_area_height + PAUSE_MENU_PADDING_BOTTOM

        self.panel_rect = pygame.Rect(
            (SCREEN_WIDTH - PAUSE_MENU_PANEL_WIDTH) // 2,
            (SCREEN_HEIGHT - panel_height) // 2,
            PAUSE_MENU_PANEL_WIDTH,
            panel_height,
        )

    def _compute_button_rects(self):
        self.btn_rects = []
        btn_x = self.panel_rect.centerx - PAUSE_MENU_BTN_WIDTH // 2
        btn_y = self.panel_rect.top + PAUSE_MENU_PADDING_TOP + 40

        for _ in PAUSE_MENU_ITEMS:
            rect = pygame.Rect(btn_x, btn_y, PAUSE_MENU_BTN_WIDTH, PAUSE_MENU_BTN_HEIGHT)
            self.btn_rects.append(rect)
            btn_y += PAUSE_MENU_BTN_HEIGHT + PAUSE_MENU_BTN_GAP

    def show(self):
        self.active = True
        self.selected = None
        self._input_mode = "mouse"
        self._hovered = None
        self._prev_mouse_pos = None

    def hide(self):
        self.active = False

    def toggle(self):
        if self.active:
            self.hide()
        else:
            self.show()

    def handle_input(self, actions: dict) -> str | None:
        """
        处理输入，返回动作字符串或 None。
        """
        if not self.active:
            return None

        mouse_pos = actions.get("mouse_pos", None)
        mouse_moved = (mouse_pos != self._prev_mouse_pos) if mouse_pos else False
        self._prev_mouse_pos = mouse_pos

        mouse_clicked = actions.get("mouse_clicked", False)

        if mouse_pos and mouse_moved:
            for i, rect in enumerate(self.btn_rects):
                if rect.collidepoint(mouse_pos):
                    self._hovered = i
                    if self._input_mode != "mouse":
                        self.selected = i
                    self._input_mode = "mouse"
                    if mouse_clicked:
                        return PAUSE_MENU_ITEMS[i]["action"]
                    break
            else:
                self._hovered = None

        if "CANCEL" in actions["context"]:
            self.hide()
            return "RESUME"

        if "NAV_UP" in actions["context"]:
            self._input_mode = "keyboard"
            if self.selected is None:
                self.selected = self._hovered if self._hovered is not None else 3
            else:
                self.selected = (self.selected - 1) % len(PAUSE_MENU_ITEMS)
        elif "NAV_DOWN" in actions["context"]:
            self._input_mode = "keyboard"
            if self.selected is None:
                self.selected = self._hovered if self._hovered is not None else 0
            else:  
                self.selected = (self.selected + 1) % len(PAUSE_MENU_ITEMS)

        if "CONFIRM" in actions["context"]:
            self._input_mode = "keyboard"
            if self.selected is None:
                self.selected = self._hovered if self._hovered is not None else 0
            #测试用排查断点
            print(f"键盘输入返回的事件{PAUSE_MENU_ITEMS[self.selected]}")
            return PAUSE_MENU_ITEMS[self.selected]["action"]

        return None

    def draw(self, screen: pygame.Surface):
        if not self.active:
            return

        sw, sh = screen.get_width(), screen.get_height()
        colors = PAUSE_MENU_COLORS

        mask = pygame.Surface((sw, sh))
        mask.set_alpha(PAUSE_MENU_MASK_ALPHA)
        mask.fill(colors["mask"])
        screen.blit(mask, (0, 0))

        pygame.draw.rect(screen, colors["panel_bg"], self.panel_rect, border_radius=12)
        pygame.draw.rect(screen, colors["panel_border"], self.panel_rect, 3, border_radius=12)

        title = self.font_title.render("游戏暂停", True, colors["title"])
        title_rect = title.get_rect(center=(self.panel_rect.centerx, self.panel_rect.top + PAUSE_MENU_PADDING_TOP + 10))
        screen.blit(title, title_rect)

        highlight_index = self._hovered if self._input_mode == "mouse" else self.selected

        for i, (item, rect) in enumerate(zip(PAUSE_MENU_ITEMS, self.btn_rects)):
            is_highlighted = (i == highlight_index)

            if is_highlighted:
                btn_bg = colors["btn_bg_hover"]
                btn_border = colors["btn_border_hover"]
            else:
                btn_bg = colors["btn_bg"]
                btn_border = btn_bg

            pygame.draw.rect(screen, btn_bg, rect, border_radius=8)
            pygame.draw.rect(screen, btn_border, rect, 2, border_radius=8)

            btn_text = self.font_btn.render(item["label"], True, colors["btn_text"])
            btn_text_rect = btn_text.get_rect(center=rect.center)
            screen.blit(btn_text, btn_text_rect)

        hint = self.font_hint.render("↑↓ 选择  Enter 确认  ESC 返回", True, colors["hint"])
        hint_rect = hint.get_rect(center=(self.panel_rect.centerx, self.panel_rect.bottom - 20))
        screen.blit(hint, hint_rect)
