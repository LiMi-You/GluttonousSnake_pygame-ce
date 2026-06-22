"""
debug/probe_window.py — 独立探针窗口（imgui 版）

使用 pygame.Window + Dear ImGui 创建独立的调试探针窗口。
支持位置记忆、F1 开关。
"""
from __future__ import annotations
import pygame
import pygame.window
import imgui
from OpenGL.GL import glClearColor, glClear, GL_COLOR_BUFFER_BIT
from imgui.integrations.pygame import PygameRenderer

from .probe_core import DebugProbe
from .probe_panel import ProbePanel
from .debug_config import DebugConfig

# ── 窗口配置 ──
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_TITLE = "Debug Probe"


class ProbeWindow:
    """独立探针窗口（imgui）"""

    def __init__(self, game_surface: pygame.Surface, probe: DebugProbe,
                 npc_manager=None, config: DebugConfig | None = None):
        self.probe = probe
        self.npc_manager = npc_manager
        self.config = config or DebugConfig()
        self.enabled = False

        # 默认位置：游戏窗口右侧
        game_x, game_y = pygame.display.get_window_position()
        game_w, game_h = game_surface.get_size()
        self._default_x = game_x + game_w
        self._default_y = game_y

        # 记忆位置
        self._saved_x = self._default_x
        self._saved_y = self._default_y

        # 窗口和面板
        self._window: pygame.window.Window | None = None
        self._panel: ProbePanel | None = None
        self._renderer: PygameRenderer | None = None

        # imgui context 只创建一次（生命周期跟进程）
        imgui.create_context()

        # 刷新控制
        self._update_interval = 100
        self._last_update = 0

    def toggle(self):
        if self.enabled:
            self._close()
        else:
            self._open()

    def set_npc_manager(self, npc_manager):
        """设置NPC管理器引用（GameScreen 初始化后调用）"""
        self.npc_manager = npc_manager
        if self._panel:
            self._panel.npc_manager = npc_manager

    def set_snake(self, snake):
        """设置玩家蛇引用（GameScreen 初始化后调用）"""
        self._snake_ref = snake
        if self._panel:
            self._panel.set_snake(snake)

    def set_item_manager(self, item_manager):
        """设置道具管理器引用"""
        self._item_manager_ref = item_manager
        if self._panel:
            self._panel.set_item_manager(item_manager)

    def set_buff_manager(self, buff_manager):
        """设置Buff管理器引用"""
        self._buff_manager_ref = buff_manager
        if self._panel:
            self._panel.set_buff_manager(buff_manager)

    def _open(self):
        if self._window is not None:
            return

        self._window = pygame.window.Window(
            size=(WINDOW_WIDTH, WINDOW_HEIGHT),
            title=WINDOW_TITLE,
            opengl=True,
            resizable=True
        )
        self._window.position = (self._saved_x, self._saved_y)

        # 初始化 renderer
        self._renderer = PygameRenderer()

        # 设置显示尺寸
        io = imgui.get_io()
        io.display_size = (WINDOW_WIDTH, WINDOW_HEIGHT)

        self._panel = ProbePanel(self.probe, self.npc_manager, self.config)
        # 同步所有已有引用到 panel
        if hasattr(self, '_snake_ref') and self._snake_ref:
            self._panel.set_snake(self._snake_ref)
        if hasattr(self, '_item_manager_ref') and self._item_manager_ref:
            self._panel.set_item_manager(self._item_manager_ref)
        if hasattr(self, '_buff_manager_ref') and self._buff_manager_ref:
            self._panel.set_buff_manager(self._buff_manager_ref)
        # 同步配置值
        self._panel._sync_config_to_npc()
        self._panel._sync_config_to_items()
        self._panel._sync_config_to_phase()
        self._panel._sync_config_to_weight()
        self.enabled = True

    def _close(self):
        if self._window:
            try:
                self._saved_x, self._saved_y = self._window.position
            except Exception:
                pass
            self._window.destroy()
            self._window = None
            self._panel = None
            self._renderer = None
        self.enabled = False

    def handle_event(self, event: pygame.event.Event):
        if not self.enabled or not self._window:
            return

        # 只处理属于当前窗口的事件，防止事件串扰
        if hasattr(event, 'window') and event.window != self._window:
            return

        # 拦截 VIDEORESIZE：不传给 renderer（它会调用 pygame.display.set_mode 改变主窗口）
        # 只更新 imgui 的 display_size
        if event.type == pygame.VIDEORESIZE:
            io = imgui.get_io()
            io.display_size = (event.w, event.h)
            return

        if self._renderer:
            self._renderer.process_event(event)

        if event.type == pygame.WINDOWCLOSE:
            self._close()

        elif event.type == pygame.WINDOWRESIZED:
            io = imgui.get_io()
            io.display_size = (event.x, event.y)

    def update(self, current_time: int):
        if not self.enabled or not self._window:
            return

        if current_time - self._last_update < self._update_interval:
            return
        self._last_update = current_time

        # 处理输入
        self._renderer.process_inputs()

        # 开始新帧
        imgui.new_frame()

        # 绘制面板
        self._panel.draw()

        # 渲染
        glClearColor(0.07, 0.07, 0.09, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)

        imgui.render()
        self._renderer.render(imgui.get_draw_data())

        self._window.flip()
