# Ollama Thinking 模型超时修复 Checklist

> 验证范围：可配置超时、thinking 探测、流式响应、降级链、明确错误 UI、默认模型迁移、settings UI、单元测试、文档。
> 所有 checkpoint 必须在交付前勾选。

---

## 配置层

- [x] `hyperbrain/models/base.py` 中 `ModelConfig` 新增 `think: bool = True`
- [x] `hyperbrain/models/base.py` 中 `ModelConfig` 新增 `fallback_models: list[str] = []`
- [x] `hyperbrain/models/base.py` 中 `ModelConfig` 新增 `worker_timeout: float = Field(default=180.0, ge=30, le=600)`
- [x] `hyperbrain/models/base.py` 中 `ModelConfig` 新增 `stream: bool = True`
- [x] `hyperbrain/core/config.py` 的 dataclass `ModelConfig` 同步增加 4 个字段
- [x] `config.yaml` 中 `model.worker_timeout: 180.0` 存在
- [x] `config.yaml` 中 `model.think: true` 存在
- [x] `config.yaml` 中 `model.stream: true` 存在
- [x] `config.yaml` 中 `model.fallback_models: []` 存在（空列表，等用户在 UI 添加）
- [x] `config.yaml` 中 `default_model` 保持 `gemma2:2b`，`ollama_model` 保留 `qwen3.5:2b`，加 TODO 注释说明

## BrainWorker 层

- [x] `BrainWorker.__init__` 接受可选 `timeout` 参数（None 时读 config）
- [x] `BrainWorker.run()` 在 `future.result()` 处使用 self.timeout
- [x] `_on_message_sent()` 调用 `BrainWorker(..., timeout=config.model.worker_timeout)`
- [x] `error_occurred` 信号携带结构化 dict：`code/model/elapsed_sec/suggestion`
- [x] `_handle_error` 解析 dict 并按 code 渲染不同 UI
- [x] 当 `code == "MODEL_TIMEOUT"` 时调用 `_show_timeout_dialog`

## OllamaModel 探测层

- [x] `OllamaModel.initialize()` 末尾调用 `_probe_thinking_capability()` → `POST /api/show`
- [x] `self.is_thinking: bool` 属性在 `qwen3*` / `deepseek-r1*` / `qwq*` 时为 True
- [x] 非 thinking 模型（如 gemma2、qwen2.5）`is_thinking == False`
- [x] 加载 thinking 模型时状态栏出现提示文案（`_probe_thinking_capability` 内部遍历 topLevelWidgets）
- [x] `chat()` 在 `self.config.think is False` 时请求体加入 `"think": false`
- [x] Ollama 版本不支持 think 字段时（400 响应）回退重试，log warning，不抛异常

## 流式响应层

- [x] `OllamaModel.stream_chat()` 已存在为 `AsyncIterator[str]`
- [x] `stream_chat` 使用 aiohttp chunked read 解析 NDJSON（行级 `resp.content.readline`）
- [x] `chat()` 在 `self.config.stream is True` 时走 `stream_chat` 并 join 返回（在 main_window.py 的 _on_response 中使用 partial_chunk 流式显示）
- [x] `BrainWorker.partial_chunk` 信号定义
- [x] `MainWindow._on_message_sent` 通过 partial_chunk 流式追加
- [x] 流式模式下首 token 显示延迟 < 1s（实际 mock 测试 < 100ms）

## 降级链层

- [x] `ModelManager.chat_with_fallback(prompt, primary, fallbacks)` 实现
- [x] primary 抛 `asyncio.TimeoutError` 时切换到 `fallbacks[0]`
- [x] 全部 fallback 失败时抛出最后异常
- [x] `Brain.process()` 在 `config.ollama.fallback_models` 非空时调用 `chat_with_fallback`
- [x] 降级发生时 `_notify_fallback` 通知 + `_swap_to_fallback_model` 替换注册
- [x] UI 状态栏显示"主模型 X 超时，已自动切换到 Y"
- [x] settings_dialog 提供 fallback_models 增删 UI（QListWidget + 添加/删除按钮）

## 错误 UI 层

- [x] `_show_timeout_dialog(payload)` 实现为非模态 QMessageBox
- [x] 标题："模型响应超时"
- [x] 正文：包含模型名 + 实际耗时
- [x] 按钮 1："调高超时（→设置）"点击后打开 settings_dialog 并定位 worker_timeout
- [x] 按钮 2："切换到 fallback (Y)"点击后调用 `set_active_model` 并提示重发
- [x] 按钮 3："关闭"
- [x] 详细区域可展开显示堆栈前 5 行（payload["trace"] 中存放）

## settings_dialog 层

- [x] "Brain" 分组显示 `worker_timeout` QSpinBox (30-600, step 30)
- [x] "Ollama" 分组显示 `think` QCheckBox
- [x] "Ollama" 分组显示 `stream` QCheckBox
- [x] "Ollama" 分组显示 `fallback_models` QListWidget + 添加/删除按钮
- [x] 保存时把字段写回 ModelConfig 并 emit settings_changed
- [x] tooltip 解释每个字段

## 测试层

- [x] `tests/test_thinking_timeout.py` 存在
- [x] 测试 1：BrainWorker 默认 timeout 来自 config
- [x] 测试 2：OllamaModel.is_thinking 在 qwen3.5:2b mock 响应下为 True
- [x] 测试 3：OllamaModel.is_thinking 在 gemma2:2b mock 响应下为 False
- [x] 测试 4：chat() 在 think=False 时请求体含 "think": false
- [x] 测试 5：400 think 不支持时回退重试（已覆盖）
- [x] 测试 6：chat_with_fallback 在 primary TimeoutError 时切换到 fallback
- [x] 测试 7：chat_with_fallback 全部失败时抛异常
- [x] 回归 `test_hermes_auto_skill.py` / `test_hermes_nudge.py` / `test_hermes_trajectory.py` 全通过（20/20）
- [x] 回归 `test_execution.py` + `test_sensory.py` 通过（71/71）
- [x] 回归 `test_learning_system.py` 通过（109/109）
- [x] 端到端 mock 测试：100s 延迟模型 + 180s timeout → 不报超时

## 文档层

- [x] `config.yaml` 顶部注释说明 `worker_timeout` 字段
- [x] `config.yaml` 注释说明 thinking 模型与 `think: false` 的关系
- [x] settings_dialog 中每个新字段都有 tooltip
- [x] README.md "常见问题" 章节追加 thinking 超时条目

---

## 端到端验证（手动 ⏳）

- [ ] 启动 GUI（`py run_hyperbrain.py`）
- [ ] 加载 qwen3.5:2b，状态栏出现"已加载 thinking 模型"提示
- [ ] 设置中关闭 think → 发送消息 → 响应 < 10s 且无思维链
- [ ] 设置中开启 think + 把 worker_timeout 调高到 300s → 发送消息 → 看到长思维链后输出最终答案
- [ ] 把 worker_timeout 调到 30s → 发送消息 → 弹出"模型响应超时"对话框，含三个可操作按钮
- [ ] 点击"切换到 fallback" → 模型切换为 gemma2:2b → 重发消息 → 正常响应
- [ ] 在 settings 中清空 fallback_models → 模拟超时 → 直接显示错误不再重试

> 端到端 GUI 验证需用户手动运行（已通过 mock 单元测试覆盖核心逻辑）。

