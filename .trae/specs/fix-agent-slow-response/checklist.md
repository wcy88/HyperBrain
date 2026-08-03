# Agent 响应慢全面调试与修复 Checklist

> 验证范围：chat stream 模式 + think 安全默认 + 分层计时 + fire-and-forget + 性能剖析 + 测试。
> 所有 checkpoint 必须在交付前勾选。

---

## chat() stream 模式（任务1）

- [ ] `OllamaModel.chat()` 在 `config.stream=True` 时调用 `stream_chat()` 并 join
- [ ] `OllamaModel.chat()` 在 `config.stream=False` 时保持 `payload["stream"] = False`
- [ ] stream 模式返回的 `ModelResponse.content` 是完整文本
- [ ] stream 模式 `ModelResponse.usage` 正确
- [ ] 现有 21 个 test_thinking_timeout 测试不挂

## think 安全默认值（任务2）

- [ ] `config.yaml` 中 `think: false`
- [ ] `config.py` 中 `think` 字段默认 `False`
- [ ] settings_dialog think QCheckBox 有警告 tooltip
- [ ] `get_config().model.think` 返回 `False`

## 分层计时（任务3）

- [ ] `Brain.process()` 每层有 `[perf] <layer>: Xms` 日志
- [ ] 总耗时有 `[perf] TOTAL: Xms` 日志
- [ ] 总耗时 > 10s 时有 WARNING 标注最慢层
- [ ] 日志级别为 INFO（非 DEBUG）

## 后处理 fire-and-forget（任务4）

- [ ] 步骤 9-14 用 `asyncio.create_task()` 包裹
- [ ] fire-and-forget task 内部 try/except
- [ ] `process()` 在模型返回后立即返回 `ProcessingResult`
- [ ] 后处理仍正常执行（记忆/DB 有数据）
- [ ] 后处理失败不影响已返回的 `ProcessingResult`

## 性能剖析脚本（任务5）

- [ ] `scripts/profile_agent.py` 存在且可运行
- [ ] 输出分层耗时表格
- [ ] 标注瓶颈层
- [ ] 给出针对性建议
- [ ] 支持 `--model` / `--prompt` / `--iterations` 参数
- [ ] GBK 兼容（ASCII 输出）

## 单元测试（任务6）

- [ ] `tests/test_agent_perf.py` 存在
- [ ] 测试 chat stream=True 走 stream_chat
- [ ] 测试 chat stream=False 走原路径
- [ ] 测试分层计时日志存在
- [ ] 测试后处理 fire-and-forget
- [ ] 测试 think 默认 false
- [ ] 测试 profile_agent.py 可 import

## 回归

- [ ] `py -3.14 -m pytest tests/test_thinking_timeout.py tests/test_diagnose_ollama.py tests/test_diagnose_cli_gbk.py tests/test_agent_perf.py -v` 全部通过
- [ ] 现有 69 个测试不挂
