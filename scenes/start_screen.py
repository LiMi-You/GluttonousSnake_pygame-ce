# scenes/start_screen.py
import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, COLORS
from scenes.base_scene import Scene

class StartScreen(Scene):
    def __init__(self, screen):
        self.screen = screen
        # 加载背景图（先放一张测试图，后续替换成你的美工资源）
        self.background = pygame.image.load("assets/images/start_bg.png").convert()
        self.background = pygame.transform.scale(self.background, (1017, 720))
        
        # 准备文字（可以抽到单独的方法中，但简单项目放在 __init__ 也可）
        self.font = pygame.font.Font(None, 36)
        self.text_surface = self.font.render("Press ENTER to Start", True, (255, 255, 255))
        # 动态计算文字位置（相对于屏幕，支持分辨率自适应）
        self.text_rect = self.text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100))
        
        #按钮区域
        self.btn_rect = pygame.Rect(SCREEN_WIDTH // 2 , SCREEN_HEIGHT - 100, 240, 60)
        self.btn_text = self.font.render("CLICK TO START", True, COLORS["bg"])

    def on_enter(self): 
        print("🟢 进入 START")
        pygame.mixer.music.load("assets/sounds/start_bgm.mp3")
        pygame.mixer.music.play(-1,0,0)
    
    def on_exit(self): 
        print("🔴 离开 START")

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
            if self.btn_rect.collidepoint(pygame.mouse.get_pos()):
                return "LOBBY"
            

        return None
    
    def update(self):
        """
        开始页不需要动态更新，留空
        场景逻辑更新（如倒计时、动画状态等）
        """
        pass
    
    def draw(self, screen):
        """绘制开始页"""
        super().draw(self.screen)
        screen.blit(self.background, (131, 0))
        screen.blit(self.text_surface, self.text_rect)
        pygame.draw.rect(self.screen, COLORS["white"], self.btn_rect, border_radius=10, width=1)
        self.screen.blit(self.btn_text, self.btn_text.get_rect(center=self.btn_rect.center))