# 修复 Ollama Model 字段重启后变回 test_model 问题

## Why
用户反馈：在设置对话框的"模型"页签中，Ollama Model 字段显示 `test_model`（一个无效的占位值）。
重启 HyperBrain 后，该字段仍然显示 `test_model`，即使在 UI 中改成 `qwen3.5:2b` / `qwen3.5:0.8b` 等真实模型名并点击"应用"或"确定"。
导致后续对话找不到可用模型（`ollama list` 中根本没有 `test_model`），实际生效模型也错乱。

## What Changes
- **核心修复1**：把 `config.yaml` 中写死的 `ollama_model: test_model` 改成用户实际可用的模型（`qwen3.5:0.8b`），并加注释说明默认值与回退策略
- **核心修复2**：在 `settings_dialog._update_config()` 中对 `ollama_model` 字段做基本校验（空字符串、纯空白、与 `gemma2:2b` / `test_model` 等占位符相同的拒绝保存）
- **核心修复3**：在 `settings_dialog._apply_settings()` / `_save_and_close()` 中增加保存成功 / 失败的明确日志与状态栏反馈
- **核心修复4**：在 `ConfigManager.save_config()` 中增加写后回读校验：保存后立即读回 yaml，确认 `ollama_model` 字段值与内存一致；不一致时回滚 + 报警
- **核心修复5**：在 `settings_dialog` 中加一个"诊断"按钮（可选），点击后弹出 `diagnose_ollama.py` Step 4 列出的本地模型列表供用户选择
- **核心修复6**：清理 `config.yaml` 中的过时占位符（`test_model` / `null` API key 等），并把 `default_model` 与 `ollama_model` 同步为同一个值
- **BREAKING**：无

## Impact
- Affected specs: 模型配置、设置对话框 UI、config 持久化
- Affected code:
  - `config.yaml`（修正写死的 test_model）
  - `hyperbrain/ui/settings_dialog.py`（添加校验 + 反馈 + 诊断按钮）
  - `hyperbrain/core/config.py`（save_config 增加写后回读）

## 根本原因（代码审查）

### 问题 1：config.yaml 中写死 test_model
- [config.yaml:99](file:///e:/超脑/超脑002/config.yaml#L99)：当前值为 `ollama_model: test_model`
- [config.py:58](file:///e:/超脑/超脑002/hyperbrain/core/config.py#L58)：默认值为 `"gemma2:2b"`
- 实际值 ≠ 默认值 → 必然是某次手动编辑 / 测试残留 / 工具误写入了 `test_model`
- `grep -rn 'test_model' hyperbrain/` 在 `tests/test_models.py` 中只找到 `test_model_config_validation` 等 4 个**方法名**，**没有任何字符串字面量**写入
- 推测来源：用户在 UI 中曾输入 `test_model` 测试，或某次迁移脚本误写
- 后果：每次启动 `load_config` 都从 yaml 读到 `test_model`，覆盖 dataclass 默认值 `gemma2:2b`

### 问题 2：保存路径可能不一致
- [settings_dialog.py:57](file:///e:/超脑/超脑002/hyperbrain/ui/settings_dialog.py#L57)：`self._config = get_config()` 使用全局单例
- [settings_dialog.py:955](file:///e:/超脑/超脑002/hyperbrain/ui/settings_dialog.py#L955)：`save_config(self._config)` 调用全局 `save_config`
- [config.py:480-482](file:///e:/超脑/超脑002/hyperbrain/core/config.py#L480-L482)：自动检测路径 `Path(__file__).resolve().parent.parent.parent / "config.yaml"`
- [config.py:578](file:///e:/超脑/超脑002/hyperbrain/core/config.py#L578)：保存路径 `path or self._config_path or "config.yaml"`
- 路径解析结果：`e:\超脑\超脑002\hyperbrain\core\..\..\config.yaml` = `e:\超脑\超脑002\config.yaml` ✓ 一致
- 但 `_config_path` 在 `load_config` 时被设置（[config.py:491](file:///e:/超脑/超脑002/hyperbrain/core/config.py#L491)），**如果从未调用过 `load_config`，则 `_config_path` 为 None，会回退到 `"config.yaml"`（相对路径）**，可能写到错误位置

### 问题 3：save_config 缺少写后校验
- [config.py:571-591](file:///e:/超脑/超脑002/hyperbrain/core/config.py#L571-L591)：`save_config` 用 `yaml.dump` 写入后无回读校验
- 风险：磁盘写满、权限问题、文件锁等异常可能被吞掉

### 问题 4：UI 无占位符保护
- [settings_dialog.py:711](file:///e:/超脑/超脑002/hyperbrain/ui/settings_dialog.py#L711)：`self.ollama_model_edit.setText(config.model.ollama_model)` 直接加载
- [settings_dialog.py:994](file:///e:/超脑/超脑002/hyperbrain/ui/settings_dialog.py#L994)：`self._config.model.ollama_model = self.ollama_model_edit.text()` 直接赋值
- 用户输入 `test_model` 也能保存

### 问题 5：fallback 同步逻辑不会写入磁盘
- [main_window.py:1262](file:///e:/超脑/超脑002/hyperbrain/ui/main_window.py#L1262)：`self.brain.config.model.ollama_model = model_name` 只改内存
- [model_manager.py:623](file:///e:/超脑/超脑002/hyperbrain/models/model_manager.py#L623)：`cfg.ollama_model = target_model.model_name` 只改内存
- **不会触发 yaml 落盘**（仅在 settings_dialog Apply 时才会保存）
- 这是预期行为，但需要明确：fallback 切换只在本次会话生效，重启后回到 yaml 中的值

## ADDED Requirements

### Requirement: config.yaml 字段值有效性校验
系统在加载配置时 SHALL 校验 `model.ollama_model` 是否为有效模型名（非空、非 `test_model` 等占位符）。

#### Scenario: 加载时检测到占位符值
- **WHEN** `load_config` 读到 `ollama_model: test_model`
- **THEN** 1) logger.warning 打印警告；2) 自动回退到默认 `gemma2:2b`；3) 不崩溃

#### Scenario: 加载时检测到空值
- **WHEN** `ollama_model` 为空字符串
- **THEN** 1) 替换为 `gemma2:2b`；2) 警告日志

### Requirement: 设置对话框保存时校验
系统SHALL在用户点击"应用"或"确定"时校验 Ollama Model 字段，拒绝占位符值。

#### Scenario: 输入 test_model 占位符
- **WHEN** 用户在 Model 字段输入 `test_model` 并点击"应用"
- **THEN** 1) 弹窗提示"无效模型名，请填写 ollama list 中存在的模型"；2) 不保存

#### Scenario: 输入空白
- **WHEN** 用户在 Model 字段只输入空格
- **THEN** 1) 弹窗提示；2) 不保存；3) 恢复原值

### Requirement: save_config 写后回读校验
系统SHALL在 `save_config` 写入 yaml 后立即回读关键字段，验证持久化成功。

#### Scenario: 写后回读成功
- **WHEN** `save_config` 写入 `ollama_model=qwen3.5:0.8b`
- **THEN** 回读 yaml，验证 `ollama_model == "qwen3.5:0.8b"`，一致则 logger.info "Config saved OK"

#### Scenario: 写后回读失败
- **WHEN** 回读 yaml 时字段值不一致（磁盘错误、权限问题）
- **THEN** 1) logger.error 打印差异；2) 弹窗提示用户"配置保存失败，请检查磁盘权限"

