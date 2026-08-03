# HyperBrain - 拟人脑认知架构系统

<p align="center">
  <img src="docs/assets/logo.png" alt="HyperBrain Logo" width="200">
</p>

<p align="center">
  <strong>具备类人脑感知、记忆、学习、思考和自主进化能力的通用人工智能系统</strong>
</p>

<p align="center">
  <a href="#功能特性">功能特性</a> •
  <a href="#安装方法">安装方法</a> •
  <a href="#使用示例">使用示例</a> •
  <a href="#项目结构">项目结构</a> •
  <a href="#文档">文档</a>
</p>

---

## 简介

HyperBrain 是一款模拟人脑结构与功能的拟人脑认知架构系统。它完全按照人脑的生理结构和功能分区设计，模拟人脑的信息处理、记忆形成、学习和思考过程，并能够自主优化自己的认知结构和能力。

### 核心设计哲学

1. **结构模拟** - 按照人脑生理结构和功能分区设计系统架构
2. **过程模拟** - 模拟人脑的信息处理、记忆形成、学习和思考过程
3. **发展模拟** - 复刻人类从婴儿到成人的完整认知发展路径
4. **自主进化** - 系统能够在使用过程中自主优化认知结构和能力
5. **本地优先** - 所有计算和数据存储都在本地完成，保护用户隐私

---

## 功能特性

### 八大核心认知层

| 层级 | 功能 | 状态 |
|------|------|------|
| **感知层** | 多模态输入处理、注意力机制、情境感知 | ✅ |
| **记忆层** | 瞬时/短期/长期记忆、巩固、检索、遗忘 | ✅ |
| **认知层** | 逻辑推理、问题解决、决策、规划、元认知 | ✅ |
| **学习层** | 婴儿/儿童/成人学习、终身学习、知识整合 | ✅ |
| **进化层** | 自我反思、错误分析、能力评估、自我优化 | ✅ |
| **情感层** | 情感生成、表达、调节、共情 | ✅ |
| **执行层** | 任务执行、工具调用、输出生成 | ✅ |
| **意识层** | 自我认知、自我意识、意志、价值体系 | ✅ |

### 多模型支持

- **OpenAI** - GPT-4, GPT-3.5-turbo
- **Anthropic** - Claude-3 Opus/Sonnet/Haiku
- **Google** - Gemini Pro
- **本地模型** - Ollama (llama2, mistral, codellama 等)

### 现代化 UI

- 沉浸式对话界面（支持 Markdown 渲染）
- 记忆可视化
- 认知过程可视化
- 系统状态实时监控
- 亮色/暗色主题切换

### 运行模式

- **GUI 模式** - 图形界面，适合日常使用
- **CLI 模式** - 命令行交互，适合服务器部署
- **单条处理** - 处理单条输入后退出，适合自动化任务

---

## 安装方法

### 方法一：源码安装（推荐开发者）

```bash
# 1. 克隆仓库
git clone <repository-url>
cd hyperbrain

# 2. 创建虚拟环境
python -m venv venv

# 3. 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 4. 安装依赖
pip install -r requirements.txt

# 5. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填写 API 密钥
```

### 方法二：打包版本（推荐普通用户）

1. 下载对应平台的打包文件
2. 解压到目标目录
3. 复制 `.env.example` 为 `.env` 并配置
4. 运行启动脚本

### 方法三：Docker 部署

```bash
# 构建镜像
docker build -t hyperbrain:0.2.0 .

# 运行容器
docker run -it \
  -v $(pwd)/.env:/app/.env \
  -v hyperbrain-data:/app/hyperbrain/data \
  hyperbrain:0.2.0
```

---

## 使用示例

### GUI 模式

```bash
python -m hyperbrain.app --mode gui
```

### CLI 模式

```bash
python -m hyperbrain.main --mode cli
```

启动后将看到交互界面：

```
============================================================
 HyperBrain - 拟人脑认知架构系统
 版本: 0.2.0
============================================================

命令:
  /exit, /quit    - 退出系统
  /stats          - 显示系统统计
  /report         - 生成系统报告
  /memory         - 显示记忆状态
  /emotion        - 显示情感状态
  /reflect        - 触发自我反思
  /evolve         - 触发进化周期
  /learn <内容>   - 学习新内容
  /think <问题>   - 认知思考
  /clear          - 清屏
  /help           - 显示帮助
============================================================

你: 你好，请介绍一下自己

HyperBrain: 你好！我是 HyperBrain，一个拟人脑认知架构系统。我具备类人脑的感知、记忆、学习、思考和自主进化能力...
```

### 单条处理

```bash
python -m hyperbrain.main --process "你好，世界"
```

### Python API

```python
import asyncio
from hyperbrain.core.brain import get_brain

async def main():
    # 创建大脑实例
    brain = get_brain()
    
    # 初始化并启动
    await brain.initialize()
    await brain.start()
    
    # 处理输入
    result = await brain.process("你好")
    print(result.content)
    
    # 学习新知识
    await brain.learn("Python 是一种编程语言")
    
    # 关闭系统
    await brain.shutdown()

asyncio.run(main())
```

