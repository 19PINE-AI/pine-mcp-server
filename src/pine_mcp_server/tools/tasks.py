"""Task control tools — start and stop task execution."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from pine_assistant.errors import PineAIError

if TYPE_CHECKING:
    from fastmcp import FastMCP
    from pine_mcp_server.server import PineClient


def register_task_tools(mcp: FastMCP, pine: PineClient) -> None:

    @mcp.tool
    async def pine_task_start(session_id: str) -> str:
        """Start task execution after billing is confirmed.

        Only call after: [BILLING] free task, [BILLING] payment received,
        or [PAYMENT] completed. Do NOT call if [TASK READY] says credits
        confirmed/auto-started — the task is already running.
        """
        try:
            result = await pine.client.sessions.start_task(session_id)
            return json.dumps({
                "success": True,
                "message": result.get("message", "Task started."),
            })
        except PineAIError as e:
            return json.dumps({"success": False, "error": e.code, "message": str(e)})
        except Exception as e:
            return json.dumps({"success": False, "error": "unexpected_error", "message": str(e)})

    @mcp.tool
    async def pine_task_stop(session_id: str) -> str:
        """Stop a running Pine AI task."""
        try:
            result = await pine.client.sessions.stop_task(session_id)
            return json.dumps({
                "success": True,
                "message": result.get("message", "Task stopped."),
            })
        except PineAIError as e:
            return json.dumps({"success": False, "error": e.code, "message": str(e)})
        except Exception as e:
            return json.dumps({"success": False, "error": "unexpected_error", "message": str(e)})
