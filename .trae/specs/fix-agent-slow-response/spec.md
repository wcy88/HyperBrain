# Agent 响应慢全面调试与修复 Spec

## Why
用户反馈"Ollama 直接很快，但走 HyperBrain Agent 很慢，之前可以现在不行"。经代码审查发现多个叠加瓶颈：`chat()` 强制 `stream=False`（等全量响应）、`think:true` + thinking 模型（生成思维链 30-100s）、记忆检索同步阻塞、后处理同步阻塞、无分层计时无法定位。需要全面修复。

## What Changes
- **`hyperbrain/models/ollama_model.py`** — `chat()` 在 `config.stream=True` 时走 `stream_chat()` 并 join 返回（而非强制 `stream=False`）
- **`hyperbrain/core/brain.py`** — 每层加计时日志 + 后处理（记忆存储/学习/DB 写入）改为 fire-and-forget + `think` 默认安全值
- **`hyperbrain/models/model_manager.py`** — `chat()` 透传 stream 配置
- **`config.yaml`** — `think: false`（安全默认值，thinking 模型不会自动生成思维链）
- **新增** `scripts/profile_agent.py` — 一键性能剖析脚本
- **新增** `tests/test_agent_perf.py` — 性能相关单元测试

**BREAKING 变更**：`config.yaml` 中 `think` 默认从 `true` 改为 `false`。需要思维链的用户需手动开启。

## Impact
- 受影响 spec：`fix-ollama-thinking-timeout`（think 配置默认值变更）、`fix-chat-no-response`（stream 模式变更）
- 受影响代码：
  - `hyperbrain/core/brain.py`（process 流程重构）
  - `hyperbrain/models/ollama_model.py`（chat stream 逻辑）
  - `hyperbrain/models/model_manager.py`（chat 透传）
  - `config.yaml`（think 默认值）
  - `scripts/profile_agent.py`（新增）
  - `tests/test_agent_perf.py`（新增）

## 根因分析

### 调用链（从 MainWindow 到 Ollama 返回）

```
MainWindow._on_message_sent()
  → BrainWorker.run()
    → brain.process(user_input)
      1. sensory.perceive()              — async, ~1ms
      2. emotional.process_input()       — sync, ~1ms
      3. memory.retrieve(top_k=5)        — sync, 10-500ms ⚠️ (embedding + brute-force + lock)
      4. cognitive.think()               — sync, ~1ms
      5. consciousness.make_decision()   — sync, ~1ms
      6. _build_system_prompt()          — sync, ~1ms
      7. db.get_conversation_history()   — sync, 5-50ms ⚠️
      8. model_manager.chat_with_fallback() / chat()
         → OllamaModel.chat()
           payload["stream"] = False     — 🔴 强制非流式，等全量响应
           think=true + thinking model   — 🔴 生成 800+ token 思维链，30-100s
           @with_retry(max_retries=2)    — 失败重试 + 0.5s/1s 退避
           circuit_breaker               — 可能 OPEN 导致立即失败
      9. execution.execute()             — async, ~1ms
      10. memory.working_memory.add()    — sync, ~1ms
      11. memory.store()                 — sync, 5-50ms ⚠️
      12. learning.learn()               — sync, ~1ms
      13. db.insert_conversation() x2    — sync, 5-20ms ⚠️
      14. hermes hooks                   — sync, ~1ms
```

### 5 个瓶颈（按严重程度排序）

| # | 瓶颈 | 严重度 | 说明 |
|---|------|--------|------|
| 1 | `chat()` 强制 `stream=False` | 🔴 高 | Ollama 直接用流式（首 token <1s），Agent 等全量（5-100s）。`config.stream=true` 但 `chat()` 写死 `payload["stream"] = False` |
| 2 | `think:true` + thinking 模型 | 🔴 高 | `qwen3.5:2b` 是 thinking 模型，`think=true` 时生成 800+ token 思维链再出答案，30-100s |
| 3 | 后处理同步阻塞 | 🟡 中 | 步骤 10-14 是同步操作，阻塞 `process()` 返回，用户多等 20-100ms |
| 4 | 记忆检索 lock 竞争 | 🟡 中 | `memory.retrieve()` 持 `_lock`，如果 `consolidate()` 在跑（每 5 分钟），检索被阻塞 |
| 5 | 无分层计时 | 🟡 中 | 出了慢响应无法定位是哪一步慢，只能猜 |

## ADDED Requirements

### Requirement: chat() 支持 stream 模式
`OllamaModel.chat()` SHALL 在 `config.stream=True` 时走 `stream_chat()` 并 join 返回完整内容，而非强制 `payload["stream"] = False`。

