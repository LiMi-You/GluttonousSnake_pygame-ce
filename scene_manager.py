# scene_manager.py
import pygame
from scenes.registry import get_scene_class, SCENE_REGISTRY
from input_manager import InputManager
from pause_menu import PauseMenu
from debug import DebugProbe, ProbeWindow, DebugConfig

class SceneManager:
    def __init__(self, screen, initial_scene_id: str, input_manager: InputManager):
        self.screen = screen
        self.input_manager = input_manager
        self.current_scene_id = None
        self.current_scene = None
        self._running = True

        # 暂停菜单
        self.pause_menu = PauseMenu()

        # 调试探针
        self.debug_probe = DebugProbe()
        self.debug_config = DebugConfig.load()
        self.probe_window = ProbeWindow(screen, self.debug_probe, config=self.debug_config)

        # 初始化第一个场景
        self.switch(initial_scene_id)

    def switch(self, scene_id: str):
        """切换场景：根据ID从工厂获取类并实例化"""
        if scene_id == self.current_scene_id and self.current_scene:
            return

        # 1. 清理旧场景 (可选：调用 on_exit)
        if self.current_scene:
            self.current_scene.on_exit()

        # 2. 从工厂获取新场景类并实例化
        try:
            SceneClass = get_scene_class(scene_id)
            self.current_scene = SceneClass(self.screen, debug_probe=self.debug_probe,
                                            debug_config=self.debug_config)
            
            self.current_scene_id = scene_id

            # 3. 如果是 GAME 场景，将引用传递给探针窗口
            if scene_id == "GAME":
                if hasattr(self.current_scene, 'npc_manager'):
                    self.probe_window.set_npc_manager(self.current_scene.npc_manager)
                if hasattr(self.current_scene, 'snake'):
                    self.probe_window.set_snake(self.current_scene.snake)
                if hasattr(self.current_scene, 'item_manager'):
                    self.probe_window.set_item_manager(self.current_scene.item_manager)
                if hasattr(self.current_scene, 'buff_manager'):
                    self.probe_window.set_buff_manager(self.current_scene.buff_manager)
                # 同步配置（panel 可能还没创建，set_* 方法内部已处理）
                if self.probe_window._panel:
                    self.probe_window._panel._sync_config_to_npc()
                    self.probe_window._panel._sync_config_to_items()
                    self.probe_window._panel._sync_config_to_phase()
                    self.probe_window._panel._sync_config_to_weight()
            
            # 4. 同步输入上下文
            self.input_manager.set_context(self.current_scene_id)
            
            self.current_scene.on_enter()
            
        except ValueError as e:
            print(f"错误: {e}")

    def handle_frame(self, events):
        """处理单帧逻辑"""
        # 🔹 窗口关闭事件 —— 最高优先级拦截
        for event in events:
            if event.type == pygame.QUIT:
                return False          # 通知主循环退出

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
            saved_ctx = self.input_manager.context
            self.input_manager.set_context("OVERLAY")
            overlay_actions = self.input_manager.get_actions()
            self.input_manager.context = saved_ctx

            mouse_pressed = pygame.mouse.get_pressed()
            overlay_actions["mouse_clicked"] = mouse_pressed[0]
            overlay_actions["mouse_pos"] = pygame.mouse.get_pos()

            result = self.pause_menu.handle_input(overlay_actions)

            if result == "RESUME":
                self.pause_menu.hide()
            elif result == "SETTINGS":
                pass
            elif result == "EXIT_LOBBY":
                self.pause_menu.hide()
                self.switch("LOBBY")
            elif result == "EXIT_GAME":
                return False

            if result is not None:
                actions["context"] = set()
        else:
            if "GLOBAL_QUIT" in actions["global"]:
                self.pause_menu.show()
        
        # 🔸 兜底处理：场景为空时只处理全局事件，跳过渲染
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
