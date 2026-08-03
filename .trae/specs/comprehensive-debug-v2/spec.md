# 全面调试与 Bug 修复 Spec（第二轮）

## Why
在完成 fix-test-model-revert、show-thinking-process 等多轮修改后，项目积累了新的问题：config.yaml 配置不一致（三个不同模型名）、测试文件卡住/失败、aiohttp 资源泄漏、eval 安全漏洞、40+ 处异常被静默吞掉。需要全面调试修复，确保项目可正常运行。

## What Changes
- **修复1**：同步 config.yaml 中三个不一致的模型名（`ollama_model` / `default_model` / `hermes.trainer.base_model`）
- **修复2**：删除失败的 `tests/test_temp_verify.py`（临时文件，断言已过时）
- **修复3**：为 `tests/test_gui_session_manager.py` 中 5 个发起真实 HTTP 请求的测试添加 mock，避免卡住
- **修复4**：修复 `tool_invocation.py:596` 的 `eval(expression)` 安全漏洞（限制命名空间）
- **修复5**：修复 `tool_invocation.py:540` 的裸 `except:` → `except Exception:`
- **修复6**：修复 `brain.py` 中 3 处 fire-and-forget `asyncio.create_task` 的异常静默问题
- **修复7**：修复 `ollama_model.py` 中 aiohttp ClientSession 未关闭的资源泄漏
- **修复8**：修复 `test_e2e_test_model_revert.py` 和 `test_config_save_verify.py` 的 `PytestReturnNotNoneWarning`
- **修复9**：缩短 `test_hermes_nudge.py` 的 `asyncio.sleep(2.6)` 和 `test_hermes_trajectory.py` 的 `asyncio.sleep(2.0)`
- **BREAKING**：无

## Impact
- Affected specs: fix-test-model-revert（config.yaml 再次修正）、system-check-and-debug（测试修复）
- Affected code:
  - `config.yaml`（模型名同步）
  - `hyperbrain/layers/execution/tool_invocation.py`（eval 安全 + 裸 except）
  - `hyperbrain/core/brain.py`（asyncio task 异常处理）
  - `hyperbrain/models/ollama_model.py`（aiohttp session 清理）
  - `tests/test_gui_session_manager.py`（添加 mock）
  - `tests/test_temp_verify.py`（删除）
  - `tests/test_e2e_test_model_revert.py`（修复 warning）
  - `tests/test_config_save_verify.py`（修复 warning）
  - `tests/test_hermes_nudge.py`（缩短 sleep）
  - `tests/test_hermes_trajectory.py`（缩短 sleep）

## 根因调查结果

### 问题 1：config.yaml 三个模型名不一致
```yaml
model:
  default_model: qwen3.5:0.8b        # ← 第一个
  ollama_model: minimax-m3:cloud     # ← 第二个（用户手动改的）
hermes:
  trainer:
    base_model: gemma2:2b            # ← 第三个
```
- `default_model` 和 `ollama_model` 不同步，导致 `ModelManager` 可能在 fallback 时选错模型
- `hermes.trainer.base_model` 指向 `gemma2:2b`（可能未安装），trainer 启动会失败

### 问题 2：test_temp_verify.py 断言过时
- 断言 `ollama_model == 'qwen3.5:0.8b'`，但用户已改为 `minimax-m3:cloud`
- 这是上一轮创建的临时验证文件，应删除

### 问题 3：test_gui_session_manager.py 真实网络请求
- 5 个测试直接对 `http://localhost:11434` 发起 HTTP 请求
- `test_ollama_service_available`：aiohttp GET /api/tags（5s 超时）
- `test_discover_local_models`：discover_local_models() 真实 HTTP
- `test_ollama_model_chat`：model.initialize() + model.chat()（120s 超时）
- `test_brain_process`：brain.initialize() + brain.start() + brain.process()（120s 超时）
- `test_full_conversation_flow`：同上
- Ollama 未运行时，单次请求最长阻塞 120 秒

