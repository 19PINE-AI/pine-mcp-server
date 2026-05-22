"""Authentication tools — email verification flow."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from pine_mcp_server.tools._helpers import format_error

if TYPE_CHECKING:
    from fastmcp import FastMCP
    from pine_mcp_server.server import PineClient


def register_auth_tools(mcp: FastMCP, pine: PineClient) -> None:

    @mcp.tool
    async def pine_auth_request_code(email: str) -> str:
        """Step 1: Send a verification code to the user's Pine AI email.

        After calling this, ask the user to check their email (including spam)
        and provide the code. Then call pine_auth_verify_code with the code
        and the returned request_token.
        """
        try:
            result = await pine.client.auth.request_code(email)
            token = result.get("request_token", "")
            return json.dumps({
                "success": True,
                "request_token": token,
                "message": f"Verification code sent to {email}. Ask the user for the code.",
            })
        except Exception as e:
            return format_error(e)

    @mcp.tool
    async def pine_auth_verify_code(email: str, code: str, request_token: str) -> str:
        """Step 2: Verify the email code and activate Pine AI credentials.

        Use the request_token from pine_auth_request_code and the code
        the user received. On success, all Pine tools become available.
        """
        try:
            result = await pine.client.auth.verify_code(email, code, request_token)
            access_token = result.get("access_token", "")
            user_id = result.get("id", "")
            pine.set_credentials(access_token, user_id)
            return json.dumps({
                "success": True,
                "message": "Authentication successful. You can now use all Pine AI tools.",
                "user_id": user_id,
            })
        except Exception as e:
            return format_error(e)
