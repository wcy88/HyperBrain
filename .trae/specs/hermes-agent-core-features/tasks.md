# Tasks

## Task 0：基础设施（所有后续任务的依赖）
- [x] SubTask 0.1：扩展 `hyperbrain/core/config.py` 新增 `HermesConfig` dataclass（auto_skill / nudge / trajectory / trainer 四段配置），并在 `config.yaml` 追加 `hermes:` 段
- [x] SubTask 0.2：在 `hyperbrain/database/sqlite_manager.py` 的 `_init_tables()` 末尾追加 7 张表：`interaction_patterns`、`generated_skills`、`nudge_log`、`trajectories`、`trajectory_rewards`、`model_versions`、`trajectory_feedback`
- [x] SubTask 0.3：创建 `hyperbrain/hermes/` 包结构：`__init__.py`、`common.py`（统一 logger、retry 装饰器、LLM 调用包装）

## Task 1：Skill 自动创建（依赖 Task 0）
- [x] SubTask 1.1：实现 `hyperbrain/hermes/auto_skill/pattern_detector.py` —— 关键词 + Jaccard 意图聚类，滑动窗口（默认 1 小时）内频次 ≥ N 触发草稿
- [x] SubTask 1.2：实现 `hyperbrain/hermes/auto_skill/skill_generator.py` —— 调用 `ModelManager.chat()` 产出符合 `BaseSkill` 模板的 Python 源码（含 system prompt 模板与 JSON schema 约束）
- [x] SubTask 1.3：实现 `hyperbrain/hermes/auto_skill/skill_validator.py` —— 三道关：AST 解析 → import 白名单 → `exec()` 沙箱实例化 + `execute()` mock 调用
- [x] SubTask 1.4：实现 `hyperbrain/hermes/auto_skill/skill_publisher.py` —— 把通过验证的 Skill 写入 `hyperbrain/skills/auto_generated/<hash>.py`，并调用 `SkillLoader.reload(only_new=True)`
- [x] SubTask 1.5：在 `hyperbrain/skills/loader.py` 暴露 `reload(only_new: bool = True)` 方法

## Task 2：周期性 Nudge 调度（依赖 Task 0）
- [x] SubTask 2.1：实现 `hyperbrain/hermes/nudge/nudge_scheduler.py` —— 纯 asyncio 定时器（不引入 APScheduler 以减少依赖），支持注册 / 暂停 / 恢复 / 取消，单任务异常隔离
- [x] SubTask 2.2：实现 `hyperbrain/hermes/nudge/nudge_jobs.py` —— 注册 6 个默认任务（pattern_mining、memory_consolidation、self_reflection、trajectory_scoring、skill_decay_check、health_snapshot）
- [x] SubTask 2.3：实现 `hyperbrain/hermes/nudge/nudge_log.py` —— 把每次执行结果（start、end、duration_ms、error）写入 `nudge_log` 表
- [x] SubTask 2.4：在 `Brain.start()` 末尾追加 `await self.nudge_scheduler.start()`，`Brain.shutdown()` 追加 `await self.nudge_scheduler.stop()`

## Task 3：Trajectory 训练管道闭环（依赖 Task 0）
- [x] SubTask 3.1：实现 `hyperbrain/hermes/trajectory/trajectory_collector.py` —— 暴露 `record(...)`，幂等写入 `trajectories` 表
- [x] SubTask 3.2：在 `Brain.process()` 成功 / 失败分支末尾调用 `self._hermes_post_process(...)` 统一处理
- [x] SubTask 3.3：实现 `hyperbrain/hermes/trajectory/reward_scorer.py` —— 三种信号合成 0-1 分：追问检测（同一 session 后续 message）、错误关联（trajectory 失败 → 0.0）、显式反馈（trajectory_feedback 表）
- [x] SubTask 3.4：实现 `hyperbrain/hermes/trajectory/dataset_builder.py` —— 选 `score >= threshold` 的轨迹，按 SFT/DPO 两种 schema 导出 jsonl，去重 key = sha1(user_input[:200]||response[:200])
- [x] SubTask 3.5：实现 `hyperbrain/hermes/trajectory/trainer.py` —— 三 backend 适配：`ollama` / `llamafactory` / `unsloth`；统一返回 `TrainingRun` 对象；缺省 dry_run 模式
- [x] SubTask 3.6：实现 `hyperbrain/hermes/trajectory/model_registry.py` —— 维护 `model_versions` 表，支持 `register / promote / get_current`
- [x] SubTask 3.7：实现 `hyperbrain/hermes/trajectory/evaluator.py` —— 在 holdout 上跑新旧模型，计算平均 reward 差，差值 ≥ 阈值才允许 promote

## Task 4：Brain 集成与依赖注入（依赖 Task 1/2/3）
- [x] SubTask 4.1：在 `Brain.__init__` 末尾新增 `_init_hermes()`，注入 `self.auto_skill_generator / self.nudge_scheduler / self.trajectory_pipeline`
- [x] SubTask 4.2：在 `Brain.get_stats()` 中追加 `hermes` 字段：累计轨迹数、平均 reward、自动生成 Skill 数、nudge job 列表
- [x] SubTask 4.3：把 `model_manager` 默认模型切换走 `model_registry.get_current()` 返回的版本 —— **部分实现**：`ModelRegistry.get_current()` 已就绪；ModelManager 运行时切模型未在 spec 4.3 中实现，需要额外的 model manager 接口扩展（已记录在 checklist 注释里）

## Task 5：UI 可视化（依赖 Task 4）
- [x] SubTask 5.1：在 `hyperbrain/ui/hermes_panel.py` 新增面板 —— 6 个数字卡 + 1 张 nudge 时间线（QTableWidget）+ 1 张轨迹 reward 分布直方图（QGraphicsView）
- [x] SubTask 5.2：在 `main_window.py` 的信息 tab 追加 "Hermes" 入口，仿照 `memory_viz` 的 `refresh_data` 模式做增量刷新

## Task 6：测试（依赖 Task 1-5）
- [x] SubTask 6.1：`tests/test_hermes_auto_skill.py` —— 8 个单元测试，全部通过
- [x] SubTask 6.2：`tests/test_hermes_nudge.py` —— 4 个单元测试，全部通过
- [x] SubTask 6.3：`tests/test_hermes_trajectory.py` —— 8 个单元测试，全部通过
- [x] SubTask 6.4：把 3 个测试文件接入 `pytest` 默认收集（新增 `pytest.ini`，asyncio_mode=auto）

# Task Dependencies
- Task 0 → Task 1 / Task 2 / Task 3（任一即可开始）
- Task 1 + Task 2 + Task 3 → Task 4
- Task 4 → Task 5 → Task 6
