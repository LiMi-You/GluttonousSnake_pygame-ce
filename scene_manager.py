# scene_manager.py
import pygame
from input_manager import InputManager

class SceneManager:
    def __init__(self, screen, input_manager: InputManager):
        self.screen = screen
        self.input = input_manager
        self.scenes = {}          # 存储已注册的场景实例 {"START": StartScreen, ...}
        self.current_key = None
        self.current_scene = None
        self._running = True

    def add_scene(self, key, scene_instance):
        """注册场景"""
        self.scenes[key] = scene_instance

    def switch(self, key: str):
        """切换场景：自动调用 on_exit / on_enter"""
        if key == "QUIT":
            self._running = False
            return
        if key not in self.scenes:
            print(f"⚠️ 场景 '{key}' 未注册，切换失败")
            return

        # 1. 退出旧场景
        if self.current_scene:
            self.current_scene.on_exit()

        # 2. 切换指针
        self.current_key = key
        self.current_scene = self.scenes[key]

        # 3. 进入新场景
        # 🎯 切换场景时自动更新输入上下文
        self.input.set_context(key)
        self.current_scene.on_enter()

    def handle_frame(self, events):
        """
        处理事件，并监听场景返回的切换指令
        主循环调用：处理事件 → 输入映射 → 场景响应
        """
        self.input.process_events(events)
        input_state = self.input.get_actions()

        # 1. 优先处理全局指令
        if "PAUSE" in input_state["global"]:
            self.switch("PAUSE")  # 假设你后续有 PauseScreen
            return
        if "TOGGLE_FULLSCREEN" in input_state["global"]:
            pygame.display.toggle_fullscreen()

        if self.current_scene:
            next_key = self.current_scene.handle_input(input_state)
            if next_key:
                self.switch(next_key)

    def update(self):
        if self.current_scene:
            self.current_scene.update()

    def draw(self):
        if self.current_scene:
            self.current_scene.draw(self.screen)

    @property
    def is_running(self):
        return self._running
