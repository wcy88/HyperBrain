"""
Skill 代码生成器

通过 LLM 产出符合 BaseSkill 模板的 Python 源码。
- 使用 JSON schema 约束输出
- 失败时返回 None，由 validator 兜底
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from hyperbrain.hermes.common import (
    get_hermes_logger,
    safe_chat,
)
from hyperbrain.models.base import ChatMessage

logger = get_hermes_logger("skill_generator")

# 提示 LLM 输出的 JSON 结构（不强制遵守，但示例化）
_GEN_PROMPT = """你是一名 Python 工程师。基于以下"用户意图样例"，设计一个新的 Skill 类。

约束：
1. 必须继承自 `hyperbrain.skills.base.BaseSkill`
2. 必须设置类属性 name / description / version / category / tags
3. 必须实现 `async def execute(self, **kwargs) -> SkillResult`
4. execute 内部不允许做危险操作（import os / subprocess / shutil 等被禁止）
5. 只能 import 白名单内的标准库：asyncio, json, re, math, datetime, pathlib,
   typing, dataclasses, enum, collections, itertools, functools, statistics,
   random, string, textwrap
6. execute 内部如出现异常，必须捕获并返回 SkillResult(success=False, ...)
7. 只用 Python 标准库；如需调用外部 API，用 'aiohttp' 或 'urllib.request'

请按以下 JSON schema 输出（**只输出 JSON，不要任何额外文字、代码块、注释**）：
{{
  "skill_name": "<snake_case>",
  "class_name": "<PascalCase + Skill>",
  "description": "<一句话中文描述>",
  "category": "<tools | data | info | network | other>",
  "tags": ["tag1", "tag2"],
  "source_code": "<完整 Python 源码字符串，必须含 import 行>"
}}

用户意图样例：
{samples}

请生成。"""


class SkillGenerator:
    """调用 LLM 产出 Skill 源码"""

    def __init__(self, model_manager):
        self.model_manager = model_manager

    async def generate(
        self,
        intent_key: str,
        samples: List[str],
    ) -> Optional[Dict[str, Any]]:
        """
        调一次 chat，返回结构化 dict 或 None。
        """
        sample_text = "\n".join(f"- {s}" for s in samples[:5])
        prompt = _GEN_PROMPT.format(samples=sample_text)

        messages = [
            ChatMessage(role="system", content="你只输出合法 JSON。"),
            ChatMessage(role="user", content=prompt),
        ]
        try:
            raw = await safe_chat(
                self.model_manager, messages, fallback="", retries=1, timeout=60
            )
        except Exception as e:  # noqa: BLE001
            logger.warning(f"LLM call failed: {e}")
            return None
        if not raw:
            return None
        return self._parse(raw, intent_key=intent_key)

    # ---------- 内部 ----------

    def _parse(self, raw: str, *, intent_key: str) -> Optional[Dict[str, Any]]:
        # LLM 经常加 ```json 包裹，先剥掉
        raw = raw.strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        data: Optional[Dict[str, Any]] = None
        try:
            data = json.loads(raw)
        except Exception:
            # 退化：从 raw 中抠第一个 {...} 块
            m = re.search(r"\{[\s\S]*\}", raw)
            if m:
                try:
                    data = json.loads(m.group(0))
                except Exception as e:  # noqa: BLE001
                    logger.warning(f"JSON parse failed after extraction: {e}")
        if not isinstance(data, dict):
            return None

        # 字段补全
        data.setdefault("skill_name", f"auto_{intent_key[:8]}")
        data.setdefault("class_name", "".join(
            p.capitalize() for p in data["skill_name"].split("_")
        ) + "Skill")
        data.setdefault("description", f"auto-generated skill for intent {intent_key}")
        data.setdefault("category", "other")
        if not isinstance(data.get("tags"), list):
            data["tags"] = ["auto_generated", intent_key]
        if not isinstance(data.get("source_code"), str) or not data["source_code"]:
            return None
        return data
