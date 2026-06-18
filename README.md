# 🐍 GluttonousSnake — 贪吃蛇大作战

> 一个基于 **pygame-ce** 构建的现代贪吃蛇游戏，拥有完整的场景系统、道具系统、NPC 蛇 AI 子系统与动态难度机制。

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![pygame-ce](https://img.shields.io/badge/pygame--ce-2.5.7-purple?logo=pygame)
![版本](https://img.shields.io/badge/版本-v0.8.1-orange)
![状态](https://img.shields.io/badge/状态-开发完成-brightgreen)

---

## 📖 简介

**GluttonousSnake** 是一个功能丰富的贪吃蛇游戏，从经典玩法出发，逐步扩展出：

- 多种**AI 蛇**同场竞技（觅食、追击、游走、混合策略）
- 动态**道具系统**（基础食物、稀有移动道具、难度阶段解锁）
- 智能**权重驱动生成**（根据场上数量、蛇长、分数动态调整）
- 完整的**游戏流程**（开始→大厅→加载→游戏→制作人员）
- 平滑的**分数滚动动画**、**连击系统**、**退出覆盖层**

> 项目虽小，"五脏俱全"——从架构设计到细节打磨，尽力做到了力所能及的最好。

---

## ✨ 核心特性

### 🎮 游戏玩法
| 特性 | 说明 |
|:---|---|
| **经典贪吃蛇** | 方向控制、吃食物增长、撞墙/撞己/撞NPC即死 |
| **分数倍率** | 蛇越长得分越高（`倍率 = 1.0 + (长度−3) × 0.1`） |
| **连击系统** | 2 秒内连续吃道具触发连击，结算时显示最大连击数 |
| **分数滚动动画** | 数码管风格 15 位零填充，加分后 2 秒内平滑滚动 |
| **退出确认覆盖层** | ESC 弹出半透明确认框，支持键盘/鼠标操作 |

### 🧠 NPC 蛇子系统（5 种 AI 类型）
| 类型 | 颜色 | 行为 | 掉落 |
|:---|---:|:---|:---:|
| 🟣 **StandardSnake** 标准蛇 | `#7148ff` | 随机行走 | 无 |
| 🟪 **ForagingSnake** 觅食蛇 | `#fe22ff` | 贪心接近附近道具 | 3 个食物 |
| ⚫ **LootSnake** 战利品蛇 | `#22233e` | 混合模式：15% 贪心 + 85% 随机 | 6 个（含稀有） |
| ⚪ **MythicSnake** 神话蛇 | `#bafffe` | 大范围游走，低转向概率 | 10 个（含稀有） |
| 🔴 **HunterSnake** 猎手蛇 | `#ff1c50` | BFS 最短路径追击玩家 | 5 个食物 |

- **障碍规避**：所有 NPC 共享前瞻碰撞检测与方向评分系统
- **渐进式出生**：蛇头先出现，逐步展开至完整长度
- **死亡掉落**：沿蛇身均匀分布掉落道具，稀有道具受场上上限约束

### 🎁 道具系统
| 道具 | 分类 | 分值 | 特性 |
|:---|---:|---:|:---|
| 🍎 **普通食物** `score_boost` | 基础 | 1000 | 最常见，场上最多 30 个 |
| ✨ **幸运食物** `lucky_patrol_food` | 稀有 | 5000 | 自动在 4×4 区域内随机移动，场上最多 3 个 |

- **动态权重引擎**：场上数量压制、蛇长因子、分数因子共同调节生成概率
- **3 阶段难度**：前期(基本食物为主)→中期(解锁全部)→后期(障碍/减益权重↑)

### 🏗️ 架构设计
| 模块 | 职责 |
|:---|---|
| `scene_manager.py` | 场景生命周期管理 + 工厂注册表模式 |
| `input_manager.py` | 上下文感知的按键映射系统（支持按住时长检测） |
| `items/` | 道具定义 → 实例化 → 权重生成 → 碰撞处理 |
| `entities/npc/` | NPC 实体 → 出生管理 → AI 导航 → 碰撞管理 |
| `utils/stats_manager.py` | 统计数据单一数据源（分数/长度/连击） |

---

## 🚀 快速开始

### 环境要求

- **Python** ≥ 3.10
- **pygame-ce** ≥ 2.5.7

### 安装

```bash
# 1. 克隆或进入项目目录
cd GluttonousSnake_pygame-ce

# 2. （推荐）创建虚拟环境
python -m venv .venv

# 3. 激活虚拟环境
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

# 4. 安装依赖
pip install -r requirements.txt
```

### 运行

```bash
python main.py
```

---

## 🎮 操作说明

| 操作 | 按键 |
|:---|---|
| **移动** | ⬆ ⬇ ⬅ ➡ 方向键 |
| **确认/开始** | `Enter` / `Space` |
| **退出游戏** | `ESC`（弹出确认框） |
| **全屏切换** | `F11` |
| **Credits 退出** | 长按 `R` 键 2.5 秒 |
| **鼠标** | 开始/制作人按钮点击、退出覆盖层点击 |

---

## 📁 项目结构

```
GluttonousSnake_pygame-ce/
├── main.py                  # 🚪 游戏入口
├── scene_manager.py         # 🎬 场景管理器（核心）
├── input_manager.py         # ⌨️ 输入中枢（核心）
├── quit_overlay.py          # 🚪 退出确认覆盖层
├── settings.py              # ⚙️ 配置中心
│
├── assets/                  # 🎨 资源文件
│   ├── images/              #   .png 图片
│   ├── sounds/              #   .mp3, .wav 音效
│   ├── media/               #   .mp4 视频
│   └── fonts/               #   .ttf, .otf 字体
│
├── scenes/                  # 🎬 游戏场景
│   ├── base_scene.py        #     场景基类
│   ├── registry.py          #     工厂注册表
│   ├── start_screen.py      #     开始界面
│   ├── lobby_screen.py      #     大厅界面
│   ├── loading_screen.py    #     加载过渡
│   ├── game_screen.py       #     🎯 游戏主场景
│   └── credits_scene.py     #     制作人员名单
│
├── entities/                # 👾 游戏实体
│   ├── player.py            #     玩家贪吃蛇
│   └── npc/                 #     🤖 NPC 子系统
│       ├── npc_types.py     #       类型定义（5种）
│       ├── npc_base.py      #       NPC蛇实体基类
│       ├── spawn_manager.py #       出生管理器
│       ├── collision_manager.py #   碰撞管理器
│       ├── npc_manager.py   #       管理器总控
│       └── navigation/      #       🧭 导航策略
│           ├── base_strategy.py
│           ├── obstacle_avoidance.py # 障碍规避
│           ├── random_walk.py        # 随机行走
│           ├── greedy_item.py        # 贪心道具
│           ├── chase_player.py       # BFS追击
│           ├── wander.py             # 游走
│           └── hybrid.py             # 混合模式
│
├── items/                   # 🎁 道具系统
│   ├── item_defs.py         #     道具定义表
│   ├── item_base.py         #     道具实例基类
│   ├── item_manager.py      #     道具管理器
│   ├── difficulty_phases.py #     📊 难度阶段
│   └── weight_calculator.py #     ⚖️ 动态权重引擎
│
├── utils/                   # 🛠️ 工具模块
│   ├── helpers.py           #     12方向向量 + 工具函数
│   ├── stats_manager.py     #     📈 统计管理器
│   └── video_player.py      #     🎬 视频播放器
│
└── docs/
    ├── CHANGELOG.md          # 📋 更新日志
    └── CHANGELOG_OLD.md
```

---

## 🧭 游戏流程

```
START ──→ LOBBY ──→ LOAD ──→ GAME
  │                              │
  └── CREDITS ←──────────────────┘
       （视频播放 + 长按R退出）
```

1. **START** — 开始界面，选择「开始游戏」或「制作人」
2. **LOBBY** — 大厅，点击「开始游戏」
3. **LOAD** — 加载过渡（随机 3~5 秒），自动进入游戏
4. **GAME** — 🎯 游戏主场景，操控贪吃蛇吃食物、躲避 NPC 蛇
5. **CREDITS** — 播放制作人员视频，鼠标移动显示跳过提示，长按 R 退出

---

## 🧩 技术栈

| 技术 | 用途 |
|:---|---|
| **Python 3.10+** | 编程语言 |
| **pygame-ce 2.5.7** | 游戏框架（社区版，pygame 的现代化分支） |
| **BFS 寻路** | HunterSnake 追击玩家的路径规划 |
| **Lerp 插值** | 分数滚动动画平滑过渡 |
| **轮盘赌算法** | 道具加权随机生成 |
| **工厂 + 注册表模式** | 场景动态创建与扩展 |

---

## ⚠️ 已知不足 / 未来方向

> 项目主体已完成，以下为开发过程中识别但未解决的改进项，留作备忘供后续参考：

- **道具系统不完善** — 目前只注册了 2 种道具（基础食物 + 幸运食物），`CAT_BUFF`/`CAT_DEBUFF`/`CAT_OBSTACLE` 分类尚未实现具体功能（加速/减速/障碍物/清场等）
- **NPC 设计不合理** — 5 种 NPC 的行为差异化不够明显，部分参数未充分调优
- **Buff 系统缺失** — 蛇的时效性效果管理未实现，无法支持增益/减益状态
- **道具拾取反馈** — 缺少拾取音效与视觉特效
- **音效资源** — 部分音效文件可能不完整或未测试
- **平衡性** — NPC 出生频率、道具权重、分数倍率等参数未经充分游戏测试

---

## 📜 更新历史

各版本的详细变更记录请参见 [`docs/CHANGELOG.md`](docs/CHANGELOG.md)。

| 版本 | 日期 | 亮点 |
|:---|---:|:---|
| v0.8.1 | 2026-06-17 | 🎬 Credits 交互增强、Loading 过渡、分数滚动动画、帧框架场景切换 |
| v0.8.0 | 2026-06-07 | 🤖 NPC 蛇子系统完整交付（5种 AI + 导航策略 + 碰撞管理 + 死亡掉落） |
| v0.7.0 | 2026-06-07 | ⚖️ 动态权重系统、难度阶段、可移动道具子系统 |
| v0.6.0 | 2026-06-03 | 🎁 道具系统基础设施、统计管理器 |
| v0.5.0 | 2024-05-25 | 🚪 退出确认覆盖层、鼠标事件支持 |
| v0.4.0 | 2024-05-22 | 🏗️ 场景工厂模式重构 |

---

## 📄 许可证

本项目仅供学习交流使用。

---

## 🙏 致谢

- [pygame-ce](https://github.com/pygame-community/pygame-ce) — 社区驱动的 pygame 分支
- [Smiley Sans](https://github.com/atelier-anchor/Smiley-Sans) — 字体
- [DS-Digital](https://www.dafont.com/ds-digital.font) — 数码管字体
- [Keep a Changelog](https://keepachangelog.com/) — 更新日志格式规范