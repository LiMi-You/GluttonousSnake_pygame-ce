# 暂停菜单系统 - 实现需求

> 本文档供其他会话阅读并实现。请严格按照文档中的文件、函数、参数进行修改。

---

## 一、目标

将 `quit_overlay.py`（退出确认框）重构为 `pause_menu.py`（暂停菜单系统），支持四个功能入口：继续游戏、游戏设置、退出本局、退出游戏。

---

## 二、文件变更清单

| 文件 | 操作 | 说明 |
|-----|------|------|
| `quit_overlay.py` | 删除 | 旧文件，不再使用 |
| `pause_menu.py` | 新建 | 暂停菜单主类 |
| `scene_manager.py` | 修改 | 更新导入和调用 |
| `settings.py` | 修改 | 新增菜单配置常量 |

---

## 三、`settings.py` 新增内容

在文件末尾追加以下常量：

```python
# ==================== 暂停菜单参数 ====================
PAUSE_MENU_PANEL_WIDTH = 400        # 面板宽度（px）
PAUSE_MENU_BTN_WIDTH = 280          # 按钮宽度（px）
PAUSE_MENU_BTN_HEIGHT = 50          # 按钮高度（px）
PAUSE_MENU_BTN_GAP = 16             # 按钮垂直间距（px）
PAUSE_MENU_PADDING_TOP = 60         # 面板上内边距（px）
PAUSE_MENU_PADDING_BOTTOM = 40      # 面板下内边距（px）
PAUSE_MENU_PADDING_X = 60           # 面板左右内边距（px）
PAUSE_MENU_MASK_ALPHA = 180         # 遮罩透明度（0-255）

# 暂停菜单颜色
PAUSE_MENU_COLORS = {
    "mask": (0, 0, 0),
    "panel_bg": (30, 35, 50),
    "panel_border": (80, 180, 200),
    "title": (255, 255, 255),
    "btn_text": (220, 220, 230),
    "btn_bg": (50, 60, 80),
    "btn_bg_hover": (70, 150, 170),
    "btn_border_hover": (120, 210, 230),
    "hint": (140, 140, 160),
}

# 暂停菜单按钮定义（顺序决定渲染顺序）
PAUSE_MENU_ITEMS = [
    {"id": "resume",     "label": "继续游戏", "action": "RESUME"},
    {"id": "settings",   "label": "游戏设置", "action": "SETTINGS"},
    {"id": "exit_lobby", "label": "退出本局", "action": "EXIT_LOBBY"},
    {"id": "exit_game",  "label": "退出游戏", "action": "EXIT_GAME"},
]
```

---

## 四、`pause_menu.py` 新建

### 4.1 类结构

