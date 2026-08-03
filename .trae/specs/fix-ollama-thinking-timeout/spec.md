# Ollama Thinking 模型超时修复 Spec

## Why
当前默认模型 `qwen3.5:2b` 属于"thinking"模型，对简单输入（如"hi"）会先生成 800+ tokens 的思维链，导致 Ollama 端响应耗时 100 秒以上；而 `BrainWorker` 默认超时仅 90 秒，因此用户在 GUI 中几乎必然看到"请求超时，请稍后重试"。该问题反复出现（用户用了"又"），表明它是默认配置与默认模型不匹配的系统性问题，需要在配置、流式回显、降级、错误信息四个层面统一处理。

## What Changes
- **可配置超时**：将 `BrainWorker` 的 90 秒硬编码超时改为可配置（默认 180 秒），并允许在 settings_dialog 中调整。
- **Thinking 模型探测与抑制**：启动时调用 `/api/show` 探测 `qwen3`/`deepseek-r1`/`qwq` 等 thinking 模型家族，提示用户或在请求体中加入 `think: false`（Ollama 0.9+ 支持）以跳过思维链。
- **流式响应**：将 `OllamaModel.chat()` 改为支持 streaming 模式，让 UI 在生成过程中显示部分内容，避免用户长时间看到"思考中..."误以为卡死。
- **降级链**：在 `ModelManager` 中支持"主模型超时后自动回退到备选模型"的降级链配置（默认主 `qwen3.5:2b` → 备 `gemma2:2b`）。
- **可执行错误信息**：超时错误从通用"请求超时，请稍后重试"改为包含"模型名 + 实际耗时 + 建议操作"的明确提示，并引导用户去 settings 切换模型或调高超时。
- **默认模型迁移**：将默认 `default_model` 从 `qwen3.5:2b` 改为更轻量的 `gemma2:2b`（非 thinking，响应 < 5s），`qwen3.5:2b` 仍可在设置中选择。

## Impact
- 受影响 spec：`fix-chat-no-response`（BrainWorker 出现处，需协调 timeout 改动）、`fix-model-and-shortmem`（模型切换链路）。
- 受影响代码：
  - `hyperbrain/ui/main_window.py`（BrainWorker、`_on_message_sent`、错误显示）
  - `hyperbrain/ui/settings_dialog.py`（新增 timeout / fallback 字段）
  - `hyperbrain/models/ollama_model.py`（streaming、think 参数、/api/show 探测）
  - `hyperbrain/models/model_manager.py`（降级链、超时传播）
  - `hyperbrain/models/base.py`（ModelConfig 增加 timeout / think / fallback 字段）
  - `hyperbrain/core/config.py`（同步 dataclass 默认值与 config.yaml）
  - `config.yaml`（`default_model`、`brain.worker_timeout`、`ollama.think`）
  - `hyperbrain/core/brain.py`（process 路径上的降级与异常透传）

## ADDED Requirements

### Requirement: 可配置 Worker 超时
系统 SHALL 在 `BrainWorker` 构造时支持传入 `timeout` 参数（默认 180 秒，来自 `config.brain.worker_timeout`），并允许用户通过 settings_dialog 修改该值（范围 30-600 秒）。

#### Scenario: 默认 180s 超时
- **WHEN** 用户在设置中未自定义超时即发送消息
- **THEN** `BrainWorker` 使用 180s 超时
- **AND** UI 不再对 thinking 模型误报超时

#### Scenario: 用户手动调高到 300s
- **WHEN** 用户在 settings 中将 `worker_timeout` 改为 300
- **THEN** 下次发送消息时 BrainWorker 使用 300s

### Requirement: Thinking 模型探测
系统 SHALL 在 `OllamaModel.initialize()` 完成后调用 `/api/show` 检查 `model_info`/`capabilities` 字段；若模型家族匹配 `qwen3*` / `deepseek-r1*` / `qwq*`，标记 `is_thinking=True`，并在日志/状态栏显示提示。

#### Scenario: 加载 qwen3.5:2b
- **WHEN** 启动加载 qwen3.5:2b
- **THEN** `OllamaModel.is_thinking == True`
- **AND** 状态栏出现"已加载 thinking 模型，建议在设置中关闭 think 或切换到非 thinking 模型"

