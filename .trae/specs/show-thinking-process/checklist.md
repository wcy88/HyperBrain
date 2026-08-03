# Ollama 思考模型思维链可视化 Checklist

> 验证范围：ModelResponse.thinking 字段 + stream_chat 区分 yield + think 默认 true + --timeout-think 180 + GUI 折叠区 + Brain 透传 + 测试。
> 所有 checkpoint 必须在交付前勾选。

---

## ModelResponse + thinking 解析（任务1）

- [x] `ModelResponse.thinking: str = ""` 字段存在
- [x] `_parse_chat_response` 提取 `resp.message.thinking` 字段
- [x] 缺失 thinking 字段时返回空字符串
- [x] 现有 21 个 test_thinking_timeout 测试不挂

## stream_chat yield 区分（任务2）

- [x] `stream_chat()` yield `(type, text)` 元组（type ∈ {"thinking", "content"}）
- [x] `chat()` 在 stream=True 时 join 累加 thinking 和 content
- [x] join 后 thinking 完整保留
- [x] join 后 content 完整保留

## think 默认 true（任务3）

- [x] `config.yaml` 中 `think: true`
- [x] `hyperbrain/core/config.py` 默认 `think: bool = True`
- [x] `hyperbrain/models/base.py` `ModelConfig.think: bool = True`
- [x] settings_dialog think QCheckBox 默认勾选
- [x] `get_config().model.think == True`

## --timeout-think 默认 180（任务4）

- [x] `diagnose_ollama.py` argparse `--timeout-think` 默认 180
- [x] argparse help 文本更新
- [x] 跑 `py -3.14 scripts/diagnose_ollama.py --model qwen3.5:2b` Step 6 用 180s

## BrainWorker.partial_thinking（任务5）

- [x] `BrainWorker.partial_thinking = pyqtSignal(str)` 定义
- [x] `BrainWorker.run()` 改为流式调用 `mm.stream_chat()`
- [x] stream yield type="thinking" → emit partial_thinking
- [x] stream yield type="content" → emit partial_chunk（兼容现有）
- [x] result_ready 携带完整 thinking + content

## MainWindow 思维链 UI（任务6）

- [x] `_on_partial_thinking(text)` 槽函数实现
- [x] AI 消息气泡有"💭 思考过程"折叠区
- [x] 默认折叠，点击展开/折叠
- [x] 展开时淡灰色 `#888888` 等宽字体 12px
- [x] 非 thinking 模型不显示折叠区
- [ ] 实跑 qwen3.5:2b 看到思维链（GUI 手动验证）

## Brain 透传 thinking（任务7）

- [x] `Brain.process()` 把 `model_response.thinking` 存到 `result.metadata["thinking"]`
- [x] thinking 不写入长期记忆
- [x] thinking 不写入工作记忆

## 单元测试（任务8）

- [x] `tests/test_thinking_visualization.py` 存在
- [x] 测试 ModelResponse.thinking
- [x] 测试 _parse_chat_response 提取 thinking
- [x] 测试 _parse_chat_response 缺失字段
- [x] 测试 stream_chat yield 元组
- [x] 测试 chat stream=True join
- [x] 测试 BrainWorker.partial_thinking emit
- [x] 测试 config.think 默认 True
- [x] 测试 diagnose_ollama.py --timeout-think 默认 180

## 端到端验证

- [x] `py -3.14 -m pytest tests/test_thinking_timeout.py tests/test_diagnose_ollama.py tests/test_diagnose_cli_gbk.py tests/test_thinking_visualization.py -v` 全部通过
- [x] 现有 69+ 个测试不挂
- [x] `py -3.14 scripts/diagnose_ollama.py --model qwen3.5:2b --timeout-think 180` 6 步全 PASS
- [ ] 启动 GUI 跑 qwen3.5:2b 看到思维链折叠区（GUI 手动验证）

## 回归

- [x] `py -3.14 -m pytest tests/ -v` 不挂
- [ ] GUI 启动不报错（GUI 手动验证）
- [ ] 主流程（用户发消息 → AI 回复）正常（GUI 手动验证）
