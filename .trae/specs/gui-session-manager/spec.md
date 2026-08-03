# HyperBrain GUI 会话管理与设置修复规格说明书

## Why
GUI已成功打开，但存在三个关键问题：1) 设置按钮点击导致程序崩溃退出；2) Ollama模型连接失败导致AI对话功能不可用；3) 缺少会话管理功能，用户无法查看、编辑、删除或继续历史会话。

## What Changes
- 修复设置对话框（settings_dialog.py）崩溃问题
- 添加左侧会话管理列表面板（会话列表、新建、编辑、删除、继续会话）
- 修复或配置大模型连接（Ollama/OpenAI/Anthropic/Google）
- 添加会话数据持久化存储（SQLite）
- 更新主窗口布局以支持会话侧边栏

## Impact
- Affected specs: UI界面、会话管理、模型配置
- Affected code: hyperbrain/ui/main_window.py, hyperbrain/ui/settings_dialog.py, hyperbrain/ui/chat_widget.py, hyperbrain/core/config.py, hyperbrain/database/sqlite_manager.py
- 新增文件: hyperbrain/ui/session_manager.py

## ADDED Requirements
### Requirement: 会话管理侧边栏
系统SHALL在GUI左侧提供会话管理面板，支持查看、新建、编辑、删除和继续历史会话。

#### Scenario: 查看会话列表
- **WHEN** 用户打开GUI界面
- **THEN** 左侧显示会话列表，包含会话名称、最后活动时间

#### Scenario: 新建会话
- **WHEN** 用户点击"新建会话"按钮
- **THEN** 创建新会话并切换到该会话的聊天界面

#### Scenario: 继续会话
- **WHEN** 用户点击历史会话
- **THEN** 加载该会话的历史消息并继续对话

#### Scenario: 编辑会话
- **WHEN** 用户右键会话选择"编辑"
- **THEN** 可以修改会话名称

#### Scenario: 删除会话
- **WHEN** 用户右键会话选择"删除"
- **THEN** 弹出确认对话框，确认后删除会话及历史消息

### Requirement: 设置对话框修复
系统SHALL修复设置对话框，点击设置按钮不崩溃，能正常显示和保存配置。

#### Scenario: 打开设置
- **WHEN** 用户点击菜单栏"文件-设置"或工具栏设置按钮
- **THEN** 设置对话框正常打开，显示所有配置项

#### Scenario: 保存设置
- **WHEN** 用户在设置对话框修改配置并点击保存
- **THEN** 配置保存成功，对话框关闭，系统应用新配置

### Requirement: 大模型连接配置
系统SHALL提供模型连接配置界面，支持配置OpenAI/Anthropic/Google/Ollama API密钥。

#### Scenario: 配置API密钥
- **WHEN** 用户在设置中输入API密钥
- **THEN** 系统验证连接并保存配置

## MODIFIED Requirements
无

## REMOVED Requirements
无