### Requirement: 关闭思维链
当 `config.ollama.think == false` 时，系统 SHALL 在 chat 请求体中加入 `"think": false`（Ollama 0.9+）；当 `is_thinking` 为 true 且未配置 `think: false` 时，UI 在发送前提示用户。

#### Scenario: 显式关闭 think
- **WHEN** 配置 `ollama.think = false` 且模型为 qwen3.5
- **THEN** 请求体含 `"think": false`
- **AND** 模型直接输出最终答案，不生成思维链

### Requirement: 流式响应
系统 SHALL 支持 `OllamaModel.stream_chat()` 异步生成器，按 chunk 推送增量文本；GUI 在 streaming 模式下实时追加到聊天窗口。

#### Scenario: 启用 streaming
- **WHEN** 配置 `ollama.stream = true`（默认）
- **THEN** 用户在消息发出后 0.5s 内即可看到首个 token
- **AND** 长响应不再被"思考中..."误导

### Requirement: 模型降级链
系统 SHALL 在 `ModelManager` 中支持 `fallback_models: list[str]`；当主模型连续超时 ≥1 次后，自动切换到 fallback 模型并继续对话。

#### Scenario: 主模型超时降级
- **WHEN** qwen3.5:2b 响应超时（> 180s）
- **THEN** 当前回合使用 fallback 模型 gemma2:2b 重试
- **AND** UI 显示"主模型超时，已自动切换到 gemma2:2b"

#### Scenario: 用户禁用降级
- **WHEN** 用户在 settings 中清空 `fallback_models`
- **THEN** 超时后直接显示错误，不重试

### Requirement: 明确超时错误信息
当 `BrainWorker` 触发 `asyncio.TimeoutError` 时，系统 SHALL emit `error_occurred` 信号，携带结构化错误：`{code: "MODEL_TIMEOUT", model: "...", elapsed_sec: N, suggestion: "..."}`，UI 显示"模型 qwen3.5:2b 在 180 秒内未响应。建议：1) 在设置中调高超时；2) 切换到 gemma2:2b；3) 关闭 think。"

#### Scenario: 触发超时
- **WHEN** 模型耗时 > worker_timeout
- **THEN** UI 显示上述明确错误（不再是"请求超时，请稍后重试"）
- **AND** 错误中包含"打开设置"快捷按钮

### Requirement: 默认模型改为非 thinking
系统 SHALL 将 `config.yaml` 中 `default_model` 从 `qwen3.5:2b` 改为 `gemma2:2b`（或其他本地已确认非 thinking 的轻量模型）；`qwen3.5:2b` 保留作为可选 advanced 模型。

#### Scenario: 全新启动
- **WHEN** 用户首次启动 HyperBrain 且未手动选模型
- **THEN** 默认使用 gemma2:2b
- **AND** 首条消息响应 < 10s

## MODIFIED Requirements

### Requirement: BrainWorker 超时
**原**：`BrainWorker.__init__(self, brain, text, async_thread, timeout: float = 90.0)`
**改**：`BrainWorker.__init__(self, brain, text, async_thread, timeout: float | None = None)`，None 时从 `config.brain.worker_timeout` 读取，默认 180s。
**影响文件**：`hyperbrain/ui/main_window.py` L48-L60。

### Requirement: OllamaModel.chat() 流式
**原**：使用 `"stream": False`，一次性返回完整响应。
**改**：新增 `stream_chat()` 异步生成器 + 在 `chat()` 中检测 `config.ollama.stream` 决定是否走 streaming。
**影响文件**：`hyperbrain/models/ollama_model.py` L210-L260。

### Requirement: ModelConfig 字段
**原**：`timeout: float = Field(default=60.0, ge=1.0, le=300.0)`、`max_tokens`、`temperature`。
**改**：增加 `think: bool = True`、`fallback_models: list[str] = []`、`worker_timeout: float = 180.0, ge=30, le=600`、`stream: bool = True`。
**影响文件**：`hyperbrain/models/base.py` L210-L230、`hyperbrain/core/config.py` ModelConfig dataclass。

## REMOVED Requirements

### Requirement: 硬编码 90s 超时
**Reason**：硬编码 90s 与默认 thinking 模型延迟不匹配，是反复超时的根因。
**Migration**：替换为可配置 180s 默认值 + 显式错误信息。`fix-chat-no-response` 引入的 BrainWorker 形态保留，仅放宽超时。

