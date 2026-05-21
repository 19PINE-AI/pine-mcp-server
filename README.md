# Pine Assistant MCP Server

A local [MCP](https://modelcontextprotocol.io) server that lets any LLM agent manage [Pine AI](https://www.19pine.ai) tasks — negotiate bills, cancel subscriptions, resolve disputes, and make phone calls on your behalf.

Built on the [`pine-assistant`](https://pypi.org/project/pine-assistant/) Python SDK.

## Installation

```bash
pip install pine-mcp-server
```

Or run directly with `uvx` (no install needed):

```bash
uvx pine-mcp-server
```

## Quick Start

### 1. Get your Pine AI credentials

You need an `access_token` and `user_id` from Pine AI. Either:

- Sign up at [19pine.ai](https://www.19pine.ai) and retrieve your credentials, or
- Use the built-in auth tools (`pine_auth_request_code` / `pine_auth_verify_code`) to authenticate via email.

### 2. Configure your MCP client

**Claude Desktop** — edit `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "pine-assistant": {
      "command": "uvx",
      "args": ["pine-mcp-server"],
      "env": {
        "PINE_ACCESS_TOKEN": "your-access-token",
        "PINE_USER_ID": "your-user-id"
      }
    }
  }
}
```

**Cursor** — edit `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "pine-assistant": {
      "command": "uvx",
      "args": ["pine-mcp-server"],
      "env": {
        "PINE_ACCESS_TOKEN": "your-access-token",
        "PINE_USER_ID": "your-user-id"
      }
    }
  }
}
```

If you prefer `pip install`, replace `"command": "uvx"` with `"command": "pine-mcp-server"` and remove the `"args"` field.

### 3. Use it

Ask your LLM agent something like:

> "Use Pine AI to negotiate my Comcast internet bill. My account number is 12345."

The agent will create a session, send your request, and check back for updates.

## How It Works

The server follows a **"load conversation"** model — like refreshing a browser page:

1. **Create a session** — `pine_session_create`
2. **Send a message** describing the task — `pine_send_message`
3. **Wait, then check** what Pine replied — `pine_get_history`
4. **Start the task** when ready — `pine_task_start`
5. **Check again** for results — `pine_get_history`

There is no real-time streaming. The agent periodically loads the conversation history to see updates, similar to refreshing the Pine web app.

## Available Tools

### Authentication

| Tool | Description |
|------|-------------|
| `pine_auth_request_code` | Request a verification code via email |
| `pine_auth_verify_code` | Verify the code and obtain credentials |

### Sessions

| Tool | Description |
|------|-------------|
| `pine_session_create` | Create a new Pine session |
| `pine_session_list` | List sessions with optional filters |
| `pine_session_get` | Get details about a session |
| `pine_session_delete` | Delete a session |
| `pine_session_url` | Get the web URL to view a session |

### Conversation

| Tool | Description |
|------|-------------|
| `pine_get_history` | Load conversation history (the core "refresh" tool) |
| `pine_send_message` | Send a text message to Pine |
| `pine_send_form_response` | Submit a form that Pine sent |
| `pine_send_auth_confirmation` | Submit an OTP/verification code |
| `pine_send_location_response` | Submit location coordinates |
| `pine_send_location_selection` | Submit a location selection |

### Tasks

| Tool | Description |
|------|-------------|
| `pine_task_start` | Start task execution |
| `pine_task_stop` | Stop a running task |

### Attachments

| Tool | Description |
|------|-------------|
| `pine_upload_attachment` | Upload a local file (bill, screenshot, etc.) |
| `pine_delete_attachment` | Delete an uploaded attachment |

### Social & Scheduling

| Tool | Description |
|------|-------------|
| `pine_social_share` | Share results on social media to earn credits |
| `pine_update_call_reminder` | Update a scheduled call reminder |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `PINE_ACCESS_TOKEN` | Yes* | Pine AI access token |
| `PINE_USER_ID` | Yes* | Pine AI user ID |
| `PINE_BASE_URL` | No | Pine AI backend URL (default: `https://www.19pine.ai`) |
| `PINE_DEVICE_ID` | No | Stable device identifier. Recommended when the server runs as a subprocess (Claude Desktop, Cursor) — otherwise a fresh random ID is generated on each launch if `~/.pine/device_id` is unwritable. |

\* Not required if you authenticate at runtime using the auth tools.

## Development

```bash
pip install -e ".[dev]"
```

## License

MIT
