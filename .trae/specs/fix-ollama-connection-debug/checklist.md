# Ollama 连接调试与修复 Checklist

> 验证范围：诊断 CLI 6 步、GUI 诊断对话框、OllamaConnectionError 结构化、BrainWorker 透传、model_name 漂移告警、fallback 校验、文档。
> 所有 checkpoint 必须在交付前勾选。

---

## 诊断 CLI 脚本（scripts/diagnose_ollama.py）

- [x] 脚本存在
- [x] Step 1 进程检查：Windows `tasklist` / Unix `pgrep` 都能识别 ollama 进程
- [x] Step 2 端口检查：5s 内 TCP connect host:port
- [x] Step 3 API 根：GET /api/version 返回 200
- [x] Step 4 模型列表：GET /api/tags 解析 models 数组
- [x] Step 5 模型元数据：POST /api/show {name: ollama_model} 返回 200
- [x] Step 6 生成测试：POST /api/generate num_predict=5 timeout=10s 拿到响应
- [x] 命令行支持 `--base-url` `--model` `--json` 参数
- [x] 输出格式：每行 `[STEP N] PASS/FAIL/WARN: <message>` 或 JSON
- [x] FAIL 时给出修复建议（"请运行 ollama serve"等）

## GUI 诊断对话框（hyperbrain/ui/diagnose_dialog.py）

- [x] 菜单"工具" → "诊断 Ollama 连接" 入口存在
- [x] 点击后弹出 QDialog 含 QTextEdit 显示 6 步结果
- [x] PASS 行绿色、FAIL 行红色、WARN 行黄色
- [x] 实时刷新（子进程每输出一行就追加）
- [x] "重新尝试连接" 按钮调用 model_manager.initialize_all()
- [x] "打开设置" 按钮跳到模型 tab

## 结构化错误（OllamaConnectionError）

- [x] `OllamaConnectionError` 异常类定义在 `ollama_model.py`
- [x] 异常字段：`stage / model / url / detail / suggestion`
- [x] `initialize()` 捕获 ClientConnectorError → stage="TCP_CONNECT"
- [x] `initialize()` HTTP 非 200 → stage="HTTP_TAGS"
- [x] `chat()` ClientResponseError → stage="HTTP_CHAT"
- [x] `chat()` asyncio.TimeoutError → stage="HTTP_CHAT_TIMEOUT"
- [x] `_probe_thinking_capability` 失败仅 WARN 不抛

## BrainWorker 透传

- [x] BrainWorker.run() 捕获 OllamaConnectionError → emit 结构化 dict
- [x] emit dict 含 `code="OLLAMA_CONNECT_FAIL"` + stage + url + suggestion
- [x] `_handle_error` 解析 OLLAMA_CONNECT_FAIL：根据 stage 渲染不同建议
- [x] 新增 `_show_connection_dialog` 复用 QMessageBox 风格

## ModelManager 启动校验

- [x] `_log_registration_summary` 打印所有注册模型
- [x] 当 `ollama_default.model_name != cfg.ollama_model` → log ERROR
- [x] 打印所有 `ollama_*` 模型的注册名
- [x] 不在初始化阶段强制修复（仅 WARN）

## fallback_models 校验

- [x] `_validate_fallback_models` 方法存在
- [x] 启动时对每个 fallback model 调 /api/show
- [x] 不存在 → 状态栏 WARN
- [x] `chat_with_fallback` chain 中跳过不存在的

## 测试

- [x] `tests/test_diagnose_ollama.py` 存在
- [x] 测试 CLI 6 步解析 PASS/FAIL/WARN 输出
- [x] 测试 OllamaConnectionError 各 stage
- [x] 测试 BrainWorker emit OLLAMA_CONNECT_FAIL
- [x] 测试 ModelManager._log_registration_summary 在漂移时打 ERROR
- [x] 测试 _validate_fallback_models 跳过不存在 model

## 文档

- [x] README 新增"连接不上怎么办"章节
- [x] settings_dialog 提示"遇到连接问题？点击菜单 工具 → 诊断 Ollama 连接"

## 端到端验证（手动 ⏳）

- [ ] 启动 GUI → 工具 → 诊断 Ollama 连接 → 6 步全 PASS
- [ ] 临时把 ollama 进程 kill → 再点诊断 → Step 1 FAIL + 红色显示
- [ ] 临时把 config ollama_base_url 改成不存在的端口 → Step 2 FAIL
- [ ] 临时把 ollama_model 改成不存在的名字 → Step 4/5 FAIL
- [ ] 故意制造 thinking 模型超时（>180s）→ 旧超时对话框触发
- [ ] 故意制造网络断开 → 新连接错误对话框触发，stage=TCP_CONNECT
- [ ] 设置 fallback_models = ["gemma2:2b", "fakemodel:7b"] → 启动时 WARN

