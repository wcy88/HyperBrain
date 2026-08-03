# Agent 响应慢全面调试与修复任务清单

> 目标：修复"Ollama 直接快但走 Agent 慢"的 5 个叠加瓶颈，让 Agent 响应时间接近直接用 Ollama。

---

## 任务 1：chat() 支持 stream 模式

- [ ] 1.1 修改 `OllamaModel.chat()`：当 `self.config.stream is True` 时，调用 `stream_chat()` 并 join 返回
- [ ] 1.2 保留 `config.stream=False` 时的现有行为（`payload["stream"] = False`）
- [ ] 1.3 stream 模式下 `ModelResponse` 的 `content` 是 join 后的完整文本
- [ ] 1.4 stream 模式下 `ModelResponse.usage` 仍正确统计 token
- [ ] 1.5 验证：`py -3.14 -m pytest tests/test_thinking_timeout.py -v` 不挂

## 任务 2：think 默认安全值 + 设置 UI 警告

- [ ] 2.1 `config.yaml` 中 `think: true` → `think: false`
- [ ] 2.2 `hyperbrain/core/config.py` 中 `think` 字段默认值改为 `False`
- [ ] 2.3 `hyperbrain/ui/settings_dialog.py` 中 think QCheckBox 旁加警告 tooltip："开启后 thinking 模型会先生成思维链再回答，响应时间可能增加 30-100 秒"
- [ ] 2.4 验证：`py -3.14 -c "from hyperbrain.core.config import get_config; c=get_config(); print('think=', c.model.think)"` 输出 `think= False`

## 任务 3：Brain.process() 分层计时

- [ ] 3.1 在 `process()` 每层前后加 `time.time()` 计时
- [ ] 3.2 每层完成后 log INFO：`f"[perf] {layer_name}: {elapsed_ms:.0f}ms"`
- [ ] 3.3 总耗时在 `process()` 末尾 log INFO：`f"[perf] TOTAL: {total_ms:.0f}ms"`
- [ ] 3.4 如果总耗时 > 10s，额外 log WARNING 标注最慢层
- [ ] 3.5 验证：跑 `py -3.14 -c "import asyncio; from hyperbrain.core.brain import Brain; b=Brain(); asyncio.run(b.initialize()); r=asyncio.run(b.process('hello')); print(r.content[:50])"` 看到分层计时日志

## 任务 4：后处理 fire-and-forget

- [ ] 4.1 把步骤 9-14（记忆存储 + 学习 + DB 写入 + Hermes 钩子）包裹在 `asyncio.create_task()` 中
- [ ] 4.2 fire-and-forget task 内部 try/except 包好，失败仅 log error
- [ ] 4.3 `process()` 在模型返回后立即构造 `ProcessingResult` 并返回
- [ ] 4.4 验证：`process()` 返回时间 ≈ 模型响应时间 + 前处理时间（不含后处理）
- [ ] 4.5 验证：后处理仍正常执行（记忆/DB 有数据）

## 任务 5：性能剖析脚本 `scripts/profile_agent.py`

- [ ] 5.1 创建脚本，发送一条 "hello" 到 Brain
- [ ] 5.2 捕获分层计时输出
- [ ] 5.3 格式化输出表格（层名 / 耗时 / 占比）
- [ ] 5.4 标注瓶颈层（耗时 > 总耗时 50% 的层）
- [ ] 5.5 给出针对性建议（如 "model.chat 占 98%，检查 stream/think 配置"）
- [ ] 5.6 支持 `--model` / `--prompt` / `--iterations N` 参数
- [ ] 5.7 GBK 兼容（ASCII 输出）
- [ ] 5.8 验证：`py -3.14 scripts/profile_agent.py` 正常输出

## 任务 6：单元测试 `tests/test_agent_perf.py`

- [ ] 6.1 测试 `OllamaModel.chat()` 在 `config.stream=True` 时走 `stream_chat()`
- [ ] 6.2 测试 `OllamaModel.chat()` 在 `config.stream=False` 时走原路径
- [ ] 6.3 测试 `Brain.process()` 分层计时日志存在
- [ ] 6.4 测试 `Brain.process()` 后处理不阻塞返回（mock 验证 create_task 被调用）
- [ ] 6.5 测试 `config.yaml` think 默认为 false
- [ ] 6.6 测试 `profile_agent.py` 可 import 不挂
- [ ] 6.7 回归：`py -3.14 -m pytest tests/ -v` 全部通过

---

## 任务依赖关系

```
任务1 (stream) ─────┐
任务2 (think 默认) ─┤── 任务6 (测试) ── 任务7 (回归验证)
任务3 (分层计时) ───┤
任务4 (fire-forget) ┤
任务5 (profile) ────┘
```

并行：1/2/3/4/5 可并行；6 依赖 1-5；7 最后

---

## 关键文件清单

| 文件 | 改动 |
|------|------|
| `hyperbrain/models/ollama_model.py` | 改（chat stream 逻辑） |
| `hyperbrain/core/brain.py` | 改（分层计时 + fire-and-forget） |
| `hyperbrain/core/config.py` | 改（think 默认值） |
| `hyperbrain/ui/settings_dialog.py` | 改（think 警告 tooltip） |
| `config.yaml` | 改（think: false） |
| `scripts/profile_agent.py` | 新增 |
| `tests/test_agent_perf.py` | 新增 |
