# HyperBrain 环境配置总结

## 当前环境状态 ✅

### Python环境
- **Python 版本**: 3.13.1 (32位)
- **安装路径**: E:\软件\python\python.exe
- **虚拟环境**: 已创建在 e:\超脑\超脑002\venv

### 已成功安装的依赖

#### 核心功能依赖
- numpy>=1.26.0 ✅
- PyQt5>=5.15.0 ✅ (UI界面，32位兼容)
- pyqtgraph>=0.14.0 ✅ (图表绘制)
- markdown>=3.5.0 ✅
- pygments>=2.17.0 ✅
- pyyaml>=6.0.0 ✅

#### 网络与API
- requests>=2.31.0 ✅
- aiohttp>=3.9.0 ✅
- openai>=2.37.0 ✅
- anthropic>=0.103.1 ✅
- google-generativeai>=0.8.6 ✅

#### 数据验证与配置
- pydantic>=2.13.0 ✅
- pydantic-settings>=2.14.0 ✅
- python-dotenv>=1.2.0 ✅

#### 日志与工具
- loguru>=0.7.0 ✅
- colorama>=0.4.0 ✅
- tqdm>=4.60.0 ✅

#### 测试与打包
- pytest>=9.0.0 ✅
- pytest-asyncio>=1.3.0 ✅
- pyinstaller>=6.20.0 ✅

### 使用的Fallback替代方案

由于32位Python限制，以下使用了替代实现：

1. **faiss-cpu**: 使用内置的 fallback 实现（无依赖的向量搜索）
2. **pandas**: 当前未安装（可选依赖）
3. **PyQt6**: 替代为 PyQt5（32位兼容）

### 系统功能验证 ✅

已成功运行测试，所有功能正常：

- ✅ 所有8个认知层成功初始化
  - 感知层 (Sensory)
  - 记忆层 (Memory)
  - 认知层 (Cognitive)
  - 学习层 (Learning)
  - 情感层 (Emotional)
  - 执行层 (Execution)
  - 意识层 (Consciousness)
  - 进化层 (Evolution)
- ✅ 数据库初始化成功 (SQLite)
- ✅ 向量存储初始化成功 (使用fallback)
- ✅ CLI模式运行正常

### 使用说明

#### 激活虚拟环境
```powershell
# Windows PowerShell
.\venv\Scripts\Activate.ps1

# 或者使用完整路径
& 'E:\超脑\超脑002\venv\Scripts\Activate.ps1'
```

#### 运行HyperBrain
```powershell
# CLI模式 - 处理单条消息
& 'E:\超脑\超脑002\venv\Scripts\python.exe' -m hyperbrain.main --process "你的消息"

# 交互CLI模式
& 'E:\超脑\超脑002\venv\Scripts\python.exe' -m hyperbrain.main --mode cli

# GUI模式 (PyQt5)
& 'E:\超脑\超脑002\venv\Scripts\python.exe' -m hyperbrain.main --mode gui
```

## 下一步（可选，用于完整功能）

### 安装64位Python

为了获得完整的功能支持（包括PyQt6、faiss-cpu、pandas等），建议安装64位Python：

1. **下载64位Python 3.11.9**: https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe
2. **安装时勾选**: "Add Python 3.11 to PATH"
3. **自定义安装路径**，例如：E:\software\python311
4. **安装完成后**，重新创建虚拟环境和安装依赖

详细步骤请参见 [INSTALL_PYTHON.md](INSTALL_PYTHON.md)

### 配置大模型API

为了使系统能够响应消息，需要配置一个或多个大模型API：

1. **Ollama本地模型** (推荐，免费):
   - 下载并安装: https://ollama.com/
   - 运行: `ollama pull llama2`
   - 启动服务: `ollama serve`

2. **OpenAI API**:
   - 获取API Key: https://platform.openai.com/account/api-keys
   - 在环境变量或配置文件中设置

3. **Anthropic API**:
   - 获取API Key: https://console.anthropic.com/
   - 在环境变量或配置文件中设置

4. **Google Gemini API**:
   - 获取API Key: https://aistudio.google.com/
   - 在环境变量或配置文件中设置

## 项目文件说明

- `requirements.txt`: 主要依赖列表（已更新为PyQt5兼容）
- `requirements_32bit.txt`: 32位Python优化依赖列表
- `INSTALL_PYTHON.md`: 64位Python安装指南
- `hyperbrain/qt_compat.py`: PyQt5/PyQt6兼容性层（新增）

## 故障排除

### 虚拟环境问题
如果虚拟环境有问题，可以删除并重新创建：
```powershell
Remove-Item -Recurse -Force venv
& 'E:\软件\python\python.exe' -m venv venv
& 'E:\超脑\超脑002\venv\Scripts\pip.exe' install -r requirements.txt
```

### 依赖安装失败
如果某些依赖安装失败，可以尝试：
```powershell
& 'E:\超脑\超脑002\venv\Scripts\pip.exe' install --only-binary :all: 包名
```
或者使用清华镜像源：
```powershell
& 'E:\超脑\超脑002\venv\Scripts\pip.exe' install -i https://pypi.tuna.tsinghua.edu.cn/simple 包名
```
