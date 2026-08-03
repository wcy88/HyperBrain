# 修复 max_tokens Pydantic 验证上限

## Why
用户在测试时遇到 Pydantic 验证错误：
```
2026-06-05 15:43:03 | ERROR | __main__:main:343 | Fatal error: 1 validation error for ModelConfig
max_tokens
  Input should be less than or equal to 8192 [type=less_than_equal, input_value=32768, input_type=int]
```

Pydantic 模型 `ModelConfig`（在 `hyperbrain/models/base.py`）的 `max_tokens` 字段有 `Field(le=8192)` 约束（之前 8K 模型时代的硬编码），与我们在 `validate()` 中放宽的 32768 不一致。用户要求把上限改成 **256K**（现代大模型支持）。

## What Changes
- **核心修复1**：[models/base.py:215](file:///e:/超脑/超脑002/hyperbrain/models/base.py#L215) `max_tokens` Pydantic Field 上限从 8192 → 262144（256K）
- **核心修复2**：[core/config.py](file:///e:/超脑/超脑002/hyperbrain/core/config.py) `ModelConfig.validate()` 中 `max_tokens ≤ 32768` → `max_tokens ≤ 262144`，同步一致
- **核心修复3**：[settings_dialog.py:250](file:///e:/超脑/超脑002/hyperbrain/ui/settings_dialog.py#L250) `max_tokens_spin.setRange(1, 32768)` → `setRange(1, 262144)`，与 Pydantic 验证一致
- **核心修复4**：tooltip 文本更新（提到 256K 模型如 Gemini 1.5、GPT-4.1）
- **核心修复5**：[settings_dialog.py:251](file:///e:/超脑/超脑002/hyperbrain/ui/settings_dialog.py#L251) `setSingleStep(512)` → `setSingleStep(1024)`（步长与新范围匹配）
- **核心修复6**：添加单元测试验证 Pydantic 上限
- **BREAKING**：无（仅放宽上限，缺省值不变）

## Impact
- Affected specs: 模型配置验证、设置对话框
- Affected code:
  - `hyperbrain/models/base.py`（Pydantic ModelConfig，line 215，**实际错误源**）
  - `hyperbrain/core/config.py`（dataclass ModelConfig.validate()，line 59-60）
  - `hyperbrain/ui/settings_dialog.py`（spin box 范围 + 步长 + tooltip）
  - 现有 `test_settings_params.py` 需更新

## 根本原因（代码审查）

| 位置 | 当前 | 问题 |
|------|------|------|
| `models/base.py:215` | `max_tokens: int = Field(default=2048, ge=1, le=8192, description="...")` | Pydantic le=8192 是 8K 时代的硬编码 |
| `core/config.py:59` | `if self.max_tokens < 1 or self.max_tokens > 32768` | 与 Pydantic le=8192 冲突（32768 > 8192）|
| `settings_dialog.py:250` | `setRange(1, 32768)` | UI 允许 32768，但 Pydantic 验证会拒 |

**调用链**：
1. 用户在 UI 把 `max_tokens` 设为 32768
2. `settings_dialog._on_settings_changed` 把 32768 写到 `config.model.max_tokens`（dataclass，不报错）
3. `model_manager._load_from_config()` 调用 `ModelConfig(max_tokens=32768, ...)`（Pydantic）
4. Pydantic 验证失败 → `Fatal error: 1 validation error for ModelConfig`

## ADDED Requirements

### Requirement: ModelConfig Pydantic 验证上限 256K
系统SHALL允许 max_tokens 最高 262144（256K），匹配现代大模型。

#### Scenario: 设置 max_tokens=100000
- **WHEN** 用户将 max_tokens 设为 100000
- **THEN** Pydantic 验证通过
- **AND** config 加载成功

#### Scenario: 设置 max_tokens=262144（上限）
- **WHEN** 用户将 max_tokens 设为 262144
- **THEN** Pydantic 验证通过

#### Scenario: 设置 max_tokens=262145（超过上限）
- **WHEN** 用户将 max_tokens 设为 262145
- **THEN** Pydantic 验证失败抛 `ValidationError`
- **AND** validate() 也抛 ConfigValidationError

### Requirement: UI spin box 范围匹配
系统SHALL让 UI 的 max_tokens spin box 范围与 Pydantic 验证一致。

#### Scenario: 打开设置对话框
- **WHEN** 用户打开设置 → 模型标签 → Max Tokens
- **THEN** 范围显示 1-262144
- **AND** 步长 1024（不是 512）
- **AND** tooltip 提到 256K 模型

### Requirement: validate() 与 Pydantic 一致
系统SHALL让 `core/config.py` 的 `ModelConfig.validate()` 的上限与 Pydantic Field 一致。

#### Scenario: validate 检查
- **WHEN** `ModelConfig(max_tokens=200000).validate()` 被调用
- **THEN** 验证通过（不抛异常）

#### Scenario: validate 拒绝超出范围
- **WHEN** `ModelConfig(max_tokens=300000).validate()` 被调用
- **THEN** 抛 `ConfigValidationError("max_tokens 必须在 1-262144 之间")`

## MODIFIED Requirements

### Requirement: ModelConfig Pydantic Field
原 `Field(le=8192)` 太严格。

**修改后**（`models/base.py:215`）：
```python
class ModelConfig(PydanticBaseModel):
    max_tokens: int = Field(default=4096, ge=1, le=262144, description="最大生成token数 (1-256K)")
```

### Requirement: settings_dialog max_tokens_spin
原范围 1-32768 与 Pydantic 冲突。

**修改后**（`settings_dialog.py:249-260`）：
```python
self.max_tokens_spin = QSpinBox()
self.max_tokens_spin.setRange(1, 262144)
self.max_tokens_spin.setSingleStep(1024)
self.max_tokens_spin.setMinimumWidth(100)
self.max_tokens_spin.setToolTip(
    "单次回复最大 token 数\n"
    "GPT-4: 8K, GPT-4-32K: 32K\n"
    "Claude 3: 8K-200K, Gemini 1.5: 1M, GPT-4.1: 1M\n"
    "推荐 4096（兼容大多数模型）\n"
    "上限 256K"
)
self.max_tokens_spin.setValue(4096)
```

### Requirement: core/config.py ModelConfig.validate() 上限
原 `> 32768` 太严格。

**修改后**（`config.py:59-60`）：
```python
if self.max_tokens < 1 or self.max_tokens > 262144:
    raise ConfigValidationError("max_tokens 必须在 1-262144 之间")
```

## REMOVED Requirements
无

## 验证策略

### 单元测试
1. 更新 `test_settings_params.py`：
   - 测试 `max_tokens_spin.maximum() == 262144`
   - 测试 `max_tokens_spin.singleStep() == 1024`
2. 新增 `test_models_pydantic.py`（或扩展 `test_models.py`）：
   - 测试 `ModelConfig(model_name="x", provider=ModelProvider.OPENAI, max_tokens=100000)` 验证通过
   - 测试 `ModelConfig(max_tokens=262144)` 验证通过
   - 测试 `ModelConfig(max_tokens=262145)` 抛 ValidationError
   - 测试 `ConfigModelConfig(max_tokens=200000).validate()` 不抛 ConfigValidationError
   - 测试 `ConfigModelConfig(max_tokens=300000).validate()` 抛 ConfigValidationError

### 端到端测试
1. 启动 GUI → 打开设置 → 设置 Max Tokens=100000 → 点击"应用"
2. 验证无 Pydantic 错误
3. 状态栏显示"设置已应用: ollama/xxx"

### 回归测试
- 原有 28 个测试无破坏
- `test_models.py` 中现有 ModelConfig 用例（默认 2048）继续通过
