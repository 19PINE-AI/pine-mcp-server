"""Shared helpers for MCP tools."""

from __future__ import annotations

import json
from typing import Any

from pine_assistant.errors import PineAIError


def _walk_causes(exc: BaseException) -> list[str]:
    """Walk an exception's __cause__ / __context__ chain.

    The Socket.IO failure path is several layers deep
    (python-engineio → python-socketio → pine-assistant → pine-mcp-server),
    and only the chain reveals the underlying HTTP status code or transport
    error. Returns each link as "ClassName: message", root cause first wins
    nothing — we keep order from outer to inner so the immediate raise site
    appears first.
    """
    chain: list[str] = []
    seen: set[int] = set()
    cur: BaseException | None = exc
    while cur is not None and id(cur) not in seen:
        seen.add(id(cur))
        chain.append(f"{type(cur).__name__}: {cur}")
        cur = cur.__cause__ or cur.__context__
    return chain


def format_error(exc: BaseException, **extra: Any) -> str:
    """Format any exception into the MCP tool's error JSON envelope.

    Known PineAIError subclasses carry a stable `.code` (e.g. "connection_error",
    "auth_error") — use it as the error code. Everything else becomes
    "unexpected_error" with the exception class name surfaced so callers can
    tell apart e.g. socketio.ConnectionError from a generic RuntimeError
    without grepping the message text.
    """
    if isinstance(exc, PineAIError):
        payload: dict[str, Any] = {
            "success": False,
            "error": exc.code,
            "message": str(exc),
            "exception_type": type(exc).__name__,
        }
        if exc.details:
            payload["details"] = exc.details
    else:
        payload = {
            "success": False,
            "error": "unexpected_error",
            "message": str(exc) or repr(exc),
            "exception_type": type(exc).__name__,
        }
    chain = _walk_causes(exc)
    if len(chain) > 1:
        payload["cause_chain"] = chain
    payload.update(extra)
    return json.dumps(payload)
