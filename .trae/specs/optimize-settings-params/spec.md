# 优化设置对话框参数范围和默认值

## Why
用户反馈设置对话框中两处参数设置区域（模型标签的"General Parameters" + 系统标签的"认知层/执行层/学习层"）的参数范围和默认值不合理：
- **Max Tokens 范围过小**（1-8192）：现代模型（GPT-4-32K、Claude 3 200K、DeepSeek 64K）支持更大的输出
- **Max Tokens 缺省值不一致**：config.py 默认为 2000，UI 显示 8192
- **最大思维链长度 50 过大**：实际推理很少需要 50 步，造成 UI 浪费
- **学习率 singleStep=0.0001**：调节太精细，操作不便
- **缺少 tooltip 帮助说明**：用户不知道每个参数的合理范围
- **API Key 缺省占位符**：OpenAI 显示 "sk-..." 让用户误以为已配置

## What Changes
- **核心优化1**：[settings_dialog.py:243](file:///e:/超脑/超脑002/hyperbrain/ui/settings_dialog.py#L243) `max_tokens_spin` 范围从 `1-8192` 改为 `1-32768`，缺省值 4096（匹配现代模型）
- **核心优化2**：[settings_dialog.py:275](file:///e:/超脑/超脑002/hyperbrain/ui/settings_dialog.py#L275) `max_chain_spin` 范围从 `1-50` 改为 `1-20`，缺省值 5
- **核心优化3**：[settings_dialog.py:311-314](file:///e:/超脑/超脑002/hyperbrain/ui/settings_dialog.py#L311-L314) `learning_rate_spin` singleStep 从 `0.0001` 改为 `0.001`
- **核心优化4**：为所有 spin box 添加 `setToolTip()`，包含合理范围建议
- **核心优化5**：清除 API Key 占位符 "sk-..." 误导，改为 "（可选，未填则不启用）"
- **核心优化6**：添加"参数已应用"反馈（状态栏/短暂提示）
- **核心优化7**：[config.py:37](file:///e:/超脑/超脑002/hyperbrain/core/config.py#L37) `max_tokens` 缺省值从 2000 改为 4096（与 UI 一致）
- **核心优化8**：[config.py:93](file:///e:/超脑/超脑002/hyperbrain/core/config.py#L93) `max_chain_length` 范围验证改为 1-20
- **核心优化9**：添加"重置为推荐值"快捷按钮（仅针对这 8 个关键参数）
- **核心优化10**：当用户输入超出推荐范围时显示警告（不阻止保存）
- **BREAKING**：无（仅范围/缺省值变化）

## Impact
- Affected specs: 设置对话框 UI、配置默认值
- Affected code:
  - `hyperbrain/ui/settings_dialog.py`（spin box 范围/缺省/tooltip）
  - `hyperbrain/core/config.py`（缺省值与验证范围）
  - `hyperbrain/ui/main_window.py`（无变化）

## 根本原因（代码审查）

| 文件 | 行 | 当前值 | 问题 |
|------|---|--------|------|
| `settings_dialog.py` | 243 | `max_tokens_spin.setRange(1, 8192)` | 上限 8192 不支持 GPT-4-32K（32K）、Claude 3（200K）|
| `settings_dialog.py` | 244 | `setSingleStep(128)` | 步长 128 OK |
| `settings_dialog.py` | 275 | `max_chain_spin.setRange(1, 50)` | 上限 50 远超实际需求（典型 5-10 步）|
| `settings_dialog.py` | 313 | `setSingleStep(0.0001)` | 步长过小，调整 0.001→0.0011 需要点 1 次 |
| `settings_dialog.py` | 235-252 | 无 tooltip | 用户不知道参数的合理范围 |
| `settings_dialog.py` | (占位符) | `sk-...` | 容易让用户误以为已配置 |
| `config.py` | 37 | `max_tokens: int = 2000` | 与 UI 显示的 8192 不一致（可能是因为 setRange 触发了 setValue）|
| `config.py` | 93 | `max_chain_length: int = 5` | OK，但缺少范围验证 |
| `config.py` | 99-104 | 范围验证 | 缺少 `max_chain_length` 上限验证 |

## ADDED Requirements

### Requirement: 参数范围合理化
系统SHALL在设置对话框中提供与现代 AI 模型匹配的合理参数范围。

#### Scenario: Max Tokens 范围扩展
- **WHEN** 用户查看 Max Tokens 字段
- **THEN** 范围为 `1-32768`，step=512，缺省 4096
- **AND** tooltip 显示 "GPT-4: 8K, GPT-4-32K: 32K, Claude 3: 8K-200K, DeepSeek: 8K"

#### Scenario: 最大思维链长度范围优化
- **WHEN** 用户查看最大思维链长度字段
- **THEN** 范围为 `1-20`，step=1，缺省 5
- **AND** tooltip 显示 "典型推理 3-10 步，>15 步可能显著变慢"

#### Scenario: 学习率步长优化
- **WHEN** 用户点击学习率步进按钮
- **THEN** 每次调整 0.001（从 0.001 到 0.002）
- **AND** tooltip 显示 "常用范围 0.0001-0.01，>0.1 会导致不稳定"

### Requirement: 配置缺省值与 UI 一致
系统SHALL保证 config.py 的缺省值与 UI 显示的初始值一致。

#### Scenario: 启动时 Max Tokens 显示
- **WHEN** 用户打开设置对话框（第一次）
- **THEN** Max Tokens 显示 4096（与 config.py 缺省一致）

#### Scenario: 启动时最大思维链显示
- **WHEN** 用户打开设置对话框（第一次）
- **THEN** 最大思维链显示 5（与 config.py 缺省一致）

### Requirement: 参数帮助提示
系统SHALL为每个关键参数提供 tooltip 说明。

#### Scenario: 鼠标悬停参数
- **WHEN** 用户鼠标悬停在 Temperature 字段上
- **THEN** 显示 tooltip "控制输出随机性，0=确定性，2=最大创造性，缺省 0.7 平衡"

#### Scenario: 鼠标悬停超时字段
- **WHEN** 用户鼠标悬停在 Timeout 字段上
- **THEN** 显示 tooltip "API 调用超时（秒），慢速模型建议 >60s"

### Requirement: API Key 占位符清晰
系统SHALL使用不会误导的占位符。

#### Scenario: OpenAI API Key 字段
- **WHEN** 用户查看 OpenAI API Key 字段
- **THEN** 占位符为 "（可选，未填则不启用）"，不是 "sk-..."

### Requirement: 重置为推荐值
系统SHALL提供"重置为推荐值"快捷按钮。

#### Scenario: 点击重置按钮
- **WHEN** 用户点击"重置为推荐值"
- **THEN** 8 个关键参数恢复推荐值：Temperature=0.7, Max Tokens=4096, Timeout=90, 推理深度=3, 最大思维链=5, 置信度阈值=0.7, 最大执行时间=30, 重试次数=3, 学习率=0.001

### Requirement: 范围超出警告
系统SHALL在用户输入超出推荐范围时显示警告。

#### Scenario: Max Tokens 设置为 30000
- **WHEN** 用户将 Max Tokens 设为 30000
- **THEN** 字段下方显示警告 "推荐范围 1-8192（GPT-4 标准），更大需要支持 32K+ 的模型"

#### Scenario: 警告不阻止保存
- **WHEN** 用户点击"应用"即使有警告
- **THEN** 值仍被保存（只警告，不阻止）

### Requirement: 参数应用反馈
系统SHALL在用户点击"应用"后显示反馈。

#### Scenario: 点击应用按钮
- **WHEN** 用户点击"应用"
- **THEN** 状态栏显示 "设置已应用" 持续 3 秒

## MODIFIED Requirements

### Requirement: settings_dialog General Parameters
原范围过小，缺省值不一致。

**修改后**：
```python
# Temperature: 0-2, step=0.1, default=0.7
self.temperature_spin = QDoubleSpinBox()
self.temperature_spin.setRange(0.0, 2.0)
self.temperature_spin.setSingleStep(0.1)
self.temperature_spin.setDecimals(1)
self.temperature_spin.setToolTip("控制输出随机性\n0=确定性，2=最大创造性\n推荐 0.7（平衡）")

# Max Tokens: 1-32768, step=512, default=4096
self.max_tokens_spin = QSpinBox()
self.max_tokens_spin.setRange(1, 32768)
self.max_tokens_spin.setSingleStep(512)
self.max_tokens_spin.setValue(4096)  # 显式设置缺省
self.max_tokens_spin.setToolTip("单次回复最大 token 数\nGPT-4: 8K, GPT-4-32K: 32K\nClaude 3: 8K-200K")

# Timeout: 1-300, step=5, default=90
self.timeout_spin = QSpinBox()
self.timeout_spin.setRange(1, 300)
self.timeout_spin.setSuffix(" sec")
self.timeout_spin.setSingleStep(5)
self.timeout_spin.setValue(90)  # 显式设置缺省
self.timeout_spin.setToolTip("API 调用超时\n慢速模型建议 >60s")
```

### Requirement: settings_dialog 认知层
原最大思维链范围过大。

**修改后**：
```python
# 推理深度: 1-10, default=3
self.reasoning_depth_spin = QSpinBox()
self.reasoning_depth_spin.setRange(1, 10)
self.reasoning_depth_spin.setValue(3)
self.reasoning_depth_spin.setToolTip("推理层数\n1=直接回答，10=多步推理\n推荐 3-5")

# 最大思维链长度: 1-20, step=1, default=5
self.max_chain_spin = QSpinBox()
self.max_chain_spin.setRange(1, 20)
self.max_chain_spin.setValue(5)
self.max_chain_spin.setToolTip("思维链最大步骤数\n典型 3-10 步，>15 步会显著变慢")

# 置信度阈值: 0-1, step=0.05, default=0.7
self.confidence_threshold_spin = QDoubleSpinBox()
self.confidence_threshold_spin.setRange(0.0, 1.0)
self.confidence_threshold_spin.setSingleStep(0.05)
self.confidence_threshold_spin.setDecimals(2)
self.confidence_threshold_spin.setValue(0.7)
self.confidence_threshold_spin.setToolTip("低于此置信度的回答会被标记为不确定\n推荐 0.6-0.8")
```

### Requirement: settings_dialog 执行层
保持不变，但添加 tooltip。

**修改后**：
```python
# 最大执行时间: 1-300, step=5, default=30
self.max_exec_time_spin = QSpinBox()
self.max_exec_time_spin.setRange(1, 300)
self.max_exec_time_spin.setSuffix(" 秒")
self.max_exec_time_spin.setSingleStep(5)
self.max_exec_time_spin.setValue(30)
self.max_exec_time_spin.setToolTip("任务最大执行时间\n超过则中断（防止死循环）")

# 重试次数: 0-10, step=1, default=3
self.retry_spin = QSpinBox()
self.retry_spin.setRange(0, 10)
self.retry_spin.setValue(3)
self.retry_spin.setToolTip("API 失败重试次数\n0=不重试，3=重试 3 次")

# 启用并行执行
self.parallel_check = QCheckBox("启用并行执行")
self.parallel_check.setToolTip("同时执行多个独立任务（提升速度）")
```

### Requirement: settings_dialog 学习层
学习率步长优化。

**修改后**：
```python
# 学习率: 0.0001-0.1, step=0.001, default=0.001
self.learning_rate_spin = QDoubleSpinBox()
self.learning_rate_spin.setRange(0.0001, 0.1)
self.learning_rate_spin.setSingleStep(0.001)  # 从 0.0001 改为 0.001
self.learning_rate_spin.setDecimals(4)
self.learning_rate_spin.setValue(0.001)
self.learning_rate_spin.setToolTip("学习率\n常用 0.0001-0.01\n>0.1 会导致不稳定")

# 启用在线学习
self.online_learning_check = QCheckBox("启用在线学习")
self.online_learning_check.setToolTip("实时从对话中学习（推荐开启）")
```

### Requirement: API Key 占位符
原 `sk-...` 误导用户。

**修改后**：
```python
self.openai_key_edit = QLineEdit()
self.openai_key_edit.setPlaceholderText("（可选，未填则不启用）")
self.openai_key_edit.setEchoMode(QLineEdit.EchoMode.Password)

# 同样修改 anthropic_key_edit 和 google_key_edit
self.anthropic_key_edit.setPlaceholderText("（可选，未填则不启用）")
self.google_key_edit.setPlaceholderText("（可选，未填则不启用）")
```

### Requirement: config.py 缺省值与验证
原缺省值与 UI 不一致，缺少范围验证。

**修改后**：
```python
@dataclass
class ModelConfig:
    temperature: float = 0.7  # OK
    max_tokens: int = 4096  # 从 2000 改为 4096
    timeout: float = 90.0
    retry_attempts: int = 3
    
    def validate(self):
        if not 0 <= self.temperature <= 2:
            raise ConfigValidationError("temperature 必须在 0-2 之间")
        if self.max_tokens < 1 or self.max_tokens > 32768:
            raise ConfigValidationError("max_tokens 必须在 1-32768 之间")
        if self.timeout < 1 or self.timeout > 300:
            raise ConfigValidationError("timeout 必须在 1-300 之间")

@dataclass
class CognitiveConfig:
    reasoning_depth: int = 3
    max_thinking_time: int = 30
    enable_meta_cognition: bool = True
    max_chain_length: int = 5  # OK
    confidence_threshold: float = 0.7  # OK
    enable_reflection: bool = True
    
    def validate(self):
        if self.reasoning_depth < 1 or self.reasoning_depth > 10:
            raise ConfigValidationError("reasoning_depth 必须在 1-10 之间")
        if self.max_chain_length < 1 or self.max_chain_length > 20:
            raise ConfigValidationError("max_chain_length 必须在 1-20 之间")
        if not 0 <= self.confidence_threshold <= 1:
            raise ConfigValidationError("confidence_threshold 必须在 0-1 之间")
```

## REMOVED Requirements
无

## 验证策略

### 单元测试
1. `test_settings_params.py`：
   - 测试 Max Tokens 范围是 1-32768
   - 测试 最大思维链长度 范围是 1-20
   - 测试 学习率 step 是 0.001
   - 测试 所有参数都有 tooltip
   - 测试 config.py 缺省值与 UI 一致

### 端到端测试
1. 启动 GUI → 打开设置 → 验证：
   - 模型标签的 Max Tokens 显示 4096（不是 8192）
   - 系统标签的最大思维链长度范围 1-20
   - 鼠标悬停各字段显示 tooltip
   - 点击"恢复默认"恢复推荐值
   - 点击"应用"状态栏显示"设置已应用"

### 回归测试
- 原有 20 个测试无破坏