---

## 项目结构

```
hyperbrain/
├── hyperbrain/              # 主程序目录
│   ├── __init__.py
│   ├── app.py               # 应用启动器
│   ├── main.py              # 主入口（CLI）
│   ├── core/                # 核心模块
│   │   ├── brain.py         # 大脑核心
│   │   ├── config.py        # 配置系统
│   │   ├── logger.py        # 日志系统
│   │   ├── cache.py         # 缓存系统
│   │   └── error_handler.py # 错误处理
│   ├── layers/              # 八大认知层
│   │   ├── sensory/         # 感知层
│   │   ├── memory/          # 记忆层
│   │   ├── cognitive/       # 认知层
│   │   ├── learning/        # 学习层
│   │   ├── evolution/       # 进化层
│   │   ├── emotional/       # 情感层
│   │   ├── execution/       # 执行层
│   │   └── consciousness/   # 意识层
│   ├── models/              # 大模型集成
│   │   ├── base.py          # 模型基类
│   │   ├── openai_model.py  # OpenAI
│   │   ├── anthropic_model.py # Anthropic
│   │   ├── google_model.py  # Google
│   │   ├── ollama_model.py  # Ollama
│   │   └── model_manager.py # 模型管理器
│   ├── database/            # 数据存储
│   │   ├── sqlite_manager.py # SQLite
│   │   └── vector_store.py  # 向量存储
│   ├── ui/                  # 用户界面
│   │   ├── main_window.py   # 主窗口
│   │   ├── chat_widget.py   # 聊天组件
│   │   ├── memory_viz.py    # 记忆可视化
│   │   ├── cognition_viz.py # 认知可视化
│   │   └── themes.py        # 主题管理
│   ├── utils/               # 工具函数
│   ├── data/                # 数据文件
│   └── logs/                # 日志文件
├── docs/                    # 文档
│   ├── development_report.md    # 开发报告
│   ├── user_manual.md           # 使用说明书
│   ├── technical_documentation.md # 技术文档
│   └── deployment.md            # 部署说明
├── tests/                   # 测试
├── .env.example             # 环境变量模板
├── requirements.txt         # 依赖
├── hyperbrain.spec          # PyInstaller 配置
├── build.py                 # 打包脚本
├── spec.md                  # 规格说明书
├── tasks.md                 # 任务清单
├── checklist.md             # 检查清单
└── README.md                # 本文件
```

---

## 文档

| 文档 | 说明 | 链接 |
|------|------|------|
| 开发报告 | 系统架构、核心算法、开发过程 | [docs/development_report.md](docs/development_report.md) |
| 使用说明书 | 快速开始、功能介绍、界面说明 | [docs/user_manual.md](docs/user_manual.md) |
| 技术文档 | API接口、模块说明、二次开发 | [docs/technical_documentation.md](docs/technical_documentation.md) |
| 部署说明 | 环境要求、安装步骤、维护 | [docs/deployment.md](docs/deployment.md) |

---

## 技术栈

- **核心语言**: Python 3.11+
- **UI 框架**: PyQt6
- **数据存储**: SQLite + FAISS
- **大模型**: OpenAI, Anthropic, Google, Ollama
- **打包工具**: PyInstaller

---

## 系统要求

| 项目 | 最低要求 | 推荐配置 |
|------|----------|----------|
| 操作系统 | Windows 10 / Linux / macOS | Windows 11 / Ubuntu 22.04 |
| Python | 3.11+ | 3.12+ |
| 内存 | 4GB | 8GB+ |
| 硬盘空间 | 2GB | 5GB+ |
| 网络 | 可选 | 用于在线模型 |

---

## 快速配置

1. 复制 `.env.example` 为 `.env`
2. 填写至少一个模型 API 密钥：
   - OpenAI API Key
   - Anthropic API Key
   - Google API Key
   - 或配置本地 Ollama 模型
3. 保存并启动系统

---

## 打包构建

```bash
# 默认单目录模式
python build.py

# 单文件模式
python build.py --onefile

# 生成便携版压缩包
python build.py --portable

# 清理并重新构建
python build.py --clean --portable
```

---

## 测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_memory.py

