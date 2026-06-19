# scenes/start_screen.py
import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, COLORS
from scenes.base_scene import Scene


class StartScreen(Scene):
    def __init__(self, screen, **kwargs):
        self.screen = screen
        # 加载背景图（先放一张测试图，后续替换成你的美工资源）
        self.background = pygame.image.load("assets/images/start_bg.png").convert()
        self.background = pygame.transform.scale(self.background,(SCREEN_WIDTH,SCREEN_HEIGHT))
        
        #按钮开始游戏
        self.startgame = pygame.image.load("assets/images/start_game.png").convert_alpha()
        self.startgame = pygame.transform.scale(self.startgame,(SCREEN_WIDTH,SCREEN_HEIGHT))

        #按钮制作人
        self.credits = pygame.image.load("assets/images/credits.png").convert_alpha()
        self.credits = pygame.transform.scale(self.credits,(SCREEN_WIDTH,SCREEN_HEIGHT))
        
        #按钮区域
        self.btn_start = pygame.Rect(953, 240, 163, 105)
        self.btn_credits = pygame.Rect(960, 366, 117, 88)

    def on_enter(self): 
        print("🟢 进入 START")
        pygame.mixer.music.load("assets/sounds/start_bgm.mp3")
        pygame.mixer.music.play(-1,0,0)
    
    def on_exit(self): 
        print("🔴 离开 START")
        pygame.mixer.music.fadeout(500)
        pygame.mixer.music.unload()

    def handle_input(self, input_state: dict) -> str |None:
        """
        处理单个事件，返回场景切换信号
        ✅ 场景只关心“动作”，不关心是键盘、手柄还是鼠标
        """
        #测试用排查断点
        # print(f"🎮 场景输入状态: {input_state}")

        if "CONFIRM" in input_state["context"]:
            return "LOBBY"
        
        # 鼠标点击仍可直接处理（UI交互常见，，不强制走 InputManager）
        if pygame.mouse.get_pressed()[0]:
            if self.btn_start.collidepoint(pygame.mouse.get_pos()):
                return "LOAD"
            if self.btn_credits.collidepoint(pygame.mouse.get_pos()):
                return "CREDITS"
            
            

        return None
    
    def update(self):
        """
        开始页不需要动态更新，留空
        场景逻辑更新（如倒计时、动画状态等）
        """
        pass
    
    def draw(self, screen):
        """绘制开始页"""
        super().draw(screen)
        screen.blit(self.background, (0, 0))
        screen.blit(self.startgame, (0, 0))
        screen.blit(self.credits, (0, 0))
        # pygame.draw.rect(self.screen, COLORS["white"], self.btn_start, border_radius=10, width=0)
        # pygame.draw.rect(self.screen, COLORS["white"], self.btn_credits, border_radius=10, width=0)