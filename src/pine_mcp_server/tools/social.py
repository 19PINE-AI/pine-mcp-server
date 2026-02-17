"""Social sharing and scheduling tools."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from pine_assistant.errors import PineAIError

if TYPE_CHECKING:
    from fastmcp import FastMCP
    from pine_mcp_server.server import PineClient


def register_social_tools(mcp: FastMCP, pine: PineClient) -> None:

    @mcp.tool
    async def pine_social_share(
        session_id: str,
        platform: str,
        shared_url: str,
    ) -> str:
        """Share completed task results on social media to earn Pine credits.

        Args:
            session_id: The completed session to share results from.
            platform: One of "x", "facebook", or "linkedin".
            shared_url: The URL of the social media post.
        """
        try:
            result = await pine.client.sessions.social_share(
                session_id, platform, shared_url,
            )
            return json.dumps({
                "success": True,
                "amount": result.get("amount", 0),
                "status": result.get("status", ""),
                "message": f"Shared on {platform}. Credits earned: {result.get('amount', 0)}",
            })
        except PineAIError as e:
            return json.dumps({"success": False, "error": e.code, "message": str(e)})
        except Exception as e:
            return json.dumps({"success": False, "error": "unexpected_error", "message": str(e)})

    @mcp.tool
    async def pine_update_call_reminder(
        session_id: str,
        message_id: str,
        scheduled_time: str,
        enabled: bool,
    ) -> str:
        """Update a scheduled call reminder. Confirm timing with the user first.

        Args:
            session_id: The session with the scheduled call.
            message_id: The call reminder's message_id.
            scheduled_time: ISO 8601 datetime for the call.
            enabled: True to enable, False to disable.
        """
        try:
            result = await pine.client.sessions.update_scheduled_call_reminder(
                session_id, message_id, scheduled_time, enabled,
            )
            status = "enabled" if enabled else "disabled"
            return json.dumps({
                "success": True,
                "message": f"Call reminder {status} for {scheduled_time}.",
            })
        except PineAIError as e:
            return json.dumps({"success": False, "error": e.code, "message": str(e)})
        except Exception as e:
            return json.dumps({"success": False, "error": "unexpected_error", "message": str(e)})
