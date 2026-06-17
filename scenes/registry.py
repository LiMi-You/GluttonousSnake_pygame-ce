# scenes/registry.py
from .start_screen import StartScreen
from .lobby_screen import LobbyScreen
from .game_screen import GameScreen
from .credits_scene import CreditsScreen
from .loading_screen import LoadingScreen

# 场景工厂注册表：key为场景ID字符串，value为场景类
SCENE_REGISTRY = {
    "START": StartScreen,
    "LOBBY": LobbyScreen,
    "GAME":  GameScreen,
    "CREDITS": CreditsScreen,
    "LOAD": LoadingScreen
}

def get_scene_class(scene_id: str):
    """获取场景类，若不存在则抛出异常或返回默认场景"""
    if scene_id not in SCENE_REGISTRY:
        raise ValueError(f"未找到场景ID: {scene_id}")
    return SCENE_REGISTRY[scene_id]