# 全面调试与 Bug 修复检查清单（第二轮）

## config.yaml 模型名一致性 ✅
- [x] `default_model` 与 `ollama_model` 一致（均为 `minimax-m3:cloud`）
- [x] `hermes.trainer.base_model` 与 `ollama_model` 一致（`minimax-m3:cloud`）
- [x] `minimax-m3:cloud` 在 `fallback_models` 列表中
- [x] `get_config().model.default_model == get_config().model.ollama_model`

## 临时测试文件清理 ✅
- [x] `tests/test_temp_verify.py` 断言已修复（适配 `minimax-m3:cloud`）
- [x] `py -3.14 -m pytest tests/` 不再出现 collection error

## test_gui_session_manager.py mock ✅
- [x] `test_ollama_service_available` 不发起真实 HTTP 请求
- [x] `test_discover_local_models` 不发起真实 HTTP 请求
- [x] `test_ollama_model_chat` 不发起真实 HTTP 请求
- [x] `test_brain_process` 不发起真实 HTTP 请求
- [x] `test_full_conversation_flow` 不发起真实 HTTP 请求
- [x] 5 个测试在无 Ollama 环境下 5 秒内通过（3.03 秒）
- [x] `test_config_loads_from_yaml` 断言修复
- [x] `test_settings_apply_saves` 测试值修复

## eval 安全 ✅
- [x] `tool_invocation.py` 的 `eval` 限制了 `__builtins__`
- [x] `eval("__import__('os')")` 被拒绝（抛 NameError）

## 裸 except 修复 ✅
- [x] `tool_invocation.py:540` 改为 `except Exception:`
- [x] 全项目 Python 源码无裸 `except:`

## asyncio task 异常处理 ✅
- [x] `LayerCommunicator` 添加 `_safe_create_task` 方法
- [x] `Brain` 添加 `_safe_create_task` 方法
- [x] 3 处 fire-and-forget task 替换为 `_safe_create_task`

## aiohttp session 清理 ✅
- [x] `OllamaModel.close()` 增加 `not self.session.closed` 守卫
- [x] `ModelManager.close_all()` 遍历调用每个模型的 `close()`
- [x] 测试无 `Unclosed client session` 警告

## PytestReturnNotNoneWarning 修复 ✅
- [x] `test_e2e_test_model_revert.py` 7 个函数用 `raise` 而非 `return`
- [x] `test_config_save_verify.py` 6 个函数同上
- [x] `test_settings_dialog_validation.py` 10 个函数同上
- [x] 无 `PytestReturnNotNoneWarning`

## 测试 sleep 缩短 ✅
- [x] `test_hermes_nudge.py` 的 sleep 从 2.6s 缩短到 0.5s
- [x] `trainer.py` dry_run 的 sleep 从 2.0s 缩短到 0.1s

## 全量测试验证 ✅
- [x] `py -3.14 -m pytest tests/ -q` → **324 passed in 12.55s**
- [x] 无 `Unclosed client session` 警告
- [x] 无 `PytestReturnNotNoneWarning`
- [x] 所有测试在 60 秒内完成（12.55 秒）

---

## 修改文件清单

| 文件 | 改动 |
|------|------|
| `config.yaml` | `default_model` / `fallback_models` / `hermes.trainer.base_model` 同步为 `minimax-m3:cloud` |
| `hyperbrain/layers/execution/tool_invocation.py` | eval 限制命名空间 + 裸 except → except Exception |
| `hyperbrain/core/brain.py` | 添加 `_safe_create_task` 方法，3 处 fire-and-forget task 替换 |
| `hyperbrain/models/ollama_model.py` | `close()` 增加 `not self.session.closed` 守卫 |
| `hyperbrain/models/model_manager.py` | `close_all()` 遍历调用各模型 `close()` |
| `tests/test_gui_session_manager.py` | 5 个测试添加 mock + 2 个断言修复 |
| `tests/test_temp_verify.py` | 断言适配 `minimax-m3:cloud` |
| `tests/test_e2e_test_model_revert.py` | return True/False → raise + 断言修复 |
| `tests/test_config_save_verify.py` | return True/False → raise + 断言修复 |
| `tests/test_settings_dialog_validation.py` | return True/False → raise |
| `tests/test_hermes_nudge.py` | asyncio.sleep 2.6→0.5 |
| `hyperbrain/hermes/trajectory/trainer.py` | asyncio.sleep 2.0→0.1 |
