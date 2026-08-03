"""
Hermes 公共工具

- 统一 logger
- 带降级的 LLM 调用包装
- 文本到意图 key 的稳定哈希
"""
from __future__ import annotations

import asyncio
import hashlib
import re
from functools import wraps
from typing import Any, Awaitable, Callable, Optional

from hyperbrain.core.logger import get_logger


def get_hermes_logger(name: str):
    """统一前缀的 logger，区别于 8 层模块。"""
    return get_logger(f"hermes.{name}")


def safe_chat(
    model_manager,
    messages,
    *,
    fallback: str = "",
    retries: int = 1,
    timeout: float = 30.0,
):
    """
    异步调 LLM，统一捕获异常，失败时返回 fallback 字符串。

    Hermes 子系统对 LLM 失败的容忍度高：宁可降级也不能阻塞主流程。
    """
    async def _do() -> str:
        last_err: Optional[Exception] = None
        for _ in range(retries + 1):
            try:
                resp = await asyncio.wait_for(
                    model_manager.chat(list(messages)),
                    timeout=timeout,
                )
                content = getattr(resp, "content", None) or ""
                if content:
                    return content
            except Exception as e:  # noqa: BLE001
                last_err = e
                continue
        if last_err is not None:
            get_hermes_logger("common").warning(
                f"safe_chat failed: {last_err}, using fallback"
            )
        return fallback

    return _do()


# 与 LLM 输出无关的纯 Python 工具：把任意输入文本压缩为稳定 intent key
_NOISE_RE = re.compile(r"[\s\W_]+", re.UNICODE)
_CN_STOPWORDS = {
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一个",
    "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好",
    "自己", "这", "那", "把", "让", "请", "帮", "吗", "呢", "啊", "吧", "嗯",
}


def intent_key_from_text(text: str) -> str:
    """
    把任意用户输入压成稳定的 intent key，用于聚类。

    规则：
    1. 转小写
    2. 去标点 / 多余空白
    3. 中文停用词剔除
    4. 截断到前 32 字符
    5. 取 sha1 前 10 位
    """
    if not text:
        return "empty"
    s = text.strip().lower()
    s = _NOISE_RE.sub(" ", s)
    tokens = [t for t in s.split(" ") if t and t not in _CN_STOPWORDS]
    if not tokens:
        tokens = list(s.replace(" ", "")[:8])
    key = " ".join(tokens)[:32] or "x"
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:10]


def async_try(func: Callable[..., Awaitable[Any]], *args, **kwargs) -> Awaitable[Any]:
    """
    装饰器：捕获异步任务中的异常并打日志，不向外抛。
    用于 nudge 任务，确保一个任务失败不会拖垮其他任务。
    """
    @wraps(func)
    async def wrapper(*a, **kw):
        try:
            return await func(*a, **kw)
        except Exception as e:  # noqa: BLE001
            get_hermes_logger("async_try").error(
                f"{func.__name__} failed: {e}", exc_info=False
            )
            return None

    return wrapper
