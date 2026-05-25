--- docs/CHANGELOG.md (原始)
# CHANGELOG

所有对该项目的显著更改都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
本项目遵循 [语义化版本规范](https://semver.org/spec/v2.0.0.html)。

---

## [v0.5.0] - 2024-05-25

### ✨ Added — 退出确认覆盖层 & 鼠标事件支持

#### 涉及文件

| 文件 | 操作 |
|:---|:---|
| `quit_overlay.py` | **新增** — 退出确认覆盖层，独立可复用的 UI 组件 |
| `scene_manager.py` | **修改** — 集成覆盖层生命周期与鼠标状态传递 |
| `input_manager.py` | **修改** — 新增 `OVERLAY` 上下文按键映射 |

#### 改动详情

**1. 新增 `quit_overlay.py`**
- 在场景之上绘制半透明遮罩 + 确认对话框（"是"/"否"两个按钮）
- 支持键盘（← → 切换选项，Enter/Space 确认，ESC 取消）和鼠标两种交互
- 按钮矩形预计算并存储为实例属性 `self.btn_rects`，供绘制与碰撞检测复用
- `draw()` 方法增加实时鼠标悬停检测（`hovered_index`），高亮逻辑独立于键盘焦点 `self.selected`

**2. 修改 `scene_manager.py`**
- `SceneManager.__init__()` 中初始化 `QuitOverlay` 实例
- `handle_frame()` 中覆盖层激活时：
  - 临时切换 InputManager 上下文为 `"OVERLAY"`，重新映射按键
  - 通过 `pygame.mouse.get_pressed()` / `pygame.mouse.get_pos()` 获取鼠标状态，附加到 `overlay_actions` 字典
  - 覆盖层返回 `True` 时主循环退出；返回 `False` 或 `None` 时继续渲染
- 覆盖层未激活时：`ESC` 键触发 `GLOBAL_QUIT` → 显示覆盖层（不直接退出）
- 渲染顺序：场景绘制 → 覆盖层绘制（确保覆盖层在顶层）

**3. 修改 `input_manager.py`**
- `context_maps` 新增 `"OVERLAY"` 上下文：
  - `← / →` → `NAV_LEFT / NAV_RIGHT`
  - `Enter / Space` → `CONFIRM`
  - `ESC` → `CANCEL`

#### 交互流程
```
用户按 ESC → 覆盖层显示（原场景保留在底层）
  ├── 点击"是" 或 按 → 选中"是"再按 Enter → 退出游戏
  ├── 点击"否" 或 按 → 选中"否"再按 Enter → 关闭覆盖层
  ├── 按 ESC → 关闭覆盖层
  └── 鼠标悬停按钮 → 按钮高亮（与键盘焦点独立）

键盘焦点与鼠标悬停互不干扰：
  - self.selected: 键盘 ← → 控制
  - hovered_index: draw() 中实时检测鼠标位置
  - is_active = (i == self.selected) or (i == hovered_index)
```

---

## [v0.4.0] - 2024-05-22

### 🏗️ 场景工厂模式重构

#### 改动说明
将场景注册逻辑从 `main.py` 抽离到独立的场景注册表模块，实现场景管理与主程序的彻底解耦。

#### 涉及文件改动

**1. 新增 `scenes/registry.py`**
```python
# scenes/registry.py
from .start_screen import StartScreen
# from .game_screen import GameScreen
# from .pause_screen import PauseScreen

SCENE_REGISTRY = {
    "START": StartScreen,
    # "GAME": GameScreen,
    # "PAUSE": PauseScreen,
}

def get_scene_class(scene_id: str):
    """根据场景ID获取场景类"""
    if scene_id not in SCENE_REGISTRY:
        raise ValueError(f"未找到场景ID: {scene_id}")
    return SCENE_REGISTRY[scene_id]
```

**2. 修改 `scene_manager.py`**
- 移除 `add_scene()` 方法
- `__init__` 改为接收 `initial_scene_id` 而非 `screen`
- `switch()` 方法改为通过 `get_scene_class()` 动态实例化场景
- 自动处理场景上下文映射

**3. 修改 `main.py`**
- 移除所有 `scene_mgr.add_scene()` 调用
- `SceneManager` 初始化改为传入初始场景ID
- 主循环更简洁，无需关心场景注册细节

#### 优势对比

| 维度 | 改造前 | 改造后 |
|:---|:---|:---|
| **main.py 行数** | 每新增场景 +2 行注册代码 | 固定不变 |
| **场景耦合度** | main.py 强依赖所有场景类 | 仅依赖 registry.py |
| **新增场景流程** | 导入 → 实例化 → 注册 (3步) | 仅需在 registry.py 注册 (1步) |
| **可测试性** | 需实例化整个 main 才能测场景 | 可单独测试场景类 |
| **配置化潜力** | 硬编码在 Python 中 | 可扩展为 JSON/YAML 配置 |

#### 新增场景示例（改造后）
```python
# 步骤1: 创建 scenes/game_screen.py
class GameScreen(Scene):
    context_alias = "GAME"  # 可选，默认与场景ID相同
    def handle_input(self, input_state):
        if "PAUSE" in input_state["global"]:
            return "PAUSE"
        return None

# 步骤2: 在 scenes/registry.py 添加一行
SCENE_REGISTRY["GAME"] = GameScreen

# ✅ 完成！无需修改 main.py 或 scene_manager.py
```

---

## [v0.3.0] - 2024-05-20

### ✨ Added
- `SceneManager`: 场景管理中枢，统一负责场景注册、状态切换与生命周期调度（`on_enter` / `on_exit`）。
- `InputManager`: 输入抽象层，将原始 `pygame.event` 映射为语义化动作（如 `CONFIRM`、`NAV_UP`），支持上下文动态切换与全局快捷键拦截。
- `scenes/base_scene.py`: 场景抽象基类，定义标准接口契约与生命周期钩子。
- 全局指令优先级：`ESC`（暂停/退出）、`F11`（全屏切换）在任何场景均优先拦截，无需重复实现。

### 🔄 Changed
- `settings.py` 严格限定为**纯静态配置**，仅保留分辨率、FPS、颜色等常量，彻底移除运行时状态。
- `main.py` 重构为管理器驱动架构，主循环精简为单帧事件投递与状态更新。
- 场景输入接口升级：`handle_event(event)` → `handle_input(input_state: dict)`。场景不再直接消费 `pygame.Event`，改为处理标准化输入字典。
- 事件流单一路径：全局仅调用一次 `pygame.event.get()`，统一交由 `InputManager` 消费，杜绝事件丢失。

### 🗑️ Removed
- 从 `settings.py` 移除 `scenes` 字典实例化逻辑、`current_scene_key` 及运行时状态变量。
- 移除场景中硬编码的 `pygame.K_*` 按键判断逻辑。

### 🐛 Fixed
- **上下文映射键名不匹配**：修复 `SceneManager.switch("START")` 与 `InputManager.context_maps` 键名不一致（原为 `"MENU"`），导致空格/回车键无响应的问题。现已对齐为 `"START"`。
- **事件重复消费**：修复多模块调用 `pygame.event.get()` 导致的事件丢失或重复触发问题。

### ⚠️ Breaking Changes / 迁移指南
| 旧实现 | 新实现 | 迁移操作 |
|:---|:---|:---|
| `def handle_event(self, event):` | `def handle_input(self, input_state: dict):` | 替换方法签名，通过 `input_state["context"]` 判断动作 |
| `if event.key == pygame.K_RETURN:` | `if "CONFIRM" in input_state["context"]:` | 移除硬编码键码，依赖 `InputManager` 映射表 |
| `settings.py` 中初始化场景 | `main.py` 中 `manager.add_scene()` | 在 `screen` 创建后手动注册场景实例 |
| 场景内直接处理 `QUIT` | 返回 `"QUIT"` 交由管理器拦截 | 场景仅返回目标场景 Key，由 `SceneManager` 统一收尾 |

> 💡 **`input_state` 结构参考**：
> ```python
> {
>   "global": ["PAUSE", ...],       # 全局快捷键动作（最高优先级）
>   "context": ["CONFIRM", ...],    # 当前场景专属语义动作
>   "held_keys": {pygame.K_UP, ...} # 当前物理按下的键码集合（用于长按/移动）
> }
> ```

### 📦 后续规划
- [ ] 手柄/多设备输入热插拔适配
- [ ] 输入缓冲队列（Input Buffer）与搓招状态机
- [ ] 键位配置外部化（`JSON` + 运行时热重载）
- [ ] 场景过渡动画（淡入淡出 / Loading 遮罩）
- [ ] UI 焦点自动导航与焦点环系统

---

## 📐 InputManager 架构设计

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        pygame.event.get()                       │
│                         (原始事件采集)                           │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                      InputManager.process_events()              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │ KEYDOWN      │ →  │ _pressed     │ →  │ _just_pressed    │  │
│  │ KEYUP        │ →  │ (持续按下)   │ →  │ (单帧触发防连点) │  │
│  └──────────────┘    └──────────────┘    └──────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                     InputManager.get_actions()                  │
│  ┌─────────────────────────┐    ┌─────────────────────────┐    │
│  │ global_map              │    │ context_maps[context]   │    │
│  │ - K_ESCAPE → PAUSE      │    │ - MENU: K_RETURN→CONFIRM│    │
│  │ - K_F11 → FULLSCREEN    │    │ - GAME: K_Z→ATTACK      │    │
│  └─────────────────────────┘    └─────────────────────────┘    │
│                              ↓                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 返回标准化输入字典 input_state                          │   │
│  │ {"global": [...], "context": [...], "held_keys": {...}} │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                    SceneManager.handle_frame()                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ 1. 优先拦截 global 动作 (PAUSE/FULLSCREEN)                │ │
│  │ 2. 传递 context 动作给当前场景                            │ │
│  │ 3. 处理场景返回的场景切换指令                             │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                   Scene.handle_input(input_state)               │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ 场景只关心语义化动作，不关心具体按键                      │ │
│  │ if "CONFIRM" in input_state["context"]: return "GAME"     │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 完整调用链示例

**场景：用户在开始菜单按回车键进入游戏**

```
时序图:

[Pygame]          [InputManager]        [SceneManager]        [StartScreen]
    │                    │                     │                    │
    │──event.get()────→ │                     │                    │
    │                    │                     │                    │
    │──KEYDOWN(K_RETURN)│                     │                    │
    │─────────────────→ │                     │                    │
    │                    │                     │                    │
    │                    │ process_events()    │                    │
    │                    │ - _pressed.add(K_RETURN)                 │
    │                    │ - _just_pressed.add(K_RETURN)            │
    │                    │                     │                    │
    │                    │ get_actions()       │                    │
    │                    │ - 查 global_map: 无匹配                  │
    │                    │ - 查 context_maps["START"]:              │
    │                    │   K_RETURN → "CONFIRM"                   │
    │                    │ - 返回 {"global":[], "context":["CONFIRM"], ...}
    │                    │──────────────────→  │                    │
    │                    │                     │                    │
    │                    │                     │ handle_input()     │
    │                    │                     │─────────────────→  │
    │                    │                     │                    │ 检查 input_state["context"]
    │                    │                     │                    │ if "CONFIRM" in context:
    │                    │                     │                    │   return "GAME"
    │                    │                     │ ←───────────────── │
    │                    │                     │                    │
    │                    │                     │ switch("GAME")     │
    │                    │                     │ - current_scene.on_exit()
    │                    │                     │ - 实例化 GameScreen
    │                    │ set_context("GAME") │ - input.set_context("GAME")
    │                    │ ←────────────────── │ - new_scene.on_enter()
    │                    │ (更新 context 映射)  │                    │
    │                    │                     │                    │
```

### 核心设计原则

1. **三层解耦**
   - **采集层**: `process_events()` 只负责收集原始按键
   - **映射层**: `get_actions()` 将键码转换为语义动作
   - **响应层**: `Scene.handle_input()` 根据动作做出业务反应

2. **上下文感知**
   - 同一按键在不同场景有不同含义（如回车在菜单是确认，在游戏中可能是互动）
   - 通过 `CONTEXT_ALIAS` 实现场景复用映射（如 PAUSE 场景复用 MENU 映射）

3. **全局优先级**
   - ESC/F11 等全局快捷键在任何场景都优先拦截
   - 场景无法覆盖全局指令，保证用户体验一致性

4. **单帧检测**
   - `_just_pressed` 集合每帧清空，防止长按重复触发
   - `_pressed` 集合保持长按状态，供持续移动等逻辑使用

5. **输入抽象**
   - 场景代码不直接依赖 pygame 键码
   - 未来扩展手柄/触摸输入时，只需修改 InputManager，场景代码零改动