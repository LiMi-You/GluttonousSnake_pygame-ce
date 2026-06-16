# scenes/redits_screen.py
import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, COLORS
from scenes.base_scene import Scene
from utils.video_player import VideoPlayer

class CreditsScreen(Scene):
    def __init__(self, screen: pygame.Surface):
        super().__init__(screen)
        self.screen = screen

        self.player = VideoPlayer("assets/media/Credits_faster.mp4", loop=False, buffer_size=120, preload=True)

    def on_enter(self):
        self.player.load()
        self.player.play()

    def on_exit(self):
        pass

    def draw(self, screen: pygame.Surface):
        super().draw(screen)
        screen.fill((0, 0, 0))
        self.player.render(screen)