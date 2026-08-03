# 64位Python安装指南

## 手动安装步骤

### 1. 下载Python 3.11.9 64位

请访问以下链接下载Python 3.11.9 (64-bit)：
https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe

### 2. 安装Python

下载后，按以下步骤安装：

1. 运行 `python-3.11.9-amd64.exe
2. **重要**: 勾选 "Add Python 3.11 to PATH"
3. 选择 "Customize installation"
4. 确保勾选所有可选功能，包括：
   - pip
   - tcl/tk and IDLE
   - Python test suite
   - py launcher
5. 点击下一步，勾选：
   - "Install for all users" (推荐)
   - "Add Python to environment variables
   - "Precompile standard library"
6. 设置安装路径为：`E:\software\python311` (或您喜欢的路径)
7. 点击 "Install"
8. 安装完成后，关闭安装程序

### 3. 验证安装

打开新的PowerShell窗口，运行：
```powershell
python --version
```
应该显示：Python 3.11.9

### 4. 接下来的步骤

安装完成后，请告诉我，我会继续：
1. 创建虚拟环境
2. 安装所有依赖（包括PyQt6等）
3. 验证系统运行