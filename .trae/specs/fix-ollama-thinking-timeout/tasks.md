# Ollama Thinking 模型超时修复任务清单

> 目标：解决 qwen3.5 等 thinking 模型响应 100s+ 触发 90s BrainWorker 超时的反复问题，统一从超时配置、流式输出、thinking 抑制、降级链、明确错误信息、默认模型六个维度修复。

---

## 任务1：扩展 ModelConfig 与 core/config 默认值
- [x] 1.1 在 `hyperbrain/models/base.py` 的 `ModelConfig` 中新增 `think: bool = True`、`fallback_models: list[str] = []`、`worker_timeout: float = Field(default=180.0, ge=30, le=600)`、`stream: bool = True`
- [x] 1.2 在 `hyperbrain/core/config.py` 的 `ModelConfig` dataclass 中同步增加上述字段，默认值与 Pydantic 一致
- [x] 1.3 在 `config.yaml` 增加 `brain.worker_timeout: 180`、`ollama.think: true`、`ollama.stream: true`、`ollama.fallback_models: ["gemma2:2b"]` 段
- [x] 1.4 把 `default_model` 从 `qwen3.5:2b` 改为 `gemma2:2b`（前提：用户本地已拉取该模型；否则保留原值并加 TODO 注释）

## 任务2：BrainWorker 可配置超时
- [x] 2.1 修改 `hyperbrain/ui/main_window.py` 中 `BrainWorker.__init__` 的 `timeout` 参数默认值为 `None`
- [x] 2.2 在 `BrainWorker.run()` 中读取 `self.brain.config.brain.worker_timeout` 当 `timeout is None`
- [x] 2.3 在 `_on_message_sent()` 中将构造参数改为 `timeout=settings.brain.worker_timeout`
- [x] 2.4 在 `error_occurred.emit()` 处改为 emit 结构化字典：`{"code": "MODEL_TIMEOUT", "model": ..., "elapsed_sec": ..., "suggestion": ...}`
- [x] 2.5 在 `_on_brain_error()` 中根据 `code` 渲染不同 UI（MODEL_TIMEOUT 走专门带"打开设置"按钮的提示）

## 任务3：OllamaModel 增加 /api/show 探测与 think 字段
- [x] 3.1 在 `OllamaModel.initialize()` 末尾调用 `POST /api/show {name: model_name}`，读取返回 JSON
- [x] 3.2 通过 `model_info`/`capabilities`/`details.family` 匹配 `qwen3*` / `deepseek-r1*` / `qwq*` → 设置 `self.is_thinking = True`
- [x] 3.3 在日志和状态栏（`MainWindow._update_status`）中输出"已加载 thinking 模型 X，建议关闭 think 或切换到非 thinking 模型"
- [x] 3.4 修改 `chat()` 构造请求体时根据 `self.config.think` 决定是否加入 `"think": false`（Ollama 0.9+ 支持）
- [x] 3.5 当 Ollama 版本不支持 think 字段时（响应 400）→ 回退原行为并 log warning

## 任务4：OllamaModel 流式响应
- [x] 4.1 在 `OllamaModel` 新增 `async def stream_chat(self, prompt, **kwargs) -> AsyncIterator[str]`，内部使用 `stream=True` + `aiohttp` chunked read
- [x] 4.2 `chat()` 检测 `self.config.stream`：`True` 时调用 `stream_chat()` 并 join chunk 返回（保持向后兼容）
- [x] 4.3 在 `BrainWorker` 中新增 `partial_chunk` 信号，`process_stream` 模式下按 chunk emit
- [x] 4.4 `MainWindow._on_message_sent` 接收 `partial_chunk` → 追加到当前 AI 气泡（QTextEdit append / cursor 移到末尾）

## 任务5：ModelManager 降级链
- [x] 5.1 在 `ModelManager.chat_with_fallback(prompt, primary, fallbacks)` 中实现：先尝试 primary，超时则用 fallback[0] 重试，依次类推
- [x] 5.2 `Brain.process()` 在调用 model 前查询 `config.ollama.fallback_models`，非空时走 `chat_with_fallback`
- [x] 5.3 当发生降级时，emit `model_fallback` 信号，UI 状态栏显示"主模型 X 超时，已切换到 Y"
- [x] 5.4 用户可在 settings_dialog 中编辑 fallback_models 列表（QListWidget + 添加/删除按钮）

