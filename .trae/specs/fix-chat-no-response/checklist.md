# HyperBrain 聊天不回复问题修复检查清单

## app.py 重构检查
- [x] `run_gui()` 方法已改为同步方法（移除 async 关键字）
- [x] `run_gui()` 中创建 `AsyncLoopThread` 并初始化 Brain
- [x] `run_gui()` 中正确关闭 Brain 和 `AsyncLoopThread`
- [x] `main()` 函数中 GUI 模式不调用 `asyncio.run()`
- [x] `main()` 函数中 CLI 模式仍调用 `asyncio.run()`

## BrainWorker 线程类检查
- [x] `BrainWorker` 继承 `QThread`
- [x] 定义 `result_ready(str)` 信号
- [x] 定义 `error_occurred(str)` 信号
- [x] `run()` 方法使用 `asyncio.run_coroutine_threadsafe()` 执行 `brain.process()`
- [x] `run()` 方法使用 `future.result(timeout=...)` 设置超时
- [x] 超时时间从配置读取（默认 90 秒）

## MainWindow 消息处理检查
- [x] `_on_message_sent()` 创建 `BrainWorker` 实例
- [x] `BrainWorker` 信号连接到主线程槽函数
- [x] 槽函数在主线程中更新 UI（`add_message`）
- [x] 发送消息后显示"思考中..."提示
- [x] 收到响应后清除提示并显示内容
- [x] 发生错误时显示错误信息

## 入口点统一检查
- [x] `启动GUI.bat` 调用正确的入口点
- [x] `app.py` 和 `main.py` 入口点一致
- [x] 无重复的事件循环创建

## 集成测试检查（基础）
- [x] GUI 能正常启动不报错
- [x] 发送消息后 UI 不卡死（可以移动窗口、点击按钮）
- [x] 收到响应后正确显示在聊天区域
- [x] 超时情况下显示"请求超时"错误
- [x] 关闭窗口后程序正常退出（无残留进程）
- [x] 连续发送多条消息，每条都能正确处理

## UI 可读性改进检查（新增）
- [x] `themes.py` 中暗色主题 `text_primary` 已改为 `#ffffff`
- [x] `chat_widget.py` 中 `time_label` 颜色使用主题 `text_secondary`
- [x] 暗色主题下消息正文显示为纯白（`#ffffff`）
- [x] 亮色主题下消息正文不受影响（仍为 `#212121`）
- [x] 时间标签在暗色/亮色主题下均清晰可读

## 超时取消功能检查（新增）
- [x] `BrainWorker.stop()` 方法支持取消正在运行的 future
- [x] 用户点击"停止"按钮后，当前请求被终止
- [x] 超时后显示错误信息，输入框恢复可用
- [x] 取消/超时后"思考中..."消息被正确移除
- [x] 停止按钮在请求期间可用（enabled），完成后禁用
- [x] 取消后可立即发送新消息

## 模型调用修复检查（新增）
- [x] `ollama_model.py` 在 content 为空时尝试使用 thinking 字段
- [x] `OllamaModelUsage.__init__()` 不再传递 `total_tokens` 参数
- [x] 默认模型已改为 `gemma2:2b`（config.yaml 和 config.py）
- [x] 发现的本地模型优先级为 5，低于默认模型的 9
- [x] CLI 模式下模型调用正常，响应时间约 3-6 秒
- [x] 故障切换机制正常工作（qwen3.5 超时后切换到 gemma2:2b）

## 会话历史和消息持久化检查（新增）
- [x] `main_window.py` 中添加 `_save_message_to_db()` 方法
- [x] 用户消息发送后保存到数据库
- [x] AI 回复接收后保存到数据库
- [x] 数据库中 `conversations` 表有新消息记录
- [x] 点击历史会话能加载对应的消息

## 记忆面板数据连接检查（新增）
- [x] `memory_viz.py` 的 `refresh_data()` 优先使用 `self.brain.memory_manager`
- [x] 记忆面板能获取 Brain 的实际记忆数据
- [x] 短期记忆和长期记忆统计显示正确

## 启动脚本和依赖检查（新增）
- [x] `启动GUI.bat` 和 `start_gui.bat` 使用 `py` 命令
- [x] 所有依赖已安装（pyyaml, aiohttp, pygments, loguru, pyqt6, markdown, psutil, pydantic, numpy）
- [x] GUI 能正常启动无报错

## 最终用户体验验证（新增）
- [x] 启动 GUI 后聊天消息字体为黑色/纯白，清晰可读
- [x] 发送消息后显示"思考中..."提示
- [x] 正常响应后显示 AI 回复内容
- [x] 超时后显示错误提示，且可继续交互
- [x] 点击"停止"可取消正在进行的请求
- [x] 连续对话功能正常，无卡死或阻塞
- [x] 消息保存到数据库，可在历史会话中查看
