"""
Pine Assistant MCP Server — local stdio server wrapping the pine-assistant SDK.

Exposes Pine AI session management, messaging, task control, and history
as MCP tools for any LLM agent to use.
"""

from __future__ import annotations

import os
from typing import Optional

from fastmcp import FastMCP
from pine_assistant import AsyncPineAI

from pine_mcp_server.tools.auth import register_auth_tools
from pine_mcp_server.tools.sessions import register_session_tools
from pine_mcp_server.tools.history import register_history_tools
from pine_mcp_server.tools.messages import register_message_tools
from pine_mcp_server.tools.tasks import register_task_tools
from pine_mcp_server.tools.attachments import register_attachment_tools
from pine_mcp_server.tools.social import register_social_tools

mcp = FastMCP(
    "Pine Assistant",
    instructions=(
        "Pine AI is a personal assistant that handles customer service tasks on "
        "the user's behalf — negotiate bills, cancel subscriptions, resolve disputes, "
        "and make phone calls.\n\n"

        "## How it works (polling model — no streaming)\n"
        "There is no real-time push. You must periodically call pine_get_history to "
        "see Pine's replies, like refreshing a browser page.\n\n"

        "## Complete flow\n"
        "1. Create session: pine_session_create\n"
        "2. Send the user's request: pine_send_message\n"
        "3. Poll for Pine's response: pine_get_history (wait a few seconds between polls)\n"
        "4. Handle information gathering: Pine may send forms or questions — fill what you "
        "know, ask the user for the rest, then submit via pine_send_form_response or "
        "pine_send_message with JSON\n"
        "5. Handle billing event (see rules below)\n"
        "6. Task executes: keep polling pine_get_history for updates, OTP requests, "
        "three-way calls, and results\n\n"

        "## Billing rules — when to call pine_task_start\n"
        "- [BILLING] Free task → call pine_task_start\n"
        "- [BILLING] Payment received → call pine_task_start\n"
        "- [PAYMENT] Payment completed → call pine_task_start\n"
        "- [TASK READY] Credits confirmed / auto-started → do NOT call pine_task_start "
        "(already running)\n"
        "- [CREDITS NEEDED] → tell user to add credits at the session URL, then wait\n"
        "- [BILLING] Payment required → relay full billing details and payment URL to user, "
        "wait for [PAYMENT] completed event, then call pine_task_start\n\n"

        "## Form handling\n"
        "When pine_get_history shows a [FORM], fill fields you know from context. "
        "Ask the user for unknown fields — especially preferences, strategy choices, "
        "or info not previously mentioned. Never guess. Submit via pine_send_form_response "
        "with the form's message_id.\n\n"

        "## During task execution\n"
        "- [AUTH NEEDED] / OTP: ask the user for the code, submit via "
        "pine_send_auth_confirmation\n"
        "- [THREE-WAY CALL]: urgently tell the user to answer their phone\n"
        "- [ACTION NEEDED]: relay to the user\n"
        "- [TASK FINISHED]: share results with the user\n"
        "- Acknowledgments / work logs / status updates: stay silent, do not respond\n\n"

        "## Key principles\n"
        "- Gather info upfront (account numbers, PINs, target outcomes) to reduce "
        "back-and-forth\n"
        "- Never hallucinate OTPs, PINs, or security answers — always ask the user\n"
        "- The session URL (https://www.19pine.ai/app/chat/{session_id}) lets the user "
        "view progress, make payments, or add credits"
    ),
)


class PineClient:
    """Manages a single AsyncPineAI instance with lazy Socket.IO connection."""

    def __init__(self) -> None:
        self._access_token: Optional[str] = os.environ.get("PINE_ACCESS_TOKEN")
        self._user_id: Optional[str] = os.environ.get("PINE_USER_ID")
        self._base_url: str = os.environ.get("PINE_BASE_URL", "https://www.19pine.ai")
        self._client: Optional[AsyncPineAI] = None

    def _ensure_client(self) -> AsyncPineAI:
        if self._client is None:
            self._client = AsyncPineAI(
                access_token=self._access_token,
                user_id=self._user_id,
                base_url=self._base_url,
            )
        return self._client

    @property
    def client(self) -> AsyncPineAI:
        return self._ensure_client()

    async def ensure_connected(self) -> AsyncPineAI:
        """Lazily connect Socket.IO when first needed, and reconnect if dropped."""
        client = self._ensure_client()
        if not client.connected:
            await client.connect()
        return client

    def set_credentials(self, access_token: str, user_id: str) -> None:
        """Update credentials (e.g. after auth flow). Resets the client."""
        self._access_token = access_token
        self._user_id = user_id
        self._client = None


pine = PineClient()

register_auth_tools(mcp, pine)
register_session_tools(mcp, pine)
register_history_tools(mcp, pine)
register_message_tools(mcp, pine)
register_task_tools(mcp, pine)
register_attachment_tools(mcp, pine)
register_social_tools(mcp, pine)


def main() -> None:
    """Entry point for the pine-mcp-server command."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