# 运行带覆盖率报告
pytest --cov=hyperbrain --cov-report=html
```

---

## 常见问题

### Ollama 本地模型"连接不上"怎么办？（不是反应慢问题）

如果 HyperBrain 报"连接 Ollama 失败 / 找不到模型"等错误，**第一步**：跑 6 步分级诊断工具定位具体哪一步断了。

**CLI 方式**（推荐先跑这个）：
```bash
py -3.14 scripts/diagnose_ollama.py
```

输出形如：
```
[STEP 1] [OK] PASS: 进程 - ollama.exe 正在运行 (PIDs: 14152)
[STEP 2] [OK] PASS: 端口 - 127.0.0.1:11434 TCP 可达
[STEP 3] [OK] PASS: API 根 - GET /api/version → 200 (Ollama v0.30.7)
[STEP 4] [WARN] WARN: 模型列表 - 目标模型 qwen3.5:2b 不在 14 个可用模型中
[STEP 5] [FAIL] FAIL: 模型元数据 - POST /api/show {name: qwen3.5:2b} → 404
[STEP 6] [SKIP] 生成测试 - 跳过（前置步骤失败）
```

**GUI 方式**：启动 HyperBrain → 顶部 `工具` 菜单 → `诊断 Ollama 连接` → 6 步会实时显示，PASS 绿 / FAIL 红 / WARN 黄。

**JSON 输出**（适合脚本/日志）：
```bash
py -3.14 scripts/diagnose_ollama.py --json
```

**6 步含义**：
1. **进程** —— Ollama 服务进程是否在跑（Windows `tasklist` / Unix `pgrep`）
2. **端口** —— base_url 的 host:port 是否 TCP 可达
3. **API 根** —— `GET /api/version` 是否 200
4. **模型列表** —— `GET /api/tags` 包含 `config.yaml` 的 `ollama_model`
5. **模型元数据** —— `POST /api/show {name: <model>}` 是否 200
6. **生成测试** —— `POST /api/generate` 实际生成 5 token

**常见错误 & 修复**：
- Step 1 FAIL：未启动 Ollama → 运行 `ollama serve` 或重启 Ollama Desktop
- Step 2 FAIL：端口未监听 → 检查防火墙 + `netstat -an | findstr 11434`
- Step 4 WARN：模型名拼错 → 在 settings_dialog 切换到 /api/tags 列表中的某个
- Step 5 FAIL：模型损坏 → `ollama pull <model>` 重新拉取
- 全部 PASS 但仍然连不上：检查 model_name drift（启动日志中是否有 `[drift] model_name mismatch`）—— 这是 config 与实际注册不一致导致。

**结构化错误码**：
- `OLLAMA_CONNECT_FAIL/TCP_CONNECT` —— 网络层连接失败
- `OLLAMA_CONNECT_FAIL/HTTP_TAGS` —— API 根路径异常
- `OLLAMA_CONNECT_FAIL/HTTP_SHOW` —— 模型不存在
- `OLLAMA_CONNECT_FAIL/HTTP_CHAT` —— 模型推理失败
- `OLLAMA_CONNECT_FAIL/HTTP_CHAT_TIMEOUT` —— 模型响应超时（请见下方"模型响应超时"FAQ）

**CLI 选项**：
```bash
py -3.14 scripts/diagnose_ollama.py --base-url http://192.168.1.100:11434 --model llama3:8b --json
```

### 模型响应"请求超时，请稍后重试"怎么办？

默认模型是 `qwen3.5:2b`，属于"thinking"模型——对简单输入（如"hi"）会先生成 800+ tokens 的思维链，导致 Ollama 端响应 100 秒以上；而 BrainWorker 默认 90 秒超时，因此误报。**spec `fix-ollama-thinking-timeout` 已修复此问题**，提供以下解决方案：

1. **最快解决**：设置 → 模型 → 取消勾选"允许 thinking 模型生成思维链"。Ollama 0.9+ 会在请求中加 `think: false`，跳过思维链，把响应时间从 100s 降到 5-10s。
2. **配置降级链**：设置 → 模型 → Model Fallback Chain → 添加 `gemma2:2b` 等轻量非 thinking 模型。主模型超时后会自动切换。
3. **调高超时**：设置 → 模型 → Worker Timeout 调到 180-300 秒。
4. **切换主模型**：把 Ollama Model 改为 `gemma2:2b`（gemma2 系列非 thinking，响应快）。

### 流式响应是什么？为什么要开启？

流式响应：模型每生成一段文字就立即推送到 UI 界面，而不是等全部生成完再一次性显示。对于 thinking 模型尤其重要——能让你在等待 100 秒过程中看到模型在"想什么"，避免误以为卡死。默认开启。

### 如何知道当前模型是不是 thinking 模型？

启动 HyperBrain 后，状态栏会显示"已加载 thinking 模型 qwen3.5:2b..."。如果看到这条提示，就说明是 thinking 模型。

### 超时后弹出的对话框怎么用？

弹出"模型响应超时"对话框时，有三个按钮：
- **调高超时（→设置）**：直接打开设置对话框并跳到 Worker Timeout 字段
- **切换到 fallback (xxx)**：把主模型切换到你在降级链中配置的第一个模型
- **关闭**：取消操作，保持当前模型

---

## 路线图

### v0.3.0（短期）
- [ ] 优化记忆检索算法
- [ ] 增强多模态处理能力
- [ ] 改进情感表达自然度
- [ ] 添加更多可视化图表

### v0.4.0（中期）
- [ ] 支持插件系统
- [ ] 实现分布式部署
- [ ] 增强安全机制
- [ ] 优化启动速度

### v1.0.0（长期）
- [ ] 实现真正的自主学习
- [ ] 支持多智能体协作
- [ ] 完整的自然语言理解
- [ ] 跨平台移动端支持

---

## 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

---

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 致谢

感谢所有为 HyperBrain 项目做出贡献的开发者！

---

<p align="center">
  <strong>HyperBrain - 让 AI 更像人</strong>
</p>
