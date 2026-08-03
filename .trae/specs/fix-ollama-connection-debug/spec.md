# Ollama 连接调试与修复 Spec

## Why
用户报告"本地模型不能用了，不是反应慢的问题，哪里连接不上了"。初步诊断：
- Ollama 进程在跑（PID 14152）
- 端口 11434 监听 ✓
- `/api/tags` 返回 14 个模型（qwen3.5:0.8b/2b/9b/4b/0.6b、gemma2:2b、gemma4、llama3.1 等）
- 实际加载到 `qwen3.5:0.8b`（不是 config.yaml 里的 `qwen3.5:2b`），且 60s 才返回响应

但用户报"连接不上"且"不是反应慢的问题"，说明：
1. **缺乏诊断工具** —— 当前没有命令告诉用户"具体是哪一步断的"（进程?端口?URL?模型名?请求体?）
2. **错误信息不定位** —— 连接失败时只说"请求超时/连接失败"，无法区分"进程没起"vs"端口不对"vs"模型不存在"
3. **fallback_models 配置可能误存** —— `config.yaml` 里的 `fallback_models: []` 是默认空，但 `brain.py` 在 dataclass 中初始化为 `['gemma2:2b']` 等可能造成 model_manager 行为异常
4. **model 名称漂移** —— 测试发现实际注册的是 `qwen3.5:0.8b` 而不是 `qwen3.5:2b`，存在 model_name 被某处覆盖的可能

## What Changes
- **诊断 CLI 工具**：新增 `scripts/diagnose_ollama.py`，6 步分级检查（进程/端口/URL/tags/show/chat），每步打印 PASS/FAIL/原因，输出机器可读 JSON + 人类可读报告。
- **`MainWindow` 内置"诊断"按钮**：菜单"工具 → 诊断 Ollama 连接"，运行上述 6 步，把结果显示在 QTextEdit 中，标红 FAIL。
- **结构化连接错误**：把 `ClientConnectorError / ClientResponseError / asyncio.TimeoutError` 统一映射为 `{code, stage, model, url, detail}`，UI 显示"在哪一步断的"。
- **修复 model_name 漂移**：在 `ModelManager.__init__` 中显式打印 `config.ollama_model` + `auto_discover` 注册的所有 model，找出覆盖源；增加 `ollama_default` 与 `cfg.ollama_model` 不一致时打 ERROR。
- **配置校验**：启动时若 `fallback_models` 包含的模型名在 `/api/tags` 中不存在 → 状态栏 WARN。
- **`OllamaModel.initialize()` 失败诊断**：`ClientConnectorError` 时打印 host:port + 检查 Windows `netstat` 输出（是否真在监听）。

## Impact
- 受影响 spec：`fix-ollama-thinking-timeout`（错误信息结构化有重叠，统一格式）。
- 受影响代码：
  - `hyperbrain/models/ollama_model.py`（错误结构化 + initialize 诊断）
  - `hyperbrain/models/model_manager.py`（model_name 漂移日志 + 校验）
  - `hyperbrain/core/brain.py`（透传错误码）
  - `hyperbrain/ui/main_window.py`（诊断按钮 + 错误展示）
  - 新增 `scripts/diagnose_ollama.py`（CLI 诊断）

## ADDED Requirements

### Requirement: Ollama 连接诊断 CLI
系统 SHALL 提供 `scripts/diagnose_ollama.py`，按顺序执行 6 步诊断，输出 PASS/FAIL/WARN：
1. **Step 1: 进程**：检查 `ollama` 进程是否在跑（Windows `tasklist` / Unix `pgrep`）。
2. **Step 2: 端口**：对 `config.model.ollama_base_url` 的 host:port 做 `Test-NetConnection` / `nc -z`。
3. **Step 3: API 根**：`GET {base_url}/api/version` 返回 200。
4. **Step 4: 模型列表**：`GET {base_url}/api/tags` 返回 200 且包含 `config.model.ollama_model`。
5. **Step 5: 模型元数据**：`POST {base_url}/api/show {name: ollama_model}` 返回 200（验证模型真实存在）。
6. **Step 6: 生成测试**：`POST {base_url}/api/generate` 发送 "hi"（num_predict=5, timeout=10s）确认模型能生成。

