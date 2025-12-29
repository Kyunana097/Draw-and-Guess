# Draw & Guess 游戏服务器部署包

## 快速部署

### 1. 上传到服务器

将整个 `server-deploy` 文件夹上传到 Ubuntu 服务器：

```bash
scp -r server-deploy user@your-server-ip:~/
```

或使用 git：
```bash
git clone https://github.com/Kyunana097/Draw-and-Guess.git
cd Draw-and-Guess/server-deploy
```

### 2. 运行部署脚本

```bash
cd ~/server-deploy
chmod +x *.sh
./deploy.sh
```

### 3. 启动服务器

前台运行（调试用）：
```bash
./start-server.sh
```

后台运行（推荐）：
```bash
./start-server.sh --background
```

### 4. 停止服务器

```bash
./stop-server.sh
```

## 客户端连接

在游戏客户端的设置中填入：
- **服务器地址**：你的服务器公网 IP
- **端口**：5555

## 文件说明

| 文件 | 说明 |
|------|------|
| `deploy.sh` | 一键部署脚本 |
| `start-server.sh` | 启动服务器 |
| `stop-server.sh` | 停止服务器 |
| `server.py` | 服务器主程序 |
| `requirements.txt` | Python 依赖 |
| `server.log` | 运行日志（自动生成）|

## 常用命令

```bash
# 查看后台服务器
screen -r game-server

# 退出 screen（不停止服务器）
Ctrl+A, D

# 查看日志
tail -f server.log

# 检查端口是否在监听
netstat -tlnp | grep 5555
```

## 防火墙

确保端口 5555 已开放：
```bash
sudo ufw allow 5555/tcp
sudo ufw status
```
