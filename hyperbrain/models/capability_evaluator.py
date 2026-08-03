"""
模型能力评估

评估各模型能力、性能基准测试、质量评分、能力矩阵生成和动态评估更新。
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from hyperbrain.core.logger import get_logger
from .base import BaseModel, ChatMessage, ModelCapability, ModelProvider, ModelResponse, TaskType

logger = get_logger("models.capability_evaluator")


@dataclass
class BenchmarkResult:
    """基准测试结果
    
    Attributes:
        task_type: 任务类型
        score: 得分 (0-100)
        latency_ms: 延迟（毫秒）
        tokens_used: 使用 token 数
        response_quality: 响应质量评分 (0-100)
        accuracy: 准确性评分 (0-100)
        metadata: 额外元数据
    """
    task_type: str
    score: float
    latency_ms: float
    tokens_used: int
    response_quality: float = 0.0
    accuracy: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelEvaluation:
    """模型评估结果
    
    Attributes:
        model_name: 模型名称
        provider: 提供商
        overall_score: 综合评分
        benchmarks: 基准测试列表
        capabilities: 能力评分
        evaluated_at: 评估时间
        version: 评估版本
    """
    model_name: str
    provider: str
    overall_score: float
    benchmarks: List[BenchmarkResult]
    capabilities: Dict[str, float]
    evaluated_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0"


# 基准测试用例
_BENCHMARK_CASES: Dict[str, List[Dict[str, Any]]] = {
    "chat": [
        {
            "name": "basic_conversation",
            "messages": [
                ChatMessage.system("You are a helpful assistant."),
                ChatMessage.user("What is the capital of France?")
            ],
            "expected_keywords": ["Paris"],
            "weight": 1.0
        },
        {
            "name": "multi_turn",
            "messages": [
                ChatMessage.user("My name is Alice."),
                ChatMessage.assistant("Hello Alice! Nice to meet you."),
                ChatMessage.user("What is my name?")
            ],
            "expected_keywords": ["Alice"],
            "weight": 1.0
        }
    ],
    "reasoning": [
        {
            "name": "logical_reasoning",
            "messages": [
                ChatMessage.user("If all cats are mammals, and some mammals are pets, can we conclude that some cats are pets?")
            ],
            "expected_keywords": ["yes", "cannot", "not necessarily"],
            "weight": 1.0
        },
        {
            "name": "math_reasoning",
            "messages": [
                ChatMessage.user("What is 15 * 24 + 100?")
            ],
            "expected_keywords": ["460"],
            "weight": 1.0
        }
    ],
    "code": [
        {
            "name": "python_code",
            "messages": [
                ChatMessage.user("Write a Python function to reverse a string.")
            ],
            "expected_keywords": ["def", "reverse", "return"],
            "weight": 1.0
        }
    ],
    "creative": [
        {
            "name": "story_writing",
            "messages": [
                ChatMessage.user("Write a one-sentence story about a robot learning to paint.")
            ],
            "expected_keywords": [],
            "weight": 0.5
        }
    ],
    "summarization": [
        {
            "name": "text_summary",
            "messages": [
                ChatMessage.user("Summarize this in one sentence: Artificial intelligence is transforming many industries. Machine learning models can now process vast amounts of data. Deep learning has enabled breakthroughs in image recognition and natural language processing.")
            ],
            "expected_keywords": ["AI", "machine learning", "transforming"],
            "weight": 1.0
        }
    ],
    "translation": [
        {
            "name": "english_to_chinese",
            "messages": [
                ChatMessage.user("Translate 'Hello, how are you?' to Chinese.")
            ],
            "expected_keywords": ["你好"],
            "weight": 1.0
        }
    ]
}


class CapabilityEvaluator:
    """模型能力评估器
    
    评估各模型的能力，生成能力矩阵和评分。
    
    功能：
    - 评估各模型能力
    - 性能基准测试
    - 质量评分
    - 能力矩阵生成
    - 动态评估更新
    
    Attributes:
        evaluations: 评估结果缓存
    """
    
    def __init__(self):
        self.evaluations: Dict[str, ModelEvaluation] = {}
        self._capability_weights = {
            TaskType.CHAT: 0.15,
            TaskType.REASONING: 0.20,
            TaskType.CODE: 0.20,
            TaskType.CREATIVE: 0.10,
            TaskType.SUMMARIZATION: 0.15,
            TaskType.TRANSLATION: 0.10,
            TaskType.ANALYSIS: 0.10,
        }
    
    async def evaluate_model(
        self,
        model: BaseModel,
        task_types: Optional[List[str]] = None,
        timeout_per_test: float = 30.0
    ) -> ModelEvaluation:
        """评估单个模型
        
        Args:
            model: 要评估的模型
            task_types: 要评估的任务类型，默认全部
            timeout_per_test: 每个测试的超时时间
            
        Returns:
            ModelEvaluation: 评估结果
        """
        if not model.is_initialized:
            await model.initialize()
        
        task_types = task_types or list(_BENCHMARK_CASES.keys())
        benchmarks: List[BenchmarkResult] = []
        capability_scores: Dict[str, float] = {}
        
        for task_type in task_types:
            if task_type not in _BENCHMARK_CASES:
                continue
            
            cases = _BENCHMARK_CASES[task_type]
            task_scores: List[float] = []
            task_latencies: List[float] = []
            task_tokens: List[int] = []
            
            for case in cases:
                try:
                    result = await asyncio.wait_for(
                        self._run_benchmark_case(model, case),
                        timeout=timeout_per_test
                    )
                    benchmarks.append(result)
                    task_scores.append(result.score)
                    task_latencies.append(result.latency_ms)
                    task_tokens.append(result.tokens_used)
                except asyncio.TimeoutError:
                    logger.warning(f"Benchmark timeout: {case['name']} for {model.model_name}")
                    benchmarks.append(BenchmarkResult(
                        task_type=task_type,
                        score=0.0,
                        latency_ms=timeout_per_test * 1000,
                        tokens_used=0,
                        metadata={"timeout": True}
                    ))
                except Exception as e:
                    logger.error(f"Benchmark failed: {case['name']} for {model.model_name}: {e}")
                    benchmarks.append(BenchmarkResult(
                        task_type=task_type,
                        score=0.0,
                        latency_ms=0.0,
                        tokens_used=0,
                        metadata={"error": str(e)}
                    ))
            
            # 计算任务类型平均分
            if task_scores:
                avg_score = sum(task_scores) / len(task_scores)
                capability_scores[task_type] = avg_score
            
            await asyncio.sleep(0.5)  # 避免速率限制
        
        # 计算综合评分
        overall_score = self._calculate_overall_score(capability_scores)
        
        evaluation = ModelEvaluation(
            model_name=model.model_name,
            provider=model.provider.value,
            overall_score=overall_score,
            benchmarks=benchmarks,
            capabilities=capability_scores
        )
        
        # 缓存结果
        cache_key = f"{model.provider.value}:{model.model_name}"
        self.evaluations[cache_key] = evaluation
        
        logger.info(f"Evaluation completed for {model.model_name}: score={overall_score:.2f}")
        return evaluation
    
    async def _run_benchmark_case(self, model: BaseModel, case: Dict[str, Any]) -> BenchmarkResult:
        """运行单个基准测试用例
        
        Args:
            model: 测试模型
            case: 测试用例
            
        Returns:
            BenchmarkResult: 测试结果
        """
        start_time = time.time()
        
        response = await model.chat(case["messages"])
        
        latency_ms = (time.time() - start_time) * 1000
        tokens_used = response.usage.total_tokens if response.usage else 0
        
        # 评估响应质量
        content = response.content.lower()
        expected_keywords = [k.lower() for k in case.get("expected_keywords", [])]
        
        if expected_keywords:
            keyword_hits = sum(1 for kw in expected_keywords if kw in content)
            accuracy = (keyword_hits / len(expected_keywords)) * 100
        else:
            accuracy = 50.0  # 无关键词时默认中等分数
        
        # 响应长度评分（避免过短或过长）
        content_length = len(response.content)
        length_score = min(100, max(0, 100 - abs(content_length - 200) / 10))
        
        # 综合评分
        score = accuracy * 0.7 + length_score * 0.3
        
        return BenchmarkResult(
            task_type=case.get("name", "unknown"),
            score=score,
            latency_ms=latency_ms,
            tokens_used=tokens_used,
            response_quality=length_score,
            accuracy=accuracy,
            metadata={
                "response_length": content_length,
                "keyword_hits": keyword_hits if expected_keywords else 0,
                "expected_keywords": expected_keywords
            }
        )
    
    def _calculate_overall_score(self, capability_scores: Dict[str, float]) -> float:
        """计算综合评分
        
        Args:
            capability_scores: 能力评分字典
            
        Returns:
            float: 综合评分
        """
        if not capability_scores:
            return 0.0
        
        total_weight = 0.0
        weighted_sum = 0.0
        
        for task_type, score in capability_scores.items():
            weight = self._capability_weights.get(TaskType(task_type), 0.1)
            weighted_sum += score * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    async def evaluate_multiple(
        self,
        models: List[BaseModel],
        task_types: Optional[List[str]] = None
    ) -> Dict[str, ModelEvaluation]:
        """评估多个模型
        
        Args:
            models: 模型列表
            task_types: 要评估的任务类型
            
        Returns:
            Dict[str, ModelEvaluation]: 评估结果字典
        """
        results: Dict[str, ModelEvaluation] = {}
        
        for model in models:
            try:
                evaluation = await self.evaluate_model(model, task_types)
                cache_key = f"{model.provider.value}:{model.model_name}"
                results[cache_key] = evaluation
            except Exception as e:
                logger.error(f"Failed to evaluate {model.model_name}: {e}")
        
        return results
    
    def get_capability_matrix(self) -> Dict[str, Any]:
        """获取能力矩阵
        
        Returns:
            Dict[str, Any]: 能力矩阵
        """
        if not self.evaluations:
            return {"models": [], "tasks": [], "matrix": []}
        
        # 收集所有任务类型
        all_tasks: set[str] = set()
        for eval_result in self.evaluations.values():
            all_tasks.update(eval_result.capabilities.keys())
        
        tasks = sorted(all_tasks)
        models = sorted(self.evaluations.keys())
        
        # 构建矩阵
        matrix = []
        for model_key in models:
            eval_result = self.evaluations[model_key]
            row = {
                "model": model_key,
                "overall": eval_result.overall_score,
                "scores": {
                    task: eval_result.capabilities.get(task, 0.0)
                    for task in tasks
                }
            }
            matrix.append(row)
        
        return {
            "models": models,
            "tasks": tasks,
            "matrix": matrix,
            "generated_at": datetime.now().isoformat()
        }
    
    def get_best_model_for_task(self, task_type: str) -> Optional[str]:
        """获取某任务的最佳模型
        
        Args:
            task_type: 任务类型
            
        Returns:
            Optional[str]: 最佳模型标识
        """
        best_model = None
        best_score = -1.0
        
        for model_key, eval_result in self.evaluations.items():
            score = eval_result.capabilities.get(task_type, 0.0)
            if score > best_score:
                best_score = score
                best_model = model_key
        
        return best_model
    
    def get_model_ranking(self) -> List[Dict[str, Any]]:
        """获取模型排名
        
        Returns:
            List[Dict[str, Any]]: 排名列表
        """
        rankings = []
        
        for model_key, eval_result in self.evaluations.items():
            rankings.append({
                "model": model_key,
                "provider": eval_result.provider,
                "overall_score": eval_result.overall_score,
                "capabilities": eval_result.capabilities,
                "evaluated_at": eval_result.evaluated_at.isoformat()
            })
        
        rankings.sort(key=lambda x: x["overall_score"], reverse=True)
        
        # 添加排名
        for i, item in enumerate(rankings):
            item["rank"] = i + 1
        
        return rankings
    
    def compare_models(self, model_keys: List[str]) -> Dict[str, Any]:
        """对比多个模型
        
        Args:
            model_keys: 模型标识列表
            
        Returns:
            Dict[str, Any]: 对比结果
        """
        comparison = {
            "models": [],
            "capabilities": {},
            "latency_comparison": {},
            "cost_efficiency": {}
        }
        
        for key in model_keys:
            if key not in self.evaluations:
                continue
            
            eval_result = self.evaluations[key]
            comparison["models"].append({
                "model": key,
                "overall_score": eval_result.overall_score,
                "provider": eval_result.provider
            })
            
            # 能力对比
            for task, score in eval_result.capabilities.items():
                if task not in comparison["capabilities"]:
                    comparison["capabilities"][task] = {}
                comparison["capabilities"][task][key] = score
            
            # 延迟对比
            avg_latency = sum(b.latency_ms for b in eval_result.benchmarks) / len(eval_result.benchmarks) if eval_result.benchmarks else 0
            comparison["latency_comparison"][key] = avg_latency
            
            # 成本效率（分数/延迟）
            comparison["cost_efficiency"][key] = eval_result.overall_score / avg_latency * 1000 if avg_latency > 0 else 0
        
        return comparison
    
    def clear_cache(self) -> None:
        """清除评估缓存"""
        self.evaluations.clear()
        logger.info("Evaluation cache cleared")
    
    def get_evaluation(self, provider: str, model_name: str) -> Optional[ModelEvaluation]:
        """获取指定模型的评估结果
        
        Args:
            provider: 提供商
            model_name: 模型名称
            
        Returns:
            Optional[ModelEvaluation]: 评估结果
        """
        cache_key = f"{provider}:{model_name}"
        return self.evaluations.get(cache_key)


# 全局评估器实例
_global_evaluator: Optional[CapabilityEvaluator] = None


def get_capability_evaluator() -> CapabilityEvaluator:
    """获取全局能力评估器"""
    global _global_evaluator
    if _global_evaluator is None:
        _global_evaluator = CapabilityEvaluator()
    return _global_evaluator
