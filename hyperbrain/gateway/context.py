"""
上下文管理器 - 管理会话和上下文信息
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
from collections import deque


@dataclass
class ConversationTurn:
    """对话轮次"""
    turn_id: str
    role: str
    content: str
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class ContextManager:
    """上下文管理器"""
    
    def __init__(self, max_history: int = 50):
        self.max_history = max_history
        self.turns: deque = deque(maxlen=max_history)
        self.session_data: Dict[str, Any] = {}
        self.current_turn_id = 0
        
    def add_turn(self, role: str, content: str, metadata: Optional[Dict] = None) -> str:
        """添加对话轮次"""
        self.current_turn_id += 1
        turn = ConversationTurn(
            turn_id=f"turn_{self.current_turn_id}",
            role=role,
            content=content,
            timestamp=datetime.now().timestamp(),
            metadata=metadata or {}
        )
        self.turns.append(turn)
        return turn.turn_id
    
    def get_history(self, limit: Optional[int] = None) -> List[ConversationTurn]:
        """获取对话历史"""
        if limit and limit > 0:
            return list(self.turns)[-limit:]
        return list(self.turns)
    
    def set_session_data(self, key: str, value: Any) -> None:
        """设置会话数据"""
        self.session_data[key] = value
        
    def get_session_data(self, key: str, default: Any = None) -> Any:
        """获取会话数据"""
        return self.session_data.get(key, default)
    
    def clear_history(self) -> None:
        """清空历史"""
        self.turns.clear()
        
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "turns": [
                {
                    "turn_id": t.turn_id,
                    "role": t.role,
                    "content": t.content,
                    "timestamp": t.timestamp,
                    "metadata": t.metadata
                }
                for t in self.turns
            ],
            "session_data": self.session_data,
            "current_turn_id": self.current_turn_id
        }
