# 修复模型切换和短期记忆任务清单

> 状态：任务 1-4 已完成 ✅；任务 5 等待手动验证 ⏳
> 目标：让设置对话框的模型切换真正生效，并修复短期记忆一直为 0 的问题

---

## 任务1：连接 settings_changed 信号 ✅
- [x] 任务1.1：在 `main_window._show_settings()` 中添加 `dialog.settings_changed.connect(self._on_settings_changed)`
- [x] 任务1.2：实现 `main_window._on_settings_changed(settings)` 方法
- [x] 任务1.3：在处理器中调用 `self.brain.model_manager.register_model(...)` 重新注册模型
- [x] 任务1.4：先 `unregister_model` 旧模型（如果存在）
- [x] 任务1.5：捕获异常（防止单个 provider 失败影响其他）
- [x] 任务1.6：状态栏显示 "模型已更新" 反馈

## 任务2：Brain.process 添加工作记忆写入 ✅
- [x] 任务2.1：在 `brain.py` 的 `process()` 方法中，找到 store 到长期记忆之前的位置
- [x] 任务2.2：添加 `self.memory.working_memory.add(content=user_input, ...)` 调用
- [x] 任务2.3：添加 `self.memory.working_memory.add(content=response_content, ...)` 调用
- [x] 任务2.4：在 `_store_interaction()`（process_stream 的后台任务）中同样添加
- [x] 任务2.5：try-except 包裹（防止工作记忆失败影响主流程）
- [x] 任务2.6：使用合适的 priority（用户输入 0.7 > AI 响应 0.6）

## 任务3：修复 memory_viz 字段映射 ✅
- [x] 任务3.1：在 `memory_viz.refresh_data()` 中读取 `working_memory.get_stats()['current_chunks']` 字段
- [x] 任务3.2：兼容 `current_size` 字段（ShortTermMemory 用）
- [x] 任务3.3：回退默认值为 0（如果字段都不存在）
- [x] 任务3.4：capacity 默认 7（与 working_memory 默认值一致）
- [x] 任务3.5：调用 `update_short_term_stats(current_chunks, capacity)` 正确显示
- [x] 任务3.6：额外：当 working_memory 为空时回退到 sensory_memory

## 任务4：单元测试 ✅
- [x] 任务4.1：创建 `test_model_and_shortmem.py`（5 个测试）
  - 测试 `_show_settings` 连接了 `settings_changed` 信号 ✅
  - 测试 `_on_settings_changed` 收到信号后调用 `model_manager.register_model` ✅
  - 测试 `Brain.process` 源码包含 2 次 `working_memory.add` 调用 + 异常保护 ✅
  - 测试 `memory_viz` 字段映射（current_chunks → stm_items_label "3/7"）✅
  - 测试 `memory_viz` 回退到 `sensory_memory` ✅
- [x] 任务4.2：运行 `test_ui_refresh.py` 8/8 通过（无回归）
- [x] 任务4.3：运行 `test_all_features.py` 7/7 通过（无回归）

## 任务5：端到端验证 ⏳（手动）
- [ ] 任务5.1：启动 GUI（`py run_hyperbrain.py`）
- [ ] 任务5.2：打开设置 → 切换 Ollama 模型为 minimax-m3:cloud → 点击"应用" → 关闭对话框
- [ ] 任务5.3：发送消息 → 验证回复来源是新模型（看响应内容/速度）
- [ ] 任务5.4：发送 3-5 条消息 → 切换到记忆面板 → 概览 → 短期记忆显示 > 0
- [ ] 任务5.5：等待 5 秒，确认短期记忆数字在合理范围内（1-7）

---

## 任务依赖关系

```
任务1 (✅) ── 模型切换
任务2 (✅) ── 工作记忆写入
任务3 (✅) ── 字段映射
任务4 (✅) ── 单元测试（依赖 1, 2, 3）
任务5 (⏳) ── 端到端（手动验证）
```

---

## 实施总结

### 已修改文件
| 文件 | 改动 |
|------|------|
| `hyperbrain/ui/main_window.py` | `_show_settings` 连接 `settings_changed` 信号；新增 `_on_settings_changed` 处理器（130 行）|
| `hyperbrain/core/brain.py` | `process()` 在 store 之前写入工作记忆（用户输入 + AI 响应）；`_store_interaction()` 同样处理 |
| `hyperbrain/ui/memory_viz.py` | `refresh_data` 读取 `current_chunks`，回退到 `sensory_memory` |

### 新增文件
| 文件 | 用途 |
|------|------|
| `test_model_and_shortmem.py` | 5 个新测试（信号连接 + 处理器 + 工作记忆 + 字段映射 + 回退）|

### 关键代码位置

| 文件 | 关键方法 | 状态 |
|------|---------|------|
| `hyperbrain/ui/main_window.py` | `_show_settings` | ✅ |
| `hyperbrain/ui/main_window.py` | 新增 `_on_settings_changed` | ✅ |
| `hyperbrain/core/brain.py` | `process` | ✅ |
| `hyperbrain/core/brain.py` | `_store_interaction` | ✅ |
| `hyperbrain/ui/memory_viz.py` | `refresh_data` | ✅ |

### 测试结果

```
test_model_and_shortmem.py: 5/5 通过
  - settings_changed 信号连接
  - _on_settings_changed 注册模型
  - Brain.process 包含 working_memory.add
  - memory_viz 字段映射（current_chunks）
  - memory_viz 回退到 sensory_memory

test_ui_refresh.py: 8/8 通过（无回归）
test_all_features.py: 7/7 通过（无回归）

合计 20/20 通过 ✅
```