### 问题 4：eval 安全漏洞
- `tool_invocation.py:596`：`result = eval(expression)` —— 无命名空间限制
- 攻击者可通过 `__import__('os').system('rm -rf /')` 执行任意代码
- 对比 `calculator.py:40`：`eval(expression, {"__builtins__": {}}, self.OPERATORS)` —— 已限制

### 问题 5：裸 except
- `tool_invocation.py:540`：`except:` 会吞掉 `KeyboardInterrupt`、`SystemExit`
- 应改为 `except Exception:`

### 问题 6：fire-and-forget asyncio.create_task
- `brain.py:170`：`asyncio.create_task(callback(message))` —— 异常静默吞掉
- `brain.py:461`：`asyncio.create_task(self.shutdown())` —— 同上
- `brain.py:1185`：`asyncio.create_task(self._store_interaction(...))` —— 同上

### 问题 7：aiohttp 资源泄漏
- `ollama_model.py` 中 `aiohttp.ClientSession` 创建后未显式关闭
- 测试输出显示 `Unclosed client session` 警告 ×4

### 问题 8：PytestReturnNotNoneWarning
- `test_e2e_test_model_revert.py`：7 个测试函数 `return True/False` 而非用 `assert`
- `test_config_save_verify.py`：6 个测试函数同上

### 问题 9：测试中硬编码 sleep 过长
- `test_hermes_nudge.py:76`：`asyncio.sleep(2.6)` + `stop(timeout=3.0)` = 5.6s/测试
- `test_hermes_trajectory.py` 调用 `trainer.py:84`：`asyncio.sleep(2.0)`

## ADDED Requirements

### Requirement: config.yaml 模型名一致性
系统SHALL确保 `model.ollama_model`、`model.default_model`、`hermes.trainer.base_model` 三个字段指向同一模型或兼容的 fallback 链。

#### Scenario: 配置加载后三个字段一致
- **WHEN** `load_config` 完成
- **THEN** `default_model == ollama_model`，且 `hermes.trainer.base_model` 在 `fallback_models` 列表中

### Requirement: 测试不依赖外部服务
单元测试SHALL不对外部服务（Ollama API）发起真实 HTTP 请求，所有外部调用必须 mock。

#### Scenario: Ollama 未运行时测试通过
- **WHEN** Ollama 服务未启动
- **THEN** 所有测试在 5 秒内完成，无阻塞

### Requirement: eval 安全限制
系统SHALL在所有 `eval()` 调用中限制命名空间，禁止访问 `__builtins__`。

#### Scenario: 恶意表达式被拒绝
- **WHEN** `eval("__import__('os')", ...)`
- **THEN** 抛出 `NameError`，不执行任意代码

### Requirement: asyncio task 异常可见
系统SHALL确保所有 fire-and-forget `asyncio.create_task` 的异常被记录到日志。

#### Scenario: task 抛出异常
- **WHEN** fire-and-forget task 内部抛出异常
- **THEN** `logger.error` 记录异常信息，不静默吞掉

### Requirement: aiohttp session 清理
系统SHALL确保所有 `aiohttp.ClientSession` 在使用后显式关闭。

#### Scenario: 模型关闭后 session 关闭
- **WHEN** `OllamaModel.close()` 被调用
- **THEN** 内部 `ClientSession` 被关闭，无 `Unclosed client session` 警告

## MODIFIED Requirements

### Requirement: 测试函数规范
测试函数SHALL使用 `assert` 而非 `return True/False`，避免 `PytestReturnNotNoneWarning`。

### Requirement: 裸 except 禁止
代码中SHALL不使用裸 `except:`，必须指定异常类型（至少 `except Exception:`）。

## REMOVED Requirements
无

## 验证策略

### 测试运行
1. `py -3.14 -m pytest tests/ --ignore=tests/test_temp_verify.py -q` 全部通过
2. 无 `Unclosed client session` 警告
3. 无 `PytestReturnNotNoneWarning`
4. 所有测试在 60 秒内完成（无卡住）

### 安全验证
1. `eval("__import__('os')")` 在 tool_invocation 中被拒绝
2. 裸 `except:` 全部替换为 `except Exception:`

### 配置验证
1. `config.yaml` 中三个模型名字段一致
2. `get_config().model.default_model == get_config().model.ollama_model`
