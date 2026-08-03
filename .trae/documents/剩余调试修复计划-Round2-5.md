# HyperBrain 剩余调试修复计划（Round 2 收尾 → Round 5）

## 摘要

本计划承接上一会话已批准的 5 轮迭代修复方案。Round 1（7 个严重问题）已完成并通过测试，Round 2（5 个中等问题）代码层面已修复但验证阶段发现 `config.yaml` 被测试覆写的新问题。本计划聚焦剩余工作：收尾 Round 2 验证、完成 Round 3（轻微问题 L1-L4）、执行 Round 4（全面测试）和 Round 5（最终验证 + 清理）。

## 当前状态分析

### 已完成（Round 1 + Round 2 代码修复）
- **S1-S7 严重问题**：全部修复，358 个测试通过
- **M1-M5 中等问题**：代码层面已修复（settings_dialog asdict、vector_store deleted 过滤、model_manager fallback 隔离、memory_manager 语义 embedding、ollama_model /api/embed 端点、architecture_evolution 悬空连接清理、error_handler inspect、scheduler sorted）

### 剩余问题清单

| 编号 | 问题 | 位置 | 严重度 |
|------|------|------|--------|
| R2V | config.yaml 被测试覆写（openai_base_url 还原为 null） | `tests/test_gui_session_manager.py:81` + `config.yaml:102` | 中 |
| L1 | 代码块正则不兼容（c++/c#/单行代码块） | `hyperbrain/ui/chat_widget.py:307` | 轻 |
| L2 | event_loop fixture 与新版 pytest-asyncio 冲突 | `hyperbrain/tests/conftest.py:17-22` | 轻 |
| L3 | slow marker 未注册（--strict-markers 导致报错） | `pytest.ini` | 轻 |
| L4 | nudge_jobs 访问私有方法 `_get_connection` | `hyperbrain/hermes/nudge/nudge_jobs.py:87,106` | 轻 |

## 提议的修改

### Round 2 收尾：修复 config.yaml 被测试覆写（R2V）

**文件 1**: `e:\超脑\超脑002\tests\test_gui_session_manager.py`
- **修改内容**: 重写 `test_config_save_persists` 测试（第 65-95 行），使用 `tempfile` 临时路径隔离测试，避免覆写项目根 config.yaml
- **原因**: 当前测试调用 `save_config(config)` 不带 path 参数，会写入 `_config_path`（即项目根 config.yaml）。测试中断时恢复代码不执行，导致 config.yaml 被污染为 `test_model`
- **方法**:
  ```python
  def test_config_save_persists(self, tmp_path):
      from hyperbrain.core.config import Config, ConfigManager, save_config
      # 使用独立临时文件，不触碰项目 config.yaml
      tmp_config = tmp_path / "test_config.yaml"
      mgr = ConfigManager()
      mgr._config_path = str(tmp_config)  # 隔离路径
      config = mgr.load_config(str(tmp_config))
      config.model.default_provider = "test_provider"
      config.model.ollama_model = "test_model"
      mgr.save_config(config)
      # 重新加载验证
      mgr2 = ConfigManager()
      config2 = mgr2.load_config(str(tmp_config))
      assert config2.model.default_provider == "test_provider"
      assert config2.model.ollama_model == "test_model"
  ```
  同时审查该文件其他测试是否也有同类问题（如 `test_config_loads_from_yaml` 第 50-63 行硬编码断言 `minimax-m3:cloud`，应改为非破坏性断言）

**文件 2**: `e:\超脑\超脑002\config.yaml`
- **修改内容**: 第 102 行 `openai_base_url: null` → `openai_base_url: ""`
- **原因**: `ModelConfig.openai_base_url: str = ""` 默认是字符串，null 会导致字符串操作（如 `url + "/v1"`）抛 `TypeError`；与同段 `ollama_base_url` 类型不一致

**文件 3**: `e:\超脑\超脑002\hyperbrain\core\config.py`
- **修改内容**: 在 `ConfigManager.save_config`（第 573 行）增加防御：当 `path` 为 None 且 `_config_path` 指向项目根 config.yaml 时，记录 warning 日志，提示测试应使用临时路径
- **原因**: 从源头防止未来测试再次覆写项目配置（可选增强，非必须）

### Round 3：修复轻微问题 L1-L4