### Requirement: 状态栏保存反馈
系统SHALL在保存成功后立即在状态栏显示反馈，告知用户保存的字段值。

#### Scenario: 保存成功
- **WHEN** 点击"应用"后 `save_config` 成功
- **THEN** 状态栏显示 "已保存: ollama=qwen3.5:0.8b" 持续 3 秒

#### Scenario: 保存失败
- **WHEN** `save_config` 抛异常或回读失败
- **THEN** 状态栏显示 "保存失败: <错误信息>" 持续 5 秒（红色）

### Requirement: 诊断按钮（可选增强）
设置对话框 SHALL在 Ollama Model 字段旁加一个"📋 列出本地模型"按钮，点击后通过 `diagnose_ollama.py` 列出本地已安装的 ollama 模型。

#### Scenario: 点击诊断按钮
- **WHEN** 用户点击"列出本地模型"
- **THEN** 弹出列表对话框显示 `ollama list` 输出，用户可双击选中填入 Model 字段

## MODIFIED Requirements

### Requirement: config.yaml 默认值
原值 `ollama_model: test_model` 是无效占位符。

**修改后**：
```yaml
model:
  ollama_model: qwen3.5:0.8b  # 默认使用 qwen3.5:0.8b（实际可用模型）
  default_model: qwen3.5:0.8b  # 与 ollama_model 保持一致
```

### Requirement: settings_dialog._update_config
原方法直接赋值不校验。

**修改后**：
```python
# 在 _update_config 中添加校验
ollama_model_value = self.ollama_model_edit.text().strip()
if not ollama_model_value:
    raise ValueError("Ollama Model 不能为空")
if ollama_model_value.lower() in ("test_model", "test", "placeholder", "default"):
    raise ValueError(f"无效的模型名: {ollama_model_value!r}，请填写 ollama list 中实际存在的模型")
self._config.model.ollama_model = ollama_model_value
```

### Requirement: ConfigManager.save_config
原方法无写后校验。

**修改后**（在写入后追加）：
```python
# 写后回读校验
if path_obj.suffix in ['.yaml', '.yml']:
    with open(path_obj, 'r', encoding='utf-8') as f:
        readback = yaml.safe_load(f)
    saved_model = readback.get('model', {}).get('ollama_model')
    expected_model = config.model.ollama_model
    if saved_model != expected_model:
        logger.error(f"Config save mismatch! saved={saved_model!r} expected={expected_model!r}")
        raise IOError(f"Config save verification failed for ollama_model")
logger.info(f"Configuration saved and verified: ollama_model={expected_model}")
```

## REMOVED Requirements
无

## 验证策略

### 单元测试
1. `test_config_save_verify.py`（新增）：
   - 测试 `save_config` 写入后回读一致
   - 测试 `save_config` 写入字段被篡改时抛 `IOError`
2. `test_settings_dialog_validation.py`（新增）：
   - 测试空字符串被拒绝
   - 测试 `test_model` 占位符被拒绝
   - 测试正常模型名通过

### 端到端测试
1. 启动 GUI → 设置 → 改 Ollama Model 为 `qwen3.5:0.8b` → 点击"应用" → 关闭
2. 检查 `config.yaml` 中 `ollama_model: qwen3.5:0.8b`
3. 重启 GUI → 设置 → 看到 Model = `qwen3.5:0.8b`（不再是 test_model）
4. 发送消息 → 验证用 qwen3.5:0.8b 响应

### 回归测试
- 原有所有测试（85+ test_thinking_visualization、test_config、test_models 等）全部通过
