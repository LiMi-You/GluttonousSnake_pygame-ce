# scenes/start_screen.py
import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT

class StartScreen:
    def __init__(self, screen):
        self.screen = screen
        # 加载背景图（先放一张测试图，后续替换成你的美工资源）
        self.background = pygame.image.load("assets/images/start_bg.png").convert()
        self.background = pygame.transform.scale(self.background, (SCREEN_WIDTH, SCREEN_HEIGHT))
        
    def handle_events(self):
        """处理开始页的输入事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "QUIT"  # 返回退出信号
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:  # 按回车进入游戏
                    return "GAME"  # 返回切换信号
                if event.key == pygame.K_ESCAPE:  # 按 ESC 退出
                    return "QUIT"
        return "START"  # 保持在开始页
    
    def update(self):
        """开始页不需要每帧更新逻辑，留空"""
        pass
    
    def draw(self):
        """渲染开始页"""
        self.screen.blit(self.background, (0, 0))
        # 可以加一些文字提示
        font = pygame.font.Font(None, 36)
        text = font.render("Press ENTER to Start", True, (255, 255, 255))
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100))
        self.screen.blit(text, text_rect)