# 调试面板设计与实现报告

> 版本: v2.0 | 日期: 2026-06-22 | 作者: MiMoCode

## 目录

1. [概述](#1-概述)
2. [架构总览](#2-架构总览)
3. [核心模块详解](#3-核心模块详解)
   - 3.1 [DebugProbe — 数据收集核心](#31-debugprobe--数据收集核心)
   - 3.2 [NPCManager — 运行时控制层](#32-npcmanager--运行时控制层)
   - 3.3 [ProbePanel — imgui 即时模式 UI](#33-probepanel--imgui-即时模式-ui)
   - 3.4 [ProbeWindow — 独立 OpenGL 窗口](#34-probewindow--独立-opengl-窗口)
4. [数据流架构](#4-数据流架构)
5. [NPC 控制功能详解](#5-npc-控制功能详解)
6. [imgui 集成原理](#6-imgui-集成原理)
7. [已知限制与后续改进](#7-已知限制与后续改进)

---

## 1. 概述

本报告详细说明贪吃蛇项目中 NPC 调试面板的实现原理。调试面板使用 Dear ImGui (pyimgui) 作为 UI 框架，运行在独立的 OpenGL 窗口中，提供对 NPC 子系统的实时监控和运行时控制能力。

### 核心能力

- **实时数据展示**: NPC 数量、状态、位置、移动参数等
- **运行时控制**: 开关生成、冻结移动、调节速度、手动生成功能
- **类型配置展示**: 各 NPC 类型的颜色、长度、掉落、导航策略等
- **权重池调节**: 实时修改各 NPC 类型的生成权重

---

## 2. 架构总览

```
┌─────────────────────────────────────────────────────────┐
│                     main.py 主循环                       │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ SceneManager │  │ ProbeWindow  │  │  GameScreen   │  │
│  │              │──│  (OpenGL)    │  │  (Pygame)     │  │
│  │  handle_frame│  │  update()    │  │  npc_manager  │  │
│  └──────┬───────┘  └──────┬───────┘  └───────┬───────┘  │
│         │                 │                  │           │
│         ▼                 ▼                  ▼           │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ DebugProbe   │  │ ProbePanel   │  │  NPCManager   │  │
│  │ (数据收集)    │  │ (imgui UI)   │  │ (运行时控制)   │  │
│  └──────────────┘  └──────────────┘  └───────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 组件职责

| 组件 | 文件 | 职责 |
|------|------|------|
| `DebugProbe` | `debug/probe_core.py` | 维护数据收集回调注册表，每帧刷新快照 |
| `ProbeWindow` | `debug/probe_window.py` | 管理独立 OpenGL 窗口生命周期，驱动 imgui 渲染 |
| `ProbePanel` | `debug/probe_panel.py` | 用 imgui 即时模式绘制所有 UI 控件 |
| `NPCManager` | `entities/npc/npc_manager.py` | NPC 生命周期管理，暴露运行时控制接口 |
| `GameScreen` | `scenes/game_screen.py` | 注册探针数据收集回调，持有 npc_manager 引用 |

---

## 3. 核心模块详解

### 3.1 DebugProbe — 数据收集核心

**文件**: `debug/probe_core.py`

#### 设计原理

DebugProbe 采用**观察者模式**的变体：各模块注册数据收集回调（collector），Probe 每帧调用所有回调并缓存快照。

```python
class DebugProbe:
    def __init__(self):
        self._collectors: dict[str, Callable[[], dict]] = {}
        self._snapshot: dict[str, Any] = {}
        self._collision_history: deque[CollisionEvent] = deque(maxlen=30)
        self._tick: int = 0
        self._frame_times: deque[float] = deque(maxlen=120)

    def register(self, key: str, collector: Callable[[], dict]):
        """注册数据收集回调"""
        self._collectors[key] = collector

    def tick(self):
        """每帧调用，刷新快照"""
        self._tick += 1
        now = time.perf_counter()
        self._frame_times.append(now - self._last_frame_time)
        self._last_frame_time = now

        snapshot = {}
        for key, collector in self._collectors.items():
            try:
                snapshot[key] = collector()
            except Exception as e:
                snapshot[key] = {"error": str(e)}
        self._snapshot = snapshot
```

#### 关键设计决策

1. **回调注册制**: 各模块（如 GameScreen）调用 `probe.register("snake", collect_snake)` 注册数据源，Probe 不需要知道具体数据结构
2. **快照缓存**: `tick()` 每帧调用一次，结果缓存在 `_snapshot` 中，UI 层只读取快照，不直接访问游戏状态
3. **异常隔离**: 单个 collector 抛异常不会影响其他数据收集
4. **性能计数**: 使用 `deque(maxlen=120)` 保留最近 120 帧的时间数据，用于 FPS 和帧耗时计算

#### 碰撞历史

```python
@dataclass
class CollisionEvent:
    tick: int              # 发生时的帧号
    subject: str           # 碰撞主体（如 "player"）
    target: str            # 碰撞目标（如 "wall", "npc:standard"）
    pos: tuple[int, int]   # 碰撞位置（网格坐标）
```

碰撞事件通过 `record_collision()` 记录，由 `GameScreen._game_step()` 在检测到碰撞时调用。环形缓冲区限制最多保留 30 条记录。

---

### 3.2 NPCManager — 运行时控制层

**文件**: `entities/npc/npc_manager.py`

#### 类常量 → 实例变量

原始设计中，NPC 出生配置是类常量（`INITIAL_SPAWN_COUNT = 2` 等），运行时无法修改。重构后改为实例变量，支持调试面板实时调节：

```python
class NPCManager:
    def __init__(self, item_manager=None, event_bus=None):
        # ── 出生配置（实例变量，支持运行时修改）──
        self.spawn_enabled: bool = True
        self.initial_spawn_count: int = 2
        self.spawn_interval_min: int = 8000
        self.spawn_interval_max: int = 15000
        self.max_npcs: int = 8
        self.initial_spawn_types: list[str] = ["standard"]

        # 周期性生成权重（可运行时调整）
        self.periodic_spawn_pool: dict[str, int] = {
            "standard": 40, "foraging": 25, "loot": 15,
            "mythic": 5, "hunter": 15,
        }

        # 运行时控制
        self.frozen: bool = False
        self.speed_multiplier: float = 1.0
```

#### 运行时控制接口

```python
def debug_spawn(self, npc_type_id: str, player_body: list) -> bool:
    """手动生成指定类型的NPC（调试用）"""
    if len(self.npcs) >= self.max_npcs:
        return False
    npc = self._try_spawn_npc(npc_type_id, player_body)
    return npc is not None

def debug_kill_all(self):
    """杀死所有NPC（调试用）"""
    for npc in self.npcs:
        if npc.is_alive:
            npc.kill()
```

#### 出生逻辑中的控制检查

```python
def update(self, player_body, active_items, delta_ms, obstacles=None):
    # 2. 周期性出生
    if self.spawn_enabled:  # ← 出生开关检查
        self._spawn_timer += delta_ms
        if self._spawn_timer >= self._next_spawn_interval:
            self._spawn_timer = 0
            self._next_spawn_interval = self._random_spawn_interval()
            if len(self.npcs) < self.max_npcs:  # ← 使用实例变量
                npc_type_id = self._weighted_random_type()
                if npc_type_id:
                    self._try_spawn_npc(npc_type_id, player_body)

    # 3. 更新每个NPC
    for npc in self.npcs:
        if not npc.is_alive:
            continue
        if self.frozen:  # ← 冻结检查
            continue

        npc._move_accumulator += delta_ms
        interval = int(npc.move_interval_ms / self.speed_multiplier)  # ← 速度倍率
```

---

### 3.3 ProbePanel — imgui 即时模式 UI

**文件**: `debug/probe_panel.py`

#### 即时模式 vs 保留模式

imgui 使用**即时模式（Immediate Mode）**：每帧重新描述一遍 UI 结构，框架自动处理交互状态。

```python
# 即时模式：每帧执行，imgui 自动判断点击、悬停等
if imgui.button("Kill All NPCs"):
    mgr.debug_kill_all()

# 保留模式（如 React/Vue）：创建一次，后续修改
<button onClick={killAll}>Kill All</button>
```

即时模式的优势：
- **零状态管理**: 不需要 `visible`、`disabled` 等状态变量
- **代码即 UI**: UI 结构和业务逻辑在同一段代码中
- **自动交互**: 按钮点击、滑块拖动、复选框切换都由框架处理

#### 控件映射

| imgui 控件 | 用途 | 示例 |
|-----------|------|------|
| `imgui.checkbox(label, value)` | 开关控制 | Spawn Enabled, Freeze All |
| `imgui.slider_int(label, val, min, max)` | 整数范围调节 | Max NPCs, Spawn Interval |
| `imgui.slider_float(label, val, min, max)` | 浮点范围调节 | Speed Multiplier |
| `imgui.button(label)` | 点击操作 | Kill All, Spawn standard |
| `imgui.tree_node(label)` | 可折叠区域 | NPC Controls, Type Configs |
| `imgui.progress_bar(value)` | 进度显示 | Spawn Timer |
| `imgui.text(label)` | 只读文本 | FPS, NPC 状态信息 |

#### NPC Controls 区块结构

```
NPC Controls (折叠树)
├── Spawn Config
│   ├── [checkbox] Spawn Enabled
│   ├── [slider] Initial Count (0~10)
│   ├── [slider] Max NPCs (1~20)
│   ├── [slider] Interval Min (1000~30000 ms)
│   └── [slider] Interval Max (1000~30000 ms)
├── Runtime
│   ├── [checkbox] Freeze All NPC
│   ├── [slider] Speed Multiplier (0.1~5.0)
│   └── [button] Kill All NPCs
├── Spawn Timer
│   └── [progress bar] Timer / Next Interval
├── Manual Spawn
│   ├── [button] Spawn standard
│   ├── [button] Spawn foraging
│   ├── [button] Spawn loot
│   ├── [button] Spawn mythic
│   └── [button] Spawn hunter
├── Type Configs (只读)
│   ├── 标准蛇 (standard)
│   ├── 觅食蛇 (foraging)
│   ├── 战利品蛇 (loot)
│   ├── 神话蛇 (mythic)
│   └── 猎手蛇 (hunter)
└── Spawn Pool Weights
    ├── [slider] standard (0~100)
    ├── [slider] foraging (0~100)
    ├── [slider] loot (0~100)
    ├── [slider] mythic (0~100)
    └── [slider] hunter (0~100)
```

#### 数据绑定方式

imgui 控件直接读写 NPCManager 的实例变量：

```python
# checkbox 直接修改 mgr.spawn_enabled
_, mgr.spawn_enabled = imgui.checkbox("Spawn Enabled", mgr.spawn_enabled)

# slider 直接修改 mgr.max_npcs
_, mgr.max_npcs = imgui.slider_int("Max NPCs", mgr.max_npcs, 1, 20)
```

imgui 的 `checkbox` 和 `slider_*` 返回 `(changed, new_value)` 元组。第一个值表示用户是否拖动了控件，第二个值是新值。直接赋值给 `mgr.xxx` 即可生效。

---

### 3.4 ProbeWindow — 独立 OpenGL 窗口

**文件**: `debug/probe_window.py`

#### 窗口创建

使用 `pygame.window.Window` 创建独立的 OpenGL 窗口：

```python
self._window = pygame.window.Window(
    size=(WINDOW_WIDTH, WINDOW_HEIGHT),
    title=WINDOW_TITLE,
    opengl=True,
    resizable=True
)
```

#### imgui 上下文管理

```python
def __init__(self, ...):
    # imgui context 只创建一次（生命周期跟进程）
    imgui.create_context()
```

**关键决策**: `imgui.create_context()` 放在 `__init__` 而非 `_open()`，避免多次开关窗口时重复创建 context 导致内存泄漏。

#### 渲染循环

```python
def update(self, current_time: int):
    # 1. 处理输入
    self._renderer.process_inputs()

    # 2. 开始新帧
    imgui.new_frame()

    # 3. 绘制面板（描述 UI 结构）
    self._panel.draw()

    # 4. OpenGL 渲染
    glClearColor(0.07, 0.07, 0.09, 1.0)
    glClear(GL_COLOR_BUFFER_BIT)

    imgui.render()
    self._renderer.render(imgui.get_draw_data())

    self._window.flip()
```

#### 事件过滤（防联动）

```python
def handle_event(self, event):
    if not self.enabled or not self._window:
        return

    # 只处理属于当前窗口的事件
    if hasattr(event, 'window') and event.window != self._window:
        return

    # 拦截 VIDEORESIZE：不传给 renderer（它会调用 pygame.display.set_mode 改变主窗口）
    if event.type == pygame.VIDEORESIZE:
        io = imgui.get_io()
        io.display_size = (event.w, event.h)
        return

    if self._renderer:
        self._renderer.process_event(event)
```

**问题与修复**: PygameRenderer 的 `process_event` 处理 `VIDEORESIZE` 事件时会调用 `pygame.display.set_mode()`，这操作的是主显示器（游戏窗口），导致探针窗口 resize 时游戏窗口也跟着变。修复方案是拦截 `VIDEORESIZE` 事件，不传给 renderer。

---

## 4. 数据流架构

### 4.1 数据收集流程

```
GameScreen.update()
    │
    ├── npc_manager.update()          ← NPC 逻辑更新
    │
    └── debug_probe.tick()            ← 刷新快照
            │
            ├── collector["snake"]()  ← 读取 snake 状态
            ├── collector["npcs"]()   ← 读取 npc_manager 状态
            ├── collector["items"]()  ← 读取 item_manager 状态
            ├── collector["collision"]()
            ├── collector["stats"]()
            └── collector["weights"]()
                    │
                    ▼
            probe._snapshot = {...}   ← 缓存快照
```

### 4.2 UI 渲染流程

```
main.py 主循环
    │
    ├── scene_mgr.handle_frame(events)
    │       └── probe_window.handle_event(event)  ← 事件过滤 + imgui 输入
    │
    └── scene_mgr.probe_window.update(ticks)      ← 限频 10fps
            │
            ├── renderer.process_inputs()
            ├── imgui.new_frame()
            ├── panel.draw()
            │       ├── snapshot = probe.get_snapshot()  ← 读取快照
            │       ├── _draw_npc_controls(snapshot)     ← 绘制控件
            │       │       └── imgui.slider_int(...)    ← 直接修改 npc_manager
            │       └── _draw_npcs(snapshot)             ← 绘制 NPC 列表
            ├── imgui.render()
            └── renderer.render(draw_data)
```

### 4.3 控制流（UI → 游戏）

```
用户拖动 imgui 滑块
    │
    ▼
ProbePanel._draw_npc_controls()
    └── _, mgr.max_npcs = imgui.slider_int("Max NPCs", mgr.max_npcs, 1, 20)
            │
            ▼
NPCManager.max_npcs = 新值
            │
            ▼
下次 NPCManager.update() 时
    └── if len(self.npcs) < self.max_npcs:  ← 使用新值
            └── self._try_spawn_npc(...)
```

---

## 5. NPC 控制功能详解

### 5.1 出生控制 (Spawn Config)

| 控件 | 绑定变量 | 范围 | 效果 |
|------|----------|------|------|
| Spawn Enabled | `mgr.spawn_enabled` | bool | 关闭后停止所有 NPC 生成 |
| Initial Count | `mgr.initial_spawn_count` | 0~10 | 游戏开始时生成的 NPC 数量 |
| Max NPCs | `mgr.max_npcs` | 1~20 | 场上同时存在的最大 NPC 数 |
| Interval Min | `mgr.spawn_interval_min` | 1000~30000 ms | 两次生成之间的最小间隔 |
| Interval Max | `mgr.spawn_interval_max` | 1000~30000 ms | 两次生成之间的最大间隔 |

### 5.2 运行时控制 (Runtime)

| 控件 | 绑定变量 | 效果 |
|------|----------|------|
| Freeze All NPC | `mgr.frozen` | 冻结所有 NPC 移动（AI 仍运行但不步进） |
| Speed Multiplier | `mgr.speed_multiplier` | 全局速度倍率（影响所有 NPC 的移动间隔） |
| Kill All NPCs | `mgr.debug_kill_all()` | 一键杀死所有 NPC，触发死亡掉落 |

### 5.3 手动生成 (Manual Spawn)

每个 NPC 类型一个按钮，调用 `mgr.debug_spawn(type_id, player_body)`。成功生成后 NPC 从 UNFOLDING 状态开始渐进式展开。

### 5.4 权重池调节 (Spawn Pool Weights)

每种 NPC 类型一个 slider（0~100），直接修改 `mgr.periodic_spawn_pool[type_id]`。下次 `_weighted_random_type()` 被调用时自动使用新权重。

### 5.5 类型配置展示 (Type Configs)

只读展示 `NPC_TYPE_DEFS` 中各类型的关键参数：
- 长度范围 (min_length ~ max_length)
- 移动间隔 (move_interval_ms)
- 掉落配置 (has_drops, drop_count)
- 拾取能力 (can_pickup, pickup_chance)
- 导航策略 (nav_strategy)
- 颜色 (color)

---

## 6. imgui 集成原理

### 6.1 安装

```bash
pip install imgui[pygame]  # 需要 Python 3.8~3.13 和预编译 wheel
pip install PyOpenGL       # OpenGL 绑定
```

### 6.2 初始化流程

```python
import imgui
from imgui.integrations.pygame import PygameRenderer

# 1. 创建 imgui 上下文（全局单例，只创建一次）
imgui.create_context()

# 2. 创建 Pygame 渲染器
renderer = PygameRenderer()

# 3. 设置显示尺寸
io = imgui.get_io()
io.display_size = (width, height)
```

### 6.3 每帧渲染

```python
# 1. 处理输入
renderer.process_inputs()

# 2. 开始新帧
imgui.new_frame()

# 3. 描述 UI（即时模式，每帧重新执行）
imgui.begin("Window Title", True)  # True = 可关闭
imgui.text("Hello")
if imgui.button("Click"):
    do_something()
imgui.end()

# 4. 渲染到 OpenGL
imgui.render()
renderer.render(imgui.get_draw_data())
```

### 6.4 关键 API

| API | 说明 |
|-----|------|
| `imgui.begin(title, open)` | 开始一个窗口，返回 `(expanded, open)` |
| `imgui.end()` | 结束当前窗口 |
| `imgui.tree_node(label)` | 开始折叠节点，返回 `bool`（是否展开） |
| `imgui.tree_pop()` | 结束折叠节点 |
| `imgui.text(text)` | 显示文本 |
| `imgui.checkbox(label, val)` | 复选框，返回 `(changed, new_val)` |
| `imgui.slider_int(label, val, min, max)` | 整数滑块 |
| `imgui.slider_float(label, val, min, max, fmt)` | 浮点滑块 |
| `imgui.button(label)` | 按钮，返回 `bool`（是否点击） |
| `imgui.progress_bar(value, size, overlay)` | 进度条 |
| `imgui.separator()` | 分隔线 |
| `imgui.same_line()` | 同行显示下一个控件 |

---

## 7. 已知限制与后续改进

### 当前限制

1. **NPC 类型配置不可运行时修改**: `NPC_TYPE_DEFS` 是全局字典，修改会影响所有实例。如需支持运行时修改类型参数，需要引入实例级别的类型配置覆盖。
2. **SpawnManager 参数未暴露**: `MAX_SPAWN_ATTEMPTS`、`MIN_CLEAR_DIRECTIONS` 等选址参数仍是类常量，未加入控制面板。
3. **导航策略不可运行时切换**: NPC 的导航策略在创建时确定，运行时无法动态切换。

### 后续改进方向

1. **NPC 类型配置编辑器**: 允许在面板中修改各类型的长度、速度、掉落等参数
2. **出生位置可视化**: 在游戏画面上标记 NPC 的出生位置和安全区域
3. **导航路径可视化**: 显示 AI 的决策路径和安全方向
4. **碰撞热力图**: 可视化场上碰撞高频区域
5. **性能分析**: 添加每个子系统的耗时统计

---

## 附录：文件变更清单

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `debug/probe_core.py` | 修改 | 删除未使用的 `field` 导入和 `_scalars` 收集逻辑 |
| `debug/probe_panel.py` | 重写 | 添加 Player Controls + NPC Controls 独立窗口，集成 DebugConfig |
| `debug/probe_window.py` | 修改 | 添加 npc_manager/snake/config 引用，修复 VIDEORESIZE 联动 |
| `debug/debug_config.py` | 新建 | JSON 配置持久化（PlayerConfig, NpcConfig, DisplayConfig） |
| `debug/__init__.py` | 修改 | 导出 DebugConfig |
| `entities/player.py` | 修改 | 添加 invincible/god_mode/_speed_multiplier 调试标志 |
| `entities/npc/npc_manager.py` | 重构 | 类常量改为实例变量，添加 frozen/speed_multiplier/debug_spawn/debug_kill_all |
| `scenes/game_screen.py` | 修改 | 扩展 collect_npcs 数据，碰撞检测支持 invincible/god_mode |
| `scene_manager.py` | 修改 | 加载 DebugConfig，传递 npc_manager/snake 给 ProbeWindow |
| `.gitignore` | 修改 | 添加 imgui.ini, debug_config.json |
