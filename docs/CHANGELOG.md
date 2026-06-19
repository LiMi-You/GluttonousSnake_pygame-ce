--- docs/CHANGELOG.md (原始)
# CHANGELOG

所有对该项目的显著更改都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
本项目遵循 [语义化版本规范](https://semver.org/spec/v2.0.0.html)。

---

## [v0.9.0] - 2026-06-19

### ✨ Added — 调试探针系统（Debug Probe）

#### 涉及文件

| 文件 | 操作 |
|:---|:---|
| `debug/__init__.py` | **新增** — 探针模块包导出 |
| `debug/probe_core.py` | **新增** — 数据收集核心（回调注册、快照、碰撞历史、FPS计算） |
| `debug/probe_panel.py` | **新增** — UI面板（7个可折叠区块、鼠标滚轮滚动、窗口缩放适配） |
| `debug/probe_window.py` | **新增** — 独立pygame窗口（位置记忆、10fps限频刷新） |
| `input_manager.py` | **修改** — 添加 F1 → `TOGGLE_DEBUG` 映射 |
| `scene_manager.py` | **修改** — 创建 `ProbeWindow`，分发窗口事件 |
| `scenes/game_screen.py` | **修改** — 注册探针收集器，每帧 `tick()` 驱动数据收集 |
| `scenes/base_scene.py` | **修改** — `__init__` 接受 `**kwargs`（兼容探针注入） |
| `scenes/start_screen.py` | **修改** — `__init__` 接受 `**kwargs` |
| `scenes/lobby_screen.py` | **修改** — `__init__` 接受 `**kwargs` |
| `scenes/credits_scene.py` | **修改** — `__init__` 接受 `**kwargs` |
| `scenes/loading_screen.py` | **修改** — `__init__` 接受 `**kwargs` |

#### 功能说明

**按 F1 打开/关闭独立探针窗口**，显示游戏运行时的全部隐藏数据：

| 区块 | 数据内容 |
|:---|:---|
| Player Snake | 蛇头位置、当前/下一方向、长度、移动累加器、是否刚吃、身体预览 |
| NPCs | 存活/总数、每条蛇的类型、状态(UNFOLDING/ACTIVE/DEAD)、位置、方向 |
| Items | 场上总数、生成计时器、按类型分组、移动道具位置和方向 |
| Weight Calc | 分数、蛇长、当前阶段、允许分类、各修正因子、每个道具的详细权重 |
| Collision | 占据格子数、最近碰撞事件历史 |
| Performance | FPS（颜色编码）、帧耗时、总tick数 |
| Stats | 分数、连击、游戏时长、蛇长、已收集道具统计 |

#### 权重计算显示详情

每个道具显示完整的权重计算过程：
```
score_boost: w=87 (base=100 x0.91 x1.00 x0.10 x1.0) [9/30]
              │       │      │      │      │       │
              │       │      │      │      │       └─ [场上数/上限]
              │       │      │      │      └─ 阶段倍率
              │       │      │      └─ 分数因子（幸运/增益类在100k分前×0.1）
              │       │      └─ 蛇长因子
              │       └─ 场上数量压制（1 - (当前/上限)²）
              └─ 最终权重
```

#### 窗口特性

- **独立pygame.Window**：不影响游戏窗口，可自由拖动
- **位置记忆**：关闭后重新打开恢复上次位置
- **鼠标滚轮滚动**：数据超出窗口高度时可滚动查看
- **10fps限频**：不浪费性能，数据实时性足够

#### 架构

```
GameScreen.update()
  → probe_core.tick()        # 收集各模块数据到snapshot

ProbeWindow.update()          # 独立于游戏的10fps刷新
  → probe_panel.draw(surface) # 从snapshot读取并渲染
  → window.flip()             # 刷新探针窗口
```

---

## [v0.8.0] - 2026-06-07

### ✨ Added — NPC蛇子系统（Phase 1-6 完整交付）

#### 涉及文件

| 文件 | 操作 |
|:---|:---|
| `entities/npc/__init__.py` | **新增** — NPC子系统包导出 |
| `entities/npc/npc_types.py` | **新增** — NPC类型定义（`NPCTypeDef`数据类 + 5种NPC注册） |
| `entities/npc/npc_base.py` | **新增** — NPCSnake实体基类（渐进式出生 + 生命周期状态机） |
| `entities/npc/spawn_manager.py` | **新增** — 出生管理器（安全区域选址 + 渐进式创建） |
| `entities/npc/collision_manager.py` | **新增** — 碰撞管理器（全局占据图 + 碰撞预判） |
| `entities/npc/npc_manager.py` | **新增** — NPC管理器总控（生命周期 + 死亡掉落 + GameScreen集成入口） |
| `entities/npc/navigation/__init__.py` | **新增** — 导航子系统 + 策略工厂 `create_strategy()` |
| `entities/npc/navigation/base_strategy.py` | **新增** — `NavContext`上下文 + `NavigationStrategy`抽象接口 |
| `entities/npc/navigation/obstacle_avoidance.py` | **新增** — 共享障碍规避组件（方向过滤/优先级排序/前瞻检测） |
| `entities/npc/navigation/random_walk.py` | **新增** — `RandomWalkStrategy`（StandardSnake） |
| `entities/npc/navigation/greedy_item.py` | **新增** — `GreedyItemStrategy`（ForagingSnake） |
| `entities/npc/navigation/chase_player.py` | **新增** — `ChasePlayerStrategy` BFS追击（HunterSnake） |
| `entities/npc/navigation/wander.py` | **新增** — `WanderStrategy` 大范围游走（MythicSnake） |
| `entities/npc/navigation/hybrid.py` | **新增** — `HybridStrategy` 混合模式（LootSnake） |
| `entities/__init__.py` | **修改** — 导出 `Snake` |
| `scenes/game_screen.py` | **修改** — 集成 `NPCManager`（出生/更新/碰撞/渲染） |
| `items/item_defs.py` | **修改** — `score_boost.max_on_screen` 1→30（支持NPC掉落） |
| `items/item_manager.py` | **修改** — `_spawn_one()` 新增 `occupied_cells` 参数 + 掉落位置验证 |

#### NPC蛇类型一览

| 类型ID | 名称 | 颜色 | 长度 | 掉落 | 拾取道具 | 导航策略 |
|:---|:---|:---|:---|:---|:---|:---|
| `standard` | 标准蛇 | `#7148ff` | 3-6 | 无 | 否 | RandomWalk |
| `foraging` | 觅食蛇 | `#fe22ff` | 15 | 3个 | 是(60%) | GreedyItem |
| `loot` | 战利品蛇 | `#22233e` | 25-40 | 6个(混稀有) | 是(15%) | Hybrid |
| `mythic` | 神话蛇 | `#bafffe` | 35-50 | 10个(混稀有) | 否 | Wander |
| `hunter` | 猎手蛇 | `#ff1c50` | 25 | 5个 | 否 | ChasePlayer(BFS) |

#### 四大基础能力

**1. 出生管理 (`SpawnManager`)**
- **安全区域选址**：200次随机采样，验证候选点满足：
  - 未被玩家/NPC/障碍物占据
  - 至少2个方向有2格畅通空间
  - 周围区域（半径≈蛇长/2+3）占用率<35%
- **智能方向选择**：按连续空闲格数+远离玩家方向评分
- **渐进式出生**：`NPCSnake`初始仅含蛇头（`body=[head_pos]`），每步移动增长1格，直到达到目标长度后自动切换为`ACTIVE`
- 状态机：`UNFOLDING → ACTIVE → DEAD`

**2. 移动障碍规避 (`ObstacleAvoidance`)**
- `filter_safe_directions()` — 过滤掉前方有障碍的方向（委托CollisionManager）
- `pick_best_direction()` — 优先级：偏好方向 > 当前方向 > 随机 > 反向
- `lookahead_clear()` — 前瞻检测（看前方N格是否畅通）
- `direction_toward()` — 计算从head指向target的偏好方向

**3. 路径导航规划 (5种可插拔策略)**
- `RandomWalkStrategy` — 20%随机转向 + 保持方向 + 障碍规避
- `GreedyItemStrategy` — 曼哈顿距离12格内扫描最近道具，贪心接近
- `ChasePlayerStrategy` — BFS最短路径寻路（最大深度40格），每3步重算
- `WanderStrategy` — 低转向概率(8%) + 前瞻3格提前偏转
- `HybridStrategy` — 15%概率切换贪心模式，持续5-12步后恢复随机

**4. 碰撞管理 (`CollisionManager`)**
- 每帧重建全局占据图（player + npc:xxx + obstacle）
- `check_move()` — 单步碰撞预判，返回`CollisionType`枚举（SAFE/HIT_WALL/HIT_SELF/HIT_PLAYER_BODY/HIT_NPC_BODY）
- `get_safe_directions()` — 返回所有安全移动方向
- 玩家碰撞：`GameScreen._game_step()`中预判玩家新蛇头是否进入NPC身体

#### 出生配置

| 参数 | 值 |
|:---|:---|
| 初始出生数量 | 2只（仅StandardSnake） |
| 周期性出生间隔 | 8-15秒随机 |
| 场上最大NPC数 | 8只 |
| 周期性出生权重 | standard:40, foraging:25, loot:15, hunter:15, mythic:5 |

#### 死亡掉落（Phase 6 完整交付）

- **掉落条件**：`has_drops=False`的NPC（StandardSnake）不掉落，其余按 `drop_count` 配置掉落
- **掉落类型混合**：
  - 低掉落量（≤5，ForagingSnake/HunterSnake）：全部掉落 `score_boost`
  - 高掉落量（≥6，LootSnake/MythicSnake）：每隔1个混入 `lucky_patrol_food`（稀有移动道具）
- **掉落位置**：沿蛇身均匀分布（循环取模），自动去重避免同一格重复掉落
- **边界安全**：仅掉落界内位置（防御性过滤），掉落位置冲突时自动搜索附近空闲格
- **上限尊重**：`lucky_patrol_food.max_on_screen=3` 达到上限后自动跳过
- `score_boost.max_on_screen` 由 1→30 以支持大量掉落

#### 架构：NPC子系统模块关系

```
GameScreen
  └─ NPCManager（总控）
       ├─ SpawnManager        ← 出生管理
       │    └─ NPCSnake       ← 实体（UNFOLDING→ACTIVE→DEAD）
       ├─ CollisionManager    ← 每帧占据图 + 碰撞预判
       │    ├─ Player body
       │    └─ NPC bodies
       ├─ NavigationSystem    ← AI决策
       │    ├─ RandomWalkStrategy   (StandardSnake)
       │    ├─ GreedyItemStrategy   (ForagingSnake)
       │    ├─ ChasePlayerStrategy  (HunterSnake, BFS)
       │    ├─ WanderStrategy       (MythicSnake)
       │    └─ HybridStrategy       (LootSnake)
       │         └─ ObstacleAvoidance（共享组件）
       ├─ ItemManager         ← 道具交互（拾取/掉落）
       └─ 死亡掉落             ← _handle_death_drops()
```

#### 帧更新流程

```
NPCManager.update(player_body, items, delta_ms)
  1. CollisionManager.rebuild()        ← 重建占据图
  2. 周期性出生计时器                   ← 8-15s间隔
  3. for each NPC:
       accumulate delta_ms
       while accumulator >= move_interval:
         a. strategy.next_direction()  ← AI决策
         b. collision_mgr.check_move() ← 碰撞预判
         c. if SAFE: npc.move()       ← 执行移动
         d. check_npc_item_pickup()   ← 拾取道具(可选)
         e. if COLLISION: npc.kill()  ← 标记死亡
  4. _cleanup_dead() → _handle_death_drops() ← 清理+掉落
```

#### 项目结构变化

```
GluttonousSnake_pygame-ce/
├── entities/
│   ├── __init__.py              # 修改 — 导出 Snake
│   ├── player.py                # 玩家蛇（原有，不变）
│   ├── enemy.py                 # （保留，已被 npc/ 替代）
│   └── npc/                     # ← 新增包
│       ├── __init__.py           # 包导出
│       ├── npc_types.py          # NPC类型定义 + 枚举
│       ├── npc_base.py           # NPCSnake实体基类
│       ├── spawn_manager.py      # 出生管理器
│       ├── collision_manager.py  # 碰撞管理器
│       ├── npc_manager.py        # NPC管理器总控
│       └── navigation/           # ← 导航子系统
│           ├── __init__.py
│           ├── base_strategy.py
│           ├── obstacle_avoidance.py
│           ├── random_walk.py
│           ├── greedy_item.py
│           ├── chase_player.py
│           ├── wander.py
│           └── hybrid.py
├── items/
│   ├── item_defs.py             # 修改 — score_boost max_on_screen 1→30
│   └── item_manager.py          # 修改 — _spawn_one 支持位置验证
└── scenes/
    └── game_screen.py           # 修改 — 集成 NPCManager
```

---

## [v0.7.0] - 2026-06-07

### ✨ Added — 动态权重系统 & 可移动道具子系统

#### 涉及文件

| 文件 | 操作 |
|:---|:---|
| `items/difficulty_phases.py` | **新增** — 难度阶段系统（`DifficultyPhase` 数据类 + 3 阶段配置表 + 查询函数） |
| `items/weight_calculator.py` | **新增** — 动态权重计算引擎（3 个修正因子 + 轮盘赌选择） |
| `utils/helpers.py` | **新建** — 12 方向向量表（钟表方向）+ 随机方向选取 + 范围检测 |
| `items/item_defs.py` | **修改** — 增加分类标签（5 类）、移动字段（4 个）、注册 `LuckyPatrolFoot` |
| `items/item_base.py` | **重构** — `grid_x`/`grid_y` 改为属性；新增 `fx`/`fy` 小数坐标层 + 移动状态 |
| `items/item_manager.py` | **扩展** — 权重驱动生成、可移动道具更新、全场清理、生成边界约束 |
| `scenes/game_screen.py` | **修改** — 传递 `score`/`snake_length` 给权重引擎；道具平滑渲染 |
| `settings.py` | **修改** — 新增阶段阈值常量 + 移动速度常量 |

#### 改动详情

**1. 道具分类系统（`item_defs.py`）**
- `ItemDef` 新增 `category` 字段，5 种分类常量：`CAT_BASIC`、`CAT_LUCKY`、`CAT_BUFF`、`CAT_DEBUFF`、`CAT_OBSTACLE`
- 注册第二个道具类型 `lucky_patrol_food`（LuckyPatrolFoot）：
  - 分类 `CAT_LUCKY`，占格 1×1，权重 15，同时上限 3，分值 5000
  - 移动配置：`move_range=4`（4×4 格圆形区域），`move_speed=1`，12 方向随机转向

**2. 难度阶段系统（`items/difficulty_phases.py`）**
- `DifficultyPhase` 数据类：`min_score`、`min_length`、`allowed_categories`、`weight_multipliers`
- 3 阶段配置（叠加模式——所有满足条件的阶段同时生效）：

| 阶段 | 条件 | 允许分类 | 倍率调整 |
|:---|:---|:---|:---|
| 前期 | 分数 < 100k | basic + lucky | lucky 由 score_modifier 压制到 0.1× |
| 中期 | 分数 ≥ 100k | 全部 5 类 | 无额外倍率 |
| 后期 | 蛇长 ≥ 20 | 全部 5 类 | obstacle ×1.5, debuff ×1.3 |

- 查询函数：`get_active_phases()`、`get_allowed_categories()`、`merge_multipliers()`、`get_allowed_item_ids()`

**3. 动态权重引擎（`items/weight_calculator.py`）**
- `build_weight_table()` — 根据当前游戏状态实时计算每个道具的有效权重
- 3 个修正因子：
  - **场上数量压制** `calc_screen_count_modifier()`：`1 − (current/max)²`（平方衰减）
  - **蛇长因子** `calc_length_modifier()`：长蛇 → 障碍物/减益权重↑，幸运类权重↓
  - **分数因子** `calc_score_modifier()`：100k 分前稀有类 ×0.1，之后线性增长至 ×2.0
- `pick_item_by_weight()` — 轮盘赌算法加权随机选择
- `build_weight_table` 接受 `item_defs` 显式参数（依赖可追溯）

**4. 移动道具子系统**
- **12 方向向量表**（`utils/helpers.py`）：360° 等分 12 份，预计算 12 个单位向量
- `get_random_direction()` / `get_new_direction()` — 随机/非重复方向选取
- `is_within_range()` — 圆形区域范围检测
- **`ItemInstance` 重构**（`items/item_base.py`）：
  - `fx`/`fy`（小数格坐标）作为位置主源，`grid_x`/`grid_y` 改为实时计算属性
  - 新增 `move_dir`、`move_dir_idx`、`spawn_origin` 移动状态字段
- **`ItemManager._update_moving_items()`**（`item_manager.py`）：
  - 每帧独立更新（不受蛇步频限制），支持 `dt_ms` 帧率归一化
  - 范围约束：超出 `move_range` → 随机换方向 + 钳制回边界
  - 全场反弹：已预置 `move_bounce` 逻辑（供未来 `UniqueBouncingLuckyProp` 使用）
- **平滑渲染**（`game_screen.py`）：`_draw_items()` 使用 `fx`/`fy` 计算像素位置，移动道具不再一跳一格

**5. 全场清理接口**
- `ItemManager.clear_all_items(exclude_ids)` — 支持选择性保留的道具清场（供 LuckyClearBlock 等使用）

**6. 生成边界越界修复**
- `_find_valid_position()` 新增 `move_range` 参数：生成时可移动道具的位置被约束在安全区域内，确保圆形移动范围完全在地图内
- `move_range=4`（half=2，整数无小数）→ 有效生成区域 25×21（地图 29×25）

#### 架构：权重驱动的道具生成流程

```
GameScreen.update()
  └─ ItemManager.update(score, snake_length)
       ├─ _update_moving_items(dt_ms)     ← 可移动道具独立运动
       └─ _spawn_weighted(score, length)  ← 权重驱动生成
            ├─ get_active_phases()        → 确定当前阶段
            ├─ get_allowed_item_ids()     → 从阶段获取允许的道具列表
            ├─ build_weight_table()       → 动态权重计算
            │    ├─ base_weight
            │    ├─ calc_screen_count_modifier()
            │    ├─ calc_length_modifier()
            │    ├─ calc_score_modifier()
            │    └─ phase_multipliers
            └─ pick_item_by_weight()      → 轮盘赌选择
                 └─ _spawn_one()          → 生成（含边界约束）
```

#### 项目结构变化

```
GluttonousSnake_pygame-ce/
├── items/
│   ├── __init__.py
│   ├── item_defs.py                    # 修改 — 分类标签 + 移动字段 + LuckyPatrolFoot
│   ├── item_base.py                    # 重构 — 小数坐标层 + 移动状态
│   ├── item_manager.py                 # 扩展 — 权重引擎 + 移动更新 + 清场 + 边界约束
│   ├── difficulty_phases.py            # ← 新增 — 难度阶段系统
│   └── weight_calculator.py            # ← 新增 — 动态权重计算引擎
├── utils/
│   ├── __init__.py
│   ├── stats_manager.py
│   └── helpers.py                      # ← 新建 — 12方向向量 + 移动工具函数
├── scenes/
│   └── game_screen.py                  # 修改 — 传递游戏状态 + 平滑渲染
└── settings.py                         # 修改 — 新增阶段阈值 + 移动速度常量
```

#### 后续规划
- [x] 道具权重系统（动态调整、阶段解锁、安全区）
- [ ] 多类型道具功能实现（加速/减速/障碍物/清场等）
- [ ] 蛇的 Buff 系统（时效性效果管理，为 LuckyClearBlock 准备）
- [x] NPC 系统集成（NPC 死亡掉落基础食物） → 见 v0.8.0
- [ ] 道具拾取音效与视觉反馈

---

## [v0.6.0] - 2026-06-03

### ✨ Added — 道具系统基础设施 & 统计管理器

#### 涉及文件

| 文件 | 操作 |
|:---|:---|
| `items/item_defs.py` | **新增** — 道具定义表（`ItemDef` 数据类 + `ITEM_DEFS` 注册表） |
| `items/item_base.py` | **新增** — 道具实例基类（`ItemInstance`，位置/占格/碰撞检测） |
| `items/item_manager.py` | **新增** — 道具管理器（生成计时、空闲位置查找、蛇头碰撞检测） |
| `items/__init__.py` | **新增** — 道具系统包导出 |
| `utils/stats_manager.py` | **新增** — 统计管理器（分数/蛇长/连击/收集计数） |
| `utils/__init__.py` | **修改** — 导出 `StatsManager` |
| `settings.py` | **修改** — 新增道具系统常量（`ITEM_RENDER_SIZE`、`ITEM_SPAWN_INTERVAL` 等） |
| `scenes/game_screen.py` | **修改** — 集成 `ItemManager` + `StatsManager`，移除旧食物系统 |

#### 改动详情

**1. 道具系统（`items/` 包）**
- `ItemDef` 数据类：定义道具类型配置（ID、名称、占格大小、权重、颜色、分数值、图片资源）
- `ItemInstance` 实例类：表示地图上的一个具体道具，提供 `contains()` 和 `occupied_cells` 属性
- `ItemManager` 管理器：
  - 基于计时器的自动生成机制（`ITEM_SPAWN_INTERVAL = 2000ms`）
  - 初始生成数量控制（`ITEM_BASE_SPAWN_COUNT = 3`）
  - 场上总量上限（`ITEM_MAX_ON_SCREEN = 8`）
  - 单类型上限（基于 `max_on_screen`）
  - `_find_valid_position()` —— 多格道具的空闲矩形区域查找（最多 50 次尝试）
  - `check_collision()` —— 蛇头与道具的碰撞检测（基于坐标包含判断）
- 当前仅注册 `score_boost`（基础食物），为后续多类型扩展留好接口

**2. 道具图片渲染**
- `_load_item_images()` —— 预加载 `assets/images/` 下的道具图片，统一缩放到 `ITEM_RENDER_SIZE = 23px`
- `_draw_items()` —— 使用预加载图片居中绘制每个道具，图片缺失时使用纯色圆点兜底

**3. 统计管理器（`utils/stats_manager.py`）**
- `StatsManager` 类作为游戏数据的单一数据源，`GameScreen` 写入，未来 UI 模块通过只读接口查询
- 核心数据：`score`（分数）、`snake_length`（蛇长）、`combo`（连击）、`items_collected`（收集计数）
- `add_score()` —— 自动应用蛇长倍率（`1.0 + (len - 3) × 0.1`），蛇越长得分越高
- `on_item_collected()` —— 基于 2 秒窗口的连击管理，超时则重置
- `get_all_stats()` —— 一次性返回全部数据供结算/存档

**4. 游戏场景集成**
- `GameScreen.__init__()` —— 以 `StatsManager` 替换 `self.score`，新增 `ItemManager` 实例
- `_reset_game()` —— 重置道具管理器 + 统计管理器，启动计时器
- `update()` —— 每帧更新道具生成，步进后同步蛇长到统计模块
- `_game_step()` —— 蛇头碰撞检测改为委托 `ItemManager.check_collision()`
- `_apply_item_effect()` —— 统一道具效果入口，当前仅加分和统计记录
- `_draw_score()` —— 显示"得分 + 蛇长"
- `_draw_game_over()` —— 显示"最终得分 + 最大连击"

#### 架构对比

| 维度 | 改造前（v0.5.0） | 改造后（v0.6.0） |
|:---|:---|:---|
| **食物生成** | `_spawn_food()` 单点随机 | `ItemManager` 计时驱动，支持多类型扩展 |
| **碰撞检测** | `new_head == self.food` 坐标等值判断 | `ItemManager.check_collision()` 基于区域包含 |
| **分数管理** | `self.score` 孤立整数 | `StatsManager` 集中管理，自带倍率计算 |
| **UI 查询** | 无接口，直接读 `self.score` | 只读 getter 接口，UI 模块可注入 `StatsManager` |
| **图片渲染** | 纯色圆点（`pygame.draw.circle`） | 预加载 `score_boost.png`（23×23px 居中绘制） |
| **蛇长显示** | 不显示 | HUD 显示"得分 + 长度" |
| **连击系统** | 无 | 2 秒窗口连击，结算时显示最大连击 |

#### 项目结构变化

```
GluttonousSnake_pygame-ce/
├── items/                          # ← 新增包
│   ├── __init__.py                 # 包导出
│   ├── item_defs.py                # 道具定义表
│   ├── item_base.py                # 道具实例基类
│   └── item_manager.py             # 道具管理器
├── utils/                          # ← 扩展
│   ├── __init__.py                 # 导出 StatsManager
│   └── stats_manager.py            # 新增 — 统计管理器
├── scenes/
│   └── game_screen.py              # 修改 — 集成新系统
└── settings.py                     # 修改 — 新增道具常量

assets/images/
├── score_boost.png                 # ← 新增 — 基础食物图片
└── ...
```

#### 后续规划
- [ ] 道具权重系统（动态调整、阶段解锁、安全区）
- [ ] 多类型道具注册（加速/减速/无敌/大餐等）
- [ ] 蛇的 buff 系统（时效性效果管理）
- [ ] 分数 UI 模块（独立 HUD 组件）
- [ ] 道具拾取音效与视觉反馈

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