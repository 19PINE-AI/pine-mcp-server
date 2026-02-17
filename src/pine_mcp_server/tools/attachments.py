"""Attachment tools — upload and delete files."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from pine_assistant.errors import PineAIError

if TYPE_CHECKING:
    from fastmcp import FastMCP
    from pine_mcp_server.server import PineClient


def register_attachment_tools(mcp: FastMCP, pine: PineClient) -> None:

    @mcp.tool
    async def pine_upload_attachment(file_path: str) -> str:
        """Upload a file (bill, screenshot, document) for a Pine AI session.

        Returns attachment metadata — pass it to pine_send_message via the
        attachments parameter to include the file in a message.

        Args:
            file_path: Absolute path to the file to upload.
        """
        try:
            result = await pine.client.sessions.upload_attachment(file_path)
            return json.dumps({
                "success": True,
                "attachments": result,
                "message": "File uploaded. Pass the attachments list to pine_send_message.",
            })
        except FileNotFoundError:
            return json.dumps({"success": False, "error": "file_not_found", "message": f"File not found: {file_path}"})
        except PineAIError as e:
            return json.dumps({"success": False, "error": e.code, "message": str(e)})
        except Exception as e:
            return json.dumps({"success": False, "error": "unexpected_error", "message": str(e)})

    @mcp.tool
    async def pine_delete_attachment(attachment_id: str) -> str:
        """Delete a previously uploaded attachment.

        Args:
            attachment_id: The attachment ID from pine_upload_attachment.
        """
        try:
            await pine.client.sessions.delete_attachment(attachment_id)
            return json.dumps({"success": True, "message": f"Attachment {attachment_id} deleted."})
        except PineAIError as e:
            return json.dumps({"success": False, "error": e.code, "message": str(e)})
        except Exception as e:
            return json.dumps({"success": False, "error": "unexpected_error", "message": str(e)})