**L1 - 文件**: `e:\超脑\超脑002\hyperbrain\ui\chat_widget.py`
- **修改内容**: 第 307 行正则 `r'```(\w+)?\n(.*?)```'` → `r'```([^\n`]*)\n?(.*?)```'`
- **原因**: 
  - `(\w+)?` 无法匹配 `c++`、`c#`、`objective-c++` 等含特殊字符的语言名
  - 强制 `\n` 紧跟语言标识符，导致单行代码块或语言标识后有空格时匹配失败
- **方法**: `[^\n`]*` 匹配语言标识（允许 `+`、`#`、`-` 等，排除换行和反引号），`\n?` 使换行可选

**L2 - 文件**: `e:\超脑\超脑002\hyperbrain\tests\conftest.py`
- **修改内容**: 删除第 17-22 行的 `event_loop` fixture
- **原因**: `pytest-asyncio` >= 0.21 已废弃自定义 `event_loop` fixture；`pytest.ini` 已设 `asyncio_mode = auto`，由 pytest-asyncio 自动管理事件循环。保留旧 fixture 会与新版本冲突并触发警告/错误
- **方法**: 直接移除该 fixture，依赖 `asyncio_mode = auto`

**L3 - 文件**: `e:\超脑\超脑002\pytest.ini`
- **修改内容**: 添加 `markers` 配置段
- **原因**: 第 7 行 `--strict-markers` 要求所有 marker 必须注册，否则报错。当前未注册 `slow` marker
- **方法**:
  ```ini
  markers =
      slow: marks tests as slow (deselect with '-m "not slow"')
      asyncio: asyncio test marker
  ```
  同时考虑 `testpaths = tests` 是否需要补充 `hyperbrain/tests`（探索发现 conftest.py 在 `hyperbrain/tests/`）

**L4 - 文件**: `e:\超脑\超脑002\hyperbrain\database\sqlite_manager.py` + `e:\超脑\超脑002\hyperbrain\hermes\nudge\nudge_jobs.py`
- **修改内容**: 
  1. 在 `sqlite_manager.py` 添加公共方法 `get_connection()`（无下划线前缀），返回与 `_get_connection` 相同的上下文管理器
  2. `nudge_jobs.py` 第 87、106 行 `brain.db._get_connection()` → `brain.db.get_connection()`
- **原因**: `_get_connection` 是私有方法，外部模块直接访问违反封装；一旦内部重构会直接崩溃
- **方法**: 
  ```python
  # sqlite_manager.py 新增
  def get_connection(self):
      """公共连接获取接口（上下文管理器）"""
      return self._get_connection()
  ```
  同步检查 `long_term_memory.py:161` 是否有同类问题，一并修复

### Round 4：全面测试 + 修复剩余失败

**步骤**:
1. 运行完整测试套件：`C:\Python314\python.exe -m pytest tests/ hyperbrain/tests/ -v --tb=short 2>&1`
2. 收集所有失败/错误测试
3. 逐个分析失败原因，分类：
   - 测试本身的问题（断言过时、mock 不完整）→ 修复测试
   - 代码 bug → 修复代码
   - 环境问题（venv、依赖）→ 记录并跳过
4. 重新运行直到全部通过或剩余失败有合理说明
5. 特别关注：
   - config.yaml 不再被覆写（运行测试后检查 `openai_base_url` 仍为 `""`）
   - L1-L4 修复未引入新失败
   - Round 1/2 修复的测试仍通过

### Round 5：最终验证 + 清理

**步骤**:
1. **最终测试运行**: `C:\Python314\python.exe -m pytest tests/ hyperbrain/tests/ -v 2>&1` 确认全部通过
2. **配置完整性检查**: 
   - 读取 `config.yaml` 确认 `openai_base_url: ""`（非 null）
   - 确认 `ollama_model` 与 `default_model` 一致
   - 确认 `fallback_models` 不含与主模型相同的项
3. **导入检查**: `C:\Python314\python.exe -c "import hyperbrain; from hyperbrain.core.brain import Brain; from hyperbrain.ui.chat_widget import ChatWidget; print('OK')"` 确认无导入错误
4. **清理**: 
   - 删除测试产生的临时文件（如有）
   - 确认无遗留的 `test_model` 字样在 config.yaml
5. **生成最终报告**: 汇总 5 轮修复的所有变更和测试结果

## 假设与决策

1. **Python 环境**: 使用 `C:\Python314\python.exe`（venv 损坏，指向不存在的 `E:\software\python314\python.exe`）
2. **PowerShell 语法**: 命令分隔用 `;` 而非 `&&`
3. **测试路径**: 同时运行 `tests/` 和 `hyperbrain/tests/` 两个目录
4. **R2V 防御性增强**（config.py warning 日志）标记为可选，若增加复杂度过高则跳过
5. **L4 公共方法命名**: 采用 `get_connection()`（无下划线），保持向后兼容（保留 `_get_connection` 不删除）
6. **L2 决策**: 直接删除旧 fixture 而非迁移到新 API，因为 `asyncio_mode = auto` 已足够

## 验证步骤

每个 Round 完成后执行：
1. 运行相关测试确认修复有效
2. 运行完整测试套件确认无回归
3. 检查 config.yaml 完整性

最终验证（Round 5）执行上述所有检查 + 导入检查 + 配置完整性检查。
