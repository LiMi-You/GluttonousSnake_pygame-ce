# scenes/start_screen.py
import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT
from scenes.base_scene import Scene

class StartScreen(Scene):
    def __init__(self, screen):
        self.screen = screen
        # 加载背景图（先放一张测试图，后续替换成你的美工资源）
        self.background = pygame.image.load("assets/images/start_bg.png").convert()
        self.background = pygame.transform.scale(self.background, (SCREEN_WIDTH, SCREEN_HEIGHT))
        
        # 准备文字（可以抽到单独的方法中，但简单项目放在 __init__ 也可）
        self.font = pygame.font.Font(None, 36)
        self.text_surface = self.font.render("Press ENTER to Start", True, (255, 255, 255))
        # 动态计算文字位置（相对于屏幕，支持分辨率自适应）
        self.text_rect = self.text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100))
    
    def handle_event(self, event):
        """处理单个事件，返回场景切换信号"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                return "GAME"      # 切换到游戏场景
            if event.key == pygame.K_ESCAPE:
                return "QUIT"      # 退出游戏
        # 可以继续处理其他事件（如鼠标点击）
        return None   # 没有切换需求
    
    def update(self):
        """开始页不需要动态更新，留空"""
        pass
    
    def draw(self, screen):
        """绘制开始页"""
        screen.blit(self.background, (0, 0))
        screen.blit(self.text_surface, self.text_rect)