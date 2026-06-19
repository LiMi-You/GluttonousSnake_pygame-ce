# settings.py
# ==================== 屏幕 & 性能 ====================
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 25

# ==================== 通用颜色 ====================
COLORS = {
    "bg": "purple",
    "white": (255, 255, 255),
    "black": (0, 0, 0),
}

# ==================== 场景ID常量 ====================
SCENES = {
    "START": "start",
    "LOBBY": "lobby",
    "GAME": "game",
    "END": "end",
}

# ==================== 贪吃蛇游戏参数 ====================
# 网格尺寸
CELL_SIZE = 21                     # 每个格子的像素大小
GRID_WIDTH = 29                    # 网格列数
GRID_HEIGHT = 25                   # 网格行数

# 游戏区域偏移（自动居中）
MARGIN_LEFT = SCREEN_WIDTH // 2 - (CELL_SIZE * GRID_WIDTH) // 2
MARGIN_TOP = 146                   # 游戏区域上边距

# 蛇的初始数据（网格坐标）
SNAKE_INITIAL = [(10, 7), (9, 7), (8, 7)]   # 头在右边，初始向右移动
SNAKE_INITIAL_DIRECTION = (1, 0)             # 初始方向：向右

# 移动间隔（毫秒），值越大蛇移动越慢
MOVE_INTERVAL = 130

# 贪吃蛇颜色
SNAKE_COLOR = (254, 159, 43)       # 蛇身填充色（橙色）
SNAKE_BORDER_COLOR = (0, 0, 0)     # 蛇身边框色（黑色）
SNAKE_BORDER_WIDTH = 2             # 边框线宽

# 食物颜色
FOOD_COLOR = (255, 50, 50)         # 食物填充色（红色）

# ==================== 道具系统参数 ====================
ITEM_RENDER_SIZE = 25              # 道具渲染尺寸（像素），略大于 CELL_SIZE(21)
ITEM_SPAWN_INTERVAL = 2000         # 生成间隔（毫秒）
ITEM_MAX_ON_SCREEN = 100             # 场上最多同时存在的道具数
ITEM_BASE_SPAWN_COUNT = 3          # 游戏开始时初始生成数量

# ==================== 难度阶段阈值 ====================
PHASE_EARLY_MAX_SCORE = 100000     # 前期 → 中期的分数门槛
PHASE_LATE_MIN_LENGTH = 20         # 中期 → 后期的蛇长门槛

# ==================== 可移动道具参数 ====================
MOVE_ITEM_BASE_SPEED = 0.03        # 移动速度单位（格/帧），move_speed=1 时每帧移动 0.08 格 ≈ 42px/s @25fps
# 速度公式: 实际速度(格/帧) = move_speed × MOVE_ITEM_BASE_SPEED

# 移动引擎切换：True=新引擎(movement.py)，False=旧引擎(item_manager内联)
USE_NEW_MOVEMENT = True

# 网格线颜色
GRID_LINE_COLOR = (54, 188, 217)   # 网格线颜色（青蓝）
GRID_LINE_WIDTH = 2                # 网格线宽

# 游戏背景色
GAME_BG_COLOR = (40, 40, 40)       # 深灰背景

# 游戏背景图层（相对于 assets/images/）
GAME_BG_LAYERS = [
    "bg_stripe.png",
    "left_and_right.png",
    "Large_format.png",
    "Score_board.png",
]