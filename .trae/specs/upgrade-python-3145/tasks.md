# Python 3.14.5 升级任务清单

## 任务1：依赖兼容性检查
- [x] 任务1.1：检查 PyQt6 对 Python 3.14 的支持（已确认：PyQt6 6.11.0 使用 cp310-abi3，支持 3.10+）
- [x] 任务1.2：检查 numpy 对 Python 3.14 的支持（numpy 2.4.6 支持）
- [x] 任务1.3：检查 pandas 对 Python 3.14 的支持（pandas 3.0.3 支持）
- [x] 任务1.4：检查 faiss-cpu 对 Python 3.14 的支持（OK）
- [x] 任务1.5：检查其他关键依赖的 Python 3.14 支持（全部OK）

## 任务2：卸载旧版 Python
- [x] 任务2.1：备份现有虚拟环境（可选）- venv_old 已存在
- [x] 任务2.2：删除现有虚拟环境 `venv` - 不需要，venv已经是3.14.5
- [x] 任务2.3：卸载 Python 3.11.9（删除 `E:\software\python311`）

## 任务3：下载并安装 Python 3.14.5
- [x] 任务3.1：下载 Python 3.14.5 amd64 安装程序
- [x] 任务3.2：静默安装到 `E:\software\python314`
- [x] 任务3.3：验证安装（版本号和架构）- Python 3.14.5 64-bit

## 任务4：重建虚拟环境
- [x] 任务4.1：使用 Python 3.14.5 创建虚拟环境
- [x] 任务4.2：升级虚拟环境中的 pip
- [x] 任务4.3：验证虚拟环境正常工作

## 任务5：安装依赖
- [x] 任务5.1：安装 PyQt6 和 PyQt6-Qt6
- [x] 任务5.2：安装 numpy 和 pandas
- [x] 任务5.3：安装大模型 API 包（openai、anthropic、google-generativeai）
- [x] 任务5.4：安装 faiss-cpu
- [x] 任务5.5：安装其他工具依赖（requests、aiohttp、loguru 等）
- [x] 任务5.6：安装测试依赖（pytest、pytest-asyncio）
- [x] 任务5.7：验证所有依赖安装成功

## 任务6：系统验证
- [x] 任务6.1：运行 HyperBrain CLI 测试 - 203个测试全部通过
- [x] 任务6.2：验证所有 8 个认知层正常初始化
- [x] 任务6.3：验证数据库和向量存储正常
- [x] 任务6.4：更新 requirements.txt 为 Python 3.14.5 兼容版本

# 任务依赖关系
- 任务1 → 任务2 → 任务3 → 任务4 → 任务5 → 任务6
