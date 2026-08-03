# HyperBrain Python 3.14.5 手动升级指南

## 当前状态

✅ 已完成的步骤：
- 确认 Python 3.14.5 是最新稳定版（2026年5月10日发布）
- 卸载旧版 Python 3.11.9
- 创建了自动升级脚本

⏳ 待完成的步骤：
- 下载 Python 3.14.5 安装程序
- 安装 Python 3.14.5
- 重新创建虚拟环境
- 安装依赖

---

## 手动升级步骤

### 步骤1：下载 Python 3.14.5

由于当前环境网络限制，请手动下载：

**下载地址**：https://www.python.org/ftp/python/3.14.5/python-3.14.5-amd64.exe

**文件大小**：约 27-30 MB

**保存位置**：`e:\超脑\超脑002\python-3.14.5-amd64.exe`

---

### 步骤2：安装 Python 3.14.5

下载完成后，在PowerShell中执行：

```powershell
# 静默安装Python 3.14.5到 E:\software\python314
Start-Process -FilePath "e:\超脑\超脑002\python-3.14.5-amd64.exe" `
    -ArgumentList "/quiet", "InstallAllUsers=0", "PrependPath=1", "Include_test=0", "TargetDir=E:\software\python314" `
    -Wait

# 验证安装
& 'E:\software\python314\python.exe' --version
# 应显示: Python 3.14.5

& 'E:\software\python314\python.exe' -c "import struct; print(struct.calcsize('P') * 8, 'bit')"
# 应显示: 64 bit
```

---

### 步骤3：重新创建虚拟环境

```powershell
# 删除旧虚拟环境
Remove-Item -Recurse -Force "e:\超脑\超脑002\venv"

# 创建新虚拟环境
& 'E:\software\python314\python.exe' -m venv "e:\超脑\超脑002\venv"

# 验证虚拟环境
& 'e:\超脑\超脑002\venv\Scripts\python.exe' --version
# 应显示: Python 3.14.5
```

---

### 步骤4：安装依赖

```powershell
$VenvPython = "e:\超脑\超脑002\venv\Scripts\python.exe"

# 升级pip
& $VenvPython -m pip install --upgrade pip

# 安装核心依赖（使用预编译包）
& $VenvPython -m pip install PyQt6 PyQt6-Qt6 --only-binary :all:
& $VenvPython -m pip install numpy pandas --only-binary :all:
& $VenvPython -m pip install requests aiohttp --only-binary :all:
& $VenvPython -m pip install openai anthropic google-generativeai --only-binary :all:
& $VenvPython -m pip install faiss-cpu --only-binary :all:
& $VenvPython -m pip install python-dotenv loguru --only-binary :all:
& $VenvPython -m pip install pydantic pydantic-settings --only-binary :all:
& $VenvPython -m pip install pytest pytest-asyncio --only-binary :all:
& $VenvPython -m pip install markdown pygments pyyaml --only-binary :all:
& $VenvPython -m pip install pyqtgraph pyinstaller --only-binary :all:
```

---

### 步骤5：验证系统运行

```powershell
# 测试系统
& 'e:\超脑\超脑002\venv\Scripts\python.exe' -m hyperbrain.main --process "你好，HyperBrain！"
```

---

## 一键执行脚本

如果你已经下载了安装程序，可以直接运行：

```powershell
# 安装Python
Start-Process -FilePath "e:\超脑\超脑002\python-3.14.5-amd64.exe" -ArgumentList "/quiet", "InstallAllUsers=0", "PrependPath=1", "Include_test=0", "TargetDir=E:\software\python314" -Wait

# 创建虚拟环境
& 'E:\software\python314\python.exe' -m venv "e:\超脑\超脑002\venv"

# 安装依赖
$VenvPython = "e:\超脑\超脑002\venv\Scripts\python.exe"
& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install PyQt6 PyQt6-Qt6 numpy pandas requests aiohttp openai anthropic google-generativeai faiss-cpu python-dotenv loguru pydantic pydantic-settings pytest pytest-asyncio markdown pygments pyyaml pyqtgraph pyinstaller

# 验证
& $VenvPython --version
& $VenvPython -m hyperbrain.main --process "测试"
```

---

## 常见问题

### Q: 下载速度慢或失败？
A: 可以尝试使用国内镜像或代理，或者在其他网络环境下下载后复制到当前目录。

### Q: PyQt6安装失败？
A: Python 3.14.5非常新，PyQt6可能还没有预编译包。可以：
1. 等待几天再试
2. 使用PyQt5作为替代
3. 从源码编译（需要Visual Studio Build Tools）

### Q: faiss-cpu安装失败？
A: 同样可能是因为Python 3.14太新。可以：
1. 使用系统内置的fallback向量搜索
2. 等待faiss更新支持Python 3.14

### Q: 其他依赖安装失败？
A: 对于Python 3.14这种非常新的版本，部分包可能还没有预编译版本。可以：
1. 使用 `--only-binary :all:` 跳过无法安装的包
2. 等待包作者更新
3. 考虑使用Python 3.13（稳定性更好）

---

## 备选方案

如果Python 3.14.5遇到太多兼容性问题，建议：

### 方案A：使用Python 3.13.13（次新版本，兼容性更好）
```powershell
# 下载地址
https://www.python.org/ftp/python/3.13.13/python-3.13.13-amd64.exe
```

### 方案B：继续使用Python 3.11.9（当前稳定运行）
如果升级遇到太多问题，可以重新安装Python 3.11.9：
```powershell
# 重新安装Python 3.11.9
Start-Process -FilePath "python-3.11.9-amd64.exe" -ArgumentList "/quiet", "TargetDir=E:\software\python311" -Wait

# 重新创建虚拟环境
& 'E:\software\python311\python.exe' -m venv "e:\超脑\超脑002\venv"
```

---

## 升级后检查清单

- [ ] Python 3.14.5 安装成功
- [ ] 64位架构确认
- [ ] 虚拟环境创建成功
- [ ] PyQt6 安装成功
- [ ] numpy 安装成功
- [ ] pandas 安装成功
- [ ] faiss-cpu 安装成功
- [ ] 其他依赖安装成功
- [ ] HyperBrain 系统运行正常

---

**注意**：Python 3.14.5 是非常新的版本（2026年5月发布），部分第三方包可能还没有提供预编译版本。如果遇到安装问题，请耐心等待或考虑使用Python 3.13.13。