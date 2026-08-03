# 修复模型切换和短期记忆问题

## Why
用户反馈两个新问题：
1. **模型切换无效**：在设置对话框里把 Ollama 模型改为 `minimax-m3:cloud`，点击"应用"或"确定"后，模型并没有真正切换（下次对话还是用旧模型）
2. **短期记忆一直是 0**：记忆面板的"短期记忆（工作记忆）"显示 `0/7`，即使在多次对话后也不变化

## What Changes
- **核心修复1**：在 `main_window._show_settings()` 中连接 `dialog.settings_changed` 信号到处理器
- **核心修复2**：实现 `_on_settings_changed` 处理器，从设置字典中读取新配置，调用 `brain.model_manager.register_model(...)` 重新注册（先 unregister）
- **核心修复3**：在 `Brain.process()` 中添加工作记忆写入逻辑（`self.memory.working_memory.add(...)`）
- **核心修复4**：在 `Brain.process_stream()`（如存在）同样添加工作记忆写入
- **核心修复5**：修复 `memory_viz` 短期记忆字段映射（`working_memory.get_stats()` 返回 `current_chunks` 而非 `current_size`）
- **核心修复6**：在 `memory_viz.update_short_term_stats` 中显示更准确的数据（条目数 = current_chunks）
- **核心修复7**：工作记忆添加时使用 `add_chunk` 或 `add` 方法，确保 `working_memory` 容量 (7) 正确
- **核心修复8**：添加 `Brain.working_memory` 属性访问器（如缺失）
- **BREAKING**：无

## Impact
- Affected specs: 模型配置、工作记忆、短期记忆显示
- Affected code:
  - `hyperbrain/ui/main_window.py`（连接 settings_changed 信号）
  - `hyperbrain/core/brain.py`（在 process 中调用 working_memory.add）
  - `hyperbrain/ui/memory_viz.py`（修复字段映射）
  - `hyperbrain/layers/memory/memory_manager.py`（可能需添加 get_working_memory 辅助方法）
  - `hyperbrain/models/model_manager.py`（已有 register_model/unregister_model，无需改）

## 根本原因（代码审查）

### 问题 1：模型切换无效
- [main_window.py:429-430](file:///e:/超脑/超脑002/hyperbrain/ui/main_window.py#L429-L430)：
  ```python
  dialog = SettingsDialog(self)
  dialog.exec()
  ```
  **未连接 `settings_changed` 信号**！`_apply_settings` 会 emit 信号，但没有任何 receiver。
- [settings_dialog.py:768](file:///e:/超脑/超脑002/hyperbrain/ui/settings_dialog.py#L768)：信号 emit 了但被丢弃
- 后果：`config.model.ollama_model` 被持久化到磁盘，但 `ModelManager`（运行时实例）继续用旧模型

### 问题 2：短期记忆一直是 0
- [brain.py:845](file:///e:/超脑/超脑002/hyperbrain/core/brain.py#L845)：`process()` 方法直接调用 `self.memory.store(...)` 存到长期记忆，**不经过 `working_memory`**
- [brain.py:995-999](file:///e:/超脑/超脑002/hyperbrain/core/brain.py#L995-L999)：`process_stream()` 同样问题
- 后果：`working_memory.chunks` 始终为空
- [memory_viz.py:644-648](file:///e:/超脑/超脑002/hyperbrain/ui/memory_viz.py#L644-L648)：读取 `working_memory` 的 `current_size` 字段，但 `WorkingMemory.get_stats()` 返回的是 `current_chunks`（注意：实际是 `current_size` = sum of chunk.size），但因为 working_memory 为空，所以两个都是 0

## ADDED Requirements

### Requirement: 模型切换生效
系统SHALL在用户点击"应用"或"确定"后，立即生效新的模型配置。

#### Scenario: 切换 Ollama 模型
- **WHEN** 用户在设置对话框中修改 Ollama 模型为 `minimax-m3:cloud` 并点击"应用"
- **THEN** 1) `config.model.ollama_model` 被更新；2) `ModelManager` 重新注册模型；3) 下次 `chat()` 调用使用新模型
- **AND** 状态栏或日志显示 "模型已切换为 minimax-m3:cloud"

#### Scenario: 切换默认 Provider
- **WHEN** 用户从 `ollama` 切换到 `openai`
- **THEN** 1) `config.model.default_provider` 被更新；2) 对应的 provider 模型被注册到 ModelManager；3) 下次调用走 OpenAI

#### Scenario: 切换失败回滚
- **WHEN** 新模型初始化失败（连接超时、API key 无效等）
- **THEN** 1) 旧模型继续工作；2) 错误信息提示给用户；3) 不影响后续对话

### Requirement: 短期记忆自动填充
系统SHALL在用户发送消息时，自动将消息和响应存入工作记忆。

