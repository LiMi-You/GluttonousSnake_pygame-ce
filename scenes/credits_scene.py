# scenes/credits_scene.py
import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT
from scenes.base_scene import Scene
from utils.video_player import VideoPlayer


class CreditsScreen(Scene):
    """制作人员名单场景：播放视频，支持鼠标提示 & 长按 R 退出"""

    # ── 常量 ──
    HOLD_THRESHOLD = 2500       # 长按退出阈值（毫秒）
    MOUSE_IDLE_TIMEOUT = 1.0    # 鼠标静止后隐藏提示图（秒）
    HINT_IMAGE_PATH = "assets/images/skip.png"

    def __init__(self, screen: pygame.Surface):
        super().__init__(screen)
        self.screen = screen

        # 视频播放器
        self.player = VideoPlayer(
            "assets/media/Credits_faster.mp4", loop=False, buffer_size=120, preload=True
        )

        # ── 鼠标提示图状态 ──
        self._hint_image: pygame.Surface | None = None
        self._hint_visible: bool = False
        self._last_mouse_pos: tuple[int, int] = (0, 0)
        self._mouse_last_move_tick: int = 0   # 最后一次检测到鼠标移动的时刻(ms)

    # ─────────────────────── 生命周期 ───────────────────────

    def on_enter(self):
        # 加载提示图并缩放到全屏
        try:
            raw = pygame.image.load(self.HINT_IMAGE_PATH).convert_alpha()
            self._hint_image = pygame.transform.smoothscale(
                raw, (SCREEN_WIDTH, SCREEN_HEIGHT)
            )
        except (pygame.error, FileNotFoundError) as e:
            print(f"[CreditsScreen] 提示图加载失败: {e}")
            self._hint_image = None

        self.player.load()
        self.player.play()

        # 重置状态
        self._hint_visible = False
        self._last_mouse_pos = pygame.mouse.get_pos()
        self._mouse_last_move_tick = 0

    def on_exit(self):
        self.player.stop() if hasattr(self.player, "stop") else None

    # ─────────────────────── 输入处理 ───────────────────────

    def handle_input(self, input_state: dict) -> str | None:
        # ① 鼠标移动检测 → 显示提示图
        current_pos = pygame.mouse.get_pos()
        if current_pos != self._last_mouse_pos:
            self._hint_visible = True
            self._mouse_last_move_tick = pygame.time.get_ticks()
            self._last_mouse_pos = current_pos

        # ② 长按 R 键检测（从输入管线获取按住时长）
        r_held_ms = input_state.get("held_durations", {}).get(pygame.K_r, 0)
        if r_held_ms >= self.HOLD_THRESHOLD:
            return "START"

        return None

    # ─────────────────────── 逻辑更新 ───────────────────────

    def update(self):
        # 鼠标静止超时 → 隐藏提示图
        if self._hint_visible:
            if pygame.time.get_ticks() - self._mouse_last_move_tick >= self.MOUSE_IDLE_TIMEOUT * 1000:
                self._hint_visible = False

    # ─────────────────────── 渲染 ───────────────────────

    def draw(self, screen: pygame.Surface):
        super().draw(screen)
        screen.fill((0, 0, 0))

        # 1. 视频
        self.player.render(screen)

        # 2. 鼠标提示图（全屏覆盖）
        if self._hint_visible and self._hint_image:
            screen.blit(self._hint_image, (0, 0))