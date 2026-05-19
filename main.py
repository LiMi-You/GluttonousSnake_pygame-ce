# main.py
import pygame
import sys
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS
from scenes.start_screen import StartScreen
# 后续会创建 GameScreen，提前导入占位
# from scenes.game_screen import GameScreen

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("My Pygame Game")
    clock = pygame.time.Clock()

    # 场景管理
    scenes = {
        "START": StartScreen(screen),
        # "GAME": GameScreen(screen),   # 后续实现
    }
    current_scene_key = "START"
    current_scene = scenes[current_scene_key]
    current_scene.on_enter()  # 进入开始场景（如果有初始化逻辑）

    running = True
    while running:
        # 1. 事件处理（统一获取，分发给当前场景）
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            # 将事件交给当前场景处理
            next_key = current_scene.handle_event(event)
            if next_key is not None:
                # 需要切换场景
                if next_key == "QUIT":
                    running = False
                    break
                if next_key in scenes:
                    current_scene.on_exit()       # 离开旧场景
                    current_scene = scenes[next_key]
                    current_scene_key = next_key
                    current_scene.on_enter()      # 进入新场景
                # 如果 next_key 不在 scenes 中，可以打印警告或忽略
        
        # 2. 更新当前场景逻辑
        current_scene.update()
        
        # 3. 绘制当前场景
        current_scene.draw(screen)
        
        pygame.display.flip()
        clock.tick(FPS)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()