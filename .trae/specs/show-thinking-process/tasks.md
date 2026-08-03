# Ollama 思考模型思维链可视化任务清单

> 目标：让 qwen3.5:2b 等 thinking 模型能正常生成 + 完整显示思维链，180s 超时；GUI 折叠区显示。

---

## 任务 1：ModelResponse + OllamaModel 解析 thinking 字段

- [ ] 1.1 `hyperbrain/models/base.py` 中 `ModelResponse` 新增 `thinking: str = ""` 字段
- [ ] 1.2 `OllamaModel._parse_chat_response()` 提取 `resp.message.get("thinking", "")` 存入 `ModelResponse.thinking`
- [ ] 1.3 `OllamaModel.chat()` 内部 catch OllamaConnectionError / ModelError 时也保留 thinking 字段
- [ ] 1.4 验证：`py -3.14 -c "from hyperbrain.models.base import ModelResponse; m=ModelResponse(content='hi', thinking='let me think'); print(m.thinking)"`
- [ ] 1.5 现有 21 个 test_thinking_timeout 测试不挂

## 任务 2：stream_chat 区分 yield thinking / content

- [ ] 2.1 `OllamaModel.stream_chat()` 内部把每个 chunk 的 `thinking` 字段和 `content` 字段分别处理
- [ ] 2.2 方案 A：yield `(type, text)` 元组，其中 type ∈ {"thinking", "content"}
- [ ] 2.3 方案 B：保留 yield 字符串不变，**新增** `partial_thinking` 字段在 ModelResponse 上（不推荐，因为 yield 是流式的）
- [ ] 2.4 采用方案 A：yield `(type, text)` 元组
- [ ] 2.5 `chat()` 在 `config.stream=True` 时调用 `stream_chat()` 并 join：
  - 累加 `thinking` 字段
  - 累加 `content` 字段
  - 返回 `ModelResponse(thinking=..., content=...)`
- [ ] 2.6 验证：mock Ollama 流式返回 3 个 chunk（其中 1 个含 thinking），验证 join 后 thinking 完整

## 任务 3：think 默认 true

- [ ] 3.1 `config.yaml` 中 `think: false` → `think: true`（如果之前 spec 改了 false）
- [ ] 3.2 `hyperbrain/core/config.py` 中 `think: bool = True`
- [ ] 3.3 `hyperbrain/models/base.py` 中 `ModelConfig.think: bool = True`
- [ ] 3.4 `hyperbrain/ui/settings_dialog.py` 中 think QCheckBox 默认勾选
- [ ] 3.5 验证：`py -3.14 -c "from hyperbrain.core.config import get_config; print(get_config().model.think)"` → `True`

## 任务 4：--timeout-think 默认 180

- [ ] 4.1 `scripts/diagnose_ollama.py` 中 `--timeout-think` 默认从 60 改 180
- [ ] 4.2 argparse help 文本更新
- [ ] 4.3 验证：`py -3.14 scripts/diagnose_ollama.py --model qwen3.5:2b` Step 6 用 180s

## 任务 5：BrainWorker.partial_thinking 信号

- [ ] 5.1 `hyperbrain/ui/main_window.py` 中 `BrainWorker` 类新增 `partial_thinking = pyqtSignal(str)` 信号
- [ ] 5.2 `BrainWorker.run()` 在 `await mm.chat_with_fallback(...)` 时，**改为流式调用 `mm.stream_chat()`**
- [ ] 5.3 `stream_chat()` 每次 yield `(type, text)` 时：
  - type="thinking" → `self.partial_thinking.emit(text)`
  - type="content" → `self.partial_chunk.emit(text)`（已有）
  - 累加到 `self._full_thinking` / `self._full_content`
- [ ] 5.4 `BrainWorker.error_occurred` / `result_ready` 携带 thinking 字段
- [ ] 5.5 `_handle_error` 暂不处理 thinking
- [ ] 5.6 验证：mock thinking 响应，验证 partial_thinking.emit 被调用

## 任务 6：MainWindow 思维链 UI

- [ ] 6.1 `MainWindow` 新增 `_on_partial_thinking(text)` 槽函数
- [ ] 6.2 当前 AI 消息气泡的 widget 增加可折叠的"💭 思考过程"区域
  - 默认折叠（节省空间）
  - 点击"💭 思考过程 (X 字符)" 展开
  - 展开时显示淡灰色 `#888888` 等宽字体 12px 文本
  - 展开后可再次点击折叠
- [ ] 6.3 `_on_partial_thinking` 追加文本到当前气泡的 thinking 区
- [ ] 6.4 消息完成后（`result_ready`），thinking 区显示完整文本
- [ ] 6.5 非 thinking 模型（无 partial_thinking emit）不显示折叠区
- [ ] 6.6 验证：发消息给 qwen3.5:2b，看到"💭 思考过程"折叠条 + 展开后灰色文本

## 任务 7：Brain.process 透传 thinking

- [ ] 7.1 `Brain.process()` 把 `model_response.thinking` 存到 `ProcessingResult.metadata["thinking"]`
- [ ] 7.2 不写入长期记忆（只 metadata 透传）
- [ ] 7.3 不写入工作记忆
- [ ] 7.4 验证：`process('q')` 返回的 `result.metadata["thinking"]` 含 thinking 文本

## 任务 8：单元测试 `tests/test_thinking_visualization.py`

- [ ] 8.1 测试 ModelResponse.thinking 字段
- [ ] 8.2 测试 `_parse_chat_response` 提取 thinking
- [ ] 8.3 测试 `_parse_chat_response` 缺失 thinking 字段时为空字符串
- [ ] 8.4 测试 stream_chat yield (type, text) 元组
- [ ] 8.5 测试 chat() 在 stream=True 时 join 累加 thinking
- [ ] 8.6 测试 BrainWorker.partial_thinking 信号 emit
- [ ] 8.7 测试 config.think 默认 True
- [ ] 8.8 测试 diagnose_ollama.py --timeout-think 默认 180
- [ ] 8.9 回归：现有 69 个测试不挂

---

## 任务依赖关系

```
任务1 (ModelResponse) ─┬── 任务2 (stream_chat) ─┐
任务3 (think 默认) ────┤                        ├── 任务5 (partial_thinking) ─┐
任务4 (--timeout-think)┤                        │                              ├── 任务6 (UI) ──┐
                       └── 任务7 (Brain 透传) ─┘                              │                ├── 任务8 (测试)
                                                                              ┘                │
任务1-4 可独立 ─────────────────────────────────────────────────────────────────────────────┘
```

并行：1/3/4 可独立；2 依赖 1；5 依赖 2；6 依赖 5；7 依赖 1；8 依赖全部

---

## 关键文件清单

| 文件 | 改动 |
|------|------|
| `hyperbrain/models/base.py` | 改（ModelResponse.thinking） |
| `hyperbrain/models/ollama_model.py` | 改（thinking 解析 + stream yield 元组） |
| `hyperbrain/core/brain.py` | 改（透传 thinking 到 metadata） |
| `hyperbrain/ui/main_window.py` | 改（partial_thinking 信号 + 折叠 UI） |
| `hyperbrain/core/config.py` | 改（think 默认 True） |
| `config.yaml` | 改（think: true） |
| `scripts/diagnose_ollama.py` | 改（--timeout-think 默认 180） |
| `tests/test_thinking_visualization.py` | 新增 |
