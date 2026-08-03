# 修复 Ollama Model 字段重启后变回 test_model 任务清单

> 目标：把 config.yaml 中写死的 test_model 改回用户实际可用的模型，并防止再次被占位符覆盖
> 状态：待实现

---

## 任务 1：修正 config.yaml 的默认值 ✅
- [x] 1.1 把 `ollama_model: test_model` 改为 `ollama_model: qwen3.5:0.8b`
- [x] 1.2 把 `default_model: gemma2:2b` 同步为 `default_model: qwen3.5:0.8b`（与 ollama_model 一致）
- [x] 1.3 在 `model.ollama_model` 旁加注释，说明默认值与回退策略
- [x] 1.4 用 `py -3.14 -c "from hyperbrain.core.config import get_config; print(get_config().model.ollama_model)"` 验证加载值 = `qwen3.5:0.8b`

## 任务 2：settings_dialog 增加字段校验 ✅
- [x] 2.1 在 `settings_dialog._update_config` 中读取 `ollama_model_edit.text().strip()`
- [x] 2.2 添加空值校验：空白时抛 `ValueError("Ollama Model 不能为空")`
- [x] 2.3 添加占位符拒绝列表：`test_model`, `test`, `placeholder`, `default`, `example` 抛 `ValueError`
- [x] 2.4 通过校验后才赋值给 `self._config.model.ollama_model`
- [x] 2.5 在 `_apply_settings` 中 catch `ValueError`，弹 `QMessageBox.warning` 提示用户

## 任务 3：ConfigManager.save_config 增加写后回读 ✅
- [x] 3.1 在 `config.py:ConfigManager.save_config` 中，yaml 写入后立即 open 读回（新增 `_verify_saved_config` 方法）
- [x] 3.2 比对回读字段 `model.ollama_model` 与内存值
- [x] 3.3 不一致时 `logger.error` 打印差异并 `raise IOError`
- [x] 3.4 一致时 `logger.info` 打印 "Configuration saved and verified: ollama_model=xxx"
- [x] 3.5 在 settings_dialog._apply_settings 的 try 块中 catch `IOError`，弹窗"配置保存失败，请检查磁盘权限"
- [x] 3.6 额外修复：`Config` 类缺失 `hermes` 字段（`to_dict` 引用了 `self.hermes` 但未声明），添加 `hermes: HermesConfig = field(default_factory=HermesConfig)`

## 任务 4：状态栏保存反馈 ✅
- [x] 4.1 在 `settings_dialog._apply_settings` 保存成功后，emit `settings_saved` 信号携带 saved_fields dict
- [x] 4.2 在 `main_window._show_settings` 中连接该信号到 `_on_settings_saved` 槽函数
- [x] 4.3 `_on_settings_saved` 读取 dict，更新 `self.status_label.setText(f"已保存: {provider}/{ollama}")`
- [x] 4.4 失败时由 settings_dialog._apply_settings 的 try/except 弹 QMessageBox.warning 提示

## 任务 5：诊断按钮（可选）✅
- [x] 5.1 在 settings_dialog 中 `ollama_model_edit` 旁加 `QPushButton("📋 列出本地模型")`
- [x] 5.2 点击后调用 `subprocess.run(["ollama", "list"])` 解析输出
- [x] 5.3 弹出 `QListWidget` 对话框显示模型列表
- [x] 5.4 双击项填入 `ollama_model_edit`

## 任务 6：单元测试 ✅
- [x] 6.1 创建 `tests/test_config_save_verify.py`（6 个测试）全部通过
  - 正常路径：save → 回读 → 一致 ✅
  - 异常路径：外部篡改 → 抛 `IOError` ✅
  - `Config` 类有 `hermes` 字段 ✅
  - `config.yaml` 不含 `test_model` ✅
  - `default_model == ollama_model` ✅
- [x] 6.2 创建 `tests/test_settings_dialog_validation.py`（10 个测试）全部通过
  - 空字符串被拒绝 ✅
  - `test_model` 占位符被拒绝 ✅
  - `qwen3.5:0.8b` 通过 ✅
  - `settings_saved` 信号 + emit + main_window 链接 ✅
  - 诊断按钮 + `_on_list_ollama_models` + `_show_model_picker` ✅
- [x] 6.3 运行回归测试 69/69 通过（5 个测试文件：test_config_save_verify, test_settings_dialog_validation, test_thinking_visualization, test_thinking_timeout, test_diagnose_cli_gbk）

## 任务 7：端到端验证 ✅
- [x] 7.1 启动后 `get_config().model.ollama_model` = `qwen3.5:0.8b`（不再是 test_model）✅
- [x] 7.2 模拟用户编辑 → save_config → reload → 值仍正确（`qwen3.5:0.8b`）✅
- [x] 7.3 校验逻辑覆盖空值与占位符 ✅
- [x] 7.4 `settings_saved` 信号携带 `ollama_model`, `default_provider`, `default_model` ✅
- [x] 7.5 main_window 状态栏显示 "已保存: provider/ollama" ✅
- [x] 7.6 诊断按钮 + `_on_list_ollama_models` + `_show_model_picker` 完整 ✅
- [x] 7.7 重启后（reload module）`ollama_model` 仍为 `qwen3.5:0.8b`，无回退 ✅
- [x] 7.8 端到端测试 `tests/test_e2e_test_model_revert.py` 7/7 通过

---

## 任务依赖关系

```
任务1 (config.yaml 修正)
   ↓
任务2 (UI 校验) ── 依赖任务1
   ↓
任务3 (写后回读) ── 独立
   ↓
任务4 (状态栏反馈) ── 依赖任务2,3
   ↓
任务5 (诊断按钮) ── 独立
   ↓
任务6 (单元测试) ── 依赖任务1,2,3
   ↓
任务7 (端到端) ── 依赖所有
```

---

## 关键文件清单

| 文件 | 用途 | 任务 |
|------|------|------|
| `e:\超脑\超脑002\config.yaml` | 修正 test_model 写死 | 1 |
| `e:\超脑\超脑002\hyperbrain\ui\settings_dialog.py` | UI 校验 + 状态栏反馈 + 诊断按钮 | 2, 4, 5 |
| `e:\超脑\超脑002\hyperbrain\core\config.py` | save_config 写后回读 | 3 |
| `e:\超脑\超脑002\hyperbrain\ui\main_window.py` | _on_settings_saved 槽函数 | 4 |
| `e:\超脑\超脑002\tests\test_config_save_verify.py` | 新增 | 6 |
| `e:\超脑\超脑002\tests\test_settings_dialog_validation.py` | 新增 | 6 |
