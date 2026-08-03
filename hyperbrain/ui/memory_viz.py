"""
记忆可视化

直观展示记忆内容和结构，包括记忆类型分类、关联图、搜索等
"""

import random
from typing import Optional, Dict, Any, List
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QProgressBar, QTreeWidget,
    QTreeWidgetItem, QGroupBox, QLineEdit,
    QPushButton, QTabWidget, QTableWidget,
    QTableWidgetItem, QSplitter, QComboBox,
    QSpinBox, QFormLayout, QHeaderView,
    QGraphicsView, QGraphicsScene, QGraphicsItem,
    QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRectF
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush,
    QFont, QRadialGradient, QLinearGradient
)

from hyperbrain.core.logger import get_logger
from hyperbrain.ui.themes import theme_manager

logger = get_logger("ui.memory_viz")


class MemoryGraphView(QGraphicsView):
    """
    记忆关联图视图
    
    使用图形节点展示记忆之间的关联关系
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
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        
        self._nodes: Dict[str, Dict[str, Any]] = {}
        self._edges: List[tuple] = []
        
        self._setup_scene()
    
    def _setup_scene(self):
        """设置场景背景"""
        colors = theme_manager.colors
        self.scene.setBackgroundBrush(QColor(colors["memory_graph_bg"]))
    
    def clear_graph(self):
        """清空图形"""
        self.scene.clear()
        self._nodes.clear()
        self._edges.clear()
    
    def add_node(self, node_id: str, label: str, node_type: str = "default",
                 x: float = 0, y: float = 0, size: float = 30):
        """
        添加节点
        
        Args:
            node_id: 节点唯一标识
            label: 显示标签
            node_type: 节点类型
            x: X坐标
            y: Y坐标
            size: 节点大小
        """
        colors = theme_manager.colors
        
        type_colors = {
            "episodic": QColor("#ff7043"),
            "semantic": QColor("#42a5f5"),
            "procedural": QColor("#66bb6a"),
            "emotional": QColor("#ab47bc"),
            "default": QColor(colors["accent"])
        }
        
        color = type_colors.get(node_type, type_colors["default"])
        
        # 绘制节点
        ellipse = self.scene.addEllipse(
            x - size/2, y - size/2, size, size,
            QPen(color, 2),
            QBrush(color.darker(120))
        )
        ellipse.setData(0, node_id)
        
        # 添加标签
        text = self.scene.addText(label, QFont("Microsoft YaHei", 10))
        text.setDefaultTextColor(QColor(colors["text_primary"]))
        text.setPos(x - text.boundingRect().width()/2, y + size/2 + 5)
        
        self._nodes[node_id] = {
            "label": label,
            "type": node_type,
            "x": x,
            "y": y,
            "size": size,
            "item": ellipse
        }
    
    def add_edge(self, from_id: str, to_id: str, strength: float = 1.0):
        """
        添加边
        
        Args:
            from_id: 起始节点ID
            to_id: 目标节点ID
            strength: 关联强度 (0-1)
        """
        if from_id not in self._nodes or to_id not in self._nodes:
            return
        
        from_node = self._nodes[from_id]
        to_node = self._nodes[to_id]
        
        colors = theme_manager.colors
        
        alpha = int(255 * strength)
        color = QColor(colors["cognition_edge"])
        color.setAlpha(alpha)
        
        pen = QPen(color, 1 + strength * 2)
        pen.setStyle(Qt.PenStyle.SolidLine)
        
        line = self.scene.addLine(
            from_node["x"], from_node["y"],
            to_node["x"], to_node["y"],
            pen
        )
        
        self._edges.append((from_id, to_id, strength, line))
    
    def auto_layout(self):
        """自动布局节点"""
        if not self._nodes:
            return
        
        # 简单的圆形布局
        import math
        
        count = len(self._nodes)
        radius = 150
        center_x, center_y = 0, 0
        
        for i, (node_id, node) in enumerate(self._nodes.items()):
            angle = 2 * math.pi * i / count
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            
            node["x"] = x
            node["y"] = y
            
            # 更新位置
            node["item"].setRect(x - node["size"]/2, y - node["size"]/2,
                                node["size"], node["size"])
        
        self.scene.setSceneRect(-250, -250, 500, 500)
    
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


class MemoryVisualizer(QWidget):
    """
    记忆可视化组件
    
    功能：
    1. 记忆类型分类显示
    2. 记忆关联图
    3. 记忆搜索功能
    4. 记忆详情查看
    5. 记忆统计图表
    
    Signals:
        memory_selected: 选择记忆时触发
    """
    
    memory_selected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._memories: List[Dict[str, Any]] = []
        self._setup_ui()
        
        # 定时刷新
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(5000)
        
        logger.info("MemoryVisualizer initialized")
    
    def _setup_ui(self):
        """设置UI布局"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # 概览标签页
        self.overview_tab = self._create_overview_tab()
        self.tab_widget.addTab(self.overview_tab, "概览")
        
        # 记忆列表标签页
        self.list_tab = self._create_list_tab()
        self.tab_widget.addTab(self.list_tab, "记忆列表")
        
        # 关联图标签页
        self.graph_tab = self._create_graph_tab()
        self.tab_widget.addTab(self.graph_tab, "关联图")
        
        # 统计标签页
        self.stats_tab = self._create_stats_tab()
        self.tab_widget.addTab(self.stats_tab, "统计")
        
        layout.addWidget(self.tab_widget)
    
    def _create_overview_tab(self) -> QWidget:
        """创建概览标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        
        # 短期记忆组
        stm_group = QGroupBox("短期记忆 (工作记忆)")
        stm_layout = QVBoxLayout(stm_group)
        
        stm_form = QFormLayout()
        
        self.stm_capacity_bar = QProgressBar()
        self.stm_capacity_bar.setRange(0, 100)
        self.stm_capacity_bar.setValue(0)
        stm_form.addRow("容量使用:", self.stm_capacity_bar)
        
        self.stm_items_label = QLabel("0 / 0")
        stm_form.addRow("条目数:", self.stm_items_label)
        
        self.stm_decay_label = QLabel("正常")
        stm_form.addRow("衰减状态:", self.stm_decay_label)
        
        stm_layout.addLayout(stm_form)
        layout.addWidget(stm_group)
        
        # 长期记忆组
        ltm_group = QGroupBox("长期记忆")
        ltm_layout = QVBoxLayout(ltm_group)
        
        ltm_form = QFormLayout()
        
        self.ltm_count_label = QLabel("0")
        ltm_form.addRow("总记忆数:", self.ltm_count_label)
        
        self.ltm_index_label = QLabel("未构建")
        ltm_form.addRow("索引状态:", self.ltm_index_label)
        
        self.ltm_consolidation_label = QLabel("正常")
        ltm_form.addRow("巩固状态:", self.ltm_consolidation_label)
        
        ltm_layout.addLayout(ltm_form)
        layout.addWidget(ltm_group)
        
        # 记忆类型分布
        types_group = QGroupBox("记忆类型分布")
        types_layout = QVBoxLayout(types_group)
        
        self.types_table = QTableWidget()
        self.types_table.setColumnCount(3)
        self.types_table.setHorizontalHeaderLabels(["类型", "数量", "占比"])
        self.types_table.horizontalHeader().setStretchLastSection(True)
        self.types_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        types_layout.addWidget(self.types_table)
        
        layout.addWidget(types_group)
        layout.addStretch()
        
        return widget
    
    def _create_list_tab(self) -> QWidget:
        """创建记忆列表标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)
        
        # 搜索区域
        search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索记忆...")
        self.search_input.returnPressed.connect(self._search_memories)
        search_layout.addWidget(self.search_input)
        
        self.search_button = QPushButton("搜索")
        self.search_button.clicked.connect(self._search_memories)
        search_layout.addWidget(self.search_button)
        
        self.search_type = QComboBox()
        self.search_type.addItems(["全部", "情景记忆", "语义记忆", "程序记忆", "情感记忆"])
        search_layout.addWidget(self.search_type)
        
        layout.addLayout(search_layout)
        
        # 记忆树
        self.memory_tree = QTreeWidget()
        self.memory_tree.setHeaderLabels(["内容", "类型", "重要性", "时间", "状态"])
        self.memory_tree.setColumnWidth(0, 300)
        self.memory_tree.itemClicked.connect(self._on_memory_selected)
        layout.addWidget(self.memory_tree)
        
        # 详情区域
        self.detail_group = QGroupBox("记忆详情")
        detail_layout = QVBoxLayout(self.detail_group)
        
        self.detail_label = QLabel("选择记忆查看详情")
        self.detail_label.setWordWrap(True)
        detail_layout.addWidget(self.detail_label)
        
        layout.addWidget(self.detail_group)
        
        return widget
    
    def _create_graph_tab(self) -> QWidget:
        """创建关联图标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 控制按钮
        control_layout = QHBoxLayout()
        
        self.layout_button = QPushButton("自动布局")
        self.layout_button.clicked.connect(self._auto_layout_graph)
        control_layout.addWidget(self.layout_button)
        
        self.clear_graph_button = QPushButton("清空")
        self.clear_graph_button.clicked.connect(self._clear_graph)
        control_layout.addWidget(self.clear_graph_button)
        
        control_layout.addStretch()
        
        self.graph_info_label = QLabel("节点: 0 | 连接: 0")
        control_layout.addWidget(self.graph_info_label)
        
        layout.addLayout(control_layout)
        
        # 图形视图
        self.graph_view = MemoryGraphView()
        self.graph_view.node_selected.connect(self._on_graph_node_selected)
        layout.addWidget(self.graph_view)
        
        return widget
    
    def _create_stats_tab(self) -> QWidget:
        """创建统计标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        
        # 记忆统计
        stats_group = QGroupBox("记忆统计")
        stats_layout = QFormLayout(stats_group)
        
        self.total_memories_label = QLabel("0")
        stats_layout.addRow("总记忆数:", self.total_memories_label)
        
        self.avg_importance_label = QLabel("0.0")
        stats_layout.addRow("平均重要性:", self.avg_importance_label)
        
        self.retrieval_count_label = QLabel("0")
        stats_layout.addRow("检索次数:", self.retrieval_count_label)
        
        self.storage_efficiency_label = QLabel("100%")
        stats_layout.addRow("存储效率:", self.storage_efficiency_label)
        
        layout.addWidget(stats_group)
        
        # 访问频率
        access_group = QGroupBox("访问频率 Top 10")
        access_layout = QVBoxLayout(access_group)
        
        self.access_table = QTableWidget()
        self.access_table.setColumnCount(3)
        self.access_table.setHorizontalHeaderLabels(["记忆", "访问次数", "最后访问"])
        self.access_table.horizontalHeader().setStretchLastSection(True)
        access_layout.addWidget(self.access_table)
        
        layout.addWidget(access_group)
        
        # 时间分布
        time_group = QGroupBox("时间分布")
        time_layout = QVBoxLayout(time_group)
        
        self.time_distribution_label = QLabel("暂无数据")
        time_layout.addWidget(self.time_distribution_label)
        
        layout.addWidget(time_group)
        layout.addStretch()
        
        return widget
    
    def update_short_term_stats(self, current_size: int, capacity: int,
                                decay_status: str = "正常"):
        """
        更新短期记忆统计
        
        Args:
            current_size: 当前条目数
            capacity: 容量上限
            decay_status: 衰减状态
        """
        percentage = int((current_size / capacity) * 100) if capacity > 0 else 0
        self.stm_capacity_bar.setValue(min(percentage, 100))
        self.stm_items_label.setText(f"{current_size} / {capacity}")
        self.stm_decay_label.setText(decay_status)
    
    def update_long_term_stats(self, total_memories: int, index_built: bool,
                               consolidation_status: str = "正常"):
        """
        更新长期记忆统计

        Args:
            total_memories: 总记忆数
            index_built: FAISS 索引是否构建
            consolidation_status: 巩固状态
        """
        self.ltm_count_label.setText(str(total_memories))
        if total_memories == 0:
            self.ltm_index_label.setText("无数据")
        elif index_built:
            self.ltm_index_label.setText("已构建（FAISS）")
        else:
            # 当有数据时，即使没有 FAISS，暴力搜索索引也已构建
            self.ltm_index_label.setText("已构建（暴力搜索）")
        self.ltm_consolidation_label.setText(consolidation_status)
    
    def update_memory_types(self, types_data: Dict[str, int]):
        """
        更新记忆类型分布
        
        Args:
            types_data: 类型数据 {类型: 数量}
        """
        total = sum(types_data.values()) if types_data else 0
        
        self.types_table.setRowCount(len(types_data))
        
        type_names = {
            "episodic": "情景记忆",
            "semantic": "语义记忆",
            "procedural": "程序记忆",
            "emotional": "情感记忆",
            "declarative": "陈述记忆",
            "sensory": "感觉记忆",
            "working": "工作记忆",
            "short_term": "短期记忆",
            "long_term": "长期记忆"
        }
        
        for i, (mem_type, count) in enumerate(types_data.items()):
            percentage = f"{count/total*100:.1f}%" if total > 0 else "0%"
            
            self.types_table.setItem(i, 0, QTableWidgetItem(type_names.get(mem_type, mem_type)))
            self.types_table.setItem(i, 1, QTableWidgetItem(str(count)))
            self.types_table.setItem(i, 2, QTableWidgetItem(percentage))
    
    def update_memory_list(self, memories: List[Dict[str, Any]]):
        """
        更新记忆列表
        
        Args:
            memories: 记忆数据列表
        """
        self._memories = memories
        self.memory_tree.clear()
        
        type_names = {
            "episodic": "情景记忆",
            "semantic": "语义记忆",
            "procedural": "程序记忆",
            "emotional": "情感记忆"
        }
        
        for memory in memories:
            mem_type = memory.get("type", "") or memory.get("memory_type", "")
            item = QTreeWidgetItem([
                memory.get("content", "")[:50] + "...",
                type_names.get(mem_type, mem_type),
                f"{memory.get('importance', 0):.2f}",
                memory.get("timestamp", "") or memory.get("created_at", ""),
                memory.get("status", "活跃")
            ])
            item.setData(0, Qt.ItemDataRole.UserRole, memory)
            self.memory_tree.addTopLevelItem(item)
    
    def update_graph(self, nodes: List[Dict[str, Any]], edges: List[tuple]):
        """
        更新关联图
        
        Args:
            nodes: 节点列表 [{id, label, type, x, y, size}, ...]
            edges: 边列表 [(from_id, to_id, strength), ...]
        """
        self.graph_view.clear_graph()
        
        for node in nodes:
            self.graph_view.add_node(
                node["id"],
                node["label"],
                node.get("type", "default"),
                node.get("x", 0),
                node.get("y", 0),
                node.get("size", 30)
            )
        
        for edge in edges:
            self.graph_view.add_edge(edge[0], edge[1], edge[2])
        
        self.graph_info_label.setText(f"节点: {len(nodes)} | 连接: {len(edges)}")
    
    def update_stats(self, stats: Dict[str, Any]):
        """
        更新统计数据
        
        Args:
            stats: 统计数据
        """
        self.total_memories_label.setText(str(stats.get("total", 0)))
        self.avg_importance_label.setText(f"{stats.get('avg_importance', 0):.2f}")
        self.retrieval_count_label.setText(str(stats.get("retrieval_count", 0)))
        
        efficiency = stats.get("storage_efficiency", 1.0)
        self.storage_efficiency_label.setText(f"{efficiency*100:.1f}%")
        
        # 更新访问频率表
        access_data = stats.get("access_frequency", [])
        self.access_table.setRowCount(min(len(access_data), 10))
        
        for i, item in enumerate(access_data[:10]):
            self.access_table.setItem(i, 0, QTableWidgetItem(str(item.get("content", ""))[:30]))
            self.access_table.setItem(i, 1, QTableWidgetItem(str(item.get("count", 0))))
            self.access_table.setItem(i, 2, QTableWidgetItem(str(item.get("last_access", ""))))
    
    def _search_memories(self):
        """搜索记忆"""
        query = self.search_input.text().strip()
        mem_type = self.search_type.currentText()
        
        if not query:
            return
        
        logger.info(f"Searching memories: {query}, type: {mem_type}")
        
        # 过滤记忆
        filtered = []
        for memory in self._memories:
            if query.lower() in memory.get("content", "").lower():
                if mem_type == "全部" or memory.get("type", "") == mem_type:
                    filtered.append(memory)
        
        self.update_memory_list(filtered)
    
    def _on_memory_selected(self, item: QTreeWidgetItem):
        """
        记忆选择事件
        
        Args:
            item: 选中的树项
        """
        memory = item.data(0, Qt.ItemDataRole.UserRole)
        if memory:
            content = memory.get("content", "")
            self.detail_label.setText(content)
            self.memory_selected.emit(str(memory.get("id", "")))
    
    def _on_graph_node_selected(self, node_id: str):
        """
        图形节点选择事件
        
        Args:
            node_id: 节点ID
        """
        self.memory_selected.emit(node_id)
    
    def _auto_layout_graph(self):
        """自动布局关联图"""
        self.graph_view.auto_layout()
    
    def _clear_graph(self):
        """清空关联图"""
        self.graph_view.clear_graph()
        self.graph_info_label.setText("节点: 0 | 连接: 0")
    
    def refresh_data(self):
        """
        刷新所有标签页的数据

        包括：
        - 概览（短期记忆、长期记忆、记忆类型）
        - 列表（最近 100 条记忆）
        - 关联图（记忆节点和连接）
        - 统计（总记忆数、平均重要性、检索次数等）
        """
        try:
            if hasattr(self, 'brain') and self.brain and hasattr(self.brain, 'memory'):
                memory_manager = self.brain.memory
            else:
                from hyperbrain.layers.memory.memory_manager import MemoryManager
                from hyperbrain.core.config import get_config
                config = get_config()
                memory_manager = MemoryManager(
                    db_path=config.memory.db_path,
                    vector_dim=config.memory.vector_dim,
                    enable_faiss=False
                )

            stats = memory_manager.get_stats()
            stm_stats = stats.get("working_memory", {})
            # WorkingMemory.get_stats() 返回 current_chunks（条数）和 current_size（总 size）
            # 优先使用 current_chunks（条数），因为 UI 显示"条目数"
            current_chunks = stm_stats.get("current_chunks", 0)
            if current_chunks == 0:
                # 回退：current_size（如果使用 ShortTermMemory）
                current_chunks = stm_stats.get("current_size", 0)
            capacity = stm_stats.get("capacity", 7)
            # 如果 working_memory 为空但 sensory_memory 有数据，回退到 sensory
            if current_chunks == 0:
                sensory_stats = stats.get("sensory_memory", {})
                current_chunks = sensory_stats.get("current_size", 0)
                capacity = sensory_stats.get("capacity", capacity)
            self.update_short_term_stats(current_chunks, capacity)
            ltm_stats = stats.get("long_term_memory", {})
            self.update_long_term_stats(
                ltm_stats.get("total_memories", 0),
                ltm_stats.get("faiss_enabled", False)
            )
            self.update_memory_types(ltm_stats.get("by_type", {}))

            # 1. 列表：最近 100 条记忆
            try:
                ltm = memory_manager.long_term_memory
                all_memories = ltm.get_all_memories(limit=100)
                mem_dicts = []
                for m in all_memories:
                    try:
                        mem_dicts.append(m.to_dict())
                    except Exception:
                        # 回退：手动构造字典
                        mem_dicts.append({
                            "content": str(m.content)[:100],
                            "type": getattr(m, 'memory_type', 'declarative'),
                            "importance": getattr(m, 'importance', 0.5),
                            "timestamp": str(getattr(m, 'created_at', '')),
                            "status": "活跃"
                        })
                self.set_memories(mem_dicts)
            except Exception as e:
                logger.debug(f"Memory list refresh failed: {e}")

            # 2. 关联图：节点和边
            try:
                nodes, edges = self._build_graph_data(all_memories if 'all_memories' in dir() else [])
                self.update_graph(nodes, edges)
            except Exception as e:
                logger.debug(f"Memory graph refresh failed: {e}")

            # 3. 统计：构建统计字典
            try:
                stats_data = self._build_stats_data(memory_manager, stats)
                self.update_stats(stats_data)
            except Exception as e:
                logger.debug(f"Memory stats refresh failed: {e}")
        except Exception as e:
            logger.debug(f"Memory refresh failed: {e}")

    def _build_graph_data(self, memories: List[Any]) -> tuple:
        """
        构建关联图数据

        从记忆列表中提取节点和边：
        - 节点：每个记忆为一个节点
        - 边：相同类型的记忆相互连接（最多 3 个邻居）
        """
        nodes: List[Dict[str, Any]] = []
        edges: List[tuple] = []

        # 限制最多 50 个节点
        memories = memories[:50]

        # 类型分组用于创建连接
        type_groups: Dict[str, List[str]] = {}
        for m in memories:
            mem_id = m.id
            mem_type = "declarative"
            try:
                if hasattr(m, 'memory_type'):
                    mem_type = m.memory_type.value if hasattr(m.memory_type, 'value') else str(m.memory_type)
            except Exception:
                pass

            # 节点
            content_str = str(m.content)[:30] if m.content else "empty"
            nodes.append({
                "id": mem_id,
                "label": content_str,
                "type": mem_type,
                "importance": getattr(m, 'importance', 0.5)
            })

            # 按类型分组
            type_groups.setdefault(mem_type, []).append(mem_id)

        # 边：相同类型的记忆相互连接
        for mem_type, mem_ids in type_groups.items():
            if len(mem_ids) > 1:
                for i in range(min(len(mem_ids) - 1, 3)):
                    edges.append((mem_ids[0], mem_ids[i + 1]))

        return nodes, edges

    def _build_stats_data(
        self,
        memory_manager: Any,
        stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        构建统计数据

        包含：
        - total: 总记忆数
        - avg_importance: 平均重要性
        - retrieval_count: 检索次数
        - storage_efficiency: 存储效率
        - access_frequency: 访问频率 Top 10
        """
        ltm_stats = stats.get("long_term_memory", {})
        total = ltm_stats.get("total_memories", 0)

        # 平均重要性：从数据库查询
        avg_importance = 0.0
        try:
            with memory_manager.long_term_memory._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT AVG(importance) FROM long_term_memories")
                row = cursor.fetchone()
                if row and row[0] is not None:
                    avg_importance = float(row[0])
        except Exception:
            pass

        # 检索次数：从长时记忆的 stats 中获取（如果有）
        retrieval_count = 0
        try:
            if hasattr(memory_manager.long_term_memory, '_retrieval_count'):
                retrieval_count = memory_manager.long_term_memory._retrieval_count
            elif hasattr(memory_manager.long_term_memory, 'get_retrieval_stats'):
                retrieval_count = memory_manager.long_term_memory.get_retrieval_stats()
        except Exception:
            pass

        # 存储效率：数据库大小 vs 实际记录数
        storage_efficiency = 1.0
        try:
            import os
            from hyperbrain.core.config import get_config
            config = get_config()
            db_path = config.memory.db_path
            if os.path.exists(db_path) and total > 0:
                file_size_mb = os.path.getsize(db_path) / (1024 * 1024)
                storage_efficiency = min(1.0, (total / 1000) / max(file_size_mb, 0.1))
        except Exception:
            pass

        # 访问频率 Top 10
        access_frequency: List[Dict[str, Any]] = []
        try:
            with memory_manager.long_term_memory._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT content, access_count, last_accessed
                    FROM long_term_memories
                    WHERE access_count > 0
                    ORDER BY access_count DESC
                    LIMIT 10
                """)
                for row in cursor.fetchall():
                    access_frequency.append({
                        "content": str(row[0])[:30] if row[0] else "",
                        "count": row[1] or 0,
                        "last_access": str(row[2] or "")
                    })
        except Exception:
            pass

        return {
            "total": total,
            "avg_importance": avg_importance,
            "retrieval_count": retrieval_count,
            "storage_efficiency": storage_efficiency,
            "access_frequency": access_frequency,
        }
    
    def set_memories(self, memories: List[Dict[str, Any]]):
        """
        设置记忆数据
        
        Args:
            memories: 记忆数据列表
        """
        self._memories = memories
        self.update_memory_list(memories)
