# scenes/registry.py
from .start_screen import StartScreen
# 未来新增场景在这里导入

# 场景工厂注册表：key为场景ID字符串，value为场景类
SCENE_REGISTRY = {
    "START": StartScreen
    # "MENU": MenuScene,
    # "BATTLE": BattleScene,
    # "DIALOGUE": DialogueScene,
    # 未来新增场景在这里注册，例如: "SHOP": ShopScene
}

def get_scene_class(scene_id: str):
    """获取场景类，若不存在则抛出异常或返回默认场景"""
    if scene_id not in SCENE_REGISTRY:
        raise ValueError(f"未找到场景ID: {scene_id}")
    return SCENE_REGISTRY[scene_id]