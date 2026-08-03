# 修复 max_tokens 验证任务清单

> 状态：已完成 ✅
> 目标：把 max_tokens 上限从 8192（Pydantic，models/base.py）→ 262144（256K），统一 models/base.py + core/config.py + settings_dialog.py

---

## 任务1：检查 Pydantic ModelConfig 的实际位置 ✅
- [x] 任务1.1：`models/base.py:191` 是 Pydantic `ModelConfig(PydanticBaseModel)`（**实际错误源**）
- [x] 任务1.2：`models/base.py:215` 有 `Field(default=2048, ge=1, le=8192)` 硬编码
- [x] 任务1.3：`core/config.py:32` 是 `@dataclass ModelConfig`（不触发 Pydantic 验证）
- [x] 任务1.4：`model_manager.py:_load_from_config` 调用 `ModelConfig(max_tokens=config.max_tokens)` 触发验证

## 任务2：放宽 Pydantic 验证上限 ✅
- [x] 任务2.1：`models/base.py:215` `Field(le=8192)` → `Field(le=262144)`，default 从 2048 → 4096
- [x] 任务2.2：`core/config.py:59-60` 同步 `> 32768` → `> 262144`，错误消息同步
- [x] 任务2.3：确认 `models/base.py` 缺省值 4096 与 `config.py` 缺省值一致

## 任务3：更新 settings_dialog max_tokens_spin ✅
- [x] 任务3.1：`setRange(1, 32768)` → `setRange(1, 262144)`
- [x] 任务3.2：`setSingleStep(512)` → `setSingleStep(1024)`
- [x] 任务3.3：tooltip 提到 Gemini 1.5、GPT-4.1 等 256K+ 模型

## 任务4：更新单元测试 ✅
- [x] 任务4.1：更新 `test_settings_params.py`：max_tokens 上限 262144，step 1024
- [x] 任务4.2：新增 Pydantic ModelConfig 测试 + dataclass 验证上限测试
- [x] 任务4.3：运行所有测试确认 9+7+8+5=29/29 通过

## 任务5：端到端验证 ⏳（手动）
- [x] 任务5.1：测试已覆盖关键场景（max_tokens=100000/262144/262145/300000）
- [x] 任务5.2：用户报错值 32768 现在可正常工作
- [ ] 任务5.3：手动启动 GUI 验证（可选）

---

## 任务依赖关系

```
任务1 (检查) ✅ → 任务2 (Pydantic 修复) ✅
任务3 (UI 修复) ✅ - 与 2 并行
任务4 (测试) ✅ - 依赖 1-3
任务5 (端到端) ⏳ - 依赖 4（已通过单元测试覆盖）
```

## 并行可行性

- 任务 2、3 互不依赖 → 可并行 ✅
- 任务 4 依赖 2、3 ✅

---

## 关键代码位置（已修改）

| 文件 | 关键位置 | 修改 |
|------|---------|------|
| `hyperbrain/models/base.py` | line 215, `ModelConfig.max_tokens` Field | `le=8192` → `le=262144`, default 2048 → 4096 ✅ |
| `hyperbrain/core/config.py` | line 59-60, `ModelConfig.validate()` | `> 32768` → `> 262144` ✅ |
| `hyperbrain/ui/settings_dialog.py` | line 250-260, `max_tokens_spin` | setRange + setSingleStep + tooltip ✅ |
| `test_settings_params.py` | line 44-48 + 新增 test_pydantic_model_config | 断言 262144 / 1024 + Pydantic 测试 ✅ |
| `hyperbrain/models/tests/test_models.py` | line 520 | max_tokens 默认 2048 → 4096 ✅ |

---

## 测试结果汇总

| 测试 | 通过 | 失败 |
|------|------|------|
| test_settings_params.py | 9/9 | 0 |
| test_all_features.py | 7/7 | 0 |
| test_ui_refresh.py | 8/8 | 0 |
| test_model_and_shortmem.py | 5/5 | 0 |
| **总计** | **29/29** | **0** |
