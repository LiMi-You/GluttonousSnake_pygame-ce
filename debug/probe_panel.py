"""
debug/probe_panel.py — 探针 UI 面板

在游戏窗口右侧绘制半透明调试面板，展示所有探针数据。
支持折叠区块、F1 切换显隐。
"""
from __future__ import annotations
import pygame
from typing import Any

from .probe_core import DebugProbe

# ── 面板布局常量 ──
PANEL_WIDTH = 300
PANEL_PADDING = 10
SECTION_HEADER_H = 22
LINE_H = 16
SECTION_GAP = 6

# ── 颜色 ──
CLR_PANEL_BG = (18, 18, 24, 210)
CLR_HEADER = (100, 200, 255)
CLR_KEY = (160, 160, 180)
CLR_VALUE = (240, 240, 240)
CLR_ACCENT = (255, 200, 80)
CLR_COLLISION_WARN = (255, 100, 100)
CLR_SECTION_BG = (30, 30, 40, 120)
_CLR_SECTION_BG = CLR_SECTION_BG


class ProbePanel:
    """探针侧边面板"""

    def __init__(self, screen_width: int, screen_height: int, probe: DebugProbe):
        self.screen_w = screen_width
        self.screen_h = screen_height
        self.probe = probe

        # 面板位置：游戏区域右侧
        self.panel_x = screen_width - PANEL_WIDTH
        self.panel_y = 0
        self.panel_rect = pygame.Rect(self.panel_x, self.panel_y, PANEL_WIDTH, screen_height)

        # 字体
        self._font_header = pygame.font.SysFont("Consolas", 14, bold=True)
        self._font_body = pygame.font.SysFont("Consolas", 13)
        self._font_title = pygame.font.SysFont("Consolas", 15, bold=True)

        # 区块折叠状态：{section_key: bool}  True = 展开
        self._sections: dict[str, bool] = {
            "snake": True,
            "npcs": True,
            "items": True,
            "weights": True,
            "collision": True,
            "performance": True,
            "stats": True,
        }

        # 滚动偏移
        self._scroll_y: int = 0
        self._max_scroll: int = 0

    # ── 公开接口 ──

    def scroll(self, delta: int):
        """滚动面板内容"""
        self._scroll_y = max(0, min(self._max_scroll, self._scroll_y - delta))

    def resize(self, width: int, height: int):
        """窗口大小改变时更新"""
        self.screen_w = width
        self.screen_h = height
        self.panel_x = 0  # 独立窗口中 x=0
        self.panel_rect = pygame.Rect(0, 0, width, height)

    def draw(self, screen: pygame.Surface):
        """绘制探针面板"""
        if not self.probe.enabled:
            return

        snapshot = self.probe.get_snapshot()

        # 计算总内容高度（用于滚动限制）
        total_h = self._calc_content_height(snapshot)
        self._max_scroll = max(0, total_h - self.screen_h + 40)

        # 设置裁剪区域（滚动生效）
        clip_rect = pygame.Rect(0, 0, self.screen_w, self.screen_h)
        screen.set_clip(clip_rect)

        # 绘制标题（固定在顶部）
        y = PANEL_PADDING - self._scroll_y
        y = self._draw_title(screen, y)

        # 各区块
        y = self._draw_section(screen, "snake", "Player Snake", y, snapshot, self._format_snake)
        y = self._draw_section(screen, "npcs", f"NPCs", y, snapshot, self._format_npcs)
        y = self._draw_section(screen, "items", "Items", y, snapshot, self._format_items)
        y = self._draw_section(screen, "weights", "Weight Calc", y, snapshot, self._format_weights)
        y = self._draw_section(screen, "collision", "Collision", y, snapshot, self._format_collision)
        y = self._draw_section(screen, "performance", "Performance", y, snapshot, self._format_performance)
        y = self._draw_section(screen, "stats", "Stats", y, snapshot, self._format_stats)

        # 取消裁剪
        screen.set_clip(None)

        # 滚动指示器
        if self._max_scroll > 0:
            self._draw_scroll_indicator(screen)

    # ── 内部：标题 ──

    def _draw_title(self, screen: pygame.Surface, y: int) -> int:
        text = self._font_title.render("[F1] DEBUG PROBE", True, CLR_HEADER)
        screen.blit(text, (PANEL_PADDING, y))
        return y + SECTION_HEADER_H + 4

    # ── 内部：滚动指示器 ──

    def _draw_scroll_indicator(self, screen: pygame.Surface):
        """绘制右侧滚动条"""
        bar_x = self.screen_w - 8
        bar_h = max(30, int(self.screen_h * self.screen_h / (self.screen_h + self._max_scroll)))
        bar_y = int(self._scroll_y / self._max_scroll * (self.screen_h - bar_h))
        bar_rect = pygame.Rect(bar_x, bar_y, 6, bar_h)
        pygame.draw.rect(screen, (80, 80, 100), bar_rect, border_radius=3)

    # ── 内部：计算内容高度 ──

    def _calc_content_height(self, snapshot: dict) -> int:
        """计算所有区块的总高度"""
        h = SECTION_HEADER_H + 4  # 标题
        for key, title, formatter in [
            ("snake", "Player Snake", self._format_snake),
            ("npcs", "NPCs", self._format_npcs),
            ("items", "Items", self._format_items),
            ("weights", "Weight Calc", self._format_weights),
            ("collision", "Collision", self._format_collision),
            ("performance", "Performance", self._format_performance),
            ("stats", "Stats", self._format_stats),
        ]:
            is_expanded = self._sections.get(key, True)
            lines = formatter(snapshot) if is_expanded else []
            h += SECTION_HEADER_H + (len(lines) * LINE_H if is_expanded else 0) + SECTION_GAP
        return h

    # ── 内部：通用区块 ──

    def _draw_section(
        self,
        screen: pygame.Surface,
        key: str,
        title: str,
        y: int,
        snapshot: dict,
        formatter: callable,
    ) -> int:
        is_expanded = self._sections.get(key, True)
        lines = formatter(snapshot) if is_expanded else []

        # 区块背景
        total_h = SECTION_HEADER_H + (len(lines) * LINE_H if is_expanded else 0) + SECTION_GAP
        bg = pygame.Surface((self.screen_w - 4, total_h), pygame.SRCALPHA)
        bg.fill(_CLR_SECTION_BG)
        screen.blit(bg, (2, y))

        # 区块标题
        arrow = "▼" if is_expanded else "▶"
        count_hint = self._count_hint(key, snapshot)
        header_text = f"{arrow} {title}{count_hint}"
        header_surf = self._font_header.render(header_text, True, CLR_ACCENT)
        screen.blit(header_surf, (PANEL_PADDING, y))
        y += SECTION_HEADER_H

        # 内容行
        if is_expanded:
            for label, value, color in lines:
                label_surf = self._font_body.render(f"  {label}: ", True, CLR_KEY)
                val_surf = self._font_body.render(str(value), True, color)
                screen.blit(label_surf, (PANEL_PADDING, y))
                screen.blit(val_surf, (PANEL_PADDING + label_surf.get_width(), y))
                y += LINE_H

        y += SECTION_GAP
        return y

    def _count_hint(self, key: str, snapshot: dict) -> str:
        if key == "npcs":
            data = snapshot.get("npcs", {})
            alive = data.get("alive_count", 0)
            total = data.get("total_count", 0)
            return f" ({alive}/{total})"
        if key == "items":
            data = snapshot.get("items", {})
            total = data.get("total", 0)
            return f" ({total})"
        return ""

    # ── 内部：格式化各区块数据 ──

    def _format_snake(self, snap: dict) -> list[tuple[str, str, tuple]]:
        s = snap.get("snake", {})
        DIR_MAP = {(0, -1): "UP", (0, 1): "DOWN", (-1, 0): "LEFT", (1, 0): "RIGHT"}
        head = s.get("head", (0, 0))
        cur_dir = tuple(s.get("current_direction", (0, 0)))
        nxt_dir = tuple(s.get("next_direction", (0, 0)))
        return [
            ("Head", f"{head}", CLR_VALUE),
            ("Dir(cur)", DIR_MAP.get(cur_dir, str(cur_dir)), CLR_VALUE),
            ("Dir(next)", DIR_MAP.get(nxt_dir, str(nxt_dir)), CLR_VALUE),
            ("Length", str(s.get("length", 0)), CLR_VALUE),
            ("MoveAcc", f"{s.get('move_accumulator', 0)} ms", CLR_VALUE),
            ("JustAte", str(s.get("just_ate", False)), CLR_VALUE),
            ("Body[0:5]", str(s.get("body_preview", [])), CLR_KEY),
        ]

    def _format_npcs(self, snap: dict) -> list[tuple[str, str, tuple]]:
        data = snap.get("npcs", {})
        lines: list[tuple[str, str, tuple]] = []
        lines.append(("Alive", str(data.get("alive_count", 0)), CLR_VALUE))
        lines.append(("Total", str(data.get("total_count", 0)), CLR_VALUE))

        for npc in data.get("list", []):
            state_color = CLR_VALUE
            state = npc.get("state", "")
            if state == "DEAD":
                state_color = CLR_COLLISION_WARN
            elif state == "UNFOLDING":
                state_color = CLR_ACCENT

            header = f"#{npc.get('index', '?')} {npc.get('type', '?')}"
            lines.append((header, f"{state} len={npc.get('length', 0)}", state_color))
            lines.append(
                ("  Head", f"{npc.get('head', (0,0))} dir={npc.get('direction', (0,0))}", CLR_KEY)
            )
        return lines

    def _format_items(self, snap: dict) -> list[tuple[str, str, tuple]]:
        data = snap.get("items", {})
        lines: list[tuple[str, str, tuple]] = []
        lines.append(("Total", str(data.get("total", 0)), CLR_VALUE))
        lines.append(("SpawnAcc", f"{data.get('spawn_accumulator', 0)} ms", CLR_VALUE))

        for item_type, count in data.get("by_type", {}).items():
            lines.append((f"  {item_type}", str(count), CLR_VALUE))

        # 权重快照
        weights = data.get("weight_snapshot", {})
        if weights:
            lines.append(("─ Weights", "─", CLR_KEY))
            for wid, wval in weights.items():
                lines.append((f"  {wid}", f"{wval:.1f}", CLR_ACCENT))

        # 移动道具
        moving = data.get("moving_items", [])
        if moving:
            lines.append(("─ Moving", "─", CLR_KEY))
            for m in moving[:5]:
                lines.append(
                    (f"  {m.get('id', '?')}",
                     f"f({m.get('fx', 0):.1f},{m.get('fy', 0):.1f}) dir={m.get('dir', (0,0))}",
                     CLR_KEY)
                )
            if len(moving) > 5:
                lines.append(("  ...", f"+{len(moving)-5} more", CLR_KEY))
        return lines

    def _format_weights(self, snap: dict) -> list[tuple[str, str, tuple]]:
        data = snap.get("weights", {})
        lines: list[tuple[str, str, tuple]] = []
        lines.append(("Score", str(data.get("score", 0)), CLR_ACCENT))
        lines.append(("SnakeLen", str(data.get("snake_len", 0)), CLR_VALUE))

        phases = data.get("active_phases", [])
        if phases:
            lines.append(("Phases", ", ".join(phases), CLR_VALUE))
        else:
            lines.append(("Phases", "NONE", CLR_COLLISION_WARN))

        cats = data.get("allowed_cats", [])
        lines.append(("AllowCats", ", ".join(cats) if cats else "NONE", CLR_KEY))

        mult = data.get("merged_mult", {})
        if mult:
            for cat, m in mult.items():
                lines.append((f"  Mult:{cat}", f"x{m}", CLR_ACCENT))

        details = data.get("weight_details", [])
        if details:
            lines.append(("─ Detail", "─", CLR_KEY))
            for d in details:
                item_id = d.get("id", "?")
                base = d.get("base", 0)
                count_m = d.get("count_mod", 0)
                len_m = d.get("len_mod", 0)
                score_m = d.get("score_mod", 0)
                cat_m = d.get("cat_mult", 0)
                final = d.get("final", 0)
                on_scr = d.get("on_screen", 0)
                max_s = d.get("max", 0)
                lines.append((
                    f"  {item_id}",
                    f"w={final} (base={base} x{count_m:.2f} x{len_m:.2f} x{score_m:.2f} x{cat_m:.1f}) [{on_scr}/{max_s}]",
                    CLR_VALUE,
                ))
        else:
            lines.append(("  (no allowed items)", "", CLR_KEY))

        return lines

    def _format_collision(self, snap: dict) -> list[tuple[str, str, tuple]]:
        data = snap.get("collision", {})
        lines: list[tuple[str, str, tuple]] = []
        lines.append(("Occupied", str(data.get("occupied_cells", 0)), CLR_VALUE))

        history = self.probe.get_collision_history()
        if history:
            recent = history[-3:]
            for ev in reversed(recent):
                lines.append(("Event", f"{ev.subject}→{ev.target} @{ev.pos}", CLR_COLLISION_WARN))
        else:
            lines.append(("Last", "NONE", CLR_KEY))
        return lines

    def _format_performance(self, snap: dict) -> list[tuple[str, str, tuple]]:
        fps = self.probe.get_fps()
        frame_ms = self.probe.get_frame_ms()
        fps_color = CLR_VALUE if fps >= 55 else (CLR_ACCENT if fps >= 30 else CLR_COLLISION_WARN)
        return [
            ("FPS", f"{fps:.1f}", fps_color),
            ("Frame", f"{frame_ms:.1f} ms", CLR_VALUE),
            ("Tick", str(self.probe.tick_count), CLR_KEY),
        ]

    def _format_stats(self, snap: dict) -> list[tuple[str, str, tuple]]:
        data = snap.get("stats", {})
        score = data.get("score", 0)
        combo = data.get("combo", 0)
        max_combo = data.get("max_combo", 0)
        time_ms = data.get("play_time_ms", 0)
        secs = time_ms // 1000
        mins = secs // 60
        secs = secs % 60

        items_collected = data.get("items_collected", {})
        lines: list[tuple[str, str, tuple]] = [
            ("Score", str(score), CLR_ACCENT),
            ("Combo", f"{combo} (max {max_combo})", CLR_VALUE),
            ("Time", f"{mins:02d}:{secs:02d}", CLR_VALUE),
            ("SnakeLen", str(data.get("snake_length", 0)), CLR_VALUE),
        ]
        for item_id, count in items_collected.items():
            lines.append((f"  collected:{item_id}", str(count), CLR_KEY))
        return lines

    # ── 内部：页脚 ──

    def _draw_footer(self, screen: pygame.Surface):
        tip = self._font_body.render("F1: toggle | scroll: not yet", True, CLR_KEY)
        screen.blit(tip, (self.panel_x + PANEL_PADDING, self.screen_h - 24))