#### Scenario: 全部正常
- **WHEN** 所有 6 步都 PASS
- **THEN** CLI 输出绿色 "✓ Ollama 全链路正常" + 模型响应摘要

#### Scenario: Ollama 未运行
- **WHEN** Step 1 检测不到 ollama 进程
- **THEN** CLI 输出红色 "✗ Step 1 FAIL: 未检测到 ollama 进程" + 建议 "请运行 `ollama serve`"

#### Scenario: 端口不通
- **WHEN** Step 2 端口不通
- **THEN** CLI 提示 "检查 ollama 是否真的在 11434 监听，Windows 防火墙是否拦截"

#### Scenario: 模型名错误
- **WHEN** Step 4 /api/tags 不包含 config.model.ollama_model
- **THEN** CLI 列出所有可用模型 + 提示 "请在设置中切换到以下之一: ..."

### Requirement: GUI 诊断按钮
`MainWindow` SHALL 在菜单"工具"下增加"诊断 Ollama 连接"菜单项，点击后：
- 启动 `scripts/diagnose_ollama.py` 子进程
- 在独立 `QDialog` 中显示实时输出（6 步每行 PASS/FAIL/WARN 标色）
- 完成后显示"重新尝试连接"按钮（调用 `model_manager.initialize_all()`）

#### Scenario: 诊断失败
- **WHEN** 任意一步 FAIL
- **THEN** 弹窗显示红色错误条目 + "打开设置"按钮跳到模型设置页

### Requirement: 结构化连接错误
`OllamaModel.initialize()` / `chat()` SHALL 捕获 `aiohttp.ClientConnectorError` / `ClientResponseError` / `asyncio.TimeoutError` 并统一抛出 `OllamaConnectionError(stage, model, url, detail)`，`stage ∈ {TCP_CONNECT, HTTP_VERSION, HTTP_TAGS, HTTP_SHOW, HTTP_CHAT}`。

#### Scenario: 连接被拒
- **WHEN** aiohttp 抛 ClientConnectorError
- **THEN** raise OllamaConnectionError(stage="TCP_CONNECT", url=base_url, detail=str(e))
- **AND** BrainWorker emit `{code: "OLLAMA_CONNECT_FAIL", stage: "TCP_CONNECT", url: "http://127.0.0.1:11434", suggestion: "请检查 Ollama 是否运行"}`

### Requirement: model_name 漂移告警
`ModelManager.__init__` 在 auto_discover 注册完成后 SHALL 对比 `cfg.ollama_model` 与 `self.models["ollama_default"].model_name`：
- 不一致 → 打印 ERROR 日志 + 状态栏 WARN
- 同时打印所有 `ollama_*` 模型的注册名

#### Scenario: 配置漂移
- **WHEN** config.yaml 写 `ollama_model: qwen3.5:2b` 但实际加载 `qwen3.5:0.8b`
- **THEN** 日志: "model_name drift: config=qwen3.5:2b actual=qwen3.5:0.8b (reason: ???)"
- **AND** 列出所有 `ollama_*` 注册项

### Requirement: fallback_models 存在性校验
启动时若 `cfg.fallback_models` 非空，SHALL 对每个 model_name 调 `/api/show`；任一不存在 → 状态栏 WARN "fallback 模型 X 不存在，将被忽略"。

#### Scenario: fallback 链含无效模型
- **WHEN** fallback_models=["gemma2:2b", "fakemodel:7b"]
- **THEN** 启动时 WARN: "fallback fakemodel:7b 不在 /api/tags 中"

## MODIFIED Requirements

### Requirement: 错误信息结构化
**原**：`OllamaModel.initialize()` / `chat()` 抛 `Exception` 含原始 message。
**改**：抛 `OllamaConnectionError(stage, model, url, detail)`，BrainWorker 解析 stage 显示针对性建议。
**影响文件**：`hyperbrain/models/ollama_model.py`、`hyperbrain/ui/main_window.py`。

### Requirement: ModelManager 启动校验
**原**：auto_discover 静默注册 ollama_* 模型。
**改**：注册后增加"cfg 一致性检查" + 日志报告。
**影响文件**：`hyperbrain/models/model_manager.py`。

## REMOVED Requirements
无。

