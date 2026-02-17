"""Messaging tools — send messages, forms, auth confirmations, locations."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Optional

from pine_assistant.errors import PineAIError

if TYPE_CHECKING:
    from fastmcp import FastMCP
    from pine_mcp_server.server import PineClient


def register_message_tools(mcp: FastMCP, pine: PineClient) -> None:

    @mcp.tool
    async def pine_send_message(
        session_id: str,
        content: str,
        attachments: Optional[list[dict[str, Any]]] = None,
    ) -> str:
        """Send a message to Pine AI — describe the task, answer questions, or provide info.

        Also used to submit form answers as JSON ({"field_name": "value"})
        when pine_send_form_response is not applicable. Use pine_get_history
        afterward to see Pine's response.

        Args:
            session_id: The session to send the message to.
            content: Text message or JSON form data to send.
            attachments: Optional attachment metadata from pine_upload_attachment.
        """
        try:
            client = await pine.ensure_connected()
            client.send_message(session_id, content, attachments=attachments)
            return json.dumps({
                "success": True,
                "message": "Message sent. Use pine_get_history later to see Pine's response.",
            })
        except PineAIError as e:
            return json.dumps({"success": False, "error": e.code, "message": str(e)})
        except Exception as e:
            return json.dumps({"success": False, "error": "unexpected_error", "message": str(e)})

    @mcp.tool
    async def pine_send_form_response(
        session_id: str,
        message_id: str,
        form_data: dict[str, Any],
    ) -> str:
        """Submit a form shown in pine_get_history as [FORM].

        Fill fields you know; ask the user for unknowns (especially preferences
        or security info). Use exact option labels for select fields.

        Args:
            session_id: The session containing the form.
            message_id: The form's message_id from pine_get_history output.
            form_data: {"field_name": "value"} pairs matching the form fields.
        """
        try:
            client = await pine.ensure_connected()
            client.send_form_response(session_id, message_id, form_data)
            return json.dumps({
                "success": True,
                "message": "Form submitted. Use pine_get_history to see what happens next.",
            })
        except PineAIError as e:
            return json.dumps({"success": False, "error": e.code, "message": str(e)})
        except Exception as e:
            return json.dumps({"success": False, "error": "unexpected_error", "message": str(e)})

    @mcp.tool
    async def pine_send_auth_confirmation(
        session_id: str,
        message_id: str,
        data: dict[str, Any],
    ) -> str:
        """Submit an OTP/verification code for an [AUTH NEEDED] event.

        ALWAYS ask the user for the code first — never guess or hallucinate
        OTPs, PINs, or security answers.

        Args:
            session_id: The session requesting authentication.
            message_id: The auth request's message_id from pine_get_history.
            data: Verification data, e.g. {"code": "123456"}.
        """
        try:
            client = await pine.ensure_connected()
            client.send_auth_confirmation(session_id, message_id, data)
            return json.dumps({
                "success": True,
                "message": "Auth confirmation sent. Use pine_get_history to see what happens next.",
            })
        except PineAIError as e:
            return json.dumps({"success": False, "error": e.code, "message": str(e)})
        except Exception as e:
            return json.dumps({"success": False, "error": "unexpected_error", "message": str(e)})

    @mcp.tool
    async def pine_send_location_response(
        session_id: str,
        message_id: str,
        latitude: str,
        longitude: str,
    ) -> str:
        """Submit location coordinates for a [LOCATION NEEDED] event. Ask the user if unknown.

        Args:
            session_id: The session requesting the location.
            message_id: The location request's message_id from pine_get_history.
            latitude: Latitude string (e.g. "37.7749").
            longitude: Longitude string (e.g. "-122.4194").
        """
        try:
            client = await pine.ensure_connected()
            client.send_location_response(session_id, message_id, latitude, longitude)
            return json.dumps({
                "success": True,
                "message": "Location sent. Use pine_get_history to see what happens next.",
            })
        except PineAIError as e:
            return json.dumps({"success": False, "error": e.code, "message": str(e)})
        except Exception as e:
            return json.dumps({"success": False, "error": "unexpected_error", "message": str(e)})

    @mcp.tool
    async def pine_send_location_selection(
        session_id: str,
        message_id: str,
        places: list[dict[str, Any]],
    ) -> str:
        """Submit a location selection from options Pine provided.

        Args:
            session_id: The session with the location selection.
            message_id: The location selection request's message_id.
            places: Selected place objects from Pine's provided options.
        """
        try:
            client = await pine.ensure_connected()
            client.send_location_selection(session_id, message_id, places)
            return json.dumps({
                "success": True,
                "message": "Location selection sent. Use pine_get_history to see what happens next.",
            })
        except PineAIError as e:
            return json.dumps({"success": False, "error": e.code, "message": str(e)})
        except Exception as e:
            return json.dumps({"success": False, "error": "unexpected_error", "message": str(e)})
