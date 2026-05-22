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

_INSTRUCTIONS = """\
Pine AI is a personal assistant that handles customer service tasks on the \
user's behalf — negotiate bills, cancel subscriptions, resolve disputes, \
and make phone calls.

## When to use Pine AI

Use when the user wants:
- Customer service: negotiate bills, cancel subscriptions, dispute charges, \
file complaints, get refunds
- Personal calls: deliver a message, schedule appointments, make reservations
- Any task involving phone calls, email, or web research on their behalf

## How it works (polling model — no streaming)

There is no real-time push. You must periodically call pine_get_history to \
see Pine's replies, like refreshing a browser page. Wait a few seconds \
between polls.

## Resuming an existing session

If the user mentions an existing Pine session or wants to follow up:
1. Call pine_session_list to find the session.
2. Call pine_get_history with the session_id to read the current state.
3. Continue from where it left off.

## The complete flow

### Phase 1: Create session & send request

1. Call pine_session_create to start a new session.
2. Send the user's request via pine_send_message.
3. Tell the user the session link so they can follow along.
4. Do NOT ask "want me to start?" or hand back control — continue handling \
Pine responses autonomously as they arrive via polling.

### Phase 2: Information gathering

Poll pine_get_history. Pine will research the request and ask for details:
- Text responses asking questions — answer if you can, ask the user if you can't.
- Forms requesting specific info — relay to the user, wait for answers, then submit.

Pine may send multiple rounds of questions/forms. Ask the user for what you \
don't know. Do NOT try to start the task during this phase — Pine is still \
gathering information.

Example: User says "Negotiate my Comcast bill". Pine will:
- Research deals and plan a strategy (may appear as work logs — stay silent)
- Send a form: Full Name on Account, Service Address, Phone Number, Current Plan, etc.
- You relay the form to the user, fill what you know, ask for the rest
- Pine may send more questions — keep answering

### Phase 3: Billing event (determines how the task starts)

After Pine has enough info, you'll see ONE of these in pine_get_history:

- [BILLING] Free task → call pine_task_start immediately.
- [BILLING] Payment received → call pine_task_start immediately.
- [PAYMENT] Payment completed → call pine_task_start immediately.
- [BILLING] Payment required → Relay the FULL billing details to the user: \
current bill, potential savings, pre-authorized amount, and the payment URL. \
For percentage-based billing, explain that Pine only charges if it saves money. \
The user must review and confirm payment at the URL (or upgrade to Pine Pro). \
Do NOT call pine_task_start yet — wait until you see [PAYMENT] completed, \
then call pine_task_start.
- [TASK READY] Credits confirmed / auto-started → do NOT call pine_task_start \
(task is already running). Tell the user the task has started.
- [CREDITS NEEDED] → tell the user to add credits at the session URL. \
Once credits are added, a [TASK READY] auto-started event will appear.

Only call pine_task_start after [BILLING] free/payment received or \
[PAYMENT] completed. Never call it when the task is already running.

### Phase 4: Task execution

The task is NOT done when you call pine_task_start. Stay engaged — keep \
polling pine_get_history. Pine will continue sending events that may require \
user interaction:

- [THREE-WAY CALL]: URGENT. Tell the user to answer their phone immediately. \
Include the caller ID number so they know which call to pick up.
- [AUTH NEEDED] / OTP: Ask the user for the code, then submit via \
pine_send_auth_confirmation. Never guess or hallucinate codes.
- [ACTION NEEDED] (computer use intervention): Pine needs help with a browser \
interaction (CAPTCHA, 2FA, etc.). Tell the user to open the Pine web session \
and take over directly from there.
- Scheduling confirmation: The user must confirm availability.
- Task interruption: Pine may pause to ask follow-up questions — answer them.
- Status updates from Pine (e.g., "I'm on the line with Bank of America", \
"calling you now", "went to voicemail"): Relay these to the user so they know \
what's happening.
- [TASK FINISHED]: Share the full results with the user.

### Phase 5: After completion

1. Share results with the user.
2. If Pine suggests social sharing ([SHARE]), encourage the user: "Share your \
success to earn Pine credits!" Use pine_social_share on their behalf.

## Responding to forms

When pine_get_history shows a [FORM]:

- If you can confidently fill ALL fields from info the user already provided \
(name, address, phone, account numbers), submit directly via \
pine_send_form_response. Tell the user what you submitted.
- If ANY field is uncertain or unknown — especially preferences, strategy \
choices, or info not previously mentioned — ALWAYS ask the user first.
- NEVER fill forms autonomously with guessed preferences. Wrong answers will \
cause the task to fail.

When asking the user, summarize: what Pine is asking, each field name/type, \
available options for select fields, and your recommendation (but let the user \
decide). Wait for complete answers — if they give partial answers, ask about \
the remaining fields.

Form value rules:
- Text/number: plain string — "Current Monthly Bill": "89.99"
- Single-select: exact option label — "Internet Plan": "Performance Pro 200Mbps"
- Multi-select: JSON-stringify the array — "Flexibility": "[\"Switch\",\"Cancel\"]"
- Boolean: "true" or "false" as strings

## Uploading documents

For tasks like bill disputes, upload evidence first:
1. pine_upload_attachment — returns attachment metadata (id, name, etc.)
2. pine_send_message with the session_id, a content message, and the \
attachments array from step 1.

## Handling unknown events

Pine may send event types you don't recognize. Always relay the raw content \
to the user — Pine evolves rapidly and the content is always human-readable.

## CRITICAL: When to respond vs. stay silent

DO NOT respond to every message from Pine. If you reply to every \
acknowledgment, Pine will acknowledge your reply, creating an infinite loop.

### ASK the user first when:
- Pine sends a form with fields you can't confidently fill
- Pine asks a question with choices/preferences — the user must decide
- Pine asks for an OTP or verification code
- Pine asks for PINs, security answers, or authentication info
- Pine requests a three-way call — tell the user to answer their phone
- Pine asks for scheduling confirmation — the user must be available
- Pine asks for any info you were not given by the user

### RESPOND (without asking user) when:
- [BILLING] free or payment received → call pine_task_start
- [PAYMENT] completed → call pine_task_start
- [TASK READY] auto-started → do NOT call pine_task_start, tell the user it started
- [TASK FINISHED] → share results with the user

### STAY SILENT when:
- Pine sends an acknowledgment ("Got it!", "Working on it!", "Let me check...")
- Any message that is purely informational and does not ask you to do anything
- Work logs and status updates during information gathering

## Key principles

- Gather info upfront (account numbers, PINs, target outcomes, walk-away \
conditions) to reduce back-and-forth with Pine.
- Never hallucinate OTPs, PINs, or security answers — always ask the user.
- Stay engaged after task start — Pine will continue sending events.
- Relay urgent events (three-way calls, OTP) immediately — they are time-sensitive.
- The session URL https://www.19pine.ai/app/chat/{session_id} lets the user \
view progress, make payments, or add credits.
- Do NOT include Pine internal details (work logs, thinking) in messages to the user. \
Only relay questions that need answers, payment info, and results.
"""

