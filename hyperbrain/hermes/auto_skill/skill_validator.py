"""
Skill 验证器

三道关：
1. AST 解析
2. import 白名单
3. exec 沙箱实例化 + mock execute 调用
"""
from __future__ import annotations

import ast
import asyncio
import builtins as _builtins
import importlib
import sys
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from hyperbrain.hermes.common import get_hermes_logger

logger = get_hermes_logger("skill_validator")


@dataclass
class ValidationResult:
    success: bool
    error: str = ""
    module_name: str = ""
    class_name: str = ""
    details: List[str] = field(default_factory=list)


class SkillValidator:
    """对 LLM 产出的 Skill 源码做三道关验证"""

    def __init__(self, import_whitelist: List[str]):
        self.whitelist: Set[str] = set(import_whitelist or [])
        # 隐式允许 hyperbrain.skills.base（生成器必然要继承 BaseSkill）
        self.whitelist.add("hyperbrain")

    # ---------- 公共 API ----------

    def validate(self, source_code: str) -> ValidationResult:
        # 1) AST
        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            return ValidationResult(False, f"AST parse failed: {e}")

        # 2) import 白名单
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if not self._is_allowed(alias.name):
                        return ValidationResult(
                            False, f"import not allowed: {alias.name}"
                        )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if not self._is_allowed(module):
                    return ValidationResult(
                        False, f"import-from not allowed: {module}"
                    )

        # 3) exec 沙箱
        return self._exec_sandbox(source_code)

    # ---------- 内部 ----------

    def _is_allowed(self, module: str) -> bool:
        if not module:
            return True  # from . import xxx 视为允许
        top = module.split(".")[0]
        return top in self.whitelist

    def _exec_sandbox(self, source_code: str) -> ValidationResult:
        """
        在受限 globals 中执行源码，尝试找出 BaseSkill 子类并实例化。
        """
        sandbox_globals: Dict[str, Any] = {
            "__builtins__": {
                name: getattr(_builtins, name)
                for name in (
                    "print", "len", "range", "str", "int", "float", "bool",
                    "list", "dict", "set", "tuple", "isinstance", "Exception",
                    "ValueError", "TypeError", "KeyError", "RuntimeError",
                    "True", "False", "None", "abs", "min", "max", "sum",
                    "enumerate", "zip", "map", "filter", "sorted", "reversed",
                    "any", "all", "getattr", "setattr", "hasattr",
                    "object", "type", "super", "property",
                    "__import__",  # for `from x import y`
                    "__build_class__",  # for `class Foo:`
                )
                if hasattr(_builtins, name)
            },
            "__name__": "__hermes_sandbox__",
        }
        module_name = f"_hermes_draft_{uuid.uuid4().hex[:8]}"
        try:
            code = compile(source_code, filename=module_name, mode="exec")
            exec(code, sandbox_globals)  # noqa: S102
        except Exception as e:  # noqa: BLE001
            return ValidationResult(False, f"exec failed: {e}")

        # 找出 BaseSkill 子类
        from hyperbrain.skills.base import BaseSkill
        candidate_cls = None
        for name, obj in list(sandbox_globals.items()):
            if (
                isinstance(obj, type)
                and issubclass(obj, BaseSkill)
                and obj is not BaseSkill
            ):
                candidate_cls = obj
                break
        if candidate_cls is None:
            return ValidationResult(
                False, "no BaseSkill subclass found in source"
            )

        # 4) mock execute 试调一次，确保不爆
        try:
            instance = candidate_cls()
            result = asyncio.run(instance.execute(dry_run=True))  # type: ignore[arg-type]
            if result is None:
                return ValidationResult(
                    False, "execute() returned None (must return SkillResult)"
                )
        except TypeError:
            # 如果 execute 不接受 dry_run 参数，重试一次
            try:
                instance = candidate_cls()
                result = asyncio.run(instance.execute())  # type: ignore[arg-type]
            except Exception as e:  # noqa: BLE001
                return ValidationResult(
                    False, f"execute() raised: {e}"
                )
        except Exception as e:  # noqa: BLE001
            return ValidationResult(
                False, f"execute() raised: {e}"
            )

        return ValidationResult(
            True,
            module_name=module_name,
            class_name=candidate_cls.__name__,
        )
