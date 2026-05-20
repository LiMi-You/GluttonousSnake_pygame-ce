# GluttonousSnake_pygame-ce
这是一个基于Python语言的贪吃蛇
<br><br><br>
当前版本Ver2.0项目的目录结构
```text
my_pygame_game/
│
├── main.py              # 🚪 游戏入口：只做初始化、主循环、状态切换
├── scene_manager.py     # 场景管理器（核心）
├── input_manager.py     # 输入中枢（核心）
├── settings.py          # ⚙️ 配置中心：屏幕大小、颜色、速度、字体路径等（杜绝魔法数字）、仅存纯配置常量
├── assets/              # 🎨 所有资源（统一放这里，代码里用相对路径加载）
│   ├── images/          #   .png, .jpg, .gif
│   │   └── start_bg.png
│   ├── sounds/          #   .wav, .ogg, .mp3
│   └── fonts/           #   .ttf, .otf
├── scenes/              # 游戏场景资源
│   ├── __init__.py
│   ├── base_scene.py
│   └── start_screen.py
├── entities/            # 👾 游戏实体：玩家、敌人、子弹、道具等（每个文件一个类）
│   ├── __init__.py      #   留空，让 Python 知道这是个包
│   ├── player.py
│   └── enemy.py
│
├── utils/               # 🛠️ 工具函数：碰撞检测、分数计算、资源加载器等
│   ├── __init__.py
│   └── helpers.py
│
└── README.md            # 📝 项目说明 & 开发笔记
```

[项目Ver3.0版本更新说明](docs/CHANGELOG.md)