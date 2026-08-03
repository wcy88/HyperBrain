# 优化设置参数任务清单

> 状态：任务 1-8 已完成 ✅；任务 9 等待手动验证 ⏳
> 目标：优化设置对话框的参数范围、缺省值、用户体验

---

## 任务1：优化 General Parameters ✅
- [x] 任务1.1：Max Tokens 范围 1-8192 → 1-32768
- [x] 任务1.2：Max Tokens step 128 → 512
- [x] 任务1.3：Max Tokens 显式 setValue(4096)
- [x] 任务1.4：Temperature 显式 setValue(0.7)
- [x] 任务1.5：Timeout 显式 setValue(90)
- [x] 任务1.6：为 Temperature/Max Tokens/Timeout 添加 setToolTip()

## 任务2：优化认知层 ✅
- [x] 任务2.1：推理深度显式 setValue(3)
- [x] 任务2.2：最大思维链长度范围 1-50 → 1-20
- [x] 任务2.3：最大思维链长度显式 setValue(5)
- [x] 任务2.4：置信度阈值显式 setValue(0.7)
- [x] 任务2.5：为推理深度/最大思维链/置信度阈值/反思 添加 setToolTip()

## 任务3：优化执行层 ✅
- [x] 任务3.1：最大执行时间 step=5, setValue(30)
- [x] 任务3.2：重试次数 setValue(3)
- [x] 任务3.3：并行执行添加 setToolTip()
- [x] 任务3.4：为各参数添加 setToolTip()

## 任务4：优化学习层 ✅
- [x] 任务4.1：学习率 step 0.0001 → 0.001
- [x] 任务4.2：学习率 setValue(0.001)
- [x] 任务4.3：在线学习添加 setToolTip()

## 任务5：API Key 占位符 ✅
- [x] 任务5.1：OpenAI Key 占位符 "sk-..." → "（可选，未填则不启用）"
- [x] 任务5.2：Anthropic Key 占位符 "sk-ant-..." → "（可选，未填则不启用）"
- [x] 任务5.3：Google Key 占位符 "AIza..." → "（可选，未填则不启用）"
- [x] 任务5.4：API Key 字段保持 Password echo mode

## 任务6：config.py 缺省值与验证 ✅
- [x] 任务6.1：ModelConfig.max_tokens 默认 2000 → 4096
- [x] 任务6.2：ModelConfig.validate() 添加 max_tokens 上限 32768
- [x] 任务6.3：ModelConfig.validate() 添加 timeout 上限 300
- [x] 任务6.4：CognitiveConfig.validate() 添加 reasoning_depth 上限 10
- [x] 任务6.5：CognitiveConfig.validate() 添加 max_chain_length 上限 20

## 任务7：参数应用反馈 ✅
- [x] 任务7.1：点击"应用"后状态栏显示"设置已应用: provider/model"持续 3 秒
- [x] 任务7.2：使用 QTimer.singleShot 实现 3 秒后清除
- [x] 任务7.3：3 秒后自动恢复为"系统运行中..."

## 任务8：单元测试 ✅
- [x] 任务8.1：创建 `test_settings_params.py`（8 个测试）
- [x] 任务8.2：测试 Max Tokens 范围 1-32768
- [x] 任务8.3：测试 最大思维链长度 范围 1-20
- [x] 任务8.4：测试 学习率 step=0.001
- [x] 任务8.5：测试 9 个参数都有显式 setValue 调用
- [x] 任务8.6：测试 12 个关键参数都有 tooltip
- [x] 任务8.7：测试 3 个 API Key 占位符正确
- [x] 任务8.8：测试 config.py dataclass 缺省值正确
- [x] 任务8.9：测试 config.py 验证规则（异常 + 合法值）
- [x] 任务8.10：回归测试 20/20 通过（test_ui_refresh 8/8 + test_all_features 7/7 + test_model_and_shortmem 5/5）

## 任务9：端到端验证 ⏳（手动）
- [ ] 任务9.1：启动 GUI
- [ ] 任务9.2：打开设置 → 模型标签
  - 验证 Max Tokens 显示 4096（不是 8192）
  - 验证 Max Tokens 上限 32768
  - 鼠标悬停显示 tooltip
- [ ] 任务9.3：打开设置 → 系统标签
  - 验证 最大思维链长度 范围 1-20（不是 1-50）
  - 验证 各 spin box 缺省值
  - 鼠标悬停显示 tooltip
- [ ] 任务9.4：API Key 字段
  - 占位符为 "（可选，未填则不启用）"
- [ ] 任务9.5：点击"应用" → 状态栏显示"设置已应用"，3 秒后恢复

---

## 任务依赖关系

```
任务1-5 (UI 修改) ✅ - 已完成
任务6 (config.py) ✅ - 已完成
任务7 (反馈) ✅ - 已完成
任务8 (测试) ✅ - 已完成
任务9 (端到端) ⏳ - 手动验证
```

---

## 实施总结

### 已修改文件
| 文件 | 改动 |
|------|------|
| `hyperbrain/ui/settings_dialog.py` | 9 个 spin box 范围/缺省/tooltip + 3 个 API Key 占位符 |
| `hyperbrain/core/config.py` | max_tokens 默认 4096 + ModelConfig/CognitiveConfig 验证规则 |
| `hyperbrain/ui/main_window.py` | `_on_settings_changed` 添加 3 秒后自动清除反馈 |

### 新增文件
| 文件 | 用途 |
|------|------|
| `test_settings_params.py` | 8 个新测试（范围/缺省/tooltip/占位符/验证）|

### 关键代码位置

| 文件 | 修改内容 |
|------|----------|
| `settings_dialog.py` | `_create_model_tab`（任务 1）+ `_create_cognitive_tab`（任务 2）+ `_create_execution_tab`（任务 3）+ `_create_learning_tab`（任务 4）+ API Key 创建（任务 5）|
| `config.py` | ModelConfig/CognitiveConfig dataclass 字段（任务 6）|
| `main_window.py` | `_on_settings_changed`（任务 7）|

### 测试结果

```
test_settings_params.py: 8/8 通过
  - Max Tokens 范围 1-32768
  - 最大思维链长度 范围 1-20
  - 学习率 step=0.001
  - 9 个参数都有显式 setValue 调用
  - 12 个关键参数都有 tooltip
  - 3 个 API Key 占位符正确
  - config.py dataclass 缺省值正确
  - config.py 验证规则

test_ui_refresh.py: 8/8 通过（无回归）
test_all_features.py: 7/7 通过（无回归）
test_model_and_shortmem.py: 5/5 通过（无回归）

合计 28/28 通过 ✅
```
