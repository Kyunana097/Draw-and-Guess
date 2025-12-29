# 全屏功能修复说明

## 问题描述
游戏客户端在使用全屏功能时存在以下问题：
1. **全屏无法正常切换**：点击全屏按钮后无法进入或退出全屏模式
2. **影响其他应用**：进入全屏时会把其他应用也缩小（改变显示器配置）
3. **开启游戏自动全屏**：初始化时如果启用了全屏选项会导致游戏自动启动为全屏

## 根本原因
1. **使用了 `pygame.FULLSCREEN` 而不是 `pygame.FULLSCREEN_DESKTOP`**
   - `pygame.FULLSCREEN` 会改变显示器的分辨率和刷新率，影响整个系统
   - `pygame.FULLSCREEN_DESKTOP` 使用当前显示器的原生分辨率，不影响其他应用

2. **窗口大小调整时覆盖全屏标志**
   - 在处理 `VIDEORESIZE` 事件时，防抖逻辑强制使用 `pygame.RESIZABLE` 标志
   - 这会导致即使用户已启用全屏，窗口调整后也会被强制退出全屏

## 修复方案

### 1. 初始化窗口时使用 FULLSCREEN_DESKTOP（第834-839行）
**修改前：**
```python
if APP_STATE["settings"].get("fullscreen"):
    flags = pygame.FULLSCREEN
    screen = pygame.display.set_mode((0, 0), flags)
```

**修改后：**
```python
if APP_STATE["settings"].get("fullscreen"):
    flags = pygame.FULLSCREEN_DESKTOP
    screen = pygame.display.set_mode((0, 0), flags)
```

### 2. 全屏切换函数中使用 FULLSCREEN_DESKTOP（第869-872行）
**修改前：**
```python
if new:
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
```

**修改后：**
```python
if new:
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN_DESKTOP)
```

### 3. 窗口调整时保留全屏状态（第1137-1145行）
**修改前：**
```python
try:
    screen = pygame.display.set_mode(pending_size, pygame.RESIZABLE)
except Exception:
    pass
```

**修改后：**
```python
try:
    is_fullscreen = bool(APP_STATE["settings"].get("fullscreen", False))
    if is_fullscreen:
        screen = pygame.display.set_mode(pending_size, pygame.FULLSCREEN_DESKTOP)
    else:
        screen = pygame.display.set_mode(pending_size, pygame.RESIZABLE)
except Exception:
    pass
```

## 效果验证
修复后，用户应该能够：
- ✅ 正常切换全屏和窗口模式（点击全屏按钮生效）
- ✅ 不影响其他应用（不会改变显示器配置）
- ✅ 调整窗口大小时保持全屏状态（不会被强制退出全屏）
- ✅ 记住用户的全屏偏好（重启游戏时恢复用户的选择）

## 测试步骤
1. 启动游戏，在菜单中点击"全屏: 否" → "全屏: 是"
2. 验证游戏进入全屏模式且不影响其他应用
3. 在全屏模式下调整窗口尺寸（某些系统可能支持）
4. 点击"全屏: 是" → "全屏: 否"
5. 验证游戏返回到窗口化模式（1280x720）
6. 重启游戏，验证上次的全屏设置被记住
