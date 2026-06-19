# scenes/loading_screen.py
import pygame
import random
from settings import SCREEN_WIDTH, SCREEN_HEIGHT
from scenes.base_scene import Scene

class LoadingScreen(Scene):
    """加载过渡场景：显示 loading 画面，随机等待 3~5 秒后自动跳转 GAME"""

    def __init__(self, screen: pygame.Surface, **kwargs):
        super().__init__(screen)
        self.screen = screen
        self.loadimage = pygame.image.load("assets/images/loading.png").convert_alpha()
        self.loadimage = pygame.transform.scale(self.loadimage, (SCREEN_WIDTH, SCREEN_HEIGHT))

        self._wait_ms: int = 0        # 本次等待时长（毫秒）
        self._start_tick: int = 0     # 进入场景的时刻

    def on_enter(self):
        print("🟢 进入 LOAD")
        self._wait_ms = int(random.uniform(0.0, 3.0) * 1000)
        self._start_tick = pygame.time.get_ticks()

    def on_exit(self):
        print("🔴 离开 LOAD")
        pass

    def update(self):
        elapsed = pygame.time.get_ticks() - self._start_tick
        if elapsed >= self._wait_ms:
            return "GAME"

    def draw(self, screen: pygame.Surface):
        super().draw(screen)
        screen.fill((0, 0, 0))
        screen.blit(self.loadimage, (0, 0))