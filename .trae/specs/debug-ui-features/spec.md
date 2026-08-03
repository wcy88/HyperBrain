# HyperBrain UI 功能全面调试规格说明书

## Why
用户反馈："目前只能会话，其它所有功能都不正常，全面测试一下，看看问题出在哪里了"。

通过截图分析确认，记忆面板、认知面板、监控面板的多个子标签页数据为空。最新截图显示：
- **认知面板**：能力/情感/任务/日志/思维链/推理过程/决策过程/认知状态 全部空
- **记忆面板**：列表/关联图/统计 标签页都是空的（只概览有部分数据）
- **监控面板**：能力/情感/任务 标签页是空的

根因是 **UI 组件与 Brain 数据源之间缺乏完整的刷新和绑定机制**——多个 viz 组件没有定时器，主窗口的 status_timer 也只更新状态栏文字而不刷新任何面板。

## What Changes
- **核心修复1**：扩展 `memory_viz.py::refresh_data()`，调用 `update_stats`、`update_graph`、`set_memories`，使统计页/列表页/关联图页都能显示数据
- **核心修复2**：在 `cognition_viz.py` 中新增 `refresh_data()` 方法，从 Brain 读取认知能力、情感状态、任务列表、思维链、决策、认知状态
- **核心修复3**：在 `cognition_viz.py` 中添加 `refresh_timer`（QTimer 5秒间隔）实现自动刷新
- **核心修复4**：在 `main_window.py` 中创建统一的中央刷新器，扩展 `_update_status` 调用所有 viz 组件的 refresh_data
- **核心修复5**：在 `Brain` 类中新增 `get_dashboard_data()` 方法，统一返回 UI 所需的所有快照数据
- **核心修复6**：在 `system_monitor.py` 中新增 `refresh_data(brain)` 方法，桥接 dashboard_data 与现有 update_capabilities/update_emotion/update_tasks（处理值范围 0-1 vs 0-100 的不一致）
- **核心修复7**：标签页切换时立即触发 refresh_data（即时显示）
- **验证**：启动 GUI 验证所有面板数据正常刷新

## Impact
- Affected specs: UI 刷新机制、监控面板、记忆面板、认知面板
- Affected code:
  - `hyperbrain/core/brain.py`（已添加 `get_dashboard_data`）✅
  - `hyperbrain/ui/memory_viz.py`（已扩展 `refresh_data`）✅
  - `hyperbrain/ui/cognition_viz.py`（需新增 `refresh_data` + timer）
  - `hyperbrain/ui/system_monitor.py`（需新增 `refresh_data`，修复值范围）
  - `hyperbrain/ui/main_window.py`（需扩展中央刷新器）
- 涉及系统：QTimer 定时器、数据流绑定、UI 自动刷新、值范围标准化

---

## 根本原因（代码审查）

1. `memory_viz.py::refresh_data()` 原只更新概览页（短期、长期、类型），**没有调用** `update_stats`、`update_graph`、`set_memories` → ✅ 已修复
2. `cognition_viz.py` **完全没有 refresh 机制** — 没有任何定时器或方法把 brain 数据流入面板
3. `main_window.py::status_timer` 只更新状态栏文字（"系统运行中..."），不刷新任何 viz
4. `system_monitor.py` 虽有 `update_capabilities`、`update_emotion`、`update_tasks` 方法，但**从未被调用**；且 `update_capabilities` 期望 0-1 浮点（`int(x * 100)`），与 `get_dashboard_data` 返回 0-100 范围不一致
5. Brain 之前没有暴露统一的数据访问接口，UI 组件不知道从哪里取数据 → ✅ 已添加 `get_dashboard_data()`

---

## ADDED Requirements

### Requirement: 记忆面板完整刷新
系统SHALL在记忆面板的所有子标签页（概览/列表/关联图/统计）显示正确的记忆数据。

#### Scenario: 概览页刷新
- **WHEN** `refresh_data()` 被调用
- **THEN** 短期记忆容量、长期记忆总数、索引状态、记忆类型分布正确更新

#### Scenario: 列表页刷新
- **WHEN** `refresh_data()` 被调用
- **THEN** 记忆列表显示最近 100 条长期记忆（id、类型、重要性、时间、状态）

