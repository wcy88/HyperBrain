# HyperBrain UI 功能全面调试检查清单

## Brain 数据接口检查 ✅
- [x] `brain.py` 中新增 `get_dashboard_data()` 方法
- [x] 返回字典包含 abilities、emotion、tasks、cognition_chain 等 7+ 个键
- [x] 缺失数据时返回合理的默认值（空字典/空列表/0）
- [x] abilities 值在 0-100 范围内（与 UI 进度条一致）

## memory_viz 完整刷新检查 ✅
- [x] `memory_viz.refresh_data` 调用 `set_memories` 更新列表页
- [x] `memory_viz.refresh_data` 调用 `update_graph` 更新关联图
- [x] `memory_viz.refresh_data` 调用 `update_stats` 更新统计页
- [x] `_build_graph_data` 辅助方法正确生成节点和边
- [x] 修复 `to_dict()` 的 memory_type 字段名不匹配问题
- [x] `refresh_data` 在 brain=None 时不抛异常

## cognition_viz 刷新机制检查 ✅
- [x] `cognition_viz` 中新增 `refresh_data` 方法
- [x] `cognition_viz` 中新增 `refresh_timer`（QTimer 5秒）
- [x] `refresh_data` 调用 `update_chain`（思维链页）
- [x] `refresh_data` 调用 `update_abilities`（认知状态页 - 能力进度条）
- [x] `refresh_data` 调用 `update_decision`（决策过程页）
- [x] `refresh_data` 调用 `update_status`（认知状态页 - 负载/注意力/元认知）
- [x] `update_chain` 从 `brain.get_dashboard_data()['cognition_chain']` 读取
- [x] `update_abilities` 从 `brain.get_dashboard_data()['abilities']` 读取
- [x] `update_decision` 接受 dict 格式（来自 dashboard data）
- [x] `update_status` 从 `brain.get_dashboard_data()['cognition_status']` 读取
- [x] 所有 update 方法捕获异常（防止 UI 崩溃）
- [x] `self.brain` 为 None 时安全降级
- [x] `update_chain` 兼容 brain.py 两种格式（`{type, content, ...}` 和 `{step, input, output, ...}`）

## system_monitor 连接检查 ✅
- [x] `system_monitor` 中新增 `refresh_data(brain)` 方法
- [x] `refresh_data` 调用 `update_capabilities`（能力页）
- [x] `refresh_data` 调用 `update_emotion`（情感页）
- [x] `refresh_data` 调用 `update_tasks`（任务页）
- [x] 值范围转换正确（dashboard 0-100 → update_capabilities 0-1）
- [x] 情感维度转换正确（dashboard dict → update_emotion 5 个位置参数）
- [x] 任务字段映射正确（dashboard 字段 → system_monitor 字段）
- [x] `main_window` 在中央刷新器中调用 `system_monitor.refresh_data(self.brain)`
- [x] `update_capabilities`/`update_emotion` 添加 `_norm()` 值范围保护

## main_window 中央刷新器检查 ✅
- [x] `_update_status` 调用 `memory_viz.refresh_data()`
- [x] `_update_status` 调用 `cognition_viz.refresh_data()`
- [x] `_update_status` 调用 `system_monitor.refresh_data(self.brain)`
- [x] 标签页切换时（`tab_widget.currentChanged`）立即调用 `refresh_data`
- [x] 保护机制：`self.brain` 为 None 时不调用 refresh（避免崩溃）
- [x] 每个 refresh 调用都包在 try-except 中
- [x] 使用 `set_brain()` 统一接口注入 brain

## 单元测试检查 ✅
- [x] `Brain.get_dashboard_data()` 返回正确结构（11 个键）
- [x] `memory_viz.refresh_data()` 不报错
- [x] `cognition_viz.refresh_data()` 不报错（含 brain=None 退化）
- [x] `system_monitor.refresh_data(brain)` 不报错
- [x] `test_ui_refresh.py` 所有 8 个 UI 刷新测试通过
- [x] `test_all_features.py` 所有 7 个原有功能测试通过（无回归）

## 端到端测试检查 ⏳（需要 GUI 手动验证）
- [x] 启动 GUI 正常 — 代码已就绪
- [ ] **记忆面板**：
  - 概览：显示正确（短期/长期/类型）✅
  - 列表：显示最近 100 条记忆（不再为空）
  - 关联图：节点 > 0、连接 > 0
  - 统计：总记忆数 > 0、平均重要性 > 0
- [ ] **认知面板**：
  - 思维链：步骤数 > 0（发送消息后）
  - 推理过程：显示步骤列表
  - 决策过程：显示当前决策
  - 认知状态：负载/注意力/能力 进度条显示
- [ ] **监控面板**：
  - 能力：9 个进度条显示非零值
  - 情感：当前情感/强度/历史有数据
  - 任务：活动/完成/失败计数 > 0
- [ ] 发送消息后，等待 5 秒，认知面板和监控面板的数据更新
- [ ] 快速切换标签页，确认无延迟、无崩溃

## 原 spec 功能回归测试检查 ⏳（需要 GUI 手动验证）
- [ ] 会话管理：新建/切换/删除正常
- [ ] 消息持久化：历史会话可加载
- [ ] 模型调用：Ollama 响应正常
- [ ] 记忆检索：相似查询返回相关结果
- [ ] UI 显示：字体清晰、消息气泡正常
- [ ] 停止按钮：可以取消超时请求

---

## 状态总结

| 阶段 | 状态 |
|------|------|
| 任务 1-5（数据接口 + 4 个面板刷新）| ✅ 已完成 |
| 任务 6（单元测试）| ✅ 8/8 UI + 7/7 原有测试通过 |
| 任务 7（端到端测试）| ⏳ 代码就绪，待用户手动验证 |
| 任务 8（回归测试）| ⏳ 待用户手动验证 |

## 测试运行结果

```
$ py test_ui_refresh.py
=== Brain.get_dashboard_data() 结构测试 ===  PASSED
=== memory_viz.refresh_data() 无脑降级测试 ===  PASSED
=== cognition_viz.refresh_data() 无脑降级测试 ===  PASSED
=== system_monitor.refresh_data() 无脑降级测试 ===  PASSED
=== system_monitor 值范围转换测试 ===  PASSED
=== cognition_viz update_* 方法测试 ===  PASSED
=== 主窗口中央刷新器测试 ===  PASSED
=== viz brain 注入测试 ===  PASSED
总计: 8 通过, 0 失败

$ py test_all_features.py
总计: 7 通过, 0 失败（无回归）
```

**合计 15/15 测试通过 ✅**
