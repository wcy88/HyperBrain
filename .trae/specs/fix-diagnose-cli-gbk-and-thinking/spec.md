# diagnose_ollama.py GBK 编码与 thinking 模型超时修复 Spec

## Why
用户实际跑 `scripts/diagnose_ollama.py`（PyInstaller 打包的 exe）发现两个问题：

1. **GBK 终端中文乱码** — 上一轮 spec 的"GBK 修复"不完整。`_step_print()` 的 `try/except UnicodeEncodeError` 块**仍然打印中文**（`name="进程" / detail="ollama.exe 正在运行"`），结果抛 UnicodeEncodeError 时只是隐藏了颜色，没有真正降级到 ASCII。用户在 Windows 默认 GBK 终端看到的是：
   ```
   [STEP 1] [OK] PASS: ����
     ollama.exe �������� (PIDs: 14152)
   ```
   `进程` / `正在运行` 全是 `����`（mojibake），影响可读性。

2. **Step 6 thinking 模型超时** — `qwen3.5:0.8b` 是 thinking 模型（family=qwen35 / capabilities 含 thinking），生成 5 token 也需要先输出 800+ tokens 思维链，15s 根本不够。Step 6 输出：
   ```
   [STEP 6] [FAIL] FAIL: ���ɲ���
     POST /api/generate �� -1: TimeoutError:
   ```
   这不是"连接不上"问题——是 thinking 模型的预期行为，但 CLI 把它当 FAIL，会误导用户。

## What Changes
- **`scripts/diagnose_ollama.py`** — 全面 ASCII 化用户面向字符串；新增 `--no-color` 默认开启；新增 thinking 模型自动加 `"think": false`；Step 6 timeout 提升到 60s（thinking）或 10s（非 thinking）。
- **新增单元测试** `tests/test_diagnose_cli_gbk.py` — 验证 GBK 强制编码下 `print()` 不抛异常、Step 6 thinking 模型走 `"think": false`。
- **不修改**：`scripts/diagnose_ollama.py` 的 `--json` 输出模式（`ensure_ascii=False` 保留中文，便于脚本处理）；`OllamaConnectionError` 结构化错误（上一轮已修）；GUI `diagnose_dialog.py`（它通过 QProcess 读 utf-8 不受 GBK 影响）。

**BREAKING 变更**：CLI 默认人类可读输出改为纯 ASCII（中文 → 英文）。需要中文输出请用 `chcp 65001` 切到 UTF-8 终端后跑 `py -3.14 scripts/diagnose_ollama.py` 或 GUI 菜单（GUI 用 HTML 渲染不受影响）。

## Impact
- 受影响 spec：`fix-ollama-connection-debug`（产物 `scripts/diagnose_ollama.py` 的 GBK 修复不完整）
- 受影响代码：
  - `scripts/diagnose_ollama.py`（用户面向字符串 ASCII 化 + thinking 处理）
  - `tests/test_diagnose_cli_gbk.py`（新增）

## ADDED Requirements

### Requirement: GBK 编码完全兼容
`_step_print()` / `check_process()` / `check_port()` / `check_api_steps()` 中所有用户面向字符串 SHALL 改为英文（或 ASCII 符号）。当 `sys.stdout.encoding` 为 GBK / cp936 / ascii 时不抛 `UnicodeEncodeError`。

#### Scenario: Windows GBK 终端
- **WHEN** 用户在 Windows 默认 cmd（GBK）跑 `py -3.14 scripts/diagnose_ollama.py`
- **THEN** 全部 6 步输出为纯 ASCII 英文，无 `����` 乱码

#### Scenario: UTF-8 终端（WSL / git-bash / chcp 65001）
- **WHEN** 用户在 UTF-8 终端跑
- **THEN** 输出英文（保持一致，避免依赖终端编码），仍可读

#### Scenario: GUI 调用
- **WHEN** GUI `DiagnoseDialog` 通过 QProcess 捕获 stdout
- **THEN** 子进程输出英文不影响 GUI 解析（GUI 已有 JSON mode 兜底）

### Requirement: thinking 模型自动处理
`check_api_steps()` SHALL 在 Step 5 `/api/show` 阶段检测 `capabilities` 是否含 `"thinking"` 或 `family` 含 `qwen3 / qwen35 / deepseek-r1 / qwq`：
- 若是 thinking → Step 6 请求体加 `"think": false` 且 timeout 升到 60s
- 若否 → Step 6 保持现状（timeout=15s, 不加 think 字段）

#### Scenario: qwen3.5:0.8b 是 thinking 模型
- **WHEN** `check_api_steps()` 跑 Step 5 拿到 `capabilities=["thinking"]`
- **THEN** Step 6 请求体 `{"model": ..., "prompt": "hi", "stream": false, "think": false, "options": {"num_predict": 5}}` + `timeout_sec=60`

#### Scenario: gemma2:2b 不是 thinking 模型
- **WHEN** `check_api_steps()` 跑 Step 5 拿到 `capabilities=["completion"]` 且 `family=gemma2`
- **THEN** Step 6 请求体保持现状（不加 think）+ `timeout_sec=15`

#### Scenario: thinking 模型 60s 内仍超时
- **WHEN** qwen3.5:0.8b 60s 仍未生成
- **THEN** Step 6 FAIL 但 `fix` 提示："thinking 模型首 token 慢。建议切到 gemma2:2b / qwen2.5:7b 等非 thinking 模型，或调高 --timeout-think 到 180"

### Requirement: --timeout-think CLI 参数
`diagnose_ollama.py` SHALL 新增 `--timeout-think SEC` 参数（默认 60），让用户显式覆盖 thinking 模型的 Step 6 超时。

#### Scenario: 默认 thinking 超时
- **WHEN** 不传 `--timeout-think`
- **THEN** 用默认值 60 秒

#### Scenario: 调高到 180 秒
- **WHEN** 用户跑 `... --timeout-think 180`
- **THEN** Step 6 thinking 模型用 180 秒 timeout

## MODIFIED Requirements

### Requirement: Step 6 timeout
**原**：`timeout_sec=15`（固定）
**改**：根据 thinking 检测结果动态选择 15s（普通）或 `args.timeout_think`（thinking，默认 60s）
**影响文件**：`scripts/diagnose_ollama.py`

### Requirement: 用户面向字符串
**原**：中文（"进程" / "端口" / "API 根" / "模型列表" / "模型元数据" / "生成测试" / "找到 N 个模型" / "请运行" 等）
**改**：英文（"process" / "port" / "api root" / "model list" / "model show" / "generate test" / "found N models" / "please run" 等）
**影响文件**：`scripts/diagnose_ollama.py`
**保留**：JSON 模式 `ensure_ascii=False`（让脚本/日志能读中文）

## REMOVED Requirements
无。

## 不在本次范围
- `OllamaConnectionError` 结构化错误（已由 `fix-ollama-connection-debug` 完成）
- GUI `DiagnoseDialog` 任何改动（已由 `fix-ollama-connection-debug` 完成）
- BrainWorker 透传 OLLAMA_CONNECT_FAIL（已由 `fix-ollama-connection-debug` 完成）
