import pygame
from typing import Callable, List, Tuple


class Toolbar:
    """
    右侧工具栏：颜色调色板 + 画笔大小选择 + 功能按钮（清空/橡皮）。

    通过回调与外部交互：
    - on_color(color)
    - on_brush(size)
    - on_mode(mode)  # "draw" / "erase"
    - on_clear()
    """

    def __init__(
        self,
        rect: pygame.Rect,
        colors: List[Tuple[int, int, int]],
        sizes: List[int],
        font_name: str | None = None,
    ) -> None:
        self.rect = rect
        self.colors = colors
        self.sizes = sizes
        self.on_color: Callable[[Tuple[int, int, int]], None] | None = None
        self.on_brush: Callable[[int], None] | None = None
        self.on_mode: Callable[[str], None] | None = None
        self.on_clear: Callable[[], None] | None = None
        try:
            self.font = pygame.font.SysFont(font_name or None, 18)
        except Exception:
            self.font = pygame.font.SysFont(None, 18)
        self._current_mode = "draw"

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not self.rect.collidepoint(event.pos):
                return
            lx, ly = event.pos[0] - self.rect.x, event.pos[1] - self.rect.y
            # 计算点击区域：顶部颜色块、居中画笔大小、底部按钮
            # 顶部颜色区域
            pad = 8
            swatch_size = 28
            cols_per_row = max(1, (self.rect.width - pad * 2) // (swatch_size + 6))
            rows = (len(self.colors) + cols_per_row - 1) // cols_per_row
            color_area_h = rows * (swatch_size + 6) + pad
            # 判断颜色点击
            cx, cy = pad, pad
            idx = 0
            for r in range(rows):
                for c in range(cols_per_row):
                    if idx >= len(self.colors):
                        break
                    rect = pygame.Rect(cx, cy, swatch_size, swatch_size)
                    if rect.collidepoint(lx, ly):
                        if self.on_color:
                            self.on_color(self.colors[idx])
                        return
                    cx += swatch_size + 6
                    idx += 1
                cx = pad
                cy += swatch_size + 6

            # 画笔大小区域
            brush_y = color_area_h + pad
            for i, size in enumerate(self.sizes):
                bx = pad + i * (swatch_size + 10)
                brect = pygame.Rect(bx, brush_y, swatch_size, swatch_size)
                if brect.collidepoint(lx, ly):
                    if self.on_brush:
                        self.on_brush(size)
                    return

            # 底部按钮区域：清空与橡皮
            btn_h = 32
            clear_rect = pygame.Rect(pad, self.rect.height - btn_h - pad, (self.rect.width - pad * 3) // 2, btn_h)
            erase_rect = pygame.Rect(clear_rect.right + pad, clear_rect.y, clear_rect.width, btn_h)
            if clear_rect.collidepoint(lx, ly):
                if self.on_clear:
                    self.on_clear()
                return
            if erase_rect.collidepoint(lx, ly):
                self._current_mode = "erase" if self._current_mode == "draw" else "draw"
                if self.on_mode:
                    self.on_mode(self._current_mode)
                return

    def draw(self, screen: pygame.Surface) -> None:
        # 背景与边框
        pygame.draw.rect(screen, (245, 245, 245), self.rect)
        pygame.draw.rect(screen, (200, 200, 200), self.rect, 2)

        pad = 8
        swatch_size = 28
        # 标题
        title = self.font.render("工具栏", True, (60, 60, 60))
        screen.blit(title, (self.rect.x + pad, self.rect.y + pad))

        # 颜色调色板
        cols_per_row = max(1, (self.rect.width - pad * 2) // (swatch_size + 6))
        cx = self.rect.x + pad
        cy = self.rect.y + pad + title.get_height() + 4
        idx = 0
        for _ in range((len(self.colors) + cols_per_row - 1) // cols_per_row):
            for _ in range(cols_per_row):
                if idx >= len(self.colors):
                    break
                rect = pygame.Rect(cx, cy, swatch_size, swatch_size)
                pygame.draw.rect(screen, self.colors[idx], rect)
                pygame.draw.rect(screen, (180, 180, 180), rect, 1)
                cx += swatch_size + 6
                idx += 1
            cx = self.rect.x + pad
            cy += swatch_size + 6

        # 画笔大小
        brush_label = self.font.render("画笔大小", True, (60, 60, 60))
        screen.blit(brush_label, (self.rect.x + pad, cy + 2))
        by = cy + 6 + brush_label.get_height()
        for i, size in enumerate(self.sizes):
            brect = pygame.Rect(self.rect.x + pad + i * (swatch_size + 10), by, swatch_size, swatch_size)
            pygame.draw.rect(screen, (255, 255, 255), brect)
            pygame.draw.rect(screen, (180, 180, 180), brect, 1)
            pygame.draw.circle(screen, (40, 40, 40), brect.center, max(2, size // 2))

        # 底部按钮
        btn_h = 32
        clear_rect = pygame.Rect(self.rect.x + pad, self.rect.bottom - btn_h - pad, (self.rect.width - pad * 3) // 2, btn_h)
        erase_rect = pygame.Rect(clear_rect.right + pad, clear_rect.y, clear_rect.width, btn_h)
        pygame.draw.rect(screen, (230, 230, 230), clear_rect)
        pygame.draw.rect(screen, (180, 180, 180), clear_rect, 1)
        pygame.draw.rect(screen, (230, 230, 230), erase_rect)
        pygame.draw.rect(screen, (180, 180, 180), erase_rect, 1)
        lbl_clear = self.font.render("清空", True, (40, 40, 40))
        lbl_erase = self.font.render("橡皮" if self._current_mode == "draw" else "画笔", True, (40, 40, 40))
        screen.blit(lbl_clear, (clear_rect.x + (clear_rect.width - lbl_clear.get_width()) // 2, clear_rect.y + (btn_h - lbl_clear.get_height()) // 2))
        screen.blit(lbl_erase, (erase_rect.x + (erase_rect.width - lbl_erase.get_width()) // 2, erase_rect.y + (btn_h - lbl_erase.get_height()) // 2))