#### Scenario: 关联图刷新
- **WHEN** `refresh_data()` 被调用
- **THEN** 关联图显示记忆节点（最多 50 个）和它们之间的关联边

#### Scenario: 统计页刷新
- **WHEN** `refresh_data()` 被调用
- **THEN** 总记忆数、平均重要性、检索次数、存储效率、访问频率 Top 10、时间分布正确显示

### Requirement: 认知面板完整刷新
系统SHALL在认知面板的所有 4 个子标签页显示正确的认知过程数据。

#### Scenario: 思维链页刷新
- **WHEN** `refresh_data()` 被调用
- **THEN** 步骤数 > 0；QTreeWidget 显示最近推理步骤；CognitionGraphView 渲染节点

#### Scenario: 推理过程页刷新
- **WHEN** `refresh_data()` 被调用
- **THEN** QTreeWidget 显示步骤列表（步骤/类型/内容/置信度/状态）

#### Scenario: 决策过程页刷新
- **WHEN** `refresh_data()` 被调用
- **THEN** 当前决策内容/置信度/备选方案数正确显示；决策历史表显示最近决策

#### Scenario: 认知状态页刷新
- **WHEN** `refresh_data()` 被调用
- **THEN** 认知负载进度条/注意力焦点/处理深度/3 个能力进度条/元认知状态正确显示

### Requirement: 监控面板完整刷新
系统SHALL在监控面板的所有子标签页（概览/资源/能力/情感/任务/日志）显示正确数据。

#### Scenario: 能力标签页刷新
- **WHEN** `system_monitor.refresh_data(brain)` 被调用
- **THEN** 9 个能力进度条（推理/学习/记忆/注意力/规划/问题解决/创造力/同理心/沟通）显示非零值

#### Scenario: 情感标签页刷新
- **WHEN** `system_monitor.refresh_data(brain)` 被调用
- **THEN** 当前情感/强度/效价/愉悦度/唤醒度/支配度 正确显示；情感历史表显示最近情感

#### Scenario: 任务标签页刷新
- **WHEN** `system_monitor.refresh_data(brain)` 被调用
- **THEN** 活动/完成/失败任务数正确，任务列表显示当前任务

### Requirement: 统一刷新机制
系统SHALL在主窗口中通过单一 QTimer 协调所有 viz 组件的刷新。

#### Scenario: 启动 GUI
- **WHEN** GUI 启动后
- **THEN** 所有 viz 组件每 5 秒自动刷新一次

#### Scenario: 切换标签页
- **WHEN** 用户切换到记忆/认知/监控标签页
- **THEN** 立即触发该标签页的 refresh_data（即时显示）

### Requirement: Brain 数据访问接口
系统SHALL在 Brain 类中暴露统一的数据访问接口 `get_dashboard_data()`。

#### Scenario: 调用 get_dashboard_data
- **WHEN** UI 组件调用 `brain.get_dashboard_data()`
- **THEN** 返回包含记忆统计、能力水平（0-100）、情感状态、任务列表、思维链的字典

#### Scenario: 值范围标准化
- **WHEN** `get_dashboard_data` 返回 abilities 字典
- **THEN** 所有值在 0-100 范围内（与 UI 进度条一致）

### Requirement: 安全降级
系统SHALL在 brain 实例不可用时安全降级。

#### Scenario: brain 为 None
- **WHEN** viz 组件 refresh 时 `self.brain` 为 None
- **THEN** 使用安全的默认空数据，**不抛异常**（避免 UI 崩溃）

---

## MODIFIED Requirements

### Requirement: memory_viz.refresh_data
原 `refresh_data` 仅更新概览页，需扩展为更新所有标签页。 ✅ 已修改

**修改后**:
```python
def refresh_data(self):
    # 概览
    self.update_short_term_stats(...)
    self.update_long_term_stats(...)
    self.update_memory_types(...)
    # 列表
    memories = self.brain.memory.long_term_memory.get_all_memories(limit=100)
    self.set_memories([m.to_dict() for m in memories])
    # 关联图
    nodes, edges = self._build_graph_data(memories)
    self.update_graph(nodes, edges)
    # 统计
    self.update_stats(self.brain.memory.get_stats())
```

