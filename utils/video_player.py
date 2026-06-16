"""
视频播放器工具模块
使用 OpenCV 读取视频并渲染到 Pygame Surface
支持格式: MP4, AVI, MKV, MOV, WEBM 等 (取决于系统编解码器)

特性:
- 缓冲预读取: 后台线程提前读取帧，避免播放卡顿
- 支持循环播放、暂停/恢复
- 自动缩放适配屏幕
"""

import pygame
import cv2
import numpy as np
import threading
import time
from pathlib import Path
from typing import Optional, Callable
from collections import deque


class VideoPlayer:
    """在 Pygame 中播放视频的工具类（带缓冲预读取）"""
    
    def __init__(self, video_path: str, loop: bool = False, buffer_size: int = 60, preload: bool = True):
        """
        初始化视频播放器
        
        Args:
            video_path: 视频文件路径
            loop: 是否循环播放
            buffer_size: 预读取缓冲帧数 (默认60帧, 约2秒@30fps)
            preload: 是否开启预读取 (默认开启, 关闭则实时读取)
        """
        self.video_path = Path(video_path)
        self.loop = loop
        self.buffer_size = buffer_size
        self.preload = preload
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_playing = False
        self.is_finished = False
        
        # 视频属性
        self.fps = 30
        self.frame_delay = 1000.0 / self.fps  # 毫秒
        self.width = 0
        self.height = 0
        
        # 回调函数
        self.on_finish: Optional[Callable] = None
        
        # 帧缓存 (预读取缓冲区)
        self._frame_queue: deque = deque()
        self._last_frame_time = 0
        self._last_surface: Optional[pygame.Surface] = None  # 缓存上一帧(暂停时使用)
        
        # 预读取线程控制
        self._preload_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()  # 未设置 = 暂停, 已设置 = 播放中
        self._queue_lock = threading.Lock()
        self._end_sentinel = object()  # 哨兵对象, 表示视频结束
        
    def load(self) -> bool:
        """
        加载视频文件并启动预读取线程
        
        Returns:
            bool: 是否加载成功
        """
        if not self.video_path.exists():
            print(f"视频文件不存在: {self.video_path}")
            return False
            
        self.cap = cv2.VideoCapture(str(self.video_path))
        
        if not self.cap.isOpened():
            print(f"无法打开视频文件: {self.video_path}")
            return False
            
        # 获取视频属性
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        
        if self.fps <= 0:
            self.fps = 30
            
        self.frame_delay = 1000.0 / self.fps
        
        return True
    
    def _preload_worker(self):
        """
        后台预读取线程
        持续将视频帧读取并转换为 Surface, 存入缓冲队列
        """
        while not self._stop_event.is_set():
            # 检查是否暂停
            if not self._pause_event.is_set():
                self._pause_event.wait()  # 阻塞等待恢复
                if self._stop_event.is_set():
                    break
                # 恢复后重置 cap 的位置,确保从正确位置继续
                if self.cap is not None:
                    current_pos = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, current_pos)
            
            # 检查缓冲区是否已满
            with self._queue_lock:
                queue_full = len(self._frame_queue) >= self.buffer_size
            
            if queue_full:
                time.sleep(0.001)  # 缓冲区满,短暂等待
                continue
            
            # 读取一帧
            if self.cap is None:
                break
                
            ret, frame = self.cap.read()
            
            if not ret:
                # 视频读取结束
                if self.loop:
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = self.cap.read()
                    if not ret:
                        break
                else:
                    with self._queue_lock:
                        self._frame_queue.append(self._end_sentinel)
                    break
            
            # 转换为 Pygame Surface
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            surface = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))
            
            # 存入缓冲队列
            with self._queue_lock:
                self._frame_queue.append(surface)
    
    def _start_preload(self):
        """启动预读取线程"""
        self._stop_event.clear()
        self._pause_event.set()  # 标记为播放状态
        
        self._preload_thread = threading.Thread(
            target=self._preload_worker,
            daemon=True  # 守护线程,主程序退出时自动结束
        )
        self._preload_thread.start()
    
    def _stop_preload(self):
        """停止预读取线程"""
        self._stop_event.set()
        self._pause_event.set()  # 唤醒可能在等待的线程
        
        if self._preload_thread and self._preload_thread.is_alive():
            self._preload_thread.join(timeout=0.5)  # 等待线程结束
        
        self._preload_thread = None
    
    def play(self):
        """开始播放"""
        if self.cap is None:
            if not self.load():
                return
        
        # 清空缓冲区并重新开始
        with self._queue_lock:
            self._frame_queue.clear()
        
        self.is_playing = True
        self.is_finished = False
        self._last_frame_time = pygame.time.get_ticks()
        
        if self.cap is not None:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        
        # 根据配置决定是否启动预读取线程
        if self.preload:
            self._start_preload()
    
    def stop(self):
        """停止播放"""
        self.is_playing = False
        
        if self.preload:
            self._stop_preload()
        
        with self._queue_lock:
            self._frame_queue.clear()
        
        if self.cap:
            self.cap.release()
            self.cap = None
    
    def pause(self):
        """暂停播放"""
        self.is_playing = False
        if self.preload:
            self._pause_event.clear()  # 通知预读取线程暂停
    
    def resume(self):
        """恢复播放"""
        self.is_playing = True
        self._last_frame_time = pygame.time.get_ticks()
        if self.preload:
            self._pause_event.set()  # 通知预读取线程恢复
    
    def get_frame(self) -> Optional[pygame.Surface]:
        """
        从缓冲队列获取当前帧 (预读取模式) 或实时读取 (非预读取模式)
        
        Returns:
            pygame.Surface 或 None
        """
        if not self.is_playing:
            return self._last_surface  # 暂停时返回上一帧
        
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self._last_frame_time
        
        # 根据时间流逝决定是否读取新帧
        if elapsed >= self.frame_delay:
            self._last_frame_time = current_time
            
            if self.preload:
                # 预读取模式: 从缓冲队列取帧
                with self._queue_lock:
                    if len(self._frame_queue) > 0:
                        surface = self._frame_queue.popleft()
                        
                        # 检查是否是结束哨兵
                        if surface is self._end_sentinel:
                            self.is_playing = False
                            self.is_finished = True
                            if self.on_finish:
                                self.on_finish()
                            return None
                        
                        self._last_surface = surface
                        return surface
                    else:
                        # 缓冲区为空(预读取跟不上),显示上一帧
                        return self._last_surface
            else:
                # 非预读取模式: 实时读取
                if self.cap is None:
                    return self._last_surface
                    
                ret, frame = self.cap.read()
                
                if not ret:
                    # 视频播放结束
                    if self.loop:
                        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        ret, frame = self.cap.read()
                    if not ret:
                        self.is_playing = False
                        self.is_finished = True
                        if self.on_finish:
                            self.on_finish()
                        return None
                
                # OpenCV 使用 BGR，Pygame 使用 RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                surface = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))
                self._last_surface = surface
                return surface
        
        # 时间未到,返回上一帧
        return self._last_surface
    
    def render(self, screen: pygame.Surface, 
               dest_rect: Optional[pygame.Rect] = None,
               scale_to_fit: bool = True):
        """
        直接渲染视频帧到屏幕
        
        Args:
            screen: 目标屏幕 Surface
            dest_rect: 目标矩形区域 (None 则居中显示)
            scale_to_fit: 是否缩放以适应目标区域
        """
        frame = self.get_frame()
        if frame is None:
            return
            
        if dest_rect is None:
            dest_rect = screen.get_rect()
            
        if scale_to_fit:
            # 计算缩放比例
            scale_x = dest_rect.width / frame.get_width()
            scale_y = dest_rect.height / frame.get_height()
            scale = min(scale_x, scale_y)
            
            new_width = int(frame.get_width() * scale)
            new_height = int(frame.get_height() * scale)
            frame = pygame.transform.scale(frame, (new_width, new_height))
            
            # 居中显示
            x = dest_rect.x + (dest_rect.width - new_width) // 2
            y = dest_rect.y + (dest_rect.height - new_height) // 2
            screen.blit(frame, (x, y))
        else:
            screen.blit(frame, dest_rect.topleft)
    
    def update(self, events: list) -> bool:
        """
        更新视频状态（处理事件）
        
        Args:
            events: Pygame 事件列表
            
        Returns:
            bool: 是否仍在播放
        """
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if self.is_playing:
                        self.pause()
                    else:
                        self.resume()
                elif event.key == pygame.K_ESCAPE:
                    self.stop()
                    return False
                    
        return self.is_playing or not self.is_finished


# 示例：在场景中使用
def example_usage():
    """示例：如何在游戏场景中使用视频播放器"""
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    clock = pygame.time.Clock()
    
    # 创建播放器 (缓冲60帧, 约2秒)
    player = VideoPlayer("assets/media/intro.mp4", loop=False, buffer_size=60)
    
    if not player.load():
        print("无法加载视频")
        return
        
    player.play()
    
    running = True
    while running:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
        
        # 更新并渲染视频
        screen.fill((0, 0, 0))
        player.render(screen)
        
        # 检查视频是否播放完成
        if player.is_finished:
            print("视频播放完成，进入下一场景...")
            running = False
        
        pygame.display.flip()
        clock.tick(60)
    
    player.stop()
    pygame.quit()


if __name__ == "__main__":
    example_usage()