```python
"""pause_menu.py — 暂停菜单覆盖层"""

import pygame
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    PAUSE_MENU_PANEL_WIDTH, PAUSE_MENU_BTN_WIDTH, PAUSE_MENU_BTN_HEIGHT,
    PAUSE_MENU_BTN_GAP, PAUSE_MENU_PADDING_TOP, PAUSE_MENU_PADDING_BOTTOM,
    PAUSE_MENU_PADDING_X, PAUSE_MENU_MASK_ALPHA, PAUSE_MENU_COLORS,
    PAUSE_MENU_ITEMS,
)


class PauseMenu:
    """暂停菜单覆盖层"""

    def __init__(self):
        self.active: bool = False
        self.selected: int = 0  # 当前选中项索引

        # 字体
        self.font_title = pygame.font.Font("assets/fonts/SmileySans-Obtle.ttf", 32)
        self.font_btn = pygame.font.Font("assets/fonts/SmileySans-Obtle.ttf", 24)
        self.font_hint = pygame.font.Font("assets/fonts/SmileySans-Obtle.ttf", 14)

        # 面板矩形（居中计算）
        self._compute_layout()

        # 按钮矩形列表
        self.btn_rects: list[pygame.Rect] = []
        self._compute_button_rects()

    def _compute_layout(self):
        """计算面板位置和大小"""
        # 面板高度 = 上内边距 + 标题高度 + 按钮区域 + 下内边距
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
        """计算每个按钮的矩形区域"""
        self.btn_rects = []
        btn_x = self.panel_rect.centerx - PAUSE_MENU_BTN_WIDTH // 2
        btn_y = self.panel_rect.top + PAUSE_MENU_PADDING_TOP + 40  # 40 = 标题高度

        for _ in PAUSE_MENU_ITEMS:
            rect = pygame.Rect(btn_x, btn_y, PAUSE_MENU_BTN_WIDTH, PAUSE_MENU_BTN_HEIGHT)
            self.btn_rects.append(rect)
            btn_y += PAUSE_MENU_BTN_HEIGHT + PAUSE_MENU_BTN_GAP

    # ── 生命周期 ──

    def show(self):
        self.active = True
        self.selected = 0  # 默认选中"继续游戏"

    def hide(self):
        self.active = False

    def toggle(self):
        if self.active:
            self.hide()
        else:
            self.show()

    # ── 输入处理 ──

    def handle_input(self, actions: dict) -> str | None:
        """
        处理输入，返回动作字符串或 None。
        
        返回值：
            "RESUME"      - 继续游戏
            "SETTINGS"    - 游戏设置（占位）
            "EXIT_LOBBY"  - 退出本局
            "EXIT_GAME"   - 退出游戏
            None          - 无操作
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
                    return PAUSE_MENU_ITEMS[i]["action"]

        # ── 键盘检测 ──
        # ESC / CANCEL → 关闭菜单（等同于继续游戏）
        if "CANCEL" in actions["context"]:
            self.hide()
            return "RESUME"

        # 方向键切换
        if "NAV_UP" in actions["context"]:
            self.selected = (self.selected - 1) % len(PAUSE_MENU_ITEMS)
        elif "NAV_DOWN" in actions["context"]:
            self.selected = (self.selected + 1) % len(PAUSE_MENU_ITEMS)

        # 确认选择
        if "CONFIRM" in actions["context"]:
            return PAUSE_MENU_ITEMS[self.selected]["action"]

        return None

    # ── 绘制 ──

    def draw(self, screen: pygame.Surface):
        """在屏幕上层绘制暂停菜单"""
        if not self.active:
            return

        sw, sh = screen.get_width(), screen.get_height()
        colors = PAUSE_MENU_COLORS

        # 1. 半透明遮罩
        mask = pygame.Surface((sw, sh))
        mask.set_alpha(PAUSE_MENU_MASK_ALPHA)
        mask.fill(colors["mask"])
        screen.blit(mask, (0, 0))

        # 2. 面板背景
        pygame.draw.rect(screen, colors["panel_bg"], self.panel_rect, border_radius=12)
        pygame.draw.rect(screen, colors["panel_border"], self.panel_rect, 3, border_radius=12)

        # 3. 标题
        title = self.font_title.render("游戏暂停", True, colors["title"])
        title_rect = title.get_rect(center=(self.panel_rect.centerx, self.panel_rect.top + PAUSE_MENU_PADDING_TOP + 10))
        screen.blit(title, title_rect)

        # 4. 按钮
        mouse_pos = pygame.mouse.get_pos()
        for i, (item, rect) in enumerate(zip(PAUSE_MENU_ITEMS, self.btn_rects)):
            is_selected = (i == self.selected)
            is_hovered = rect.collidepoint(mouse_pos)

            if is_selected or is_hovered:
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

        # 5. 底部提示
        hint = self.font_hint.render("↑↓ 选择  Enter 确认  ESC 返回", True, colors["hint"])
        hint_rect = hint.get_rect(center=(self.panel_rect.centerx, self.panel_rect.bottom - 20))
        screen.blit(hint, hint_rect)
```

### 4.2 关键点

1. **`handle_input` 返回字符串**：不是 True/False，而是 `"RESUME"` / `"SETTINGS"` / `"EXIT_LOBBY"` / `"EXIT_GAME"`
2. **ESC 关闭菜单**：返回 `"RESUME"`，不是 `False`
3. **鼠标悬浮自动选中**：`is_hovered` 会影响视觉，但不改变 `self.selected`（只在点击时改变）
4. **按钮循环选择**：`% len(PAUSE_MENU_ITEMS)` 实现上下循环

---

## 五、`scene_manager.py` 修改

### 5.1 导入变更

