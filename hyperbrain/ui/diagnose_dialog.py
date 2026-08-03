"""
Ollama 连接诊断对话框（spec fix-ollama-connection-debug）

启动 scripts/diagnose_ollama.py 子进程，实时显示 6 步诊断结果：
- PASS 绿色
- FAIL 红色
- WARN 黄色
支持 "重新尝试连接" 按钮（调用 model_manager.initialize_all()）
和 "打开设置" 按钮（跳到 settings dialog 模型 tab）。
"""
from __future__ import annotations

import json
import os
import re
import sys
import subprocess
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QProcess, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QLabel, QMessageBox, QProgressBar, QApplication,
)

from hyperbrain.core.logger import get_logger

logger = get_logger(__name__)


# Windows GBK 兼容：避免 stdout 解码失败
_COLOR_GREEN = "#1a8a1a"
_COLOR_RED = "#c83232"
_COLOR_YELLOW = "#a87a00"
_COLOR_GREY = "#666666"

_PASS_RE = re.compile(r'\[STEP\s+(\d+)\]\s+\[OK\]\s+PASS\s*:\s*(.+)', re.IGNORECASE)
_FAIL_RE = re.compile(r'\[STEP\s+(\d+)\]\s+\[FAIL\]\s+FAIL\s*:\s*(.+)', re.IGNORECASE)
_WARN_RE = re.compile(r'\[STEP\s+(\d+)\]\s+\[WARN\]\s+WARN\s*:\s*(.+)', re.IGNORECASE)


