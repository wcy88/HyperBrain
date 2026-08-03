# Ollama 思考模型思维链可视化 Spec

## Why
用户反馈 qwen3.5:2b（thinking 模型）当前诊断还是 60s 超时失败，且明确希望**保留 thinking 模型 + 显示思考过程**（而不是切到 gemma2:2b）。当前 `_probe_thinking_capability` 探测到 thinking 模型后只设了 `is_thinking=True`，但 `chat()` 路径在 `config.think=False` 时会强行加 `"think": false` 来抑制思维链；Ollama API 对 thinking 模型实际是**先流式输出 `thinking` 字段的思维链、再输出 `content` 字段的最终答案**，所以正确做法是：

1. **`config.think` 默认改成 `True`**（允许 thinking 模型生成思维链，spec `fix-agent-slow-response` 之前打算改 `False` 是错的）
2. **延长 thinking 模型的 Step 6 / chat 超时到 180s**（用户明确建议）
3. **解析 thinking 模型响应时区分 `thinking` 字段和 `content` 字段**
4. **GUI 显示思维链**（类似 ChatGPT o1 风格的折叠区）
5. **流式输出思维链**（让用户实时看到模型在"思考"）

## What Changes
- **`hyperbrain/models/ollama_model.py`** — 解析 `resp.message.thinking` 字段；`ModelResponse` 新增 `thinking: str` 字段；`stream_chat()` 流式 yield `(chunk_type, content)` 元组或用 `partial_thinking` 信号
- **`hyperbrain/core/config.py` + `config.yaml`** — `think` 字段默认改回 `True`；`worker_timeout` 默认从 180 改 300（spec `fix-ollama-thinking-timeout` 已设 300）
- **`hyperbrain/core/brain.py`** — `process()` 把 `model_response.thinking` 存到 `ProcessingResult.metadata["thinking"]`（不存到长期记忆）
- **`hyperbrain/ui/main_window.py`** — BrainWorker 新增 `partial_thinking` 信号；`MainWindow` 在消息气泡中显示可折叠的"思考过程"区（淡灰/小字号，背景色 `#1e1e1e`，可展开/折叠）
- **`scripts/diagnose_ollama.py`** — `--timeout-think` 默认从 60 改 180（用户建议）

**BREAKING 变更**：`config.yaml` 中 `think` 从 `false`（spec `fix-agent-slow-response` 暂未落地）恢复为 `true`；`ModelResponse` 新增字段（向后兼容，默认空字符串）。

## Impact
- 受影响 spec：
  - `fix-ollama-thinking-timeout`（think 行为）
  - `fix-diagnose-cli-gbk-and-thinking`（`--timeout-think` 默认值）
  - `fix-agent-slow-response`（被本 spec 部分推翻 —— 之前认为 think 默认 false 是"安全"，实际用户想要 think=true + 思维链可视化）
- 受影响代码：
  - `hyperbrain/models/ollama_model.py`（thinking 解析 + ModelResponse 新字段 + stream_chat 改造）
  - `hyperbrain/models/base.py`（ModelResponse 加 thinking）
  - `hyperbrain/core/brain.py`（thinking 透传）
  - `hyperbrain/ui/main_window.py`（思维链 UI 渲染）
  - `hyperbrain/core/config.py`（think 默认值）
  - `config.yaml`（think 默认 true）
  - `scripts/diagnose_ollama.py`（--timeout-think 默认 180）
- 新增测试 `tests/test_thinking_visualization.py`

## ADDED Requirements

### Requirement: 解析 thinking 字段
`OllamaModel._parse_chat_response()` SHALL 在解析响应时提取 `resp.message.get("thinking", "")` 字段，存入 `ModelResponse.thinking`。`stream_chat()` SHALL 把 `chunk.get("thinking", "")` 单独 yield。

#### Scenario: qwen3.5:2b 返回 thinking
- **WHEN** Ollama 返回 `{"message": {"thinking": "Let me think step by step...", "content": "The answer is 42."}}`
- **THEN** `ModelResponse.thinking == "Let me think step by step..."`
- **AND** `ModelResponse.content == "The answer is 42."`

#### Scenario: gemma2:2b 不返回 thinking
- **WHEN** Ollama 返回 `{"message": {"content": "Hi"}}`（无 thinking 字段）
- **THEN** `ModelResponse.thinking == ""`
- **AND** `ModelResponse.content == "Hi"`

### Requirement: 流式输出思维链
`OllamaModel.stream_chat()` SHALL 在 stream 模式下分别 yield 思维链和内容两种类型，让 GUI 能实时区分显示。