### Requirement: cognition_viz 自动刷新
原 `CognitionVisualizer` 没有任何刷新机制，需添加 `refresh_data` 和定时器。

**修改后**:
```python
class CognitionVisualizer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.brain = None  # 由 main_window 注入
        self._cognition_chain: List[CognitionNode] = []
        self._setup_ui()
        # 定时刷新
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(5000)
    
    def set_brain(self, brain):
        self.brain = brain
    
    def refresh_data(self):
        if not self.brain:
            return
        try:
            data = self.brain.get_dashboard_data()
            self.update_chain(data.get('cognition_chain', []))
            self.update_abilities(data.get('abilities', {}))
            self.update_decision(data.get('decision', {}))
            self.update_status(data.get('cognition_status', {}))
        except Exception as e:
            logger.debug(f"cognition_viz refresh failed: {e}")
```

### Requirement: system_monitor.refresh_data
原 `SystemMonitor` 只有分散的 `update_*` 方法，需新增统一的 `refresh_data(brain)`。

**修改后**:
```python
class SystemMonitor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.brain = None
        # ... 原有 _setup_ui / _setup_timers
    
    def set_brain(self, brain):
        self.brain = brain
    
    def refresh_data(self, brain=None):
        brain = brain or self.brain
        if not brain:
            return
        try:
            data = brain.get_dashboard_data()
            # abilities: 0-100 → 0-1
            abilities = data.get('abilities', {})
            capabilities = {k: max(0, min(1, v/100)) for k, v in abilities.items()}
            self.update_capabilities(capabilities)
            # emotion
            emotion = data.get('emotion', {})
            self.update_emotion(
                emotion.get('name', '平静'),
                max(0, min(1, emotion.get('intensity', 0)/100)),
                emotion.get('valence', '中性'),
                {
                    'pleasure': max(-1, min(1, emotion.get('pleasure', 0)/100)),
                    'arousal': max(0, min(1, emotion.get('arousal', 0)/100)),
                    'dominance': max(0, min(1, emotion.get('dominance', 0)/100)),
                }
            )
            # tasks
            self.update_tasks(data.get('tasks', []))
        except Exception as e:
            logger.debug(f"system_monitor refresh failed: {e}")
```

### Requirement: main_window 中央刷新器
原 `_update_status` 只更新状态栏文字，需扩展为中央刷新器。

**修改后**:
```python
def _update_status(self):
    # 原有的状态栏更新
    self.statusBar().showMessage("系统运行中...")
    
    # 新增：刷新所有 viz
    if hasattr(self, 'memory_viz') and self.memory_viz:
        try:
            self.memory_viz.refresh_data()
        except Exception as e:
            logger.debug(f"memory_viz refresh failed: {e}")
    
    if hasattr(self, 'cognition_viz') and self.cognition_viz:
        try:
            self.cognition_viz.refresh_data()
        except Exception as e:
            logger.debug(f"cognition_viz refresh failed: {e}")
    
    if hasattr(self, 'system_monitor') and self.system_monitor:
        try:
            self.system_monitor.refresh_data(self.brain)
        except Exception as e:
            logger.debug(f"system_monitor refresh failed: {e}")
    
    # 标签页切换时立即刷新
def _on_tab_changed(self, index):
    widget = self.tab_widget.widget(index)
    if hasattr(widget, 'refresh_data'):
        try:
            widget.refresh_data()
        except Exception as e:
            logger.debug(f"tab refresh failed: {e}")
```

---

## REMOVED Requirements

无

---

## 验证策略

### 单元测试
1. `Brain.get_dashboard_data()` 返回正确的数据结构（包含 7+ 个键）
2. `memory_viz.refresh_data()` 不抛异常
3. `cognition_viz.refresh_data()` 不抛异常（含 brain=None 退化情况）
4. `system_monitor.refresh_data(brain)` 不抛异常

### 端到端测试
1. 启动 GUI
2. 检查所有面板 - 都有数据
3. 等待 5 秒，确认面板自动刷新
4. 发送消息，确认认知面板的思维链/情感数据更新
5. 切换标签页，确认无延迟显示

### 回归测试
1. 会话管理（新建/切换/删除）
2. 消息持久化
3. Ollama 模型调用
4. 记忆检索
5. UI 字体、消息气泡
6. 停止按钮
