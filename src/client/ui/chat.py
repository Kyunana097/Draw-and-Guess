import pygame
from typing import List, Tuple


class ChatPanel:
    """
    简易聊天面板：显示最近的聊天消息。
    
    功能特性：
    - 存储并显示玩家输入的聊天内容
    - 自动滚动显示最新的消息（最多 200 条历史记录）
    - 根据面板高度自动调整显示的行数
    """

    def __init__(self, rect: pygame.Rect, font_size: int = 18, font_name: str | None = None) -> None:
        """初始化聊天面板
        
        Args:
            rect: 聊天面板的矩形区域
            font_size: 字体大小
            font_name: 字体名称（如 "Microsoft YaHei"），默认系统字体
        """
        self.rect = rect
        
        # 尝试加载指定字体，失败则使用默认字体
        try:
            self.font = pygame.font.SysFont(font_name or None, font_size)
        except Exception:
            self.font = pygame.font.SysFont(None, font_size)
        
        # 消息列表：每个消息是 (用户名, 文本) 元组
        self.messages: List[Tuple[str, str]] = []  # (user, text)
        # 根据面板高度自动计算最多显示的行数（每行高度 + 4 像素间距）
        self.max_lines = max(3, rect.height // (self.font.get_height() + 4))
        
        # 颜色定义
        self.bg_color = (250, 250, 250)      # 浅灰色背景
        self.border_color = (200, 200, 200)  # 灰色边框

    def add_message(self, user: str, text: str) -> None:
        """添加一条新消息到聊天面板
        
        Args:
            user: 发送者名字（如 "你", "对方", "系统"）
            text: 消息内容
        """
        self.messages.append((user, text))  # 添加消息到列表末尾
        # 限制历史消息数量不超过 200 条（防止内存溢出）
        if len(self.messages) > 200:
            self.messages = self.messages[-200:]  # 保留最新的 200 条

    def draw(self, screen: pygame.Surface) -> None:
        """每帧渲染聊天面板到屏幕
        
        - 绘制背景与边框
        - 显示最近的 max_lines 条消息
        
        Args:
            screen: pygame 屏幕 Surface 对象
        """
        # 绘制背景矩形
        pygame.draw.rect(screen, self.bg_color, self.rect)
        # 绘制边框（2像素宽）
        pygame.draw.rect(screen, self.border_color, self.rect, 2)
        
        # 计算显示范围：只显示最后 max_lines 条消息
        y = self.rect.y + 6  # 纵坐标（距顶部 6 像素）
        start = max(0, len(self.messages) - self.max_lines)  # 起始索引
        
        # 逐行渲染消息
        for user, text in self.messages[start:]:
            line = f"{user}: {text}"  # 格式化为 "用户名: 消息内容"
            surf = self.font.render(line, True, (40, 40, 40))  # 深灰色文字
            screen.blit(surf, (self.rect.x + 8, y))  # 绘制在左边距 8 像素处
            y += surf.get_height() + 4  # 下一行向下移动（行高 + 4 像素间距）