## 任务6：明确超时错误 UI
- [x] 6.1 在 `MainWindow` 中实现 `_show_timeout_dialog(payload)` 弹出非模态 QMessageBox，包含：
  - 标题："模型响应超时"
  - 正文："模型 X 在 N 秒内未响应"
  - 三个可点击按钮："调高超时（→设置）"、"切换到 fallback（Y）"、"关闭"
- [x] 6.2 "调高超时"按钮：直接打开 settings_dialog 并跳到超时设置项
- [x] 6.3 "切换到 fallback"按钮：调用 `model_manager.set_active_model("gemma2:2b")` 并提示重新发送
- [x] 6.4 错误信息底部追加技术细节（堆栈截断 5 行）供高级用户排查

## 任务7：settings_dialog 新增超时与降级 UI
- [x] 7.1 在 `settings_dialog.py` 增加 "Brain" 分组：`worker_timeout` QSpinBox（30-600，step 30）
- [x] 7.2 在 "Ollama" 分组中增加：`think` QCheckBox、`stream` QCheckBox、`fallback_models` QListWidget
- [x] 7.3 保存时把字段写回 `ModelConfig` 并 emit `settings_changed`

## 任务8：单元测试与回归
- [x] 8.1 新增 `tests/test_thinking_timeout.py`：
  - 测试 BrainWorker 默认 timeout 从 config 读取
  - 测试 OllamaModel.is_thinking 探测（mock /api/show 返回 qwen3 家族 → True）
  - 测试 chat() 在 think=False 时请求体含 "think": false
  - 测试 stream_chat() 在 mock 响应下按 chunk 输出
  - 测试 chat_with_fallback 在 primary TimeoutError 时切换到 fallback
  - 测试 _show_timeout_dialog 携带正确的 code/model/elapsed
- [x] 8.2 运行 `test_ui_refresh.py`、`test_all_features.py`、`test_model_and_shortmem.py`、`test_hermes_*.py` 全部回归（hermes 20+其他 180+ 共 200+ 通过；test_gui_session_manager 已有 1 个不相关失败，非本次改动引入）
- [x] 8.3 端到端：用 mock ollama server 模拟 100s 延迟，验证 180s timeout 下不报超时；模拟 200s 延迟验证降级链

## 任务9：文档与配置示例
- [x] 9.1 在 `config.yaml` 顶部注释解释 `worker_timeout` 字段及 thinking 模型风险
- [x] 9.2 在 `README.md`（如存在）"常见问题" 章节追加：thinking 模型超时怎么解决
- [x] 9.3 在 settings_dialog tooltip 中解释每个新增字段

---

## 任务依赖关系

```
任务1 (config) ──┬── 任务2 (BrainWorker) ──┐
                 ├── 任务3 (Ollama 探测) ──┼── 任务8 (测试)
                 ├── 任务4 (流式)         │
                 └── 任务5 (降级链) ──────┤
                                          │
任务7 (settings UI) ──────────────────────┴── 任务6 (错误 UI)
                                                 │
                                          任务9 (文档)
```

并行：任务2/3/4/5 可并行（无相互依赖，仅依赖任务1的 config 字段）。
串行：任务6/7/8 必须在 2-5 完成后才能验证。

---

## 关键文件清单

| 文件 | 改动范围 |
|------|---------|
| `hyperbrain/ui/main_window.py` | BrainWorker、`_on_message_sent`、`_show_timeout_dialog` |
| `hyperbrain/ui/settings_dialog.py` | 新增 Brain/Ollama 字段 UI |
| `hyperbrain/models/ollama_model.py` | /api/show 探测、think 字段、stream_chat |
| `hyperbrain/models/model_manager.py` | chat_with_fallback、set_active_model |
| `hyperbrain/models/base.py` | ModelConfig 新字段 |
| `hyperbrain/core/config.py` | dataclass 同步 |
| `hyperbrain/core/brain.py` | 集成 chat_with_fallback、信号透传 |
| `config.yaml` | 默认值与 fallback 列表 |
| `tests/test_thinking_timeout.py` | 新增 6+ 测试 |

