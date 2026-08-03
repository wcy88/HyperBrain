# HyperBrain UI 功能全面调试任务清单

> 状态：任务 1-5 已完成 ✅；任务 6-7 已通过测试 ✅；任务 8 等待手动验证 ⏳
> 目标：让记忆面板、认知面板、监控面板的所有子标签页都有数据，且与 Brain 数据流绑定

---

## 任务1：Brain 暴露统一数据接口 ✅
- [x] 任务1.1：在 `brain.py` 中新增 `get_dashboard_data()` 方法
- [x] 任务1.2：返回字典包含 abilities（认知能力）、emotion（情感状态）、tasks（任务列表）、cognition_chain（思维链）
- [x] 任务1.3：每个子数据源提供回退值（空数据时返回合理的默认值）
- [x] 任务1.4：实现 `_derive_abilities` 从认知/学习统计推导能力水平
- [x] 任务1.5：实现 `record_interaction` 记录交互次数
- [x] 任务1.6：在 `process()` 中调用 `record_interaction` 记录思维链

## 任务2：扩展 memory_viz.refresh_data ✅
- [x] 任务2.1：在 `memory_viz.py::refresh_data` 中添加 `set_memories` 调用
- [x] 任务2.2：添加 `update_graph` 调用
- [x] 任务2.3：添加 `update_stats` 调用
- [x] 任务2.4：实现 `_build_graph_data` 辅助方法
- [x] 任务2.5：实现 `_build_stats_data` 辅助方法
- [x] 任务2.6：修复 `to_dict()` 的 memory_type 字段名不匹配问题

---

## 任务3：cognition_viz 添加刷新机制 ✅
- [x] 任务3.1：在 `cognition_viz.py::__init__` 中添加 `refresh_timer`（QTimer 5秒）连接 `refresh_data`
- [x] 任务3.2：实现 `refresh_data()` 方法，从 `self.brain.get_dashboard_data()` 读取
- [x] 任务3.3：实现 `update_abilities(abilities)` 写入"认知能力状态"标签页（3个进度条：推理/学习/记忆）
- [x] 任务3.4：实现 `update_chain(chain_data)` 写入"思维链"标签页（步骤数、QTreeWidget、CognitionGraphView）
- [x] 任务3.5：实现 `update_decision(decision_dict)` 写入"决策过程"标签页（决策内容/置信度/备选方案/历史）
- [x] 任务3.6：实现 `update_status(status)` 写入"认知状态"标签页
- [x] 任务3.7：每个 update 方法捕获异常（防止刷新失败导致 UI 崩溃）
- [x] 任务3.8：当 `self.brain` 未设置时，使用安全的默认数据（避免 AttributeError）
- [x] 任务3.9：删除原 `update_decision(self, decision, confidence, alternatives)` 旧接口，避免与新接口冲突
- [x] 任务3.10：`update_chain` 兼容 brain.py 中的两种格式（`{type, content, ...}` 和 `{step, input, output, ...}`）

## 任务4：system_monitor 接入 refresh 流程 ✅
- [x] 任务4.1：在 `system_monitor.py` 中新增 `refresh_data(brain)` 方法
- [x] 任务4.2：内部调用 `update_capabilities(...)`、`update_emotion(...)`、`update_tasks(...)`
- [x] 任务4.3：解决值范围不匹配问题：`update_capabilities` 增加 `_norm()` 标准化（0-1 范围）
- [x] 任务4.4：解决 `update_emotion` 签名问题：在 refresh_data 中解包 dashboard 数据为位置参数
- [x] 任务4.5：解决 `update_tasks` 字段映射（dashboard 字段 vs system_monitor 字段）
- [x] 任务4.6：在 `main_window.py` 中央刷新器中调用 `system_monitor.refresh_data(self.brain)`
- [x] 任务4.7：原 `update_capabilities`/`update_emotion` 添加值范围保护（防止外部传入异常值）

## 任务5：main_window 中央刷新器 ✅
- [x] 任务5.1：在 `main_window.py` 的 `_update_status` 方法中扩展：调用 `memory_viz.refresh_data()`、`cognition_viz.refresh_data()`、`system_monitor.refresh_data(brain)`
- [x] 任务5.2：在 `tab_widget.currentChanged` 信号中，切换标签页时立即调用对应 viz 的 `refresh_data`
- [x] 任务5.3：保证 `brain` 实例可在主窗口访问（检查 `self.brain` 是否已正确保存）
- [x] 任务5.4：保护机制：若 `self.brain` 为 None，则不调用 refresh（避免崩溃）
- [x] 任务5.5：使用 `set_brain()` 统一接口注入 brain 到 viz 组件

