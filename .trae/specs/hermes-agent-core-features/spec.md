# Hermes Agent 三大核心功能规格说明书

## Why
HyperBrain 当前仅有 OpenClaw 风格的手写 Skill 加载器，缺乏"自演化、自调度、自训练"能力。Hermes Agent（开源 Agent 框架，10k+ commits，社区已验证）证明：将 **Skill 自动创建 + 周期性 nudge + Trajectory 训练闭环** 串成一条数据飞轮，可以让 Agent 真正随使用逐步变强。本 spec 把这三条能力落到 HyperBrain 当前架构里，让现有 8 层架构具备自我生长能力。

## What Changes
- 在 `hyperbrain/hermes/` 下新增三个独立子模块：`auto_skill/`（Skill 自动创建）、`nudge/`（周期性 nudge 调度）、`trajectory/`（轨迹训练管道），全部基于现有 `Brain.process()` 的事件流挂载，不破坏 8 层架构。
- 扩展 SQLite schema，新增 6 张表：`interaction_patterns`、`generated_skills`、`nudge_log`、`trajectories`、`trajectory_rewards`、`model_versions`。
- 在 `Brain.start()` / `Brain.shutdown()` 中分别启动 / 停止 `NudgeScheduler` 与 `TrajectoryPipeline`。
- 在 `config.yaml` 增加 `hermes:` 配置段，可关闭任一子系统；并在 `.env.example` 增加 `HERMES_TRAINER_BACKEND=ollama|llamafactory|unsloth`。
- **BREAKING**：默认行为变化 —— `Brain.process()` 现在会向 `trajectory_collector` 写入一条轨迹记录。`HyperBrain.pickle` 升级包会因为新增依赖（APScheduler、jinja2）需要重新打包。

## Impact
- Affected specs：记忆层（pattern mining、reward 读取）、学习层（轨迹评分）、进化层（nudge 触发）、执行层（Skill 热加载）。
- Affected code：
  - 新增：`hyperbrain/hermes/`（约 12 个文件）
  - 修改：`hyperbrain/core/brain.py`、`hyperbrain/database/sqlite_manager.py`、`hyperbrain/core/config.py`、`hyperbrain/skills/loader.py`、`config.yaml`
  - 测试：`tests/test_hermes_*.py`

## ADDED Requirements

### Requirement: 模式挖掘与 Skill 自动创建
系统 SHALL 在每次 `Brain.process()` 后将 `(user_input, response, skills_used, success_flag)` 写入 `interaction_patterns`；当同一意图在滑动窗口内出现 ≥ N 次（默认 N=3）且没有现成 Skill 覆盖时，触发自动创建。

#### Scenario: 高频意图触发 Skill 草稿生成
- **WHEN** 滑动窗口（默认 1 小时）内同一"意图聚类"出现 ≥ 3 次
- **AND** 现有 `SkillLoader.list_skills()` 不包含覆盖该意图的 Skill
- **THEN** `AutoSkillGenerator` 调用 `ModelManager.chat()` 生成一份符合 `BaseSkill` 模板的 Python 源码，写入 `hyperbrain/skills/auto_generated/<hash>.py`
- **AND** 该文件在 `generated_skills` 表中以 `status=draft` 登记

#### Scenario: 沙箱验证失败时回滚
- **WHEN** `SkillValidator` 跑 AST/imports/exec 沙箱时抛出异常或返回 `success=False`
- **THEN** 删除该草稿文件并将 `generated_skills.status` 置为 `failed`，失败原因写入 `error_log` 字段
- **AND** 同一意图 24 小时内不再重试

#### Scenario: Skill 热加载到主注册表
- **WHEN** 草稿 Skill 通过沙箱验证
- **THEN** `SkillLoader.reload()` 调用 `importlib.reload` 把它注册到主表
- **AND** `Brain.process()` 后续可经由 `SkillRouter` 命中该 Skill

### Requirement: 周期性 Nudge 调度
系统 SHALL 启动一个独立的 `NudgeScheduler`（基于 asyncio 定时器，间隔最小 10 秒），在 `Brain.start()` 时启动、`Brain.shutdown()` 时停止；默认注册 6 个 nudge 任务，全部可在 `config.yaml` 中独立开关与调整周期。

#### Scenario: 默认 Nudge 任务清单
- **WHEN** `NudgeScheduler` 启动
- **THEN** 注册以下任务（cron 表达式从 config 读取）：
  - `pattern_mining` 每 15 分钟：触发 `AutoSkillGenerator.scan()`
  - `memory_consolidation` 每 5 分钟：调用 `MemoryManager.consolidate()`
  - `self_reflection` 每 60 分钟：调用 `ConsciousnessManager.self_reflect()`
  - `trajectory_scoring` 每 30 分钟：对最近轨迹做 reward 评分
  - `skill_decay_check` 每 24 小时：标记 30 天未被调用的 Skill
  - `health_snapshot` 每 1 分钟：写入 CPU/内存/队列长度到 `nudge_log`

