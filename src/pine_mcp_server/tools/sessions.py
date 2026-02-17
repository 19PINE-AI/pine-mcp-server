"""Session CRUD tools."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Optional

from pine_assistant import AsyncPineAI
from pine_assistant.errors import PineAIError

if TYPE_CHECKING:
    from fastmcp import FastMCP
    from pine_mcp_server.server import PineClient


def register_session_tools(mcp: FastMCP, pine: PineClient) -> None:

    @mcp.tool
    async def pine_session_create() -> str:
        """Create a new Pine AI session to start a customer service task.

        Returns session_id and web URL. Next step: call pine_send_message
        with the user's request (e.g. "Negotiate my Comcast bill").
        """
        try:
            result = await pine.client.sessions.create()
            session_id = result.get("id", "")
            return json.dumps({
                "success": True,
                "session_id": session_id,
                "state": result.get("state", ""),
                "web_url": AsyncPineAI.session_url(session_id),
            })
        except PineAIError as e:
            return json.dumps({"success": False, "error": e.code, "message": str(e)})
        except Exception as e:
            return json.dumps({"success": False, "error": "unexpected_error", "message": str(e)})

    @mcp.tool
    async def pine_session_list(
        state: Optional[str] = None,
        limit: int = 30,
        offset: int = 0,
    ) -> str:
        """List Pine AI sessions with optional state filter.

        Args:
            state: Filter by state (e.g. "init", "task_ready", "in_progress").
            limit: Max sessions to return (default 30).
            offset: Pagination offset.
        """
        try:
            result = await pine.client.sessions.list(
                state=state, limit=limit, offset=offset,
            )
            sessions = result.get("sessions", [])
            lines = [f"Total: {result.get('total', len(sessions))} sessions\n"]
            for s in sessions:
                sid = s.get("id", "?")
                title = s.get("title", "Untitled")
                st = s.get("state", "?")
                lines.append(f"- [{st}] {title} (id: {sid})")
            return "\n".join(lines)
        except PineAIError as e:
            return json.dumps({"success": False, "error": e.code, "message": str(e)})
        except Exception as e:
            return json.dumps({"success": False, "error": "unexpected_error", "message": str(e)})

    @mcp.tool
    async def pine_session_get(session_id: str) -> str:
        """Get session details including state, title, and timestamps."""
        try:
            result = await pine.client.sessions.get(session_id)
            return json.dumps(result, default=str)
        except PineAIError as e:
            return json.dumps({"success": False, "error": e.code, "message": str(e)})
        except Exception as e:
            return json.dumps({"success": False, "error": "unexpected_error", "message": str(e)})

    @mcp.tool
    async def pine_session_delete(session_id: str, force_delete: bool = False) -> str:
        """Delete a Pine AI session.

        Args:
            session_id: The session to delete.
            force_delete: If True, force-delete even if the session has an active task.
        """
        try:
            await pine.client.sessions.delete(session_id, force_delete=force_delete)
            return json.dumps({"success": True, "message": f"Session {session_id} deleted."})
        except PineAIError as e:
            return json.dumps({"success": False, "error": e.code, "message": str(e)})
        except Exception as e:
            return json.dumps({"success": False, "error": "unexpected_error", "message": str(e)})

    @mcp.tool
    async def pine_session_url(session_id: str) -> str:
        """Get the web URL for a session. Share with the user for progress tracking, payments, or credits."""
        url = AsyncPineAI.session_url(session_id)
        return json.dumps({"session_id": session_id, "web_url": url})
