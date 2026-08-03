"""
行为控制模块 (Behavior Control)

控制和管理系统自身的行为和反应。

功能：
- 控制自身行为和反应
- 行为策略选择
- 行为约束检查
- 行为一致性维护
- 异常行为处理
"""

import re
import uuid
from typing import Any, Callable, Dict, List, Optional, Set, Union
from datetime import datetime
from enum import Enum
from dataclasses import dataclass

from pydantic import BaseModel, Field, ConfigDict

from hyperbrain.core.logger import get_logger
from hyperbrain.core.config import get_config

logger = get_logger("execution.behavior")


class BehaviorType(str, Enum):
    """行为类型"""
    RESPOND = "respond"           # 响应
    ASK = "ask"                   # 询问
    EXECUTE = "execute"           # 执行
    REFUSE = "refuse"             # 拒绝
    CLARIFY = "clarify"           # 澄清
    DEFER = "defer"               # 推迟
    ESCALATE = "escalate"         # 升级


class BehaviorPolicy(str, Enum):
    """行为策略"""
    HELPFUL = "helpful"           # 乐于助人
    CAUTIOUS = "cautious"         # 谨慎
    DIRECT = "direct"             # 直接
    COLLABORATIVE = "collaborative"  # 协作
    FORMAL = "formal"             # 正式
    FRIENDLY = "friendly"         # 友好


class ConstraintType(str, Enum):
    """约束类型"""
    SAFETY = "safety"             # 安全
    ETHICAL = "ethical"           # 伦理
    LEGAL = "legal"               # 法律
    PRIVACY = "privacy"           # 隐私
    CAPABILITY = "capability"     # 能力
    RESOURCE = "resource"         # 资源


class BehaviorRule(BaseModel):
    """行为规则"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    constraint_type: ConstraintType = ConstraintType.SAFETY
    
    # 规则条件（关键词或模式）
    patterns: List[str] = Field(default_factory=list)
    
    # 规则动作
    action: str = "block"  # block, warn, allow, log
    
    # 优先级
    priority: int = Field(default=5, ge=1, le=10)
    
    # 是否启用
    enabled: bool = True
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def matches(self, text: str) -> bool:
        """检查文本是否匹配规则"""
        text_lower = text.lower()
        for pattern in self.patterns:
            if pattern.lower() in text_lower:
                return True
            # 支持简单正则
            try:
                if re.search(pattern, text, re.IGNORECASE):
                    return True
            except re.error:
                pass
        return False


class BehaviorDecision(BaseModel):
    """行为决策"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    behavior_type: BehaviorType = BehaviorType.RESPOND
    policy: BehaviorPolicy = BehaviorPolicy.HELPFUL
    
    # 决策理由
    reasoning: str = ""
    
    # 约束检查
    constraints_checked: List[ConstraintType] = Field(default_factory=list)
    constraints_violated: List[ConstraintType] = Field(default_factory=list)
    
    # 置信度
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    
    # 建议的响应
    suggested_response: Optional[str] = None
    
    # 是否需要确认
    requires_confirmation: bool = False
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "behavior_type": self.behavior_type.value,
            "policy": self.policy.value,
            "reasoning": self.reasoning,
            "constraints_violated": [c.value for c in self.constraints_violated],
            "confidence": self.confidence,
            "requires_confirmation": self.requires_confirmation
        }


