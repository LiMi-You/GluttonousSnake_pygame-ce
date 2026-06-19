# input_manager.py
import pygame

class InputManager:
    def __init__(self):
        self.context = "DEFAULT"
        self._pressed = set()
        self._just_pressed = set()       # 仅单帧有效，防连触
        self._key_hold_start = {}        # {key_code: press_tick} 按下时刻记录
        
        # 🔑 全局快捷键（任何场景都优先拦截）
        self.global_map = {
            pygame.K_ESCAPE: "GLOBAL_QUIT",
            pygame.K_F11: "TOGGLE_FULLSCREEN",
            pygame.K_F1: "TOGGLE_DEBUG",
        }
        
        # 🗺️ 上下文按键映射（后续可抽到 settings.py 配置化）
        self.context_maps = {
            "MENU": {
                pygame.K_UP: "NAV_UP",
                pygame.K_DOWN: "NAV_DOWN",
                pygame.K_RETURN: "CONFIRM",
                pygame.K_SPACE: "CONFIRM",
            },
            "GAME": {
                pygame.K_LEFT: "MOVE_LEFT",
                pygame.K_RIGHT: "MOVE_RIGHT",
                pygame.K_UP: "MOVE_UP",
                pygame.K_DOWN: "MOVE_DOWN",
                pygame.K_z: "ATTACK",
                pygame.K_x: "JUMP"
            },
            "OVERLAY": {
                pygame.K_LEFT: "NAV_LEFT",
                pygame.K_RIGHT: "NAV_RIGHT",
                pygame.K_RETURN: "CONFIRM",
                pygame.K_SPACE: "CONFIRM",
                pygame.K_ESCAPE: "CANCEL",
            }
        }

        # 上下文按键别名映射
        self.CONTEXT_ALIAS = {
            "START": "MENU", 
            "GAME": "GAME", 
            "PAUSE": "MENU"
            } 

    def set_context(self, name: str):
        self.context = self.CONTEXT_ALIAS.get(name, name)

    def process_events(self, events):
        """消费 pygame 事件列表，更新输入状态"""
        self._just_pressed.clear()
        now = pygame.time.get_ticks()
        for event in events:
            if event.type == pygame.KEYDOWN:
                self._pressed.add(event.key)
                self._just_pressed.add(event.key)
                self._key_hold_start[event.key] = now      # 记录按下时刻

                #测试用排查断点
                # print(f"⌨️ 捕获按键: {pygame.key.name(event.key)} (code: {event.key})")

            elif event.type == pygame.KEYUP:
                self._pressed.discard(event.key)
                self._key_hold_start.pop(event.key, None)  # 清除时刻记录

    def get_actions(self) -> dict:
        """返回标准化输入数据，供场景消费"""

        #测试用排查断点
        # print(f"🔍 当前上下文: '{self.context}' | 可用映射: {list(self.context_maps.get(self.context, {}).keys())}")

        global_actions = []
        context_actions = []
        ctx_map = self.context_maps.get(self.context, {})

        for key in self._just_pressed:
            if key in self.global_map:
                global_actions.append(self.global_map[key])
            if key in ctx_map:
                context_actions.append(ctx_map[key])

        #测试用排查断点
        # print(f"🗺️ 映射结果 -> global: {global_actions} | context: {context_actions}")

        # 计算每个按住键的持续时长（毫秒）
        now = pygame.time.get_ticks()
        held_durations = {
            key: now - self._key_hold_start.get(key, now)
            for key in self._pressed
        }

        return {
            "global": global_actions,
            "context": context_actions,
            "held_keys": self._pressed.copy(),           # 长按状态（供持续移动等逻辑使用）
            "held_durations": held_durations,             # {key_code: ms} 按住时长
        }
    
    
