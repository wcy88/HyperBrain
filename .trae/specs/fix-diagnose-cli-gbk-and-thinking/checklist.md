# diagnose_ollama.py GBK 编码与 thinking 超时修复 Checklist

> 验证范围：scripts/diagnose_ollama.py 全面 ASCII 化 + thinking 模型自动 think:false + --timeout-think CLI 参数 + 单元测试。
> 所有 checkpoint 必须在交付前勾选。

---

## ASCII 化用户面向字符串（任务1）

- [x] `_step_print` 的 name 字符串（"process" / "port" / "api root" / "model list" / "model show" / "generate test"）都是 ASCII
- [x] `_step_print` 的 detail 字符串都是 ASCII（无中文）
- [x] `_step_print` 的 fix 字符串都是 ASCII（无中文）
- [x] `check_process()` 输出：process label + 英文 detail + 英文 fix
- [x] `check_port()` 输出：port label + 英文 detail + 英文 fix
- [x] `check_api_steps()` Step 3/4/5/6 输出：英文 label + 英文 detail + 英文 fix
- [x] 顶部 header 改英文："Ollama Connection Diagnostic" / "base_url:" / "model:" / "platform:"
- [x] `_summary()` 文案英文："Summary: PASS=X FAIL=Y WARN=Z" / "Ollama full chain works" / "X step(s) failed, see fix above"
- [x] `try/except UnicodeEncodeError` 仍保留（防御性）

## thinking 模型自动处理（任务2）

- [x] `check_api_steps()` 在 Step 5 后判断 is_thinking（基于 capabilities/family/model_name）
- [x] thinking 模型 Step 6 payload 含 `"think": false`
- [x] thinking 模型 Step 6 timeout = `args.timeout_think`（默认 60s）
- [x] 非 thinking 模型 Step 6 payload 不含 `think` key
- [x] 非 thinking 模型 Step 6 timeout = 15s
- [x] Step 6 FAIL 时 fix 文案区分 thinking / 非 thinking

## --timeout-think CLI 参数（任务3）

- [x] argparse 新增 `--timeout-think` (int, default 60)
- [x] 参数 < 10 强制升到 10
- [x] 参数 > 600 强制降到 600
- [x] `--help` 文案说明用途
- [x] 10 ≤ value ≤ 600 范围内正常生效

## 单元测试（任务4）

- [x] `tests/test_diagnose_cli_gbk.py` 存在
- [x] 测试 `_step_print` 在 GBK 强制编码下不抛 UnicodeEncodeError
- [x] 测试所有 step name 是 ASCII（`re.match(r'^[\x00-\x7f]+$', name)`）
- [x] 测试 Step 5 拿到 thinking capabilities → Step 6 payload `think == False` + `timeout == 60`
- [x] 测试 Step 5 拿到非 thinking → Step 6 payload 无 think + `timeout == 15`
- [x] 测试 `--timeout-think 180` 解析到 `args.timeout_think == 180`
- [x] 测试 `--timeout-think 5` 强制升到 10
- [x] 测试 `--timeout-think 1000` 强制降到 600
- [x] 测试 JSON 模式 `ensure_ascii=False`（中文保留）

## 端到端验证（脚本可跑）

- [x] `py -3.14 scripts/diagnose_ollama.py --model gemma2:2b` —— 6 步全 PASS，输出英文
- [x] `py -3.14 scripts/diagnose_ollama.py --model qwen3.5:0.8b` —— 6 步全 PASS（think:false + 60s）
- [x] `py -3.14 scripts/diagnose_ollama.py --model nonexistent:9b` —— Step 4/5 FAIL，输出英文
- [x] `py -3.14 scripts/diagnose_ollama.py --model qwen3.5:0.8b --json` —— JSON 含中文
- [ ] 跑 PyInstaller exe（`dist/HyperBrain/HyperBrain.exe` 调用 diagnose 子进程）也走通——GUI 通过 QProcess 读 utf-8 不受 GBK 影响

## 回归

- [x] `py -3.14 -m pytest tests/test_diagnose_ollama.py tests/test_thinking_timeout.py tests/test_diagnose_cli_gbk.py -v` —— 全部通过
- [x] 现有 53 个测试不挂
