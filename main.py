# main.py
import pygame
import sys
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, SCENES
from scenes.start_screen import StartScreen

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("My Pygame Game")
    clock = pygame.time.Clock()
    
    # 初始化场景
    current_scene = SCENES["START"]
    start_screen = StartScreen(screen)
    # game_scene = GameScene(screen)  # 后续创建
    
    running = True
    while running:
        # 根据当前场景分发逻辑
        if current_scene == SCENES["START"]:
            next_scene = start_screen.handle_events()
            start_screen.update()
            start_screen.draw()
        
        elif current_scene == SCENES["GAME"]:
            # next_scene = game_scene.handle_events()
            # game_scene.update()
            # game_scene.draw()
            pass  # 后续实现
        
        # 处理场景切换
        if next_scene == "QUIT":
            running = False
        elif next_scene in [SCENES["START"], SCENES["GAME"], SCENES["END"]]:
            current_scene = next_scene
        
        pygame.display.flip()
        clock.tick(FPS)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()