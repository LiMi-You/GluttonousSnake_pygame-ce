# GluttonousSnake_pygame-ce
这是一个基于Python语言的贪吃蛇
<br><br><br>
当前版本Ver2.0项目的目录结构
```text
GluttonousSnake_pygame-ce/
│
├── main.py              # 🚪 游戏入口：只做初始化、主循环、状态切换
├── scene_manager.py     # 场景管理器（核心）
├── input_manager.py     # 输入中枢（核心）
├── quit_overlay.py      # 退出确认覆盖层
├── settings.py          # ⚙️ 配置中心
├── assets/              # 🎨 所有资源
│   ├── images/          #   .png
│   │   ├── score_boost.png
│   │   ├── start_bg.png
│   │   └── ...
│   ├── sounds/          #   .mp3, .wav
│   └── fonts/           #   .ttf, .otf
├── items/               # 🎁 道具系统（v0.6.0 新增）
│   ├── __init__.py
│   ├── item_defs.py     # 道具定义表
│   ├── item_base.py     # 道具实例基类
│   └── item_manager.py  # 道具管理器
├── scenes/              # 🎬 游戏场景
│   ├── __init__.py
│   ├── registry.py      # 场景工厂注册表
│   ├── base_scene.py    # 场景基类
│   ├── start_screen.py  # 开始页
│   ├── lobby_screen.py  # 大厅页
│   └── game_screen.py   # 游戏主场景
├── entities/            # 👾 游戏实体
│   ├── __init__.py
│   ├── player.py        # 贪吃蛇
│   └── enemy.py         # （预留）
├── utils/               # 🛠️ 工具模块
│   ├── __init__.py
│   ├── stats_manager.py # 统计管理器（v0.6.0 新增）
│   └── helpers.py
├── docs/              
│   ├── CHANGELOG.md
│   └── CHANGELOG_OLD.md
│
└── README.md            # 📝 项目说明
```

[项目Ver4.0版本更新说明](docs/CHANGELOG.md)