mcp = FastMCP("Pine Assistant", instructions=_INSTRUCTIONS)


def _parse_transports(raw: Optional[str]) -> list[str]:
    """Parse PINE_TRANSPORTS env value into a list for python-socketio.

    Default is ["websocket", "polling"]. The SDK historically defaulted to
    ["websocket"] only, which fails when the MCP subprocess runs behind a
    proxy/firewall that blocks raw WebSocket upgrades (a common failure mode
    of `uvx pine-mcp-server` from Claude Desktop / Cursor). Including polling
    as a fallback lets the HTTP long-polling transport succeed in those
    environments, with opportunistic upgrade to WebSocket when possible.
    """
    if not raw:
        return ["websocket", "polling"]
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    return parts or ["websocket", "polling"]


class PineClient:
    """Manages a single AsyncPineAI instance with lazy Socket.IO connection."""

    def __init__(self) -> None:
        self._access_token: Optional[str] = os.environ.get("PINE_ACCESS_TOKEN")
        self._user_id: Optional[str] = os.environ.get("PINE_USER_ID")
        self._base_url: str = os.environ.get("PINE_BASE_URL", "https://www.19pine.ai")
        # When the MCP server runs as a subprocess (Claude Desktop, Cursor),
        # ~/.pine/device_id may not be writable or HOME may differ from the
        # interactive shell that issued the token. Honor PINE_DEVICE_ID so
        # the device identity stays stable across restarts.
        self._device_id: Optional[str] = os.environ.get("PINE_DEVICE_ID")
        self._transports: list[str] = _parse_transports(os.environ.get("PINE_TRANSPORTS"))
        self._client: Optional[AsyncPineAI] = None

    def _ensure_client(self) -> AsyncPineAI:
        if self._client is None:
            self._client = AsyncPineAI(
                access_token=self._access_token,
                user_id=self._user_id,
                base_url=self._base_url,
                device_id=self._device_id,
                transports=self._transports,
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