#### Scenario: 单个 Nudge 抛异常不影响其他任务
- **WHEN** 任意一个 nudge 任务执行抛出异常
- **THEN** `NudgeScheduler` 捕获并把异常写入 `nudge_log.error`
- **AND** 后续任务继续按原周期触发（不级联失败）

#### Scenario: 关闭子系统
- **WHEN** `config.yaml` 中 `hermes.nudge.enabled=false`
- **THEN** `NudgeScheduler` 启动时打印 "nudge disabled by config" 并立即返回，不注册任何任务

### Requirement: Trajectory 训练管道闭环
系统 SHALL 实现"采集→评分→成集→微调→评估→上线"六步闭环，**任意一步失败不得污染下一步**。

#### Scenario: 轨迹采集
- **WHEN** `Brain.process()` 成功返回 `ProcessingResult`
- **THEN** `TrajectoryCollector` 写入一行 `trajectories`：`{id, session_id, user_input, model_response, skills_invoked, latency_ms, created_at, reward=null}`
- **AND** 异常路径（`success=False`）也写入，但 `reward` 字段填 `-1.0` 哨兵值

#### Scenario: Reward 评分
- **WHEN** `trajectory_scoring` nudge 触发
- **THEN** `RewardScorer` 拉取 `reward IS NULL` 的轨迹，结合以下信号合成 0-1 分：
  - 用户后续轮是否追问（追问 → 0.3，闭环 → 0.9）
  - 是否触发 `EvolutionManager.record_error`（触发 → -0.5 截断到 0）
  - 显式反馈（UI 点赞 / 点踩，未来通过 `trajectory_feedback` 表读取）
- **AND** 写入 `trajectory_rewards(trajectory_id, score, signals_json, scored_at)`

#### Scenario: 训练数据集构造
- **WHEN** `DatasetBuilder` 被 nudge 或人工调用
- **THEN** 选 `score >= 0.8` 的轨迹，去重后导出 `data/training/<timestamp>.jsonl`，每行 `{messages: [...], source: "trajectory", score: ...}`，格式兼容 SFT 与 DPO

#### Scenario: 微调触发
- **WHEN** `config.yaml` 中 `hermes.trainer.enabled=true` 且新数据集行数 ≥ `min_new_samples`（默认 50）
- **THEN** `Trainer` 调用配置的 backend（`ollama` / `llamafactory` / `unsloth`）启动微调作业
- **AND** 写入 `model_versions(version_id, base_model, adapter_path, created_at, status)`，`status` 在 `queued/running/done/failed` 间流转

#### Scenario: 评估门禁
- **WHEN** 一次微调作业 `status=done`
- **THEN** `Evaluator` 拿 30 条 holdout 轨迹对新旧模型各跑一遍，比对平均 reward
- **AND** 仅当新模型相对旧模型 reward 提升 ≥ 0.05 时，把 `model_versions.promoted=true`，并由 `ModelManager` 切到该版本

#### Scenario: 闭环可视化
- **WHEN** 用户在 UI 点击 "Hermes 面板"
- **THEN** 展示六个数字卡：累计轨迹数、平均 reward、近 7 天新增 Skill 数、待训练数据集行数、当前生产模型版本、最近一次评估提升率

## MODIFIED Requirements

### Requirement: Brain 生命周期
**原**：`Brain.start()` 仅启动 consolidation / evolution / consciousness 三个后台循环。
**新**：`Brain.start()` 额外启动 `NudgeScheduler` 与 `TrajectoryPipeline`；`Brain.shutdown()` 调用它们的 `stop()` 方法并等待 graceful shutdown（最多 10 秒）。

### Requirement: SkillLoader 接口
**原**：`SkillLoader.load_skills()` 只在初始化时扫一次目录。
**新**：新增 `SkillLoader.reload(only_new=True)` 方法：扫描 `auto_generated/` 子目录，AST 解析通过后 `importlib` 动态加入 `self.skills` / `self.instances`。原方法保留为兼容入口。

### Requirement: SQLiteManager
**原**：只创建 `memories` / `conversations` / `events` 三张表。
**新**：在 `_init_tables()` 末尾追加创建 6 张 Hermes 表（见上）；所有新表 `IF NOT EXISTS`，对旧库零侵入。

## REMOVED Requirements
无。
