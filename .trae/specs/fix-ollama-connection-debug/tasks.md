# Ollama 连接调试与修复任务清单

> 目标：解决"本地模型不能用，不是反应慢问题"的不明错误。提供 6 步分级诊断 CLI + GUI 诊断按钮 + 结构化错误，定位是进程/端口/URL/模型名/模型元数据/生成哪一步断的。

---

## 任务1：编写 6 步诊断 CLI 脚本
- [ ] 1.1 创建 `scripts/diagnose_ollama.py`（用 aiohttp + argparse，跨平台）
- [ ] 1.2 实现 Step 1（进程）：Windows 用 `tasklist /FI "IMAGENAME eq ollama.exe"`，Unix 用 `pgrep -f ollama`
- [ ] 1.3 实现 Step 2（端口）：解析 base_url 的 host:port，5s 内 TCP connect
- [ ] 1.4 实现 Step 3（API 根）：`GET /api/version` 验证 Ollama 真的在响应
- [ ] 1.5 实现 Step 4（模型列表）：`GET /api/tags` 解析 models 列表，检查 cfg.ollama_model 是否在其中
- [ ] 1.6 实现 Step 5（模型元数据）：`POST /api/show` 检查模型真实可用
- [ ] 1.7 实现 Step 6（生成测试）：`POST /api/generate` num_predict=5, timeout=10s
- [ ] 1.8 每步输出结构化结果 `{"step": N, "name": "...", "status": "PASS|FAIL|WARN", "detail": "...", "fix": "..."}`
- [ ] 1.9 命令行支持 `--base-url http://127.0.0.1:11434 --model qwen3.5:2b --json` 输出模式

## 任务2：MainWindow 诊断菜单与对话框
- [ ] 2.1 在 MainWindow 菜单栏增加"工具" → "诊断 Ollama 连接"
- [ ] 2.2 创建 `hyperbrain/ui/diagnose_dialog.py`：QTextEdit 实时显示 + 标色 + "重新尝试连接" 按钮
- [ ] 2.3 启动子进程运行 `scripts/diagnose_ollama.py`，逐行解析 PASS/FAIL/WARN
- [ ] 2.4 任一步 FAIL → 显示红色 + "打开设置" 按钮（跳到模型 tab）
- [ ] 2.5 "重新尝试连接" 按钮调用 `model_manager.initialize_all()` 并 refresh 状态栏

## 任务3：结构化连接错误 OllamaConnectionError
- [ ] 3.1 在 `hyperbrain/models/ollama_model.py` 新增 `OllamaConnectionError(stage, model, url, detail)` 异常类
- [ ] 3.2 `initialize()` 捕获 ClientConnectorError → 抛 OllamaConnectionError(stage="TCP_CONNECT", ...)
- [ ] 3.3 `initialize()` 捕获 HTTP 非 200 → 抛 OllamaConnectionError(stage="HTTP_TAGS", ...)
- [ ] 3.4 `chat()` 捕获 ClientResponseError 4xx/5xx → 抛 OllamaConnectionError(stage="HTTP_CHAT", ...)
- [ ] 3.5 `chat()` 捕获 asyncio.TimeoutError → 抛 OllamaConnectionError(stage="HTTP_CHAT_TIMEOUT", ...)
- [ ] 3.6 `_probe_thinking_capability` 失败时日志 WARN 但不抛（保持向后兼容）

## 任务4：BrainWorker 透传连接错误
- [ ] 4.1 BrainWorker.run() 捕获 OllamaConnectionError → emit `{code: "OLLAMA_CONNECT_FAIL", stage, model, url, suggestion}`
- [ ] 4.2 `_handle_error` 新增 OLLAMA_CONNECT_FAIL 分支：根据 stage 渲染针对性建议
  - TCP_CONNECT → "Ollama 服务未运行或端口不通。运行 `ollama serve` 或检查防火墙"
  - HTTP_TAGS → "API 根路径异常，请检查 base_url"
  - HTTP_SHOW → "模型 X 不存在，请用 `ollama pull X` 拉取"
  - HTTP_CHAT → "模型推理失败，请检查模型是否损坏或切换到 gemma2:2b"
- [ ] 4.3 在 `_show_timeout_dialog` 旁增加 `_show_connection_dialog` 复用同一 QMessageBox 风格

## 任务5：ModelManager 启动校验与 model_name 漂移告警
- [ ] 5.1 在 `ModelManager.__init__` 末尾增加 `_log_registration_summary()`：打印所有注册项 + cfg.ollama_model 对比
- [ ] 5.2 若 `self.models["ollama_default"].model_name != config.ollama_model` → log ERROR + 状态栏 WARN
- [ ] 5.3 打印所有 `ollama_*` 模型的注册名（best-effort）
- [ ] 5.4 不在初始化阶段强制修复（避免误覆盖用户手动配置），仅 WARN

## 任务6：fallback_models 存在性校验
- [ ] 6.1 新增 `ModelManager._validate_fallback_models()` 方法
- [ ] 6.2 启动时对每个 fallback model 调 `/api/show`
- [ ] 6.3 不存在的 fallback → 状态栏 WARN "fallback X 不在 /api/tags 中，将被忽略"
- [ ] 6.4 `chat_with_fallback` 在 chain 中跳过不存在的 model（已存在会通过 `is_thinking` 等检测，但缺失时直接 raise）

## 任务7：单元测试
- [ ] 7.1 新增 `tests/test_diagnose_ollama.py`：mock subprocess 输出，验证 CLI 6 步逻辑
- [ ] 7.2 测试 OllamaConnectionError 各 stage 抛出条件
- [ ] 7.3 测试 BrainWorker 收到 OllamaConnectionError 时 emit 正确 code
- [ ] 7.4 测试 ModelManager._log_registration_summary 在 model_name 漂移时打 ERROR
- [ ] 7.5 测试 _validate_fallback_models 跳过不存在的 model

## 任务8：文档
- [ ] 8.1 README 新增"连接不上怎么办"章节：引导用户先跑 `py scripts/diagnose_ollama.py`
- [ ] 8.2 在 settings_dialog tooltip 中增加"遇到连接问题？点击菜单 工具 → 诊断 Ollama 连接"

---

## 任务依赖关系

```
任务1 (CLI) ─┬── 任务2 (GUI 诊断对话框) ──┐
             └── 任务7 (测试)              │
任务3 (异常) ─┬── 任务4 (BrainWorker) ─────┤
             └── 任务7 (测试)              │
任务5 (漂移告警) ── 任务6 (fallback 校验) ─┤
                                           │
                                       任务8 (文档)
```

并行：1/3/5/6 可并行（独立文件）
串行：2/4 依赖 1/3；7 依赖 1-6 全部；8 最后

---

## 关键文件清单

| 文件 | 改动 |
|------|------|
| `scripts/diagnose_ollama.py` | 新增（6 步 CLI 诊断） |
| `hyperbrain/ui/diagnose_dialog.py` | 新增（GUI 诊断对话框） |
| `hyperbrain/ui/main_window.py` | 增加"工具"菜单 + 诊断对话框入口 |
| `hyperbrain/models/ollama_model.py` | 新增 OllamaConnectionError 异常 + initialize 错误捕获 |
| `hyperbrain/models/model_manager.py` | `_log_registration_summary` + `_validate_fallback_models` |
| `hyperbrain/ui/main_window.py` | `_handle_error` 增加 OLLAMA_CONNECT_FAIL 分支 |
| `tests/test_diagnose_ollama.py` | 新增测试 |
| `README.md` | 新增"连接不上"章节 |

