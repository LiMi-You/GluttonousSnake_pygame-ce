import pygame
import sys
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, COLORS

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("My Pygame Game")
    clock = pygame.time.Clock()

    running = True
    while running:
        # 1. 处理事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # 2. 清屏
        screen.fill(COLORS["bg"])

        # 3. 渲染区（暂时留空，以后在这里调用实体类的 update/draw）

        # 4. 刷新屏幕
        pygame.display.flip()

        # 5. 锁定帧率
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()