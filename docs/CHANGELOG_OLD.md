# CHANGELOG

所有对该项目的显著更改都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
本项目遵循 [语义化版本规范](https://semver.org/spec/v2.0.0.html)。

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
