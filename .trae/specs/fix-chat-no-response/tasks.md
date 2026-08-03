# HyperBrain 聊天不回复问题修复任务清单

## 任务1：重构 app.py GUI 启动逻辑
- [x] 任务1.1：将 `run_gui()` 从 async 改为同步方法
- [x] 任务1.2：在 `run_gui()` 中使用 `AsyncLoopThread` 初始化 Brain
- [x] 任务1.3：确保 Qt 事件循环和 asyncio 事件循环不冲突
- [x] 任务1.4：在 GUI 关闭时正确关闭 Brain 和 `AsyncLoopThread`

## 任务2：创建 BrainWorker 线程类
- [x] 任务2.1：在 `main_window.py` 中创建 `BrainWorker`（继承 QThread）
- [x] 任务2.2：定义 `result_ready`、`error_occurred` 信号
- [x] 任务2.3：在 `run()` 方法中使用 `asyncio.run_coroutine_threadsafe()` 执行 `brain.process()`
- [x] 任务2.4：添加超时处理（使用 `future.result(timeout=...)`）

## 任务3：重构 MainWindow 消息处理
- [x] 任务3.1：移除 `AsyncLoopThread` 参数（不再需要）
- [x] 任务3.2：在 `_on_message_sent()` 中创建 `BrainWorker` 实例
- [x] 任务3.3：连接 `BrainWorker` 信号到 UI 更新槽函数
- [x] 任务3.4：添加加载状态显示（发送后显示"思考中..."）

## 任务4：统一入口点
- [x] 任务4.1：修改 `app.py` 的 `main()` 函数，GUI 模式不进入 asyncio.run()
- [x] 任务4.2：确保 CLI 模式仍使用 asyncio.run()
- [x] 任务4.3：更新 `启动GUI.bat` 使用正确的入口点

## 任务5：集成测试
- [x] 任务5.1：验证 GUI 能正常启动不报错
- [x] 任务5.2：验证发送消息后 UI 不卡死
- [x] 任务5.3：验证收到响应后正确显示
- [x] 任务5.4：验证超时情况下显示错误信息
- [x] 任务5.5：验证关闭窗口后程序正常退出

## 任务6：修复字体颜色可读性（新增）
- [x] 任务6.1：修改 `themes.py` 中暗色主题 `text_primary` 从 `#e0e0e0` 改为 `#ffffff`
- [x] 任务6.2：修改 `chat_widget.py` 中 `time_label` 硬编码颜色，改为使用主题 `text_secondary`
- [x] 任务6.3：验证亮色主题不受影响

## 任务7：增强超时取消功能（新增）
- [x] 任务7.1：增强 `BrainWorker.stop()` 方法，支持取消正在运行的 future
- [x] 任务7.2：完善 `main_window.py` 中 `_remove_thinking_message()` 方法
- [x] 任务7.3：确保超时或取消后输入框恢复可用状态
- [x] 任务7.4：验证停止按钮在请求期间可用，完成后禁用

## 任务8：最终集成验证（新增）
- [x] 任务8.1：启动 GUI 验证字体颜色为纯白
- [x] 任务8.2：验证发送消息后"思考中..."显示正常
- [x] 任务8.3：验证超时后显示错误且可继续发送新消息
- [x] 任务8.4：验证点击"停止"按钮可取消当前请求
- [x] 任务8.5：验证连续发送多条消息，每条都能正确处理

## 任务9：修复模型调用问题（新增）
- [x] 任务9.1：诊断 qwen3.5 模型返回空 content 的问题
- [x] 任务9.2：修复 `ollama_model.py` 在 content 为空时使用 thinking 字段
- [x] 任务9.3：修复 `OllamaModelUsage.__init__()` 错误传递 `total_tokens` 参数
- [x] 任务9.4：将默认模型从 `qwen3.5:2b` 改为 `gemma2:2b`
- [x] 任务9.5：修复发现的本地模型优先级过高问题（从 10 降为 5）
- [x] 任务9.6：验证 CLI 模式下模型调用正常

## 任务10：GUI 模式最终验证（新增）
- [x] 任务10.1：启动 GUI 并发送消息，验证正常响应
- [x] 任务10.2：验证微信风格消息气泡显示正确
- [x] 任务10.3：验证停止按钮功能正常
- [x] 任务10.4：验证连续对话功能正常

## 任务11：修复会话历史和消息持久化（新增）
- [x] 任务11.1：诊断会话历史为空的原因（session_id 不匹配）
- [x] 任务11.2：在 `main_window.py` 中添加 `_save_message_to_db()` 方法
- [x] 任务11.3：在 `_on_message_sent()` 中保存用户消息到数据库
- [x] 任务11.4：在 `_handle_response()` 中保存 AI 回复到数据库
- [x] 任务11.5：验证新消息正确保存到数据库

## 任务12：修复记忆面板数据连接（新增）
- [x] 任务12.1：诊断 `memory_viz.py` 创建新 MemoryManager 实例的问题
- [x] 任务12.2：修改 `refresh_data()` 优先使用 `self.brain.memory_manager`
- [x] 任务12.3：验证记忆面板能正确显示 Brain 的记忆数据

## 任务13：修复启动脚本和依赖（新增）
- [x] 任务13.1：修复 `启动GUI.bat` 和 `start_gui.bat` 使用 `py` 命令
- [x] 任务13.2：安装所有缺失的依赖（pyyaml, aiohttp, pygments, loguru, pyqt6, markdown, psutil, pydantic, numpy）
- [x] 任务13.3：验证 GUI 能正常启动

---

## 任务依赖关系
- 任务2 依赖 任务1（BrainWorker 需要 AsyncLoopThread 已初始化 Brain）
- 任务3 依赖 任务2（MainWindow 使用 BrainWorker）
- 任务4 依赖 任务1（入口点调用 run_gui）
- 任务5 依赖 任务3、任务4（最终验证）
- 任务6 独立（UI颜色修改，不影响逻辑）
- 任务7 依赖 任务2、任务3（在现有 BrainWorker 和 MainWindow 基础上增强）
- 任务8 依赖 任务6、任务7（最终验证所有改进）
- 任务9 独立（模型层修复，不影响 UI 逻辑）
- 任务10 依赖 任务8、任务9（最终 GUI 验证）
