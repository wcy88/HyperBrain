"""
自我优化器

实现系统参数的自动优化和策略调整
"""

import random
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field

from hyperbrain.core.logger import get_logger
from hyperbrain.core.config import get_config

logger = get_logger("evolution.optimizer")


@dataclass
class OptimizationResult:
    """优化结果"""
    parameter_name: str
    old_value: Any
    new_value: Any
    improvement: float
    iteration: int


@dataclass
class Individual:
    """进化个体"""
    parameters: Dict[str, Any]
    fitness: float = 0.0
    generation: int = 0


class SelfOptimizer:
    """
    自我优化系统
    
    功能：
    1. 参数自动调优
    2. 策略进化
    3. 适应度评估
    4. 选择、交叉、变异
    """
    
    def __init__(self):
        self.config = get_config().evolution
        self.population: List[Individual] = []
        self.generation = 0
        self.best_individual: Optional[Individual] = None
        self.optimization_history: List[OptimizationResult] = []
        logger.info("SelfOptimizer initialized")
    
    def initialize_population(self, 
                             base_params: Dict[str, Any],
                             population_size: Optional[int] = None) -> None:
        """
        初始化种群
        
        Args:
            base_params: 基础参数
            population_size: 种群大小
        """
        size = population_size or self.config.generation_size
        self.population = []
        
        for i in range(size):
            # 添加随机扰动
            params = self._mutate_parameters(base_params, rate=0.1)
            individual = Individual(
                parameters=params,
                generation=0
            )
            self.population.append(individual)
        
        logger.info(f"Initialized population with {size} individuals")
    
    def evolve(self, 
               fitness_func: Callable[[Dict[str, Any]], float],
               generations: int = 10) -> Individual:
        """
        执行进化
        
        Args:
            fitness_func: 适应度函数
            generations: 进化代数
            
        Returns:
            Individual: 最优个体
        """
        for gen in range(generations):
            self.generation = gen
            
            # 评估适应度
            for individual in self.population:
                individual.fitness = fitness_func(individual.parameters)
            
            # 选择
            selected = self._select()
            
            # 交叉和变异
            offspring = self._crossover_and_mutate(selected)
            
            # 更新种群
            self.population = offspring
            
            # 记录最优
            current_best = max(self.population, key=lambda x: x.fitness)
            if (self.best_individual is None or 
                current_best.fitness > self.best_individual.fitness):
                self.best_individual = current_best
            
            logger.info(f"Generation {gen}: best fitness = {current_best.fitness:.4f}")
        
        return self.best_individual
    
    def optimize_parameter(self, 
                          param_name: str,
                          current_value: float,
                          evaluate_func: Callable[[float], float],
                          search_range: Optional[tuple] = None) -> OptimizationResult:
        """
        优化单个参数
        
        Args:
            param_name: 参数名
            current_value: 当前值
            evaluate_func: 评估函数
            search_range: 搜索范围
            
        Returns:
            OptimizationResult: 优化结果
        """
        if search_range is None:
            search_range = (current_value * 0.5, current_value * 1.5)
        
        best_value = current_value
        best_score = evaluate_func(current_value)
        
        # 简单网格搜索
        steps = 10
        for i in range(steps):
            test_value = search_range[0] + (search_range[1] - search_range[0]) * i / steps
            score = evaluate_func(test_value)
            
            if score > best_score:
                best_score = score
                best_value = test_value
        
        result = OptimizationResult(
            parameter_name=param_name,
            old_value=current_value,
            new_value=best_value,
            improvement=best_score - evaluate_func(current_value),
            iteration=self.generation
        )
        
        self.optimization_history.append(result)
        logger.info(f"Optimized {param_name}: {current_value:.4f} -> {best_value:.4f}")
        return result
    
    def _mutate_parameters(self, 
                          params: Dict[str, Any], 
                          rate: Optional[float] = None) -> Dict[str, Any]:
        """变异参数"""
        rate = rate or self.config.mutation_rate
        mutated = params.copy()
        
        for key, value in mutated.items():
            if isinstance(value, (int, float)) and random.random() < rate:
                if isinstance(value, int):
                    mutated[key] = value + random.randint(-1, 1)
                else:
                    mutated[key] = value * (1 + random.uniform(-0.1, 0.1))
        
        return mutated
    
    def _select(self) -> List[Individual]:
        """选择操作（锦标赛选择）"""
        selected = []
        tournament_size = 3
        
        for _ in range(len(self.population)):
            tournament = random.sample(self.population, 
                                     min(tournament_size, len(self.population)))
            winner = max(tournament, key=lambda x: x.fitness)
            selected.append(winner)
        
        return selected
    
    def _crossover_and_mutate(self, 
                             parents: List[Individual]) -> List[Individual]:
        """交叉和变异"""
        offspring = []
        
        for i in range(0, len(parents), 2):
            parent1 = parents[i]
            parent2 = parents[(i + 1) % len(parents)]
            
            # 交叉
            child_params = {}
            for key in parent1.parameters:
                if random.random() < 0.5:
                    child_params[key] = parent1.parameters[key]
                else:
                    child_params[key] = parent2.parameters.get(key, parent1.parameters[key])
            
            # 变异
            child_params = self._mutate_parameters(child_params)
            
            child = Individual(
                parameters=child_params,
                generation=self.generation + 1
            )
            offspring.append(child)
        
        return offspring
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "generation": self.generation,
            "population_size": len(self.population),
            "best_fitness": self.best_individual.fitness if self.best_individual else 0.0,
            "total_optimizations": len(self.optimization_history)
        }
