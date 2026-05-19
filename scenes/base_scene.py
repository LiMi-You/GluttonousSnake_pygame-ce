# scenes/base_scene.py
import pygame

class Scene:
    """场景基类，所有场景都应继承此类"""
    
    def handle_event(self, event: pygame.event.Event) -> str | None:
        """
        处理单个事件。
        返回值：None 表示不切换场景，返回 "GAME"、"QUIT" 等字符串表示希望切换到的场景标识。
        """
        return None
    
    def update(self):
        """更新场景逻辑（角色移动、碰撞检测等）"""
        pass
    
    def draw(self, screen: pygame.Surface):
        """绘制场景内容"""
        pass
    
    def on_enter(self):
        """进入场景时调用（可选，用于加载资源、重置状态）"""
        pass
    
    def on_exit(self):
        """离开场景时调用（可选，用于清理资源）"""
        pass