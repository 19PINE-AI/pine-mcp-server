"""Load conversation tool — the core "refresh page" mechanism."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from pine_assistant import AsyncPineAI

from pine_mcp_server.tools._helpers import format_error

if TYPE_CHECKING:
    from fastmcp import FastMCP
    from pine_mcp_server.server import PineClient


def _format_message(msg: dict[str, Any]) -> str:
    """Format a single history message into readable text.

    Handles both flat format (type/data at top level) and envelope format
    (type/data nested under payload), since the backend response structure
    may vary.
    """
    payload = msg.get("payload") or {}
    msg_type = payload.get("type") or msg.get("type", "unknown")
    data = payload.get("data") or msg.get("data") or {}
    source = msg.get("metadata", {}).get("source", {})
    role = source.get("role", "system")
    message_id = payload.get("message_id") or msg.get("message_id", "")

    prefix = f"[{role}]" if role != "system" else "[pine]"

    if msg_type == "session:text":
        content = data.get("content", "")
        return f"{prefix} {content}"

    if msg_type == "session:form_to_user":
        user_msg = data.get("message_to_user", "")
        form = data.get("form", {})
        fields = form.get("fields", [])
        lines = [f"{prefix} [FORM] {user_msg}"]
        if message_id:
            lines.append(f"  message_id: {message_id}")
        for f in fields:
            name = f.get("name", "?")
            ftype = f.get("type", "text")
            label = f.get("label") or f.get("description") or ""
            options = f.get("options")
            line = f"  - {name} ({ftype})"
            if label:
                line += f": {label}"
            if options:
                line += f" [options: {', '.join(str(o) for o in options)}]"
            lines.append(line)
        lines.append("  Submit via pine_send_form_response with the message_id above.")
        return "\n".join(lines)

    if msg_type == "session:task_ready":
        required = data.get("required", 0)
        confirmed = data.get("confirmed", False)
        if confirmed:
            return f"{prefix} [TASK READY] Credits confirmed ({required} required). Task starting automatically."
        return f"{prefix} [CREDITS NEEDED] {required} credits required. User must add credits."

    if msg_type == "session:task_finished":
        completion = data.get("completion", {})
        title = completion.get("result_title", "Task complete")
        desc = completion.get("result_description", "")
        return f"{prefix} [TASK FINISHED] {title}" + (f" — {desc}" if desc else "")

    if msg_type == "session:reward":
        charge_type = data.get("charge_type", "")
        status = data.get("status", "")
        if charge_type == "free":
            return f"{prefix} [BILLING] Free task. Call pine_task_start to begin."
        if status == "succeeded":
            return f"{prefix} [BILLING] Payment received. Call pine_task_start to begin."
        content = data.get("content", "Payment required.")
        return f"{prefix} [BILLING] {content}"

    if msg_type == "session:payment":
        status = data.get("status", "")
        if status in ("completed", "success"):
            return f"{prefix} [PAYMENT] Payment completed. Call pine_task_start to begin."
        return f"{prefix} [PAYMENT] Payment pending."

    if msg_type == "session:interactive_auth_confirmation":
        user_msg = data.get("message_to_user", "Verification required")
        if message_id:
            return f"{prefix} [AUTH NEEDED] {user_msg} (message_id: {message_id})"
        return f"{prefix} [AUTH NEEDED] {user_msg}"

    if msg_type == "session:three_way_call":
        content = data.get("content", "")
        number = data.get("caller_id_number", "")
        return f"{prefix} [THREE-WAY CALL] {content} Caller: {number}"

    if msg_type == "session:error":
        code = data.get("code", "unknown")
        message = data.get("message", "")
        return f"{prefix} [ERROR] {code}: {message}"

    if msg_type == "session:state":
        state = data.get("content", "")
        return f"{prefix} [STATE] {state}"

    if msg_type == "session:ask_for_location":
        user_msg = data.get("message_to_user", "Location needed")
        if message_id:
            return f"{prefix} [LOCATION NEEDED] {user_msg} (message_id: {message_id})"
        return f"{prefix} [LOCATION NEEDED] {user_msg}"

    if msg_type == "session:computer_use_intervention":
        user_msg = data.get("message_to_user") or data.get("content", "")
        return f"{prefix} [ACTION NEEDED] {user_msg}"

    if msg_type == "session:social_sharing":
        share_text = data.get("share_text", "Share your results to earn credits!")
        return f"{prefix} [SHARE] {share_text}"

    if msg_type == "session:continue_in_new_task":
        new_sid = data.get("session_id", "")
        msg_text = data.get("message", "")
        return f"{prefix} [CONTINUE] {msg_text} New session: {new_sid}"

    if msg_type == "session:work_log":
        steps = data.get("steps", [])
        if not steps:
            return ""
        summaries = [f"{s.get('step_title', '?')}: {s.get('status', '?')}" for s in steps]
        return f"{prefix} [WORK LOG] {'; '.join(summaries)}"

    if msg_type == "session:message":
        content = data.get("content", "")
        return f"{prefix} {content}"

    # Fallback for other types
    if isinstance(data, dict) and data:
        content = data.get("content") or data.get("message") or ""
        if content:
            return f"{prefix} [{msg_type}] {content}"
    return f"{prefix} [{msg_type}]"


def register_history_tools(mcp: FastMCP, pine: PineClient) -> None:

    @mcp.tool
    async def pine_get_history(
        session_id: str,
        max_messages: int = 30,
        order: str = "asc",
        from_message_id: Optional[str] = None,
    ) -> str:
        """Poll Pine's conversation history — the core way to see replies (no streaming).

        Call after sending a message or starting a task. Wait a few seconds
        between polls. Look for: [FORM], [BILLING], [PAYMENT], [TASK READY],
        [CREDITS NEEDED], [AUTH NEEDED], [THREE-WAY CALL], [TASK FINISHED],
        [ACTION NEEDED].

        Args:
            session_id: The session to load history for.
            max_messages: Max messages to fetch (default 30).
            order: "asc" (oldest first) or "desc" (newest first).
            from_message_id: Fetch messages after this ID (for pagination).
        """
        try:
            client = await pine.ensure_connected()
            result = await client.get_history(
                session_id,
                max_messages=max_messages,
                order=order,
                from_message_id=from_message_id,
            )
            messages = result.get("messages", [])
            if not messages:
                return f"No messages in session {session_id} yet."

            web_url = AsyncPineAI.session_url(session_id)
            lines = [f"Session: {session_id}", f"Web URL: {web_url}", f"Messages ({len(messages)}):", ""]

            for msg in messages:
                formatted = _format_message(msg)
                if formatted:
                    lines.append(formatted)

            next_id = result.get("next_message_id")
            if next_id:
                lines.append(f"\n[More messages available — call with from_message_id=\"{next_id}\"]")

            return "\n".join(lines)
        except Exception as e:
            return format_error(e)