```python
# 旧导入
from quit_overlay import QuitOverlay

# 新导入
from pause_menu import PauseMenu
```

### 5.2 构造函数变更

```python
# 旧代码
self.quit_overlay = QuitOverlay(screen.get_width(), screen.get_height())

# 新代码
self.pause_menu = PauseMenu()
```

### 5.3 `handle_frame` 方法变更

将所有 `self.quit_overlay` 替换为 `self.pause_menu`，并调整返回值处理：

```python
def handle_frame(self, events):
    """处理单帧逻辑"""
    # 🔹 窗口关闭事件 —— 最高优先级拦截
    for event in events:
        if event.type == pygame.QUIT:
            return False

    # 🔹 探针窗口事件处理
    for event in events:
        self.probe_window.handle_event(event)

    # 1. 获取标准化动作
    self.input_manager.process_events(events)
    actions = self.input_manager.get_actions()

    # 2. 全局拦截 (Alt+Enter 全屏)
    if "TOGGLE_FULLSCREEN" in actions["global"]:
        pygame.display.toggle_fullscreen()

    if "TOGGLE_DEBUG" in actions["global"]:
        self.probe_window.toggle()

    # ── 暂停菜单逻辑 ──
    if self.pause_menu.active:
        # 菜单激活时：临时切到 OVERLAY 上下文
        saved_ctx = self.input_manager.context
        self.input_manager.set_context("OVERLAY")
        overlay_actions = self.input_manager.get_actions()
        self.input_manager.context = saved_ctx

        # 叠加鼠标状态
        mouse_pressed = pygame.mouse.get_pressed()
        overlay_actions["mouse_clicked"] = mouse_pressed[0]
        overlay_actions["mouse_pos"] = pygame.mouse.get_pos()

        result = self.pause_menu.handle_input(overlay_actions)

        if result == "RESUME":
            self.pause_menu.hide()
        elif result == "SETTINGS":
            pass  # 占位，暂无操作
        elif result == "EXIT_LOBBY":
            self.pause_menu.hide()
            self.switch("LOBBY")
        elif result == "EXIT_GAME":
            return False
    else:
        # 菜单未激活：ESC → 显示菜单
        if "GLOBAL_QUIT" in actions["global"]:
            self.pause_menu.show()

    # 🔸 兜底处理
    if not self.current_scene:
        return True

    # 3. 交给当前场景处理（菜单激活时跳过）
    if not self.pause_menu.active:
        next_scene_id = self.current_scene.handle_input(actions)
        if next_scene_id and next_scene_id != self.current_scene_id:
            self.switch(next_scene_id)

    # 4. 场景更新逻辑（菜单激活时跳过 → 游戏静止）
    if not self.pause_menu.active:
        next_from_update = self.current_scene.update()
        if next_from_update and next_from_update != self.current_scene_id:
            self.switch(next_from_update)

    # 5. 场景渲染
    self.current_scene.draw(self.screen)

    # 6. 暂停菜单渲染（在场景之上）
    self.pause_menu.draw(self.screen)

    return True
```

### 5.4 关键变更点

1. **`update()` 在菜单激活时跳过**：这是实现"游戏静止"的关键
2. **`handle_input()` 在菜单激活时跳过**：防止游戏场景接收按键
3. **返回值处理**：从 `True/False` 改为字符串判断

---

## 六、删除文件

删除旧的退出确认框文件：

```
quit_overlay.py
```

---

## 七、验证清单

实现完成后，请逐项验证：

1. [ ] 游戏中按 ESC → 弹出暂停菜单，游戏完全静止
2. [ ] 四个按钮竖排显示，统一青蓝色系
3. [ ] 默认选中"继续游戏"
4. [ ] 悬浮按钮有亮度变化
5. [ ] 键盘 ↑↓ 可切换选中项（循环）
6. [ ] Enter 确认选中项
7. [ ] ESC 关闭菜单，游戏恢复
8. [ ] 点击"继续游戏" → 关闭菜单
9. [ ] 点击"退出本局" → 返回大厅
10. [ ] 点击"退出游戏" → 程序关闭
11. [ ] 游戏结束时不弹出菜单
12. [ ] 开始界面按 ESC 无反应
13. [ ] 大厅按 ESC 无反应