#### Scenario: 流式 thinking 模型
- **WHEN** 用户发送消息，Ollama 流式返回多个 chunk，每个 chunk 含 `thinking` 或 `content` 字段
- **THEN** `stream_chat()` 按顺序 yield 思维链片段和内容片段
- **AND** GUI 实时显示思维链（淡灰色）和内容（正常色）

#### Scenario: 流式非 thinking 模型
- **WHEN** 用户发送消息，Ollama 流式返回无 `thinking` 字段的 chunk
- **THEN** `stream_chat()` 只 yield 内容片段
- **AND** GUI 不显示"思考过程"区

### Requirement: 思维链 UI 渲染
`MainWindow` SHALL 在 AI 消息气泡中显示可折叠的"思考过程"区。默认折叠（节省空间），点击展开。

#### Scenario: 收到 thinking 响应
- **WHEN** BrainWorker 发 `partial_thinking` 信号，content 含 thinking
- **THEN** 消息气泡顶部出现"💭 思考过程（点击展开）"折叠条
- **AND** 点击后展开显示完整 thinking 文本（淡灰色 `#888888`，等宽字体，小字号 12px）
- **AND** 展开后仍可折叠

#### Scenario: 收到非 thinking 响应
- **WHEN** BrainWorker 不发 `partial_thinking` 信号
- **THEN** 消息气泡不显示"思考过程"折叠条
- **AND** 正常显示 content

### Requirement: think 默认 true
`config.yaml` 和 `hyperbrain/core/config.py` 的 `think` 字段 SHALL 默认为 `True`，允许 thinking 模型生成思维链。

#### Scenario: 新安装/重置
- **WHEN** 用户首次安装或重置 config
- **THEN** `think: true`
- **AND** qwen3.5:2b 等 thinking 模型生成 800+ token 思维链 + 最终答案
- **AND** GUI 显示思维链折叠区

#### Scenario: 用户手动关闭
- **WHEN** 用户在设置中取消勾选"允许 thinking 模型生成思维链"
- **THEN** `think: false`
- **AND** 请求体加 `"think": false`（Ollama 跳过思维链直接出答案）

### Requirement: --timeout-think 默认 180
`diagnose_ollama.py` 的 `--timeout-think` 默认 SHALL 为 `180` 秒（用户建议），覆盖当前 60s 默认。

#### Scenario: 不传 --timeout-think
- **WHEN** 用户跑 `py -3.14 scripts/diagnose_ollama.py --model qwen3.5:2b`
- **THEN** Step 6 用 180s timeout

#### Scenario: 调低
- **WHEN** 用户跑 `... --timeout-think 60`
- **THEN** Step 6 用 60s

### Requirement: BrainWorker.partial_thinking 信号
`BrainWorker` SHALL 新增 `partial_thinking = pyqtSignal(str)` 信号，在 stream 模式下实时发思维链片段。

#### Scenario: 流式 thinking 模型
- **WHEN** `stream_chat()` yield 一个 thinking chunk
- **THEN** `partial_thinking.emit(chunk_text)`
- **AND** MainWindow 的对应槽函数追加到折叠区

#### Scenario: 流式完成
- **WHEN** `stream_chat()` 全部 yield 完毕
- **THEN** `partial_thinking` 不再 emit
- **AND** `result_ready.emit(full_content)` 发最终 content

## MODIFIED Requirements

### Requirement: ModelResponse 字段
**原**：`ModelResponse` 字段为 `content, model, usage, finish_reason, metadata`
**改**：新增 `thinking: str = ""` 字段
**影响文件**：`hyperbrain/models/base.py` + `hyperbrain/models/ollama_model.py`

### Requirement: 诊断 CLI --timeout-think 默认值
**原**：默认 60（spec `fix-diagnose-cli-gbk-and-thinking`）
**改**：默认 180（本 spec）
**影响文件**：`scripts/diagnose_ollama.py`

## REMOVED Requirements
无。

## 取消之前 spec 的相关决定

- **spec `fix-agent-slow-response`** 任务 2 的"think 默认 false"决定**取消**，本 spec 恢复 think=true
- **spec `fix-agent-slow-response`** 任务 1 的 `chat()` 走 stream_chat 仍保留（用户也需要流式体验）
- **spec `fix-agent-slow-response`** 任务 3-6（分层计时 + fire-and-forget + profile_agent + tests）仍保留

## 不在本次范围
- 思维链的 LLM 评估/打分（不存到长期记忆）
- 思维链的可编辑/删除（暂时只读）
- 思维链的搜索/过滤（只展示当前消息的）
