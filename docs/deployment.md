# HyperBrain 部署说明

## 目录

1. [环境要求](#1-环境要求)
2. [安装步骤](#2-安装步骤)
3. [配置说明](#3-配置说明)
4. [启动方法](#4-启动方法)
5. [更新和维护](#5-更新和维护)

---

## 1. 环境要求

### 1.1 硬件要求

| 组件 | 最低配置 | 推荐配置 | 说明 |
|------|----------|----------|------|
| CPU | 2核 | 4核+ | 多核有利于并发处理 |
| 内存 | 4GB | 8GB+ | 记忆系统需要较多内存 |
| 硬盘 | 2GB SSD | 10GB SSD | 用于存储数据和日志 |
| 网络 | 可选 | 推荐 | 用于在线大模型 API |

### 1.2 软件要求

| 软件 | 版本 | 说明 |
|------|------|------|
| Python | 3.11+ | 必需 |
| pip | 23.0+ | 必需 |
| Git | 2.40+ | 可选，用于源码安装 |

### 1.3 操作系统支持

| 操作系统 | 版本 | 支持状态 |
|----------|------|----------|
| Windows | 10/11 | 完全支持 |
| Linux | Ubuntu 20.04+ | 完全支持 |
| Linux | CentOS 8+ | 完全支持 |
| macOS | 12+ (Monterey) | 完全支持 |

### 1.4 可选依赖

| 依赖 | 用途 | 安装命令 |
|------|------|----------|
| CUDA | GPU 加速 | 根据 NVIDIA 驱动版本安装 |
| Ollama | 本地模型 | `curl -fsSL https://ollama.com/install.sh \| sh` |

---

## 2. 安装步骤

### 2.1 方法一：源码安装（推荐开发者）

#### 步骤 1：获取源码

```bash
# 克隆仓库
git clone <repository-url>
cd hyperbrain

# 或下载源码压缩包并解压
# unzip hyperbrain-v0.2.0.zip
# cd hyperbrain-v0.2.0
```

#### 步骤 2：创建虚拟环境

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate

# Linux/macOS:
source venv/bin/activate
```

#### 步骤 3：安装依赖

```bash
# 升级 pip
python -m pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt

# 验证安装
python -c "import hyperbrain; print('安装成功')"
```

#### 步骤 4：配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件（使用你喜欢的编辑器）
nano .env
# 或
notepad .env
```

### 2.2 方法二：打包版本安装（推荐普通用户）

#### Windows

1. 下载 `HyperBrain-0.2.0-windows-x86_64-onedir.zip`
2. 解压到目标目录，如 `C:\Program Files\HyperBrain`
3. 复制 `.env.example` 为 `.env`
4. 配置 API 密钥
5. 运行 `启动 HyperBrain.bat`

#### Linux

```bash
# 下载
curl -O https://example.com/HyperBrain-0.2.0-linux-x86_64-onedir.tar.gz

# 解压
tar -xzf HyperBrain-0.2.0-linux-x86_64-onedir.tar.gz

# 进入目录
cd HyperBrain-0.2.0-linux-x86_64-onedir

# 配置
cp .env.example .env
nano .env

# 运行
./start.sh
```

#### macOS

```bash
# 下载
curl -O https://example.com/HyperBrain-0.2.0-darwin-arm64-onedir.tar.gz

# 解压
tar -xzf HyperBrain-0.2.0-darwin-arm64-onedir.tar.gz

# 进入目录
cd HyperBrain-0.2.0-darwin-arm64-onedir

# 配置
cp .env.example .env
nano .env

# 运行
./start.sh
```

### 2.3 方法三：Docker 部署

```dockerfile
# Dockerfile
FROM python:3.12-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 创建数据目录
RUN mkdir -p /app/data /app/logs

# 暴露端口（如果需要 Web 服务）
EXPOSE 8000

# 启动命令
CMD ["python", "-m", "hyperbrain.app", "--mode", "cli"]
```

```bash
# 构建镜像
docker build -t hyperbrain:0.2.0 .

# 运行容器
docker run -it \
  -v $(pwd)/.env:/app/.env \
  -v hyperbrain-data:/app/hyperbrain/data \
  -v hyperbrain-logs:/app/hyperbrain/logs \
  hyperbrain:0.2.0
```

---

## 3. 配置说明

### 3.1 环境变量配置

创建 `.env` 文件，配置以下变量：

```env
# ================================
# 系统基础配置
# ================================
DEBUG=false
DATA_DIR=data
LOG_DIR=logs

# ================================
# OpenAI 配置
# ================================
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4
# OPENAI_BASE_URL=https://api.openai.com/v1

# ================================
# Anthropic 配置
# ================================
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxx
ANTHROPIC_MODEL=claude-3-opus-20240229

# ================================
# Google 配置
# ================================
GOOGLE_API_KEY=AIzaSyxxxxxxxxxxxxxxxx
GOOGLE_MODEL=gemini-pro

# ================================
# Ollama 本地模型配置
# ================================
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# ================================
# 模型默认参数
# ================================
MODEL_TEMPERATURE=0.7
MODEL_MAX_TOKENS=2048
MODEL_TIMEOUT=60

# ================================
# 记忆层配置
# ================================
MEMORY_VECTOR_DIM=1536
MEMORY_MAX_SHORT_TERM=100
MEMORY_SIMILARITY_THRESHOLD=0.75

# ================================
# UI 配置
# ================================
UI_WINDOW_WIDTH=1400
UI_WINDOW_HEIGHT=900
UI_THEME=dark
```

### 3.2 配置文件

支持 YAML 格式的配置文件：

```yaml
# config.yaml
model:
  default_model: openai
  temperature: 0.7
  max_tokens: 2000
  timeout: 30
  retry_attempts: 3

memory:
  db_path: memory.db
  vector_dim: 1536
  max_short_term_items: 100
  consolidation_interval: 300
  importance_threshold: 0.5

cognitive:
  reasoning_depth: 3
  max_thinking_time: 30
  enable_meta_cognition: true
  max_chain_length: 5
  confidence_threshold: 0.7

evolution:
  auto_evolve: true
  evolution_interval: 3600
  mutation_rate: 0.1

emotional:
  emotion_decay_rate: 0.95
  emotion_threshold: 0.3
  enable_emotional_memory: true
  enable_empathy: true

sensory:
  max_input_length: 10000
  enable_multimodal: true
  default_modality: text

execution:
  max_workers: 4
  task_timeout: 30
  enable_parallel: true

consciousness:
  awareness_threshold: 0.5
  reflection_interval: 60
  enable_self_model: true

system:
  log_level: INFO
  max_workers: 4
  enable_gui: true
```

### 3.3 配置优先级

配置加载优先级（从高到低）：

1. 命令行参数
2. 环境变量
3. 配置文件
4. 默认值

### 3.4 模型配置指南

#### OpenAI

```env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4
# 可选模型: gpt-4, gpt-4-turbo, gpt-3.5-turbo
```

#### Anthropic

```env
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxx
ANTHROPIC_MODEL=claude-3-opus-20240229
# 可选模型: claude-3-opus, claude-3-sonnet, claude-3-haiku
```

#### Google

```env
GOOGLE_API_KEY=AIzaSyxxxxxxxxxxxxxxxx
GOOGLE_MODEL=gemini-pro
# 可选模型: gemini-pro, gemini-pro-vision
```

#### Ollama（本地）

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
# 可选模型: llama2, mistral, codellama, neural-chat 等
```

安装 Ollama：

```bash
# Linux/macOS
curl -fsSL https://ollama.com/install.sh | sh

# Windows
# 下载安装程序: https://ollama.com/download/windows

# 拉取模型
ollama pull llama2
ollama pull mistral
```

---

## 4. 启动方法

### 4.1 GUI 模式

```bash
# 源码启动
python -m hyperbrain.app --mode gui

# 打包版本
./HyperBrain --mode gui

# 指定配置文件
python -m hyperbrain.app --mode gui --config config.yaml

# 调试模式
python -m hyperbrain.app --mode gui --debug
```

### 4.2 CLI 模式

```bash
# 源码启动
python -m hyperbrain.main --mode cli

# 打包版本
./HyperBrain --mode cli

# 指定日志级别
python -m hyperbrain.main --mode cli --log-level DEBUG

# 处理单条输入
python -m hyperbrain.main --process "你好，世界"
```

### 4.3 系统服务（Linux）

创建 systemd 服务：

```ini
# /etc/systemd/system/hyperbrain.service
[Unit]
Description=HyperBrain 拟人脑认知架构系统
After=network.target

[Service]
Type=simple
User=hyperbrain
WorkingDirectory=/opt/hyperbrain
Environment=PYTHONPATH=/opt/hyperbrain
EnvironmentFile=/opt/hyperbrain/.env
ExecStart=/opt/hyperbrain/venv/bin/python -m hyperbrain.app --mode cli
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 启用并启动服务
sudo systemctl enable hyperbrain
sudo systemctl start hyperbrain

# 查看状态
sudo systemctl status hyperbrain

# 查看日志
sudo journalctl -u hyperbrain -f
```

### 4.4 Windows 服务

使用 NSSM 创建服务：

```batch
# 下载 NSSM: https://nssm.cc/download

# 安装服务
nssm install HyperBrain

# 配置:
# Path: C:\Python312\python.exe
# Startup directory: C:\hyperbrain
# Arguments: -m hyperbrain.app --mode cli

# 启动服务
nssm start HyperBrain
```

---

## 5. 更新和维护

### 5.1 源码更新

```bash
# 进入项目目录
cd hyperbrain

# 激活虚拟环境
source venv/bin/activate

# 拉取最新代码
git pull origin main

# 更新依赖
pip install -r requirements.txt --upgrade

# 重启系统
```

### 5.2 数据备份

```bash
# 备份脚本 backup.sh
#!/bin/bash

BACKUP_DIR="/backup/hyperbrain/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# 备份数据库
cp hyperbrain/memory.db "$BACKUP_DIR/"

# 备份向量数据
cp -r hyperbrain/data/vectors "$BACKUP_DIR/"

# 备份配置
cp .env "$BACKUP_DIR/"
cp config.yaml "$BACKUP_DIR/" 2>/dev/null || true

# 备份日志
cp -r hyperbrain/logs "$BACKUP_DIR/"

# 压缩
tar -czf "$BACKUP_DIR.tar.gz" -C "$(dirname $BACKUP_DIR)" "$(basename $BACKUP_DIR)"
rm -rf "$BACKUP_DIR"

echo "备份完成: $BACKUP_DIR.tar.gz"
```

### 5.3 数据恢复

```bash
# 解压备份
tar -xzf backup_20240101_120000.tar.gz

# 恢复数据
cp backup_20240101_120000/memory.db hyperbrain/
cp -r backup_20240101_120000/vectors hyperbrain/data/
cp backup_20240101_120000/.env .
```

### 5.4 日志管理

```bash
# 查看实时日志
tail -f hyperbrain/logs/hyperbrain.log

# 查看错误日志
tail -f hyperbrain/logs/error.log

# 日志轮转配置 (logrotate)
# /etc/logrotate.d/hyperbrain
/opt/hyperbrain/hyperbrain/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 hyperbrain hyperbrain
}
```

### 5.5 性能监控

```bash
# 查看系统资源
htop

# 查看 Python 进程
ps aux | grep hyperbrain

# 查看内存使用
python -m hyperbrain.main --mode cli --process "/stats"

# 使用系统监控界面（GUI 模式）
# 工具菜单 -> 系统监控
```

### 5.6 常见问题排查

#### 启动失败

```bash
# 检查日志
cat hyperbrain/logs/error.log

# 检查配置
python -c "from hyperbrain.core.config import get_config; get_config().validate()"

# 检查依赖
pip check
```

#### 模型调用失败

```bash
# 测试网络
curl https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY"

# 测试本地 Ollama
curl http://localhost:11434/api/tags
```

#### 数据库错误

```bash
# 检查数据库文件
sqlite3 hyperbrain/memory.db ".tables"

# 修复数据库
sqlite3 hyperbrain/memory.db ".recover" > recover.sql
sqlite3 hyperbrain/memory.db.new < recover.sql
mv hyperbrain/memory.db.new hyperbrain/memory.db
```

### 5.7 卸载

```bash
# 停止服务
sudo systemctl stop hyperbrain
sudo systemctl disable hyperbrain

# 删除文件
rm -rf /opt/hyperbrain
rm /etc/systemd/system/hyperbrain.service

# 删除数据（谨慎操作）
rm -rf ~/.hyperbrain
```

---

## 附录

### A. 环境变量完整列表

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `DEBUG` | 调试模式 | `false` |
| `DATA_DIR` | 数据目录 | `data` |
| `LOG_DIR` | 日志目录 | `logs` |
| `OPENAI_API_KEY` | OpenAI API 密钥 | - |
| `OPENAI_MODEL` | OpenAI 模型 | `gpt-4` |
| `ANTHROPIC_API_KEY` | Anthropic API 密钥 | - |
| `ANTHROPIC_MODEL` | Anthropic 模型 | `claude-3-opus` |
| `GOOGLE_API_KEY` | Google API 密钥 | - |
| `GOOGLE_MODEL` | Google 模型 | `gemini-pro` |
| `OLLAMA_BASE_URL` | Ollama 服务地址 | `http://localhost:11434` |
| `OLLAMA_MODEL` | Ollama 模型 | `llama2` |
| `MODEL_TEMPERATURE` | 模型温度 | `0.7` |
| `MODEL_MAX_TOKENS` | 最大 Token 数 | `2048` |
| `MODEL_TIMEOUT` | 请求超时 | `60` |
| `MEMORY_VECTOR_DIM` | 向量维度 | `1536` |
| `MEMORY_MAX_SHORT_TERM` | 短期记忆容量 | `100` |
| `UI_THEME` | UI 主题 | `dark` |

### B. 端口说明

| 端口 | 用途 | 说明 |
|------|------|------|
| 11434 | Ollama | 本地模型服务 |
| 8000 | Web API | 可选的 Web 服务 |

### C. 目录结构

```
hyperbrain/
├── hyperbrain/          # 主程序目录
│   ├── core/            # 核心模块
│   ├── layers/          # 认知层
│   │   ├── sensory/     # 感知层
│   │   ├── memory/      # 记忆层
│   │   ├── cognitive/   # 认知层
│   │   ├── learning/    # 学习层
│   │   ├── evolution/   # 进化层
│   │   ├── emotional/   # 情感层
│   │   ├── execution/   # 执行层
│   │   └── consciousness/ # 意识层
│   ├── models/          # 模型层
│   ├── database/        # 数据库
│   ├── ui/              # UI界面
│   ├── utils/           # 工具
│   ├── data/            # 数据文件
│   └── logs/            # 日志文件
├── docs/                # 文档
├── tests/               # 测试
├── .env                 # 环境变量
├── config.yaml          # 配置文件
├── requirements.txt     # 依赖
└── README.md            # 说明
```