class BehaviorProfile(BaseModel):
    """行为画像"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    name: str = "default"
    default_policy: BehaviorPolicy = BehaviorPolicy.HELPFUL
    
    # 行为偏好
    response_style: str = "balanced"  # concise, detailed, balanced
    formality_level: float = Field(default=0.5, ge=0.0, le=1.0)
    proactivity: float = Field(default=0.5, ge=0.0, le=1.0)
    
    # 约束配置
    strict_mode: bool = False
    max_response_length: int = 2000
    allowed_topics: List[str] = Field(default_factory=list)
    blocked_topics: List[str] = Field(default_factory=list)
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConstraintChecker:
    """约束检查器"""
    
    def __init__(self):
        self._rules: List[BehaviorRule] = []
        self._initialize_default_rules()
        logger.info("ConstraintChecker initialized")
    
    def _initialize_default_rules(self) -> None:
        """初始化默认规则"""
        # 安全规则
        self.add_rule(BehaviorRule(
            name="harmful_content",
            description="阻止有害内容",
            constraint_type=ConstraintType.SAFETY,
            patterns=["伤害", "攻击", "暴力", "自残", "harm", "attack", "violence"],
            action="block",
            priority=1
        ))
        
        # 隐私规则
        self.add_rule(BehaviorRule(
            name="personal_info",
            description="保护个人信息",
            constraint_type=ConstraintType.PRIVACY,
            patterns=["密码", "身份证号", "银行卡", "password", "ssn", "credit card"],
            action="warn",
            priority=2
        ))
        
        # 法律规则
        self.add_rule(BehaviorRule(
            name="illegal_activity",
            description="阻止非法活动",
            constraint_type=ConstraintType.LEGAL,
            patterns=["非法", "犯罪", "盗窃", "illegal", "crime", "steal"],
            action="block",
            priority=1
        ))
        
        # 伦理规则
        self.add_rule(BehaviorRule(
            name="ethical_concerns",
            description="伦理关切",
            constraint_type=ConstraintType.ETHICAL,
            patterns=["欺骗", "操纵", "歧视", "deceive", "manipulate", "discriminate"],
            action="warn",
            priority=3
        ))
    
    def add_rule(self, rule: BehaviorRule) -> None:
        """添加规则"""
        self._rules.append(rule)
        self._rules.sort(key=lambda r: r.priority)
    
    def remove_rule(self, rule_id: str) -> bool:
        """移除规则"""
        for i, rule in enumerate(self._rules):
            if rule.id == rule_id:
                self._rules.pop(i)
                return True
        return False
    
    def check(self, text: str) -> Dict[ConstraintType, List[BehaviorRule]]:
        """
        检查约束
        
        Args:
            text: 输入文本
            
        Returns:
            Dict: 触发的规则
        """
        violations = {}
        
        for rule in self._rules:
            if not rule.enabled:
                continue
            
            if rule.matches(text):
                if rule.constraint_type not in violations:
                    violations[rule.constraint_type] = []
                violations[rule.constraint_type].append(rule)
        
        return violations
    
    def get_rules(self, 
                  constraint_type: Optional[ConstraintType] = None) -> List[BehaviorRule]:
        """获取规则"""
        if constraint_type:
            return [r for r in self._rules if r.constraint_type == constraint_type]
        return self._rules.copy()


class PolicySelector:
    """策略选择器"""
    
    def __init__(self):
        self._policies: Dict[str, BehaviorPolicy] = {
            "default": BehaviorPolicy.HELPFUL,
            "coding": BehaviorPolicy.DIRECT,
            "conversation": BehaviorPolicy.FRIENDLY,
            "analysis": BehaviorPolicy.CAUTIOUS,
            "creative": BehaviorPolicy.COLLABORATIVE
        }
        logger.info("PolicySelector initialized")
    
    def select_policy(self, 
                      context: Optional[Dict[str, Any]] = None) -> BehaviorPolicy:
        """
        选择策略
        
        Args:
            context: 上下文
            
        Returns:
            BehaviorPolicy: 选择的策略
        """
        if not context:
            return self._policies["default"]
        
        # 基于意图选择
        intent = context.get("intent", "")
        
        intent_policy_map = {
            "code_request": BehaviorPolicy.DIRECT,
            "question": BehaviorPolicy.HELPFUL,
            "greeting": BehaviorPolicy.FRIENDLY,
            "request": BehaviorPolicy.HELPFUL,
            "command": BehaviorPolicy.DIRECT
        }
        
        return intent_policy_map.get(intent, self._policies["default"])
    
    def set_policy(self, scenario: str, policy: BehaviorPolicy) -> None:
        """设置场景策略"""
        self._policies[scenario] = policy


class BehaviorController:
    """
    行为控制器
    
    控制系统行为的决策和执行。
    """
    
    def __init__(self, profile: Optional[BehaviorProfile] = None):
        self.config = get_config()
        self.profile = profile or BehaviorProfile()
        self.constraint_checker = ConstraintChecker()
        self.policy_selector = PolicySelector()
        
        self._decision_history: List[BehaviorDecision] = []
        self._behavior_log: List[Dict[str, Any]] = []
        
        logger.info("BehaviorController initialized")
    
    def decide(self,
               input_text: str,
               context: Optional[Dict[str, Any]] = None) -> BehaviorDecision:
        """
        做出行为决策
        
        Args:
            input_text: 输入文本
            context: 上下文
            
        Returns:
            BehaviorDecision: 行为决策
        """
        # 1. 约束检查
        violations = self.constraint_checker.check(input_text)
        
        # 2. 选择策略
        policy = self.policy_selector.select_policy(context)
        
        # 3. 确定行为类型
        behavior_type = self._determine_behavior_type(input_text, violations, context)
        
        # 4. 构建决策
        decision = BehaviorDecision(
            behavior_type=behavior_type,
            policy=policy,
            constraints_checked=list(violations.keys()),
            constraints_violated=list(violations.keys()) if violations else []
        )
        
        # 5. 生成理由
        decision.reasoning = self._generate_reasoning(decision, violations)
        
        # 6. 确定是否需要确认
        decision.requires_confirmation = self._needs_confirmation(decision)
        
        # 7. 生成建议响应
        decision.suggested_response = self._generate_suggested_response(
            decision, input_text
        )
        
        self._decision_history.append(decision)
        
        self._log_behavior("decide", {
            "input": input_text[:100],
            "decision": decision.to_dict()
        })
        
        return decision
    
    def _determine_behavior_type(
        self,
        input_text: str,
        violations: Dict[ConstraintType, List[BehaviorRule]],
        context: Optional[Dict[str, Any]]
    ) -> BehaviorType:
        """确定行为类型"""
        # 如果有严重违规，拒绝
        if violations:
            for rules in violations.values():
                for rule in rules:
                    if rule.action == "block":
                        return BehaviorType.REFUSE
        
        # 基于意图判断
        intent = context.get("intent", "") if context else ""
        
        intent_behavior_map = {
            "question": BehaviorType.RESPOND,
            "request": BehaviorType.EXECUTE,
            "command": BehaviorType.EXECUTE,
            "greeting": BehaviorType.RESPOND,
            "code_request": BehaviorType.EXECUTE,
            "gratitude": BehaviorType.RESPOND
        }
        
        return intent_behavior_map.get(intent, BehaviorType.RESPOND)
    
    def _generate_reasoning(
        self,
        decision: BehaviorDecision,
        violations: Dict[ConstraintType, List[BehaviorRule]]
    ) -> str:
        """生成决策理由"""
        parts = []
        
        if violations:
            parts.append(f"检测到 {len(violations)} 类约束违规")
            for constraint_type, rules in violations.items():
                rule_names = [r.name for r in rules]
                parts.append(f"  - {constraint_type.value}: {', '.join(rule_names)}")
        
        parts.append(f"选择策略: {decision.policy.value}")
        parts.append(f"行为类型: {decision.behavior_type.value}")
        
        return "; ".join(parts)
    
    def _needs_confirmation(self, decision: BehaviorDecision) -> bool:
        """判断是否需要确认"""
        # 高风险操作需要确认
        if decision.constraints_violated:
            for constraint in decision.constraints_violated:
                if constraint in (ConstraintType.SAFETY, ConstraintType.LEGAL):
                    return True
        
        # 执行类操作可能需要确认
        if decision.behavior_type == BehaviorType.EXECUTE:
            return self.profile.strict_mode
        
        return False
    
    def _generate_suggested_response(
        self,
        decision: BehaviorDecision,
        input_text: str
    ) -> Optional[str]:
        """生成建议响应"""
        if decision.behavior_type == BehaviorType.REFUSE:
            return "我无法执行此操作，因为它违反了相关约束规则。"
        
        if decision.behavior_type == BehaviorType.CLARIFY:
            return "我需要更多信息来理解您的请求。"
        
        return None
    
    def check_constraints(self, text: str) -> Dict[str, Any]:
        """
        检查约束
        
        Args:
            text: 文本
            
        Returns:
            Dict: 检查结果
        """
        violations = self.constraint_checker.check(text)
        
        return {
            "is_safe": len(violations) == 0,
            "violations": {
                k.value: [r.name for r in v]
                for k, v in violations.items()
            },
            "total_violations": sum(len(v) for v in violations.values())
        }
    
    def set_profile(self, profile: BehaviorProfile) -> None:
        """设置行为画像"""
        self.profile = profile
        logger.info(f"Behavior profile set to: {profile.name}")
    
    def add_constraint_rule(self, rule: BehaviorRule) -> None:
        """添加约束规则"""
        self.constraint_checker.add_rule(rule)
    
    def remove_constraint_rule(self, rule_id: str) -> bool:
        """移除约束规则"""
        return self.constraint_checker.remove_rule(rule_id)
    
    def get_decision_history(self, limit: int = 100) -> List[BehaviorDecision]:
        """获取决策历史"""
        return self._decision_history[-limit:]
    
    def get_behavior_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取行为日志"""
        return self._behavior_log[-limit:]
    
    def _log_behavior(self, action: str, details: Dict[str, Any]) -> None:
        """记录行为"""
        self._behavior_log.append({
            "action": action,
            "timestamp": datetime.now().isoformat(),
            "details": details
        })
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_decisions = len(self._decision_history)
        
        if total_decisions == 0:
            return {"total_decisions": 0}
        
        behavior_counts = {}
        for d in self._decision_history:
            bt = d.behavior_type.value
            behavior_counts[bt] = behavior_counts.get(bt, 0) + 1
        
        violation_count = sum(
            1 for d in self._decision_history if d.constraints_violated
        )
        
        return {
            "total_decisions": total_decisions,
            "behavior_distribution": behavior_counts,
            "violation_rate": violation_count / total_decisions,
            "total_rules": len(self.constraint_checker.get_rules()),
            "profile": self.profile.name
        }
    
    def reset(self) -> None:
        """重置控制器"""
        self._decision_history.clear()
        self._behavior_log.clear()
        logger.info("BehaviorController reset")
