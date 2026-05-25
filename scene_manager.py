# scene_manager.py
import pygame
from scenes.registry import get_scene_class, SCENE_REGISTRY
from input_manager import InputManager
from quit_overlay import QuitOverlay

class SceneManager:
    def __init__(self, screen, initial_scene_id: str, input_manager: InputManager):
        self.screen = screen
        self.input_manager = input_manager
        self.current_scene_id = None
        self.current_scene = None
        self._running = True

        # 退出确认覆盖层
        self.quit_overlay = QuitOverlay(screen.get_width(), screen.get_height())

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
            # 假设场景构造函数需要 input_manager 和其他必要依赖
            self.current_scene = SceneClass(self.screen)
            
            self.current_scene_id = scene_id
            
            # 3. 同步输入上下文 (关键步骤)
            # 场景初始化时会自动告诉 InputManager 当前需要什么按键映射
            # if hasattr(self.input_manager, 'CONTEXT_ALIAS'):
            self.input_manager.set_context(self.current_scene_id)
            
            self.current_scene.on_enter()
            
        except ValueError as e:
            print(f"错误: {e}")
            # 这里可以 fallback 到一个错误场景或主菜单

    def handle_frame(self, events):
        """处理单帧逻辑"""
        # 🔹 窗口关闭事件 —— 最高优先级拦截
        for event in events:
            if event.type == pygame.QUIT:
                return False          # 通知主循环退出

        # 1. 获取标准化动作
        self.input_manager.process_events(events)
        actions = self.input_manager.get_actions()
        
        # 2. 全局拦截 (Alt+Enter 全屏)
        if "TOGGLE_FULLSCREEN" in actions["global"]:
            pygame.display.toggle_fullscreen()
        
        # ── 退出覆盖层逻辑 ──
        if self.quit_overlay.active:
            # 覆盖层激活时：临时切到 OVERLAY 上下文重新映射按键
            # 注意：不重新调用 process_events，否则会清空 _just_pressed
            saved_ctx = self.input_manager.context
            self.input_manager.set_context("OVERLAY")
            overlay_actions = self.input_manager.get_actions()
            self.input_manager.context = saved_ctx  # 恢复原上下文

            # 叠加鼠标状态，供覆盖层检测按钮点击
            mouse_pressed = pygame.mouse.get_pressed()
            overlay_actions["mouse_clicked"] = mouse_pressed[0]
            overlay_actions["mouse_pos"] = pygame.mouse.get_pos()

            result = self.quit_overlay.handle_input(overlay_actions)
            if result is True:
                return False  # 用户确认退出
            # False 或 None → 继续渲染
        else:
            # 覆盖层未激活：ESC → 显示覆盖层（不直接退出）
            if "GLOBAL_QUIT" in actions["global"]:
                self.quit_overlay.show()
                # 不 return False，继续渲染，让用户看到原场景+覆盖层
        
        # 🔸 兜底处理：场景为空时只处理全局事件，跳过渲染
        if not self.current_scene:
            return True
    
        # 3. 交给当前场景处理（覆盖层激活时跳过，防止按键干扰）
        if not self.quit_overlay.active:
            next_scene_id = self.current_scene.handle_input(actions)
            if next_scene_id and next_scene_id != self.current_scene_id:
                self.switch(next_scene_id)
            
        # 4. 场景更新逻辑 (非输入相关的逻辑)
        self.current_scene.update()
        
        # 5. 场景渲染
        self.current_scene.draw(self.screen)
        
        # 6. 覆盖层渲染（在场景之上）
        self.quit_overlay.draw(self.screen)
        
        return True # 继续循环