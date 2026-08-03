"""
Hermes 面板

- 6 个数字卡：累计轨迹数、平均 reward、近 7 天新增 Skill 数、
             待训练数据集行数、当前生产模型版本、最近一次评估提升率
- 1 张 nudge 时间线（最近 20 条 nudge_log）
- 1 张 reward 分布直方图
- 1 个"立即评分 / 立即生成数据"按钮组
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QPen, QBrush
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QGraphicsScene,
    QGraphicsView,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from hyperbrain.core.logger import get_logger
from hyperbrain.ui.themes import theme_manager

logger = get_logger("ui.hermes_panel")


def _make_card(title: str, value: str = "—") -> QFrame:
    """生成一个数字卡（标题 + 大号数字）。"""
    card = QFrame()
    card.setObjectName("HermesCard")
    card.setFrameShape(QFrame.Shape.StyledPanel)
    card.setStyleSheet(
        "QFrame#HermesCard {"
        "  background: palette(base);"
        "  border: 1px solid palette(mid);"
        "  border-radius: 8px;"
        "  padding: 8px;"
        "}"
    )
    layout = QVBoxLayout(card)
    layout.setContentsMargins(12, 10, 12, 10)
    layout.setSpacing(2)
    title_label = QLabel(title)
    title_label.setStyleSheet("color: palette(mid); font-size: 11px;")
    value_label = QLabel(value)
    value_label.setStyleSheet("font-size: 22px; font-weight: 600;")
    value_label.setObjectName("card_value")
    layout.addWidget(title_label)
    layout.addWidget(value_label)
    layout.addStretch()
    return card


class _BarChartView(QGraphicsView):
    """轻量柱状图：QGraphicsScene 自绘。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setMinimumHeight(160)
        self.setBackgroundBrush(QBrush(QColor("#1e1e1e")))
        self._buckets: List[int] = [0] * 10

    def set_data(self, buckets: List[int]) -> None:
        self._buckets = (buckets + [0] * 10)[:10]
        self._redraw()

    def _redraw(self) -> None:
        self.scene.clear()
        w = max(self.viewport().width(), 100)
        h = max(self.viewport().height(), 100)
        n = len(self._buckets)
        bar_w = w / (n * 1.4)
        gap = bar_w * 0.4
        max_v = max(self._buckets) or 1
        for i, v in enumerate(self._buckets):
            bh = (v / max_v) * (h - 30)
            x = i * (bar_w + gap) + gap
            y = h - bh - 20
            self.scene.addRect(
                x, y, bar_w, bh,
                QPen(QColor("#5b8def")),
                QBrush(QColor("#5b8def")),
            )
            # 数值
            text = self.scene.addText(str(v), QFont("Arial", 8))
            text.setDefaultTextColor(QColor("#cccccc"))
            text.setPos(x + bar_w / 2 - 8, y - 16)
            # 横轴标签
            lbl = self.scene.addText(f"{i/10:.1f}", QFont("Arial", 7))
            lbl.setDefaultTextColor(QColor("#888888"))
            lbl.setPos(x + bar_w / 2 - 8, h - 14)


class HermesPanel(QWidget):
    """Hermes Agent 数据飞轮的可视化面板。"""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.brain: Optional[Any] = None
        self._build_ui()
        self._timer = QTimer(self)
        self._timer.setInterval(15_000)  # 15s
        self._timer.timeout.connect(self.refresh_data)
        self._timer.start()

    def set_brain(self, brain: Any) -> None:
        self.brain = brain
        self.refresh_data()

    # ---------- UI 构建 ----------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        # 6 个数字卡
        cards_grid = QGridLayout()
        cards_grid.setSpacing(8)
        self.card_trajectories = _make_card("累计轨迹")
        self.card_avg_reward = _make_card("平均 reward")
        self.card_auto_skills = _make_card("近 7 天自动 Skill")
        self.card_pending = _make_card("待训练样本")
        self.card_model = _make_card("当前生产模型")
        self.card_eval = _make_card("最近一次评估 Δ")
        for i, c in enumerate(
            [
                self.card_trajectories, self.card_avg_reward,
                self.card_auto_skills, self.card_pending,
                self.card_model, self.card_eval,
            ]
        ):
            cards_grid.addWidget(c, i // 3, i % 3)
        root.addLayout(cards_grid)

        # 操作按钮行
        btn_row = QHBoxLayout()
        self.btn_score = QPushButton("立即评分")
        self.btn_build = QPushButton("构造训练集")
        self.btn_train = QPushButton("尝试微调")
        self.btn_refresh = QPushButton("刷新")
        for b in (self.btn_score, self.btn_build, self.btn_train, self.btn_refresh):
            btn_row.addWidget(b)
        btn_row.addStretch()
        root.addLayout(btn_row)
        self.btn_score.clicked.connect(self._on_score)
        self.btn_build.clicked.connect(self._on_build)
        self.btn_train.clicked.connect(self._on_train)
        self.btn_refresh.clicked.connect(self.refresh_data)

        # 下半部分：左 nudge 时间线 / 右 reward 分布
        bottom = QHBoxLayout()
        bottom.setSpacing(8)

        nudge_box = QGroupBox("Nudge 时间线（最近 20 条）")
        nudge_layout = QVBoxLayout(nudge_box)
        self.nudge_table = QTableWidget(0, 4)
        self.nudge_table.setHorizontalHeaderLabels(["job", "started_at", "ms", "ok"])
        self.nudge_table.horizontalHeader().setStretchLastSection(True)
        self.nudge_table.verticalHeader().setVisible(False)
        nudge_layout.addWidget(self.nudge_table)
        bottom.addWidget(nudge_box, 1)

        reward_box = QGroupBox("Trajectory reward 分布")
        reward_layout = QVBoxLayout(reward_box)
        self.reward_view = _BarChartView()
        reward_layout.addWidget(self.reward_view)
        bottom.addWidget(reward_box, 1)

        root.addLayout(bottom, 1)

    # ---------- 公共 ----------

    def refresh_data(self) -> None:
        try:
            stats = self._gather_stats()
        except Exception as e:  # noqa: BLE001
            logger.debug(f"hermes panel gather failed: {e}")
            stats = {}

        # 更新 6 个数字卡
        self._set_card(self.card_trajectories, str(stats.get("trajectories_total", "—")))
        avg = stats.get("avg_reward")
        self._set_card(self.card_avg_reward, f"{avg:.3f}" if avg is not None else "—")
        self._set_card(self.card_auto_skills, str(stats.get("auto_skills_7d", "—")))
        self._set_card(self.card_pending, str(stats.get("pending_training", "—")))
        self._set_card(self.card_model, str(stats.get("current_model_version", "—")))
        delta = stats.get("last_eval_delta")
        self._set_card(
            self.card_eval,
            f"{delta:+.3f}" if delta is not None else "—",
        )

        # 更新 nudge 表格
        nudge_rows = stats.get("nudge_recent", [])
        self.nudge_table.setRowCount(len(nudge_rows))
        for i, r in enumerate(nudge_rows):
            self.nudge_table.setItem(i, 0, QTableWidgetItem(str(r.get("job_name", ""))))
            self.nudge_table.setItem(i, 1, QTableWidgetItem(str(r.get("started_at", ""))))
            self.nudge_table.setItem(i, 2, QTableWidgetItem(f"{r.get('duration_ms') or 0:.1f}"))
            self.nudge_table.setItem(i, 3, QTableWidgetItem("✓" if r.get("success") else "✗"))

        # 更新 reward 分布
        self.reward_view.set_data(stats.get("reward_buckets", []))

    # ---------- 内部 ----------

    @staticmethod
    def _set_card(card: QFrame, value: str) -> None:
        for child in card.findChildren(QLabel):
            if child.objectName() == "card_value":
                child.setText(value)
                return

    def _gather_stats(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "trajectories_total": 0,
            "avg_reward": None,
            "auto_skills_7d": 0,
            "pending_training": 0,
            "current_model_version": "—",
            "last_eval_delta": None,
            "nudge_recent": [],
            "reward_buckets": [0] * 10,
        }
        if self.brain is None:
            return out

        pipe = getattr(self.brain, "trajectory_pipeline", None)
        if pipe is not None:
            out["trajectories_total"] = pipe.collector.count()
            out["avg_reward"] = pipe.collector.avg_reward()
            out["pending_training"] = pipe.builder.count_pending(
                self.brain.config.hermes.trajectory.reward_threshold
            )
            current = pipe.registry.get_current()
            if current:
                out["current_model_version"] = current.get("version_id", "—")
                out["last_eval_delta"] = current.get("eval_delta")

            # reward 分布
            try:
                with pipe.db._get_connection() as conn:  # type: ignore[attr-defined]
                    rows = conn.execute(
                        """
                        SELECT reward FROM trajectories
                        WHERE reward IS NOT NULL AND reward >= 0
                        ORDER BY created_at DESC LIMIT 500
                        """
                    ).fetchall()
                buckets = [0] * 10
                for (r,) in rows:
                    idx = min(int(float(r) * 10), 9)
                    if idx < 0:
                        idx = 0
                    buckets[idx] += 1
                out["reward_buckets"] = buckets
            except Exception:  # noqa: BLE001
                pass

        # nudge 日志
        from hyperbrain.hermes.nudge.nudge_log import NudgeLog
        log = NudgeLog(self.brain.db)
        try:
            with self.brain.db._get_connection() as conn:  # type: ignore[attr-defined]
                rows = conn.execute(
                    """
                    SELECT job_name, started_at, duration_ms, success
                    FROM nudge_log
                    ORDER BY id DESC LIMIT 20
                    """
                ).fetchall()
            out["nudge_recent"] = [dict(r) for r in rows]
        except Exception:  # noqa: BLE001
            pass

        # 自动 Skill 数
        try:
            with self.brain.db._get_connection() as conn:  # type: ignore[attr-defined]
                row = conn.execute(
                    """
                    SELECT COUNT(*) FROM generated_skills
                    WHERE status='active'
                    AND created_at >= datetime('now', '-7 day')
                    """
                ).fetchone()
            out["auto_skills_7d"] = int(row[0] or 0)
        except Exception:  # noqa: BLE001
            pass

        return out

    # ---------- 按钮 ----------

    def _on_score(self) -> None:
        if not self.brain or not self.brain.trajectory_pipeline:
            return
        n = self.brain.trajectory_pipeline.score_pending(limit=500)
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Hermes", f"已评分 {n} 条轨迹")
        self.refresh_data()

    def _on_build(self) -> None:
        if not self.brain or not self.brain.trajectory_pipeline:
            return
        path = self.brain.trajectory_pipeline.build_dataset()
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Hermes", f"数据集已导出：{path or '样本不足'}")
        self.refresh_data()

    def _on_train(self) -> None:
        if not self.brain or not self.brain.trajectory_pipeline:
            return
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(
            self, "Hermes",
            "训练门禁：需要 hermes.trainer.enabled=true 且样本数 >= min_new_samples\n"
            "当前未启用训练（默认关闭，避免误触发 GPU 任务）"
        )
