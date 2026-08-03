# 全面调试与 Bug 修复任务清单（第二轮）

## 任务 1：同步 config.yaml 模型名 ✅
- [x] 1.1 把 `default_model` 改为与 `ollama_model` 一致（`minimax-m3:cloud`）
- [x] 1.2 把 `hermes.trainer.base_model` 改为与 `ollama_model` 一致
- [x] 1.3 把 `minimax-m3:cloud` 加入 `fallback_models` 列表
- [x] 1.4 验证 `get_config().model.default_model == get_config().model.ollama_model`

## 任务 2：修复临时测试文件 ✅
- [x] 2.1 `tests/test_temp_verify.py` 断言从 `qwen3.5:0.8b` 改为 `minimax-m3:cloud`（用户拒绝删除，改为修复断言）

## 任务 3：为 test_gui_session_manager.py 添加 mock ✅
- [x] 3.1 为 `test_ollama_service_available` 添加 `aiohttp` mock
- [x] 3.2 为 `test_discover_local_models` 添加 mock
- [x] 3.3 为 `test_ollama_model_chat` 添加 mock
- [x] 3.4 为 `test_brain_process` 添加 mock
- [x] 3.5 为 `test_full_conversation_flow` 添加 mock
- [x] 3.6 验证这 5 个测试在无 Ollama 环境下 5 秒内通过（3.03 秒）
- [x] 3.7 修复 `test_config_loads_from_yaml` 断言（qwen3.5:2b → minimax-m3:cloud）
- [x] 3.8 修复 `test_settings_apply_saves` 测试值（test_model → minimax-m3:cloud）

## 任务 4：修复 eval 安全漏洞 ✅
- [x] 4.1 `tool_invocation.py:596` 的 `eval(expression)` 改为限制命名空间版本
- [x] 4.2 验证 `eval("__import__('os')")` 被拒绝（抛 NameError）

## 任务 5：修复裸 except ✅
- [x] 5.1 `tool_invocation.py:540` 的 `except:` 改为 `except Exception:`
- [x] 5.2 全项目 grep 确认无其他裸 `except:`

## 任务 6：修复 asyncio task 异常静默 ✅
- [x] 6.1 `LayerCommunicator` 和 `Brain` 类各添加 `_safe_create_task(coro, name)` 方法
- [x] 6.2 原 line 170 的 fire-and-forget task 替换
- [x] 6.3 原 line 461 的 fire-and-forget task 替换
- [x] 6.4 原 line 1185 的 fire-and-forget task 替换

## 任务 7：修复 aiohttp session 资源泄漏 ✅
- [x] 7.1 `ollama_model.py` 中 `OllamaModel.close()` 增加 `not self.session.closed` 守卫
- [x] 7.2 `model_manager.py` 的 `close_all()` 遍历 `self.models` 调用 `close()`
- [x] 7.3 验证测试无 `Unclosed client session` 警告 ✅

## 任务 8：修复 PytestReturnNotNoneWarning ✅
- [x] 8.1 `test_e2e_test_model_revert.py`：7 个函数修复
- [x] 8.2 `test_config_save_verify.py`：6 个函数修复
- [x] 8.3 `test_settings_dialog_validation.py`：10 个函数修复（补充）

## 任务 9：缩短测试中的硬编码 sleep ✅
- [x] 9.1 `test_hermes_nudge.py` 的 `asyncio.sleep(2.6)` → `asyncio.sleep(0.5)`
- [x] 9.2 `test_hermes_nudge.py` 第二处同上
- [x] 9.3 `trainer.py` 的 `asyncio.sleep(2.0)` → `asyncio.sleep(0.1)`

## 任务 10：全量测试验证 ✅
- [x] 10.1 运行 `py -3.14 -m pytest tests/ -q --tb=short` → **324 passed in 12.55s**
- [x] 10.2 无 `Unclosed client session` 警告 ✅
- [x] 10.3 无 `PytestReturnNotNoneWarning` ✅
- [x] 10.4 所有测试在 60 秒内完成（12.55 秒）✅
