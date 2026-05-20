# main.py
import pygame
import sys
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS
from input_manager import InputManager
from scene_manager import SceneManager
from scenes.start_screen import StartScreen
# 后续会创建 GameScreen，提前导入占位
# from scenes.game_screen import GameScreen

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("My Pygame Game")
    clock = pygame.time.Clock()

    # 1️⃣ 初始化输入与场景管理器
    # 2️⃣ 创建场景管理器（必须在 screen 创建之后！）
    input_mgr = InputManager()
    scene_mgr = SceneManager(screen, input_mgr)

    # 2️⃣ 注册场景（此时 screen 已存在，实例化安全）
    scene_mgr.add_scene("START", StartScreen(screen))
    # scene_mgr.add_scene("GAME", GameScreen(screen))

    # 3️⃣ 初始化默认场景
    scene_mgr.switch("START")

    running = True
    while running and scene_mgr.is_running:
        # 事件处理：交给管理器，它会自动处理场景切换指令
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                scene_mgr.switch("QUIT")
                break
        
        scene_mgr.handle_frame(events)

        # 更新 & 绘制
        scene_mgr.update()
        scene_mgr.draw()

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()