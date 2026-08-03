"""
认知过程可视化

展示系统思考和推理过程，包括思维链、决策过程、推理步骤等
"""

import math
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QProgressBar, QTreeWidget,
    QTreeWidgetItem, QGroupBox, QPushButton,
    QTabWidget, QTableWidget, QTableWidgetItem,
    QGraphicsView, QGraphicsScene, QGraphicsItem,
    QGraphicsEllipseItem, QGraphicsRectItem,
    QGraphicsTextItem, QGraphicsLineItem,
    QSplitter, QTextEdit, QHeaderView, QFormLayout
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRectF, QPointF
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush,
    QFont, QLinearGradient, QRadialGradient
)

from hyperbrain.core.logger import get_logger
from hyperbrain.ui.themes import theme_manager

logger = get_logger("ui.cognition")


class CognitionStepType(Enum):
    """认知步骤类型"""
    PERCEPTION = "perception"
    REASONING = "reasoning"
    DECISION = "decision"
    REFLECTION = "reflection"
    PLANNING = "planning"
    EXECUTION = "execution"


class CognitionNode:
    """
    认知节点
    
    表示认知过程中的一个步骤
    """
    
    def __init__(self, node_id: str, step_type: CognitionStepType,
                 content: str, confidence: float = 1.0,
                 parent_id: Optional[str] = None):
        self.node_id = node_id
        self.step_type = step_type
        self.content = content
        self.confidence = confidence
        self.parent_id = parent_id
        self.children: List[str] = []
        self.timestamp = datetime.now()
        self.status = "active"
    
    def add_child(self, child_id: str):
        """添加子节点"""
        if child_id not in self.children:
            self.children.append(child_id)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.node_id,
            "type": self.step_type.value,
            "content": self.content,
            "confidence": self.confidence,
            "parent_id": self.parent_id,
            "children": self.children,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status
        }