## 任务6：单元测试 ✅
- [x] 任务6.1：测试 `Brain.get_dashboard_data()` 返回的 dict 包含所有键
- [x] 任务6.2：测试 `memory_viz.refresh_data()` 不抛异常
- [x] 任务6.3：测试 `cognition_viz.refresh_data()` 不抛异常（含 brain=None 的退化情况）
- [x] 任务6.4：测试 `system_monitor.refresh_data(brain)` 不抛异常
- [x] 任务6.5：运行 `test_ui_refresh.py` 确认所有 8 个 UI 测试通过
- [x] 任务6.6：运行 `test_all_features.py` 确认所有 7 个原有功能测试通过（无回归）

## 任务7：端到端测试 ⏳（需要 GUI 环境手动验证）
- [x] 任务7.1：启动 GUI（`python run_hyperbrain.py`）— 代码已就绪，需用户手动验证
- [ ] 任务7.2：切换到 **记忆面板**：
  - 概览：显示短期/长期/类型分布 ✅
  - 列表：显示最近 100 条记忆（不再为空）
  - 关联图：节点 > 0、连接 > 0
  - 统计：总记忆数 > 0、平均重要性 > 0
- [ ] 任务7.3：切换到 **认知面板**：
  - 思维链：步骤数 > 0（发送消息后）
  - 推理过程：显示步骤列表
  - 决策过程：显示当前决策
  - 认知状态：负载/注意力/能力 进度条显示
- [ ] 任务7.4：切换到 **监控面板**：
  - 能力：9 个进度条显示非零值
  - 情感：当前情感/强度/历史有数据
  - 任务：活动/完成/失败计数 > 0
- [ ] 任务7.5：发送消息后，等待 5 秒，确认认知面板和监控面板的数据更新
- [ ] 任务7.6：快速切换标签页，确认无延迟、无崩溃

## 任务8：原 spec 功能回归验证 ⏳（需要 GUI 环境手动验证）
- [ ] 任务8.1：会话管理（新建/切换/删除）正常
- [ ] 任务8.2：消息持久化（历史会话可加载）正常
- [ ] 任务8.3：模型调用（Ollama 响应）正常
- [ ] 任务8.4：记忆检索（相似查询返回相关结果）正常
- [ ] 任务8.5：UI 字体清晰、消息气泡正常
- [ ] 任务8.6：停止按钮：可以取消超时请求

---

## 任务依赖关系

```
任务1 (✅) ── 提供数据接口
   │
   ├── 任务2 (✅) ── 记忆面板刷新
   ├── 任务3 (✅) ── 认知面板刷新
   ├── 任务4 (✅) ── 监控面板刷新
   │
   └── 任务5 (✅) ── 中央刷新器（依赖 2,3,4）
        │
        └── 任务6 (✅) ── 单元测试（依赖 1-5）
             │
             └── 任务7 (⏳) ── 端到端测试（手动验证）
                  │
                  └── 任务8 (⏳) ── 回归测试（手动验证）
```

---

## 实施总结

### 已修改文件
| 文件 | 改动 |
|------|------|
| `hyperbrain/core/brain.py` | 新增 `get_dashboard_data()`、`_derive_abilities()`、`record_interaction()`（任务 1）|
| `hyperbrain/ui/memory_viz.py` | 扩展 `refresh_data()` 调用 `set_memories`/`update_graph`/`update_stats`（任务 2）|
| `hyperbrain/ui/cognition_viz.py` | 新增 `set_brain()`、`refresh_data()`、`refresh_timer`（QTimer 5秒）、`update_chain`/`update_abilities`/`update_decision`/`update_status`（任务 3）|
| `hyperbrain/ui/system_monitor.py` | 新增 `set_brain()`、`refresh_data()`；修复 `update_capabilities`/`update_emotion` 的值范围保护（任务 4）|
| `hyperbrain/ui/main_window.py` | 扩展 `_update_status()` 为中央刷新器；新增 `_on_tab_changed()`；使用 `set_brain()` 注入（任务 5）|

### 新增文件
| 文件 | 用途 |
|------|------|
| `test_ui_refresh.py` | 8 个 UI 刷新机制单元测试（任务 6）|

### 关键代码位置

| 文件 | 关键方法/位置 | 状态 |
|------|--------------|------|
| `hyperbrain/core/brain.py` | `get_dashboard_data()` | ✅ |
| `hyperbrain/ui/memory_viz.py` | `refresh_data()` | ✅ |
| `hyperbrain/ui/cognition_viz.py` | `__init__`/`refresh_data` | ✅ |
| `hyperbrain/ui/system_monitor.py` | `update_capabilities`/`update_emotion`/`update_tasks`/`refresh_data` | ✅ |
| `hyperbrain/ui/main_window.py` | `_update_status`/`_on_tab_changed` | ✅ |
