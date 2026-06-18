# main.py
import pygame
import sys
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS
from input_manager import InputManager
from scene_manager import SceneManager
#from scenes.start_screen import StartScreen
# 后续会创建 GameScreen，提前导入占位
# from scenes.game_screen import GameScreen

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("My Pygame Game")
    clock = pygame.time.Clock()

    # 1. 初始化输入管理器
    input_mgr = InputManager()

    # 2. 初始化场景管理器 (传入初始场景ID 和 输入管理器)
    # 不再需要在这里 import 具体的 MenuScene 等类
    scene_mgr = SceneManager(screen, initial_scene_id="START", input_manager=input_mgr)

    running = True
    while running:
        # 事件处理：交给管理器，它会自动处理场景切换指令
        events = pygame.event.get()
        
        # 将事件交给场景管理器处理
        # 如果 handle_frame 返回 False，则停止循环
        if scene_mgr.handle_frame(events) is False:
            running = False

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()