class CognitionGraphView(QGraphicsView):
    """
    认知过程图视图
    
    可视化展示思维链和推理过程
    """
    
    node_selected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        
        self._nodes: Dict[str, Dict[str, Any]] = {}
        self._edges: List[tuple] = []
        
        self._setup_scene()
    
    def _setup_scene(self):
        """设置场景"""
        colors = theme_manager.colors
        self.scene.setBackgroundBrush(QColor(colors["widget_bg"]))
    
    def clear_graph(self):
        """清空图形"""
        self.scene.clear()
        self._nodes.clear()
        self._edges.clear()
    
    def add_node(self, node_id: str, content: str, node_type: str,
                 x: float = 0, y: float = 0, confidence: float = 1.0):
        """
        添加认知节点
        
        Args:
            node_id: 节点ID
            content: 节点内容
            node_type: 节点类型
            x: X坐标
            y: Y坐标
            confidence: 置信度
        """
        colors = theme_manager.colors
        
        type_colors = {
            "perception": QColor("#42a5f5"),
            "reasoning": QColor("#66bb6a"),
            "decision": QColor("#ff7043"),
            "reflection": QColor("#ab47bc"),
            "planning": QColor("#ffa726"),
            "execution": QColor("#26c6da")
        }
        
        color = type_colors.get(node_type, QColor(colors["accent"]))
        
        # 节点大小基于内容长度
        width = min(max(len(content) * 8, 100), 200)
        height = 60
        
        # 绘制节点矩形
        rect = self.scene.addRect(
            x - width/2, y - height/2, width, height,
            QPen(color, 2),
            QBrush(color.darker(130))
        )
        rect.setData(0, node_id)
        
        # 添加类型标签
        type_text = self.scene.addText(node_type.upper(), QFont("Microsoft YaHei", 8))
        type_text.setDefaultTextColor(color.lighter(150))
        type_text.setPos(x - type_text.boundingRect().width()/2, y - height/2 + 5)
        
        # 添加内容标签
        display_content = content[:30] + "..." if len(content) > 30 else content
        content_text = self.scene.addText(display_content, QFont("Microsoft YaHei", 9))
        content_text.setDefaultTextColor(QColor(colors["text_primary"]))
        content_text.setPos(x - content_text.boundingRect().width()/2, y - 5)
        
        # 置信度指示器
        if confidence < 1.0:
            conf_width = width * confidence
            conf_rect = self.scene.addRect(
                x - width/2, y + height/2 - 4, conf_width, 4,
                QPen(Qt.PenStyle.NoPen),
                QBrush(QColor("#4caf50") if confidence > 0.7 else QColor("#ff9800") if confidence > 0.4 else QColor("#f44336"))
            )
        
        self._nodes[node_id] = {
            "content": content,
            "type": node_type,
            "x": x,
            "y": y,
            "width": width,
            "height": height,
            "item": rect,
            "confidence": confidence
        }
    
    def add_edge(self, from_id: str, to_id: str, label: str = ""):
        """
        添加边
        
        Args:
            from_id: 起始节点ID
            to_id: 目标节点ID
            label: 边标签
        """
        if from_id not in self._nodes or to_id not in self._nodes:
            return
        
        from_node = self._nodes[from_id]
        to_node = self._nodes[to_id]
        
        colors = theme_manager.colors
        
        # 计算连接点
        fx, fy = from_node["x"], from_node["y"] + from_node["height"]/2
        tx, ty = to_node["x"], to_node["y"] - to_node["height"]/2
        
        # 绘制箭头线
        pen = QPen(QColor(colors["cognition_edge"]), 2)
        line = self.scene.addLine(fx, fy, tx, ty, pen)
        
        # 添加标签
        if label:
            mid_x = (fx + tx) / 2
            mid_y = (fy + ty) / 2
            text = self.scene.addText(label, QFont("Microsoft YaHei", 8))
            text.setDefaultTextColor(QColor(colors["text_secondary"]))
            text.setPos(mid_x - text.boundingRect().width()/2, mid_y - 10)
        
        self._edges.append((from_id, to_id, line))
    
    def layout_tree(self, root_id: str, x: float = 0, y: float = 0,
                    level_height: float = 100, sibling_width: float = 220):
        """
        树形布局
        
        Args:
            root_id: 根节点ID
            x: 起始X坐标
            y: 起始Y坐标
            level_height: 层级高度
            sibling_width: 兄弟节点宽度
        """
        if root_id not in self._nodes:
            return
        
        def layout_node(node_id: str, nx: float, ny: float, level: int):
            node = self._nodes[node_id]
            node["x"] = nx
            node["y"] = ny
            
            # 更新位置
            node["item"].setRect(nx - node["width"]/2, ny - node["height"]/2,
                                node["width"], node["height"])
            
            # 布局子节点
            children = node.get("children", [])
            if children:
                child_count = len(children)
                total_width = (child_count - 1) * sibling_width
                start_x = nx - total_width / 2
                
                for i, child_id in enumerate(children):
                    if child_id in self._nodes:
                        child_x = start_x + i * sibling_width
                        child_y = ny + level_height
                        layout_node(child_id, child_x, child_y, level + 1)
        
        layout_node(root_id, x, y, 0)
        
        # 更新边
        for from_id, to_id, line in self._edges:
            if from_id in self._nodes and to_id in self._nodes:
                from_node = self._nodes[from_id]
                to_node = self._nodes[to_id]
                
                fx, fy = from_node["x"], from_node["y"] + from_node["height"]/2
                tx, ty = to_node["x"], to_node["y"] - to_node["height"]/2
                
                line.setLine(fx, fy, tx, ty)
        
        # 设置场景范围
        self.scene.setSceneRect(-400, -50, 800, 600)
    
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        pos = self.mapToScene(event.pos())
        items = self.scene.items(pos)
        
        for item in items:
            node_id = item.data(0)
            if node_id:
                self.node_selected.emit(node_id)
                break
        
        super().mousePressEvent(event)


class CognitionVisualizer(QWidget):
    """
    认知过程可视化组件
    
    功能：
    1. 思维链可视化
    2. 决策过程展示
    3. 推理步骤显示
    4. 认知状态实时更新
    
    Signals:
        step_selected: 选择认知步骤时触发
    """
    
    step_selected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)

        self.brain = None  # 由 main_window 注入
        self._cognition_chain: List[CognitionNode] = []
        self._setup_ui()

        # 定时刷新
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(5000)

        logger.info("CognitionVisualizer initialized")

    def set_brain(self, brain):
        """设置 brain 引用（由 main_window 调用）"""
        self.brain = brain

    def refresh_data(self):
        """
        刷新所有标签页的数据

        从 brain.get_dashboard_data() 读取：
        - cognition_chain → 思维链 / 推理过程
        - abilities → 认知状态的能力进度条
        - decision → 决策过程
        - cognition_status → 认知状态（负载/注意力/元认知）
        """
        if not self.brain:
            return
        try:
            data = self.brain.get_dashboard_data()
            # 1. 思维链
            try:
                chain_data = data.get("cognition_chain", [])
                self.update_chain(chain_data)
            except Exception as e:
                logger.debug(f"cognition_viz update_chain failed: {e}")
            # 2. 认知状态 - 能力进度条
            try:
                abilities = data.get("abilities", {})
                self.update_abilities(abilities)
            except Exception as e:
                logger.debug(f"cognition_viz update_abilities failed: {e}")
            # 3. 决策
            try:
                decision = data.get("decision", {})
                self.update_decision(decision)
            except Exception as e:
                logger.debug(f"cognition_viz update_decision failed: {e}")
            # 4. 认知状态
            try:
                status = data.get("cognition_status", {})
                self.update_status(status)
            except Exception as e:
                logger.debug(f"cognition_viz update_status failed: {e}")
        except Exception as e:
            logger.debug(f"cognition_viz refresh failed: {e}")

    def update_chain(self, chain_data: List[Dict[str, Any]]):
        """
        更新思维链（从 dashboard data 加载整个链条）

        Args:
            chain_data: 思维链节点数据列表
        """
        try:
            if not chain_data:
                return
            # 增量更新：只在链条增长时刷新
            current_count = len(self._cognition_chain)
            new_count = len(chain_data)
            if new_count <= current_count:
                return
            for data in chain_data[current_count:]:
                # 兼容 brain.py 中的格式 {"step", "input", "output", "time"}
                # 以及 cognition_viz 自身的格式 {"type", "content", "confidence", "parent_id"}
                if "type" in data:
                    step_type_str = data.get("type", "reasoning")
                else:
                    # 从 step 字段推断
                    step_str = str(data.get("step", "")).lower()
                    if "percept" in step_str:
                        step_type_str = "perception"
                    elif "decision" in step_str:
                        step_type_str = "decision"
                    elif "plan" in step_str:
                        step_type_str = "planning"
                    elif "reflect" in step_str:
                        step_type_str = "reflection"
                    elif "execut" in step_str or "response" in step_str:
                        step_type_str = "execution"
                    else:
                        step_type_str = "reasoning"
                try:
                    step_type = CognitionStepType(step_type_str)
                except ValueError:
                    step_type = CognitionStepType.REASONING

                # 构造内容
                if "content" in data:
                    content = str(data.get("content", ""))
                else:
                    inp = data.get("input", "")
                    outp = data.get("output", "")
                    content = f"输入: {inp}\n输出: {outp}" if inp or outp else str(data.get("step", ""))

                self.add_cognition_step(
                    step_type,
                    content,
                    data.get("confidence", 1.0),
                    data.get("parent_id")
                )
        except Exception as e:
            logger.debug(f"update_chain failed: {e}")

    def update_abilities(self, abilities: Dict[str, float]):
        """
        更新认知状态页中的能力进度条

        Args:
            abilities: 能力数据 {"reasoning": 50.0, "learning": 50.0, "memory": 50.0}
        """
        try:
            r = int(abilities.get("reasoning", 50))
            l = int(abilities.get("learning", 50))
            m = int(abilities.get("memory", 50))
            r = max(0, min(100, r))
            l = max(0, min(100, l))
            m = max(0, min(100, m))
            self.reasoning_ability_bar.setValue(r)
            self.learning_ability_bar.setValue(l)
            self.memory_ability_bar.setValue(m)
        except Exception as e:
            logger.debug(f"update_abilities failed: {e}")

    def update_decision(self, decision: Dict[str, Any]):
        """
        更新决策过程标签页

        Args:
            decision: 决策数据 {"content": "...", "confidence": 0.8, "alternatives": 3}
        """
        try:
            content = decision.get("content", "暂无决策")
            confidence = decision.get("confidence", 0)
            alternatives = decision.get("alternatives", 0)
            self.decision_content_label.setText(str(content))
            if confidence <= 1.0:
                confidence = confidence * 100
            self.decision_confidence_bar.setValue(int(max(0, min(100, confidence))))
            self.decision_alternatives_label.setText(str(alternatives))
        except Exception as e:
            logger.debug(f"update_decision failed: {e}")

    def update_status(self, status: Dict[str, Any]):
        """
        更新认知状态标签页

        Args:
            status: 认知状态数据 {"load": 0.5, "attention": "...", "depth": 0,
                                   "metacognition": {"awareness": "...", "depth": 0, "confidence": "..."}}
        """
        try:
            load = status.get("load", 0)
            attention = status.get("attention", "无")
            depth = status.get("depth", 0)
            if load <= 1.0:
                load = load * 100
            self.cognitive_load_bar.setValue(int(max(0, min(100, load))))
            self.attention_focus_label.setText(str(attention))
            self.processing_depth_label.setText(str(depth))
            meta = status.get("metacognition", {})
            if meta:
                self.update_metacognition(
                    str(meta.get("awareness", "正常")),
                    int(meta.get("depth", 0)),
                    str(meta.get("confidence", "正常"))
                )
        except Exception as e:
            logger.debug(f"update_status failed: {e}")
    
    def _setup_ui(self):
        """设置UI布局"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # 思维链标签页
        self.chain_tab = self._create_chain_tab()
        self.tab_widget.addTab(self.chain_tab, "思维链")
        
        # 推理过程标签页
        self.reasoning_tab = self._create_reasoning_tab()
        self.tab_widget.addTab(self.reasoning_tab, "推理过程")
        
        # 决策过程标签页
        self.decision_tab = self._create_decision_tab()
        self.tab_widget.addTab(self.decision_tab, "决策过程")
        
        # 认知状态标签页
        self.status_tab = self._create_status_tab()
        self.tab_widget.addTab(self.status_tab, "认知状态")
        
        layout.addWidget(self.tab_widget)
    
    def _create_chain_tab(self) -> QWidget:
        """创建思维链标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)
        
        # 控制按钮
        control_layout = QHBoxLayout()
        
        self.clear_chain_button = QPushButton("清空")
        self.clear_chain_button.clicked.connect(self.clear_chain)
        control_layout.addWidget(self.clear_chain_button)
        
        self.layout_chain_button = QPushButton("自动布局")
        self.layout_chain_button.clicked.connect(self._layout_chain)
        control_layout.addWidget(self.layout_chain_button)
        
        control_layout.addStretch()
        
        self.chain_info_label = QLabel("步骤: 0")
        control_layout.addWidget(self.chain_info_label)
        
        layout.addLayout(control_layout)
        
        # 思维链图
        self.chain_graph = CognitionGraphView()
        self.chain_graph.node_selected.connect(self._on_step_selected)
        layout.addWidget(self.chain_graph)
        
        return widget
    
    def _create_reasoning_tab(self) -> QWidget:
        """创建推理过程标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)
        
        # 推理步骤列表
        self.reasoning_tree = QTreeWidget()
        self.reasoning_tree.setHeaderLabels(["步骤", "类型", "内容", "置信度", "状态"])
        self.reasoning_tree.setColumnWidth(0, 60)
        self.reasoning_tree.setColumnWidth(1, 80)
        self.reasoning_tree.setColumnWidth(2, 300)
        self.reasoning_tree.setColumnWidth(3, 80)
        self.reasoning_tree.itemClicked.connect(self._on_reasoning_item_selected)
        layout.addWidget(self.reasoning_tree)
        
        # 推理详情
        self.reasoning_detail = QTextEdit()
        self.reasoning_detail.setReadOnly(True)
        self.reasoning_detail.setPlaceholderText("选择推理步骤查看详情...")
        self.reasoning_detail.setMaximumHeight(150)
        layout.addWidget(self.reasoning_detail)
        
        return widget
    
    def _create_decision_tab(self) -> QWidget:
        """创建决策过程标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        
        # 当前决策
        decision_group = QGroupBox("当前决策")
        decision_layout = QFormLayout(decision_group)
        
        self.decision_content_label = QLabel("暂无决策")
        self.decision_content_label.setWordWrap(True)
        decision_layout.addRow("决策内容:", self.decision_content_label)
        
        self.decision_confidence_bar = QProgressBar()
        self.decision_confidence_bar.setRange(0, 100)
        decision_layout.addRow("置信度:", self.decision_confidence_bar)
        
        self.decision_alternatives_label = QLabel("0")
        decision_layout.addRow("备选方案:", self.decision_alternatives_label)
        
        layout.addWidget(decision_group)
        
        # 决策历史
        history_group = QGroupBox("决策历史")
        history_layout = QVBoxLayout(history_group)
        
        self.decision_table = QTableWidget()
        self.decision_table.setColumnCount(4)
        self.decision_table.setHorizontalHeaderLabels(["时间", "决策", "结果", "置信度"])
        self.decision_table.horizontalHeader().setStretchLastSection(True)
        history_layout.addWidget(self.decision_table)
        
        layout.addWidget(history_group)
        layout.addStretch()
        
        return widget
    
    def _create_status_tab(self) -> QWidget:
        """创建认知状态标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        
        # 认知负载
        load_group = QGroupBox("认知负载")
        load_layout = QFormLayout(load_group)
        
        self.cognitive_load_bar = QProgressBar()
        self.cognitive_load_bar.setRange(0, 100)
        load_layout.addRow("当前负载:", self.cognitive_load_bar)
        
        self.attention_focus_label = QLabel("无")
        load_layout.addRow("注意力焦点:", self.attention_focus_label)
        
        self.processing_depth_label = QLabel("0")
        load_layout.addRow("处理深度:", self.processing_depth_label)
        
        layout.addWidget(load_group)
        
        # 认知能力
        ability_group = QGroupBox("认知能力状态")
        ability_layout = QFormLayout(ability_group)
        
        self.reasoning_ability_bar = QProgressBar()
        self.reasoning_ability_bar.setRange(0, 100)
        ability_layout.addRow("推理能力:", self.reasoning_ability_bar)
        
        self.learning_ability_bar = QProgressBar()
        self.learning_ability_bar.setRange(0, 100)
        ability_layout.addRow("学习能力:", self.learning_ability_bar)
        
        self.memory_ability_bar = QProgressBar()
        self.memory_ability_bar.setRange(0, 100)
        ability_layout.addRow("记忆能力:", self.memory_ability_bar)
        
        layout.addWidget(ability_group)
        
        # 元认知
        meta_group = QGroupBox("元认知状态")
        meta_layout = QFormLayout(meta_group)
        
        self.self_awareness_label = QLabel("正常")
        meta_layout.addRow("自我意识:", self.self_awareness_label)
        
        self.reflection_depth_label = QLabel("0")
        meta_layout.addRow("反思深度:", self.reflection_depth_label)
        
        self.confidence_level_label = QLabel("正常")
        meta_layout.addRow("置信水平:", self.confidence_level_label)
        
        layout.addWidget(meta_group)
        layout.addStretch()
        
        return widget
    
    def add_cognition_step(self, step_type: CognitionStepType, content: str,
                          confidence: float = 1.0,
                          parent_id: Optional[str] = None) -> str:
        """
        添加认知步骤
        
        Args:
            step_type: 步骤类型
            content: 步骤内容
            confidence: 置信度
            parent_id: 父步骤ID
            
        Returns:
            str: 步骤ID
        """
        step_id = f"step_{len(self._cognition_chain)}"
        
        node = CognitionNode(
            step_id, step_type, content, confidence, parent_id
        )
        
        if parent_id:
            for existing in self._cognition_chain:
                if existing.node_id == parent_id:
                    existing.add_child(step_id)
                    break
        
        self._cognition_chain.append(node)
        
        # 更新UI
        self._update_chain_graph()
        self._update_reasoning_tree()
        
        self.chain_info_label.setText(f"步骤: {len(self._cognition_chain)}")
        
        return step_id
    
    def _update_chain_graph(self):
        """更新思维链图"""
        self.chain_graph.clear_graph()
        
        if not self._cognition_chain:
            return
        
        # 添加节点
        for i, node in enumerate(self._cognition_chain):
            x = i * 200
            y = 0
            
            self.chain_graph.add_node(
                node.node_id,
                node.content,
                node.step_type.value,
                x, y,
                node.confidence
            )
        
        # 添加边
        for node in self._cognition_chain:
            if node.parent_id:
                self.chain_graph.add_edge(node.parent_id, node.node_id)
        
        # 自动布局
        if self._cognition_chain:
            self.chain_graph.layout_tree(
                self._cognition_chain[0].node_id,
                x=0, y=50
            )
    
    def _update_reasoning_tree(self):
        """更新推理树"""
        self.reasoning_tree.clear()
        
        type_names = {
            "perception": "感知",
            "reasoning": "推理",
            "decision": "决策",
            "reflection": "反思",
            "planning": "规划",
            "execution": "执行"
        }
        
        for node in self._cognition_chain:
            item = QTreeWidgetItem([
                node.node_id.split("_")[-1],
                type_names.get(node.step_type.value, node.step_type.value),
                node.content[:50] + "..." if len(node.content) > 50 else node.content,
                f"{node.confidence:.2f}",
                node.status
            ])
            item.setData(0, Qt.ItemDataRole.UserRole, node.to_dict())
            self.reasoning_tree.addTopLevelItem(item)
    
    def update_decision(self, decision: Dict[str, Any]):
        """
        更新决策过程标签页

        兼容两种调用方式：
        - update_decision({"content": "...", "confidence": 0.8, "alternatives": 3}) 字典方式（来自 dashboard data）
        - 旧的方式已被此方法统一替代

        Args:
            decision: 决策数据字典 {"content": ..., "confidence": 0-1 or 0-100, "alternatives": int}
        """
        try:
            content = decision.get("content", "暂无决策")
            confidence = decision.get("confidence", 0)
            alternatives = decision.get("alternatives", 0)
            self.decision_content_label.setText(str(content))
            try:
                cf = float(confidence)
            except (TypeError, ValueError):
                cf = 0.0
            if cf <= 1.0:
                cf = cf * 100
            self.decision_confidence_bar.setValue(int(max(0, min(100, cf))))
            self.decision_alternatives_label.setText(str(alternatives))
        except Exception as e:
            logger.debug(f"update_decision failed: {e}")

    def add_decision_history(self, decision: str, result: str,
                            confidence: float, timestamp: Optional[str] = None):
        """
        添加决策历史
        
        Args:
            decision: 决策内容
            result: 决策结果
            confidence: 置信度
            timestamp: 时间戳
        """
        row = self.decision_table.rowCount()
        self.decision_table.insertRow(row)
        
        self.decision_table.setItem(row, 0, QTableWidgetItem(
            timestamp or datetime.now().strftime("%H:%M:%S")
        ))
        self.decision_table.setItem(row, 1, QTableWidgetItem(decision[:30]))
        self.decision_table.setItem(row, 2, QTableWidgetItem(result))
        self.decision_table.setItem(row, 3, QTableWidgetItem(f"{confidence:.2f}"))
    
    def update_cognitive_status(self, load: float, attention: str,
                                depth: int, abilities: Dict[str, float]):
        """
        更新认知状态
        
        Args:
            load: 认知负载 (0-1)
            attention: 注意力焦点
            depth: 处理深度
            abilities: 能力状态 {"reasoning": 0.8, "learning": 0.7, ...}
        """
        self.cognitive_load_bar.setValue(int(load * 100))
        self.attention_focus_label.setText(attention)
        self.processing_depth_label.setText(str(depth))
        
        self.reasoning_ability_bar.setValue(
            int(abilities.get("reasoning", 1.0) * 100)
        )
        self.learning_ability_bar.setValue(
            int(abilities.get("learning", 1.0) * 100)
        )
        self.memory_ability_bar.setValue(
            int(abilities.get("memory", 1.0) * 100)
        )
    
    def update_metacognition(self, awareness: str, reflection_depth: int,
                           confidence_level: str):
        """
        更新元认知状态
        
        Args:
            awareness: 自我意识状态
            reflection_depth: 反思深度
            confidence_level: 置信水平
        """
        self.self_awareness_label.setText(awareness)
        self.reflection_depth_label.setText(str(reflection_depth))
        self.confidence_level_label.setText(confidence_level)
    
    def _on_step_selected(self, step_id: str):
        """
        步骤选择事件
        
        Args:
            step_id: 步骤ID
        """
        self.step_selected.emit(step_id)
        
        # 显示详情
        for node in self._cognition_chain:
            if node.node_id == step_id:
                self.reasoning_detail.setText(
                    f"类型: {node.step_type.value}\n"
                    f"置信度: {node.confidence:.2f}\n"
                    f"时间: {node.timestamp.strftime('%H:%M:%S')}\n"
                    f"状态: {node.status}\n\n"
                    f"内容:\n{node.content}"
                )
                break
    
    def _on_reasoning_item_selected(self, item: QTreeWidgetItem):
        """
        推理项选择事件
        
        Args:
            item: 选中的树项
        """
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data:
            self.step_selected.emit(data.get("id", ""))
    
    def clear_chain(self):
        """清空思维链"""
        self._cognition_chain.clear()
        self.chain_graph.clear_graph()
        self.reasoning_tree.clear()
        self.chain_info_label.setText("步骤: 0")
        self.reasoning_detail.clear()
    
    def _layout_chain(self):
        """布局思维链"""
        if self._cognition_chain:
            self.chain_graph.layout_tree(
                self._cognition_chain[0].node_id,
                x=0, y=50
            )
    
    def get_chain(self) -> List[Dict[str, Any]]:
        """
        获取思维链
        
        Returns:
            List[Dict]: 思维链数据
        """
        return [node.to_dict() for node in self._cognition_chain]
    
    def set_chain(self, chain_data: List[Dict[str, Any]]):
        """
        设置思维链
        
        Args:
            chain_data: 思维链数据
        """
        self.clear_chain()
        
        for data in chain_data:
            step_type = CognitionStepType(data.get("type", "reasoning"))
            self.add_cognition_step(
                step_type,
                data.get("content", ""),
                data.get("confidence", 1.0),
                data.get("parent_id")
            )
