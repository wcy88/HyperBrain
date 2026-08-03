# 修复模型切换和短期记忆检查清单

## settings_changed 信号连接检查 ✅
- [x] `main_window._show_settings` 调用 `dialog.settings_changed.connect(...)`
- [x] `main_window._on_settings_changed(settings)` 方法已实现
- [x] 处理器调用 `self.brain.model_manager.register_model(...)` 重新注册
- [x] 处理器先 unregister 旧模型
- [x] 处理器捕获异常（不崩溃）
- [x] 状态栏显示更新反馈

## 工作记忆写入检查 ✅
- [x] `Brain.process` 调用 `self.memory.working_memory.add(user_input, ...)`
- [x] `Brain.process` 调用 `self.memory.working_memory.add(response_content, ...)`
- [x] `Brain._store_interaction`（process_stream 后台任务）同样调用 working_memory.add
- [x] working_memory.add 用 try-except 包裹
- [x] 优先级合理（用户输入 0.7 > AI 响应 0.6）
- [x] 工作记忆内容截断（避免过长，使用 `[:200]`）

## memory_viz 字段映射检查 ✅
- [x] `memory_viz.refresh_data` 读取 `current_chunks` 字段
- [x] 兼容 `current_size` 字段
- [x] capacity 默认 7
- [x] 调用 `update_short_term_stats(current_chunks, capacity)`
- [x] 当 working_memory 为空时回退到 `sensory_memory`
- [x] 短期记忆显示 > 0（发送消息后）

## 单元测试检查 ✅
- [x] `test_model_and_shortmem.py` 创建（5 个测试）
- [x] 信号连接测试通过
- [x] 处理器测试通过
- [x] working_memory 源码测试通过
- [x] 字段映射测试通过
- [x] sensory_memory 回退测试通过
- [x] `test_all_features.py` 7/7 通过（无回归）
- [x] `test_ui_refresh.py` 8/8 通过（无回归）

## 端到端测试检查 ⏳（手动）
- [ ] 启动 GUI
- [ ] 设置 → Ollama 模型切换为 minimax-m3:cloud → 应用 → 关闭
- [ ] 发送消息 → 验证使用新模型（响应内容/时间）
- [ ] 发送 3-5 条消息
- [ ] 切换到记忆面板 → 概览 → 短期记忆 > 0
- [ ] 状态栏显示 "模型已更新"

---

## 状态总结

| 阶段 | 状态 |
|------|------|
| 任务 1（信号连接）| ✅ 已完成 |
| 任务 2（工作记忆写入）| ✅ 已完成 |
| 任务 3（字段映射）| ✅ 已完成 |
| 任务 4（单元测试）| ✅ 5/5 + 8/8 + 7/7 = 20/20 通过 |
| 任务 5（端到端测试）| ⏳ 手动验证 |

## 测试运行结果

```
$ py test_model_and_shortmem.py
=== settings_changed 信号连接测试 ===       PASSED
=== settings_changed 处理器注册模型 ===      PASSED
=== Brain.process 写入工作记忆 ===          PASSED
=== memory_viz 字段映射（current_chunks） === PASSED
=== memory_viz 回退到 sensory_memory ===    PASSED
总计: 5 通过, 0 失败

$ py test_ui_refresh.py
总计: 8 通过, 0 失败（无回归）

$ py test_all_features.py
总计: 7 通过, 0 失败（无回归）

**合计 20/20 测试通过 ✅**
```
