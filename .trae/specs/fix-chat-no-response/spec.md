# HyperBrain 聊天不回复问题修复规格说明书

## Why
用户发送消息后，系统显示"处理失败：Event loop is closed"或长时间无响应。根本原因是：
1. `app.py` 的 `run_gui()` 在 async 协程中运行 Qt 事件循环，导致 asyncio 和 Qt 事件循环冲突
2. `main.py` 的 `AsyncLoopThread` 方案中，`submit_coroutine` 回调在后台线程直接操作 Qt UI，存在线程安全问题
3. 消息处理缺乏超时机制，模型响应慢时用户无反馈
4. `qwen3.5` 系列模型在 Ollama 中返回空 content，导致模型响应异常
5. `OllamaModelUsage` 继承 `ModelUsage` 时错误传递了 `total_tokens` 参数（dataclass 的 `init=False` 字段）
6. 发现的本地模型优先级过高，覆盖了用户配置的默认模型

此外，用户反馈：
- 聊天消息字体颜色为浅灰色（暗色主题 `#e0e0e0`），在暗色背景下对比度不足，难以阅读，要求改为黑色（深色）
- 回复超时后对话框无法取消，需要添加取消功能

## What Changes
- **BREAKING**: 重构 `app.py` 的 GUI 启动逻辑，从 async 模式改为同步模式
- 在 `main_window.py` 中创建 `BrainWorker`（QThread）处理消息
- 使用 `pyqtSignal` 实现线程安全的 UI 更新
- 添加消息处理超时和错误处理
- 保留 `AsyncLoopThread` 用于 Brain 生命周期管理
- **UI改进**: 暗色主题 `text_primary` 从 `#e0e0e0` 改为 `#ffffff`（纯白），提升可读性
- **UI改进**: `chat_widget.py` 中 `time_label` 硬编码颜色 `#757575` 改为使用主题 `text_secondary`
- **功能增强**: BrainWorker 支持取消/停止功能，超时或用户主动取消时终止处理
- **功能增强**: 超时后显示可取消的提示对话框，用户可主动关闭
- **模型修复**: `ollama_model.py` 在 content 为空时尝试使用 thinking 字段（qwen3.5 特殊行为）
- **Bug修复**: 修复 `OllamaModelUsage.__init__()` 错误传递 `total_tokens` 参数的问题
- **配置修复**: 将默认模型从 `qwen3.5:2b` 改为 `gemma2:2b`（响应正常）
- **调度修复**: 发现的本地模型优先级从 10 降为 5，确保默认模型优先被选择

## Impact
- Affected specs: GUI模式启动、消息处理流程、线程安全、UI可读性、超时取消交互、模型调用
- Affected code: hyperbrain/app.py, hyperbrain/ui/main_window.py, hyperbrain/main.py, hyperbrain/ui/themes.py, hyperbrain/ui/chat_widget.py, hyperbrain/models/ollama_model.py, hyperbrain/models/model_manager.py, hyperbrain/core/config.py, config.yaml
- 涉及系统：asyncio 事件循环、Qt 事件循环、线程间通信、主题颜色管理、Ollama 模型集成

## ADDED Requirements
### Requirement: 消息处理线程安全
系统SHALL使用 QThread + pyqtSignal 处理消息，确保 UI 更新在主线程执行。

#### Scenario: 发送消息
- **WHEN** 用户在输入框输入消息并点击发送
- **THEN** 消息在后台线程处理，结果通过信号传回主线程显示

#### Scenario: 处理超时
- **WHEN** 模型响应超过配置的超时时间
- **THEN** 显示超时错误，不阻塞 UI，且用户可以取消当前请求

#### Scenario: 处理异常
- **WHEN** 消息处理过程中发生异常
- **THEN** 捕获异常并通过信号显示错误信息

### Requirement: 字体颜色可读性
系统SHALL在暗色主题下使用足够深的字体颜色，确保消息内容清晰可读。

#### Scenario: 暗色主题消息显示
- **WHEN** 用户使用暗色主题查看聊天消息
- **THEN** 消息正文颜色为 `#ffffff`（纯白），时间标签使用主题 `text_secondary`

### Requirement: 超时取消功能
系统SHALL在请求处理期间允许用户取消当前操作，包括超时后的状态恢复。

#### Scenario: 用户主动取消
- **WHEN** 用户点击"停止"按钮
- **THEN** 当前 BrainWorker 线程被取消，UI 恢复到可输入状态

#### Scenario: 超时后取消
- **WHEN** 请求超时后显示错误信息
- **THEN** 用户可关闭错误提示，输入框恢复可用，可发送新消息

## MODIFIED Requirements
### Requirement: GUI 启动模式
原 `app.py` 的 `run_gui()` 是 async 方法，现在改为同步方法。

**修改前**:
```python
async def run_gui(self) -> int:
    app = QApplication(sys.argv)
    window = MainWindow(brain=self.brain)
    return app.exec()
```

**修改后**:
```python
def run_gui(self) -> int:
    app = QApplication(sys.argv)
    async_thread = AsyncLoopThread()
    async_thread.run_coroutine(self.brain.initialize())
    async_thread.run_coroutine(self.brain.start())
    window = MainWindow(brain=self.brain, async_thread=async_thread)
    exit_code = app.exec()
    async_thread.run_coroutine(self.brain.shutdown())
    async_thread.stop()
    return exit_code
```

### Requirement: 暗色主题字体颜色
原暗色主题 `text_primary` 为 `#e0e0e0`（浅灰），现改为 `#ffffff`（纯白）。

**修改前**:
```python
ThemeType.DARK: {
    "text_primary": "#e0e0e0",
    ...
}
```

**修改后**:
```python
ThemeType.DARK: {
    "text_primary": "#ffffff",
    ...
}
```

### Requirement: 时间标签颜色
原 `time_label` 使用硬编码 `#757575`，现改为使用主题 `text_secondary`。

**修改前**:
```python
self.time_label.setStyleSheet("font-size: 11px; color: #757575;")
```

**修改后**:
```python
self.time_label.setStyleSheet(f"font-size: 11px; color: {colors['text_secondary']};")
```

## REMOVED Requirements
无
