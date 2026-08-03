# diagnose_ollama.py GBK 编码与 thinking 超时修复任务清单

> 目标：解决上一轮 `fix-ollama-connection-debug` 产出的 `diagnose_ollama.py` 在 Windows GBK 终端乱码 + Step 6 对 thinking 模型（qwen3.5:0.8b）15s 超时不够的 2 个真实问题。

---

## 任务 1：全面 ASCII 化用户面向字符串

- [ ] 1.1 `_step_print()` 中所有中文 label 改英文：`name="process"/"port"/"api root"/"model list"/"model show"/"generate test"`
- [ ] 1.2 `_step_print()` 的 detail 字符串改英文：`"ollama.exe running (PIDs: ...)"` / `"port X:Y TCP reachable"` / `"GET /api/version -> 200"` 等
- [ ] 1.3 fix 提示改英文：`"please run: ollama serve"` / `"model not found, try: ollama pull <model>"` 等
- [ ] 1.4 `check_process()` / `check_port()` / `check_api_steps()` 中所有 `_step_print(...)` 调用同步改
- [ ] 1.5 顶部 header 改英文：`"Ollama Connection Diagnostic"` / `"base_url: ..."` / `"model: ..."` / `"platform: ..."`
- [ ] 1.6 `_summary()` 文案改英文：`"Summary: PASS=X FAIL=Y WARN=Z"` / `"Ollama full chain works"` / `"X step(s) failed, see fix above"`
- [ ] 1.7 ASCII 化的 `try/except UnicodeEncodeError` 仍然保留（防御性，但理论上不再需要触发）

## 任务 2：thinking 模型自动检测 + think:false

- [ ] 2.1 在 `check_api_steps()` 中，Step 5 拿到 `/api/show` 响应后，**先**判断是否是 thinking 模型
- [ ] 2.2 thinking 判定规则（任一命中）：
  - `capabilities` 列表含 `"thinking"`（大小写不敏感）
  - `family` 含 `qwen3` / `qwen35` / `deepseek-r1` / `qwq`（大小写不敏感）
  - `model_name` 含 `qwen3` / `qwen35` / `deepseek-r1` / `qwq`
- [ ] 2.3 thinking 模型 → Step 6 请求体加 `"think": false` + `timeout_sec = args.timeout_think`（默认 60s）
- [ ] 2.4 非 thinking 模型 → Step 6 保持原样（不加 think, `timeout_sec=15`）
- [ ] 2.5 Step 6 FAIL 时的 fix 文案区分 thinking / 非 thinking：
  - thinking: "thinking model is slow on first token. Switch to gemma2:2b / qwen2.5:7b, or raise --timeout-think to 180"
  - 非 thinking: 保持现状（"model broken, try: ollama rm && ollama pull"）

## 任务 3：--timeout-think CLI 参数

- [ ] 3.1 argparse 新增 `--timeout-think`（int，默认 60）
- [ ] 3.2 验证范围 10-600（<10 强制 10，>600 强制 600）
- [ ] 3.3 `--help` 文本说明："Step 6 timeout (sec) for thinking models (qwen3*, deepseek-r1, qwq). Default 60."

## 任务 4：单元测试 `tests/test_diagnose_cli_gbk.py`

- [ ] 4.1 测试 `_step_print` 在强制 `sys.stdout.encoding="gbk"` 下不抛 `UnicodeEncodeError`
- [ ] 4.2 测试所有 step 名称都是 ASCII（用 `re.match(r'^[\x00-\x7f]+$', name)` 验证）
- [ ] 4.3 测试 Step 5 拿到 thinking capabilities → Step 6 收到 `payload["think"] == False` 且 `timeout=60`
- [ ] 4.4 测试 Step 5 拿到非 thinking → Step 6 payload 没有 `think` key 且 `timeout=15`
- [ ] 4.5 测试 `--timeout-think 180` CLI 参数被 parse 到 `args.timeout_think == 180`
- [ ] 4.6 测试 `--timeout-think 5` 强制升到 10（验证范围）
- [ ] 4.7 测试 `--timeout-think 1000` 强制降到 600
- [ ] 4.8 测试 JSON 模式仍输出中文（`ensure_ascii=False` 保留）

## 任务 5：验证（实跑 PyInstaller exe / py -3.14）

- [ ] 5.1 `py -3.14 scripts/diagnose_ollama.py --model gemma2:2b` —— 6 步全 PASS，输出英文
- [ ] 5.2 `py -3.14 scripts/diagnose_ollama.py --model qwen3.5:0.8b` —— 6 步全 PASS（think:false + 60s）
- [ ] 5.3 `py -3.14 scripts/diagnose_ollama.py --model nonexistent:9b` —— Step 4/5 FAIL，输出英文
- [ ] 5.4 `py -3.14 scripts/diagnose_ollama.py --model qwen3.5:0.8b --json` —— JSON 含中文（脚本可读）

---

## 任务依赖关系

```
任务1 (ASCII 化) ─┬── 任务4 (测试) ──┐
任务2 (thinking) ─┤                  ├── 任务5 (验证)
任务3 (CLI 参数) ─┘                  │
```

并行：1/2/3 可并行；4 依赖 1/2/3；5 最后

---

## 关键文件清单

| 文件 | 改动 |
|------|------|
| `scripts/diagnose_ollama.py` | 改（ASCII 化 + thinking 检测 + --timeout-think） |
| `tests/test_diagnose_cli_gbk.py` | 新增（GBK 兼容 + thinking 行为测试） |