#### Scenario: config.stream=True（默认）
- **WHEN** `self.config.stream is True`
- **THEN** `chat()` 调用 `stream_chat()` 并收集所有 chunk join 为完整响应返回
- **AND** 首 token 延迟 < 2s（而非等全量 5-100s）

#### Scenario: config.stream=False
- **WHEN** `self.config.stream is False`
- **THEN** `chat()` 保持现有行为（`payload["stream"] = False`，等全量）

### Requirement: 分层计时日志
`Brain.process()` SHALL 在每层处理前后记录耗时（ms），在 INFO 级别输出。格式：`[perf] <layer_name>: <elapsed_ms>ms`。

#### Scenario: 正常请求
- **WHEN** 用户发送消息
- **THEN** 日志输出类似：
  ```
  [perf] sensory: 1ms
  [perf] emotional: 0ms
  [perf] memory.retrieve: 45ms
  [perf] cognitive: 0ms
  [perf] consciousness: 0ms
  [perf] build_prompt: 0ms
  [perf] db.history: 12ms
  [perf] model.chat: 3200ms
  [perf] execution: 0ms
  [perf] post_process: 35ms
  [perf] TOTAL: 3293ms
  ```

#### Scenario: 慢请求定位
- **WHEN** 总耗时 > 10s
- **THEN** 日志中能清晰看到是哪一层慢（如 `model.chat: 28000ms`）

### Requirement: 后处理 fire-and-forget
`Brain.process()` 的步骤 9-14（记忆存储、学习、DB 写入、Hermes 钩子）SHALL 改为 `asyncio.create_task()` fire-and-forget，不阻塞 `process()` 返回。

#### Scenario: 正常请求
- **WHEN** 模型返回响应后
- **THEN** `process()` 立即返回 `ProcessingResult`，后处理在后台异步执行
- **AND** 用户感知的响应时间 = 模型响应时间 + 前处理时间（而非 + 后处理时间）

#### Scenario: 后处理失败
- **WHEN** 记忆存储/学习/DB 写入失败
- **THEN** 不影响已返回的 `ProcessingResult`，仅 log error

### Requirement: 性能剖析脚本
`scripts/profile_agent.py` SHALL 提供一键性能剖析：发送一条测试消息到 Brain，输出每层耗时 + 总耗时 + 瓶颈提示。

#### Scenario: 运行剖析
- **WHEN** 用户运行 `py -3.14 scripts/profile_agent.py`
- **THEN** 输出类似：
  ```
  Agent Performance Profile
  ========================
  sensory:        1ms
  emotional:      0ms
  memory.retrieve: 45ms
  cognitive:      0ms
  consciousness:  0ms
  build_prompt:   0ms
  db.history:     12ms
  model.chat:     3200ms  ← bottleneck
  execution:      0ms
  post_process:   0ms (fire-and-forget)
  ─────────────────────
  TOTAL:          3258ms
  
  Bottleneck: model.chat (98.2%)
  Suggestion: config.stream=true but chat() uses stream=False. Check OllamaModel.chat().
  ```

### Requirement: think 默认安全值
`config.yaml` 中 `think` SHALL 默认为 `false`，避免 thinking 模型自动生成思维链导致 30-100s 延迟。

#### Scenario: 新安装/重置配置
- **WHEN** 用户首次安装或重置 config.yaml
- **THEN** `think: false`，thinking 模型不会生成思维链
- **AND** 响应时间与直接用 Ollama 相当（3-10s）

#### Scenario: 用户主动开启 think
- **WHEN** 用户在设置中勾选"允许 thinking 模型生成思维链"
- **THEN** `think: true`，thinking 模型生成思维链（但响应慢 30-100s）
- **AND** 设置 UI 显示警告："开启后 thinking 模型会先生成思维链再回答，响应时间可能增加 30-100 秒"

## MODIFIED Requirements

### Requirement: OllamaModel.chat() stream 行为
**原**：`chat()` 总是 `payload["stream"] = False`，等全量响应
**改**：`chat()` 在 `config.stream=True` 时走 `stream_chat()` join 返回；`config.stream=False` 时保持原行为
**影响文件**：`hyperbrain/models/ollama_model.py`

### Requirement: Brain.process() 后处理
**原**：步骤 9-14 同步执行，阻塞 `process()` 返回
**改**：步骤 9-14 用 `asyncio.create_task()` fire-and-forget，不阻塞返回
**影响文件**：`hyperbrain/core/brain.py`

### Requirement: config.yaml think 默认值
**原**：`think: true`
**改**：`think: false`
**影响文件**：`config.yaml`

## REMOVED Requirements
无。
