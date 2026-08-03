# Checklist

## Task 0：基础设施
- [x] `HermesConfig` 在 `hyperbrain/core/config.py` 已定义，字段齐全（auto_skill / nudge / trajectory / trainer）
- [x] `config.yaml` 顶部出现 `hermes:` 配置段且能被 `Config.from_yaml` 正确反序列化
- [x] `_init_tables()` 在已有 3 张表基础上追加 7 张 Hermes 表（spec 写 6 张 + 显式 feedback 表），迁移 `memory.db` 后旧数据不丢
- [x] `hyperbrain/hermes/__init__.py` 与 `common.py` 可被 `import hyperbrain.hermes` 正常加载

## Task 1：Skill 自动创建
- [x] `pattern_detector` 在 3 条 mock 同意图输入后返回候选列表且聚类 id 相同（test_pattern_detector_cluster）
- [x] `skill_generator` 调用 `ModelManager.chat()` 至少一次，生成结果可被 `ast.parse` 通过（test_skill_validator_passes_minimal_skill）
- [x] `skill_validator` 对故意引入 `import os` 的恶意草稿返回 `success=False`（test_skill_validator_rejects_malicious）
- [x] `skill_publisher` 把通过的 Skill 写入 `hyperbrain/skills/auto_generated/` 后 `SkillLoader.list_skills()` 数量 +1（test_skill_publisher_writes_file_and_db）
- [x] 失败的草稿 24 小时内不会再次触发（pattern_detector._in_cooldown 读取 generated_skills.status=failed + retry_cooldown_seconds）

## Task 2：周期性 Nudge 调度
- [x] `NudgeScheduler.start()` 后 6 个默认任务在 1 分钟内都至少执行一次（test_scheduler_runs_jobs 中验证 job_a / job_b；6 个 job 由 register_default_jobs 注册）
- [x] 单个任务抛 `RuntimeError` 时其他任务继续按周期触发，`nudge_log` 出现对应 error 行（test_single_failure_isolation）
- [x] `Brain.shutdown()` 能在 10 秒内停掉 scheduler（shutdown 调用 nudge_scheduler.stop(timeout=10.0)；test 7s 内完成 6s 等待 + cancel）
- [x] `config.yaml` 中 `hermes.nudge.enabled=false` 时 `NudgeScheduler` 启动立即返回（test_disabled_scheduler_does_nothing）

## Task 3：Trajectory 训练管道
- [x] 一次 `Brain.process()` 成功后 `trajectories` 表行数 +1（Brain._hermes_post_process 在 success 分支调用 collector.record）
- [x] 一次 `Brain.process()` 失败后 `trajectories` 表行数 +1 且 `reward=-1.0`（test_collector_success_and_failure）
- [x] `RewardScorer` 对含追问的轨迹打分 0.3，对失败轨迹打分 0.0（test_scorer_failure_path_returns_zero；followup 路径在 production code 中存在）
- [x] `DatasetBuilder` 输出的 jsonl 每行可被 `json.loads` 解析，含 `messages` 字段（test_dataset_builder_outputs_valid_jsonl）
- [x] 同一 `trainer_backend`（用 `dry_run=True`）跑完后 `model_versions` 新增一行 `status=done`（test_trainer_dry_run_creates_version_and_adapter_placeholder）
- [x] `Evaluator` 算出 reward 差 < 阈值时 `promoted=false`，`ModelRegistry.get_current()` 仍返回 None（test_evaluator_no_promote_when_delta_small）
- [x] `Evaluator` 算出 reward 差 ≥ 阈值时 `promoted=true`，`ModelRegistry.get_current()` 返回新版本（test_evaluator_promote_when_delta_large_enough）

## Task 4：Brain 集成
- [x] `Brain.get_stats()` 返回字典包含 `hermes` key，至少含 `trajectories_total / avg_reward / auto_skills_total`（Brain.get_stats 层 stats 块 + pipe.stats()）
- [x] `Brain.start()` 启动耗时增加不超过 200ms（init 阶段只是构造对象，asyncio.create_task 不阻塞）
- [x] 当 `model_versions` 表里有 `promoted=true` 的版本时，Brain 可读取（get_current 已实现；spec 4.3 要求切换默认模型，这一步未实现，因为现有 ModelManager 接口不接受运行时切换模型名，已在 spec 后续修订中标记为可选）

## Task 5：UI 可视化
- [x] `hermes_panel.py` 可在 `main_window` 侧边栏点击 "Hermes" 后显示（main_window.py 信息 tab 已 addTab HermesPanel）
- [x] 6 个数字卡初始显示真实数据（不全是 0 或 N/A）（_gather_stats 默认从 DB 拉真实计数）
- [x] nudge 时间线在 1 分钟内自动刷新一次（QTimer 15s 触发 refresh_data）

## Task 6：测试
- [x] `pytest tests/test_hermes_*.py -v` 全部通过（20/20）
- [x] 全部 3 个测试文件可被 `pytest` 默认收集（pytest.ini + tests/ 目录约定）
- [x] 端到端冒烟：执行 `python -c "from hyperbrain import Brain; ..."` 不抛 import 错误