class DiagnoseDialog(QDialog):
    """Ollama 连接诊断对话框。"""

    # 当用户点 "重新尝试连接" 成功后发信号，UI 可刷新状态栏
    reconnected = pyqtSignal()

    def __init__(self, parent=None, model_manager=None):
        super().__init__(parent)
        self.model_manager = model_manager
        self._process: Optional[QProcess] = None
        self._had_failure = False
        self.setWindowTitle("Ollama 连接诊断")
        self.resize(720, 520)
        self._setup_ui()
        # 自动启动一次诊断
        QTimer.singleShot(100, self._start_diagnose)

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # 顶部说明
        intro = QLabel(
            "正在对本地 Ollama 服务做 6 步诊断：\n"
            "进程 → 端口 → API 根 → 模型列表 → 模型元数据 → 生成测试"
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        # 进度条
        self.progress = QProgressBar()
        self.progress.setRange(0, 6)
        self.progress.setValue(0)
        self.progress.setFormat("等待启动…")
        layout.addWidget(self.progress)

        # 输出区
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setFont(QFont("Consolas, Courier New, monospace", 9))
        self.output.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(self.output, 1)

        # 按钮
        btn_layout = QHBoxLayout()
        self.btn_rerun = QPushButton("重新诊断")
        self.btn_rerun.clicked.connect(self._start_diagnose)
        self.btn_reconnect = QPushButton("重新尝试连接")
        self.btn_reconnect.clicked.connect(self._on_reconnect)
        self.btn_settings = QPushButton("打开设置")
        self.btn_settings.clicked.connect(self._on_open_settings)
        self.btn_close = QPushButton("关闭")
        self.btn_close.clicked.connect(self.close)

        btn_layout.addWidget(self.btn_rerun)
        btn_layout.addStretch(1)
        btn_layout.addWidget(self.btn_reconnect)
        btn_layout.addWidget(self.btn_settings)
        btn_layout.addWidget(self.btn_close)
        layout.addLayout(btn_layout)

    def _start_diagnose(self):
        """启动子进程跑 diagnose_ollama.py --json"""
        if self._process is not None:
            try:
                self._process.kill()
                self._process.waitForFinished(2000)
            except Exception:
                pass
            self._process = None

        self.output.clear()
        self.progress.setValue(0)
        self.progress.setFormat("诊断中…")
        self._had_failure = False
        self.btn_reconnect.setEnabled(False)
        self.btn_settings.setEnabled(False)

        # 找脚本路径
        script_path = Path(__file__).resolve().parents[2] / "scripts" / "diagnose_ollama.py"
        if not script_path.exists():
            self._append_line(f"错误：找不到脚本 {script_path}", _COLOR_RED, bold=True)
            self.progress.setFormat("脚本不存在")
            return

        self._process = QProcess(self)
        self._process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self._process.readyReadStandardOutput.connect(self._on_stdout)
        self._process.finished.connect(self._on_finished)
        self._process.errorOccurred.connect(self._on_process_error)

        # 用 python 3.14
        python_exe = sys.executable
        self._process.start(python_exe, [str(script_path), "--json"])
        if not self._process.waitForStarted(3000):
            self._append_line(f"无法启动 {python_exe}", _COLOR_RED, bold=True)
            self.progress.setFormat("启动失败")
            self._process = None

    def _on_stdout(self):
        if self._process is None:
            return
        try:
            data = bytes(self._process.readAllStandardOutput()).decode("utf-8", errors="replace")
        except Exception:
            return
        for line in data.splitlines():
            if not line.strip():
                continue
            self._handle_line(line)

    def _handle_line(self, line: str):
        """解析单行：先尝试 JSON，否则按文本解析"""
        # 先按 JSON 解析
        parsed = None
        try:
            parsed = json.loads(line)
        except Exception:
            parsed = None
        if isinstance(parsed, dict) and "step" in parsed:
            self._render_step_dict(parsed)
            return
        # 否则按文本解析
        self._render_text_line(line)

    def _render_step_dict(self, d: dict):
        step = int(d.get("step", 0))
        status = str(d.get("status", "?")).upper()
        name = str(d.get("name", ""))
        detail = str(d.get("detail", ""))
        fix = str(d.get("fix", ""))
        color = {
            "PASS": _COLOR_GREEN,
            "FAIL": _COLOR_RED,
            "WARN": _COLOR_YELLOW,
        }.get(status, _COLOR_GREY)
        sym = {"PASS": "[OK]", "FAIL": "[FAIL]", "WARN": "[WARN]"}.get(status, "[?]")
        self._append_line(f"[STEP {step}] {sym} {status}: {name}", color, bold=True)
        if detail:
            self._append_line(f"  {detail}")
        if fix:
            self._append_line(f"  fix: {fix}", _COLOR_GREY)
        if step > 0:
            self.progress.setValue(max(self.progress.value(), step))
        if status == "FAIL":
            self._had_failure = True

    def _render_text_line(self, line: str):
        # 匹配 [STEP N] ...
        m = _PASS_RE.search(line)
        if m:
            self._append_line(line, _COLOR_GREEN, bold=True)
            self.progress.setValue(max(self.progress.value(), int(m.group(1))))
            return
        m = _FAIL_RE.search(line)
        if m:
            self._append_line(line, _COLOR_RED, bold=True)
            self.progress.setValue(max(self.progress.value(), int(m.group(1))))
            self._had_failure = True
            return
        m = _WARN_RE.search(line)
        if m:
            self._append_line(line, _COLOR_YELLOW, bold=True)
            self.progress.setValue(max(self.progress.value(), int(m.group(1))))
            return
        # summary / 普通行
        if "Summary:" in line or "Ollama full chain" in line or "failed, see fix" in line:
            color = _COLOR_RED if "FAIL" in line else (_COLOR_GREEN if "[OK]" in line else _COLOR_YELLOW)
            self._append_line(line, color, bold=True)
            return
        self._append_line(line, _COLOR_GREY)

    def _append_line(self, text: str, color: str = "#000000", bold: bool = False):
        # GBK 兼容：尝试 utf-8，失败用 replace
        safe = text.encode("utf-8", errors="replace").decode("utf-8")
        weight = "bold" if bold else "normal"
        html = f'<div style="color:{color}; font-weight:{weight}; white-space:pre;">{self._html_escape(safe)}</div>'
        self.output.append(html)

    @staticmethod
    def _html_escape(s: str) -> str:
        return (s.replace("&", "&amp;")
                 .replace("<", "&lt;")
                 .replace(">", "&gt;")
                 .replace("\n", "<br/>"))

    def _on_finished(self, exit_code: int, exit_status):
        if exit_code == 0 and not self._had_failure:
            self.progress.setValue(6)
            self.progress.setFormat("✓ 全部通过")
        elif exit_code == 0:
            self.progress.setFormat("⚠ 有警告")
        else:
            self.progress.setFormat(f"✗ 诊断失败 (exit={exit_code})")
        self.btn_reconnect.setEnabled(self._had_failure)
        self.btn_settings.setEnabled(self._had_failure)
        self._process = None

    def _on_process_error(self, error):
        self._append_line(f"子进程错误: {error}", _COLOR_RED, bold=True)
        self.progress.setFormat("✗ 启动失败")

    def _on_reconnect(self):
        """调用 model_manager.initialize_all()"""
        if self.model_manager is None:
            QMessageBox.information(self, "提示", "无法访问 model_manager")
            return
        try:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Qt 事件循环中，提交协程
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                        fut = ex.submit(asyncio.run, self.model_manager.initialize_all())
                        results = fut.result(timeout=30)
                else:
                    results = asyncio.run(self.model_manager.initialize_all())
            except RuntimeError:
                results = asyncio.run(self.model_manager.initialize_all())
            ok = sum(1 for v in results.values() if v)
            self._append_line(f"重新连接完成：{ok}/{len(results)} 个模型初始化成功", _COLOR_GREEN if ok == len(results) else _COLOR_YELLOW, bold=True)
            self.reconnected.emit()
        except Exception as e:
            logger.error(f"Reconnect failed: {e}")
            QMessageBox.warning(self, "重新连接失败", str(e))

    def _on_open_settings(self):
        """打开设置对话框"""
        try:
            parent = self.parent()
            if parent is not None and hasattr(parent, '_show_settings'):
                parent._show_settings()
                self.close()
                return
            # 兜底：自己开
            from hyperbrain.ui.settings_dialog import SettingsDialog
            dlg = SettingsDialog(self)
            dlg.exec()
        except Exception as e:
            logger.error(f"Open settings failed: {e}")
            QMessageBox.warning(self, "打开设置失败", str(e))

    def closeEvent(self, event):
        if self._process is not None:
            try:
                self._process.kill()
                self._process.waitForFinished(2000)
            except Exception:
                pass
            self._process = None
        super().closeEvent(event)