#### Scenario: 用户发送消息
- **WHEN** `Brain.process(user_input, response)` 被调用
- **THEN** 1) `self.memory.working_memory.add(content=user_input, ...)` 被调用
- **AND** 2) `self.memory.working_memory.add(content=response_content, ...)` 被调用
- **AND** 3) 记忆面板的"短期记忆"显示条目数 > 0

#### Scenario: 工作记忆容量限制
- **WHEN** 工作记忆达到 7 个条目
- **THEN** 最低优先级的旧条目被自动淘汰
- **AND** "短期记忆"显示 `7/7` 容量 100%

#### Scenario: 流式响应场景
- **WHEN** `Brain.process_stream(user_input, stream_chunks)` 被调用
- **THEN** 完成后同样调用 `working_memory.add`

### Requirement: 短期记忆字段正确显示
系统SHALL正确显示工作记忆的当前条目数和容量。

#### Scenario: 显示短期记忆统计
- **WHEN** 记忆面板概览页刷新
- **THEN** 短期记忆组显示 `current_chunks / capacity`（如 `3/7`）
- **AND** 容量使用进度条正确反映 `current_chunks / capacity`

### Requirement: 信号连接
系统SHALL在主窗口中正确连接设置对话框的 `settings_changed` 信号。

#### Scenario: 打开设置对话框
- **WHEN** 用户从"工具"菜单打开"设置"
- **THEN** `SettingsDialog.settings_changed` 信号被连接到 `_on_settings_changed`
- **AND** 关闭对话框后设置立即生效

## MODIFIED Requirements

### Requirement: main_window._show_settings
原方法只创建对话框并显示，不连接信号。

**修改后**：
```python
def _show_settings(self):
    """显示设置对话框"""
    dialog = SettingsDialog(self)
    dialog.settings_changed.connect(self._on_settings_changed)
    dialog.exec()

def _on_settings_changed(self, settings: dict):
    """
    处理设置变更
    重新注册模型到 ModelManager
    """
    try:
        if not self.brain or not hasattr(self.brain, 'model_manager'):
            return
        mm = self.brain.model_manager
        config = get_config().model

        # 1. 重新加载所有模型
        if config.openai_api_key:
            try:
                mm.unregister_model("openai_default")
            except Exception:
                pass
            mm.register_model(
                name="openai_default",
                config=ModelConfig(...)
            )
        # ... 同样的逻辑处理 anthropic/google/ollama

        logger.info(f"Models reloaded, current default: {config.default_provider}")
        # 可选：在状态栏显示
        if hasattr(self, 'status_label'):
            self.status_label.setText(f"模型已更新: {config.default_provider}/{config.ollama_model}")
    except Exception as e:
        logger.error(f"Failed to apply settings: {e}")
        if hasattr(self, 'status_label'):
            self.status_label.setText(f"设置应用失败: {e}")
```

### Requirement: Brain.process 工作记忆写入
原 `process()` 方法不调用 `working_memory.add`。

**修改后**（在 process 的合适位置）：
```python
# 在 store 之前添加工作记忆
if hasattr(self.memory, 'working_memory'):
    try:
        self.memory.working_memory.add(
            content=f"用户: {user_input[:200]}",
            chunk_type="user_input",
            priority=0.7,
            source="conversation"
        )
        self.memory.working_memory.add(
            content=f"AI: {response_content[:200]}",
            chunk_type="ai_response",
            priority=0.6,
            source="conversation"
        )
    except Exception as e:
        logger.debug(f"working_memory add failed: {e}")

# 保留原 store 到长期记忆
self.memory.store(...)
```

### Requirement: memory_viz.update_short_term_stats
原方法接收 `current_size` 字段，但 WorkingMemory.get_stats() 返回 `current_chunks`。

**修改后**：
```python
# 在 refresh_data 中
stm_stats = stats.get("working_memory", {})
current_chunks = stm_stats.get("current_chunks", 0)  # 优先 current_chunks
capacity = stm_stats.get("capacity", 7)
# 回退：current_size 字段（如 ShortTermMemory 用）
if current_chunks == 0:
    current_chunks = stm_stats.get("current_size", 0)
self.update_short_term_stats(current_chunks, capacity)
```

## REMOVED Requirements
无

## 验证策略

### 单元测试
1. `test_model_switch.py`：测试 `SettingsDialog` + `MainWindow` 集成
   - mock `SettingsDialog.settings_changed` 信号
   - 验证 `_on_settings_changed` 收到信号
   - 验证 `model_manager.register_model` 被调用
2. `test_working_memory.py`：测试 `Brain.process` 调用 `working_memory.add`
   - mock `memory_manager.working_memory.add`
   - 验证 process 后 working_memory 有内容

### 端到端测试
1. 启动 GUI → 设置 → 切换 Ollama 模型 → 点击"应用" → 发送消息 → 验证用的是新模型
2. 启动 GUI → 发送 3 条消息 → 切换到记忆面板 → 概览页 → 短期记忆显示 `3+/7`（非 0）

### 回归测试
- 原有 7 个 test_all_features.py 测试 + 8 个 test_ui_refresh.py 测试全部通过
