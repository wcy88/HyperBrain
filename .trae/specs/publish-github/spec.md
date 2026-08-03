# 发布项目到 GitHub Spec

## Why

当前 HyperBrain 项目仅存在于本地 workspace，缺乏版本控制备份与协作入口。将项目打包发布到 GitHub 可以建立远端仓库、实现代码备份，并为后续版本管理与持续集成奠定基础。

## What Changes

- 初始化（或复用）本地 Git 仓库，确保当前工作区已纳入版本控制
- 创建/更新 `.gitignore`，排除敏感文件（如 `config.yaml`、数据库、缓存、虚拟环境）和构建产物
- 将当前所有有效代码变更加入提交
- 在 GitHub 上创建远程仓库（若不存在）
- 将本地仓库推送到 GitHub 远程
- 验证远程仓库可访问且文件完整

**BREAKING**: 无破坏性变更；注意不会提交包含敏感信息的配置文件。

## Impact

- Affected specs: setup-and-run, fix-test-model-revert 等已完成调试相关的 spec
- Affected code: 整个项目工作区；仅新增/修改版本控制元文件

## ADDED Requirements

### Requirement: 本地 Git 仓库初始化与整理

The system SHALL ensure the project workspace is under Git version control with a clean `.gitignore`.

#### Scenario: 仓库已存在
- **WHEN** 本地 `.git` 目录已存在
- **THEN** 复用现有仓库，不重新初始化，避免丢失历史

#### Scenario: 仓库不存在
- **WHEN** 本地 `.git` 目录不存在
- **THEN** 执行 `git init`，将项目纳入版本控制

#### Scenario: 敏感文件排除
- **WHEN** 生成 `.gitignore`
- **THEN** 必须排除 `config.yaml`、`*.db`、`data/`、`__pycache__/`、`.venv/`、`venv/`、`*.pyc`、`.pytest_cache/` 等

### Requirement: 提交当前代码状态

The system SHALL create a commit containing the current project state.

#### Scenario: 正常提交
- **WHEN** 本地存在有效代码变更
- **THEN** 使用 conventional commit 风格提交，如 `chore: publish project to GitHub`

### Requirement: GitHub 远程仓库创建与推送

The system SHALL create a remote GitHub repository and push the local commits.

#### Scenario: 仓库已存在
- **WHEN** 远程仓库名称已被占用或已配置 remote
- **THEN** 复用现有 remote，直接推送

#### Scenario: 仓库不存在
- **WHEN** 用户未指定仓库名称
- **THEN** 默认使用 `HyperBrain` 作为仓库名

#### Scenario: 推送成功
- **WHEN** 推送完成后
- **THEN** 返回远程仓库 HTTPS/SSH URL，并验证分支可见
