# scenes/base_scene.py
import pygame
from typing import Optional

class Scene:
    """所有场景的基类：定义标准生命周期与输入接口"""
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.w = screen.get_width()
        self.h = screen.get_height()
        # 默认字体，子类可覆盖
        self.font = pygame.font.SysFont("arial", 32)

    def on_enter(self):
        """进入场景时调用（重置状态、播放BGM、加载UI等）"""
        pass

    def on_exit(self):
        """离开场景时调用（停止音频、清理缓存、保存进度等）"""
        pass

    def handle_input(self, input_state: dict) -> Optional[str]:
        """
        处理标准化输入（由 InputManager 预处理后传入）
        input_state 结构:
          {
            "global": ["PAUSE", ...],       # 全局快捷键动作
            "context": ["CONFIRM", ...],    # 当前场景专属动作
            "held_keys": {pygame.K_UP, ...} # 当前物理按下的键码集合
          }
        返回值: None 表示不切换，返回 "GAME"/"MENU" 等字符串表示目标场景
        """
        return None

    def update(self) -> Optional[str]:
        """每帧逻辑更新（移动、物理、AI、状态机等）
        返回值: None 表示不切换，返回 "GAME"/"MENU" 等字符串表示目标场景
        """
        return None

    def draw(self, screen: pygame.Surface):
        """每帧绘制（背景、UI、角色等）"""
        screen.fill((255,255,255))
        pass
