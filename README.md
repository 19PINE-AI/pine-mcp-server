# Pine Assistant MCP

[Pine AI](https://pine.im) is a personal assistant for real-world tasks. This
repository provides the Pine Assistant plugin for MCP clients and the earlier local
Python stdio server.

## Pine Assistant plugin

Pine Assistant (`pine`) connects a supported client to Pine through a remote MCP
server and opens browser-based OAuth authorization when the client connects.
Bring Pine AI into your agent to handle real-world tasks and follow up on
progress and results. The shared skill guides the agent through the available
tools and any details or account actions a task needs.

### Install and authorize

Ask your agent to set up Pine:

> Read https://pine.im/features/mcp and help me install Pine.

Or follow the instructions for your client below.

Install **Pine Assistant** (`pine`) from the **Pine AI** (`pine-ai`) marketplace, then begin a new
conversation. Connect and complete the Pine browser authorization when your
client asks.

**Codex**

```bash
codex plugin marketplace add https://github.com/19PINE-AI/pine-mcp-server.git --ref main
codex plugin add pine@pine-ai
```

To update it:

```bash
codex plugin marketplace upgrade pine-ai
codex plugin add pine@pine-ai
```

**Claude Code**

```bash
claude plugin marketplace add https://github.com/19PINE-AI/pine-mcp-server.git
claude plugin install pine@pine-ai
```

To update it:

```bash
claude plugin marketplace update pine-ai
claude plugin update pine@pine-ai
```

If you installed Pine from the older `pine` marketplace, migrate only that
installation before adding `pine-ai`:

```bash
codex plugin remove pine@pine
codex plugin marketplace remove pine
codex plugin marketplace add https://github.com/19PINE-AI/pine-mcp-server.git --ref main
codex plugin add pine@pine-ai
```

For Claude Code, uninstall `pine@pine` and remove its `pine` marketplace in
the plugin manager, then add the GitHub marketplace above and install
`pine@pine-ai`. This migration does not require removing unrelated client
settings or MCP connections. The renamed plugin may ask you to authorize Pine
again; do not copy tokens between the old and new configuration.

Use Pine naturally after authorizing, for example:

> Use Pine to contact a nearby bike repair shop and ask about tune-up availability.

Pine keeps working after you leave. Ask your agent for progress or results when
you return. Complete payment, account connection, or phone verification in Pine
when the task directs you there.

In Codex, use `$pine` to load the shared guidance. In Claude Code, use
`/pine:pine`.

### Connect from another MCP client

Add a Streamable HTTP MCP server with this configuration, then use the
client's Connect or Authorize control to complete OAuth in a browser:

```json
{
  "mcpServers": {
    "pine": {
      "type": "http",
      "url": "https://mcp.pine.im/mcp"
    }
  }
}
```

### Cursor

Cursor supports the Pine Assistant plugin and a manual MCP connection.

For a local native plugin install, clone this repository, copy
`plugins/pine` to `~/.cursor/plugins/local/pine`, and reload Cursor:

```bash
git clone https://github.com/19PINE-AI/pine-mcp-server.git
mkdir -p ~/.cursor/plugins/local
cp -R pine-mcp-server/plugins/pine ~/.cursor/plugins/local/pine
```

Use **Developer: Reload Window**, then enable Pine in **Customize** and complete
browser authorization. When updating, replace the existing local `pine` folder
instead of copying a second `pine` folder inside it. Team administrators can also
import this repository as a marketplace.

For a manual connection, add the Streamable HTTP configuration above in
Cursor's MCP settings, then use its authorization control.

## Legacy local stdio server

The published `pine-mcp-server` Python package is separate from the plugin
distribution: `pip` and `uvx` do not install the
[client plugin](https://github.com/19PINE-AI/pine-mcp-server/tree/main/plugins/pine).
It runs a local stdio MCP server backed by the
[`pine-assistant`](https://pypi.org/project/pine-assistant/) SDK.

Install it with pip:

```bash
pip install pine-mcp-server
```

Or run it without installing:

```bash
uvx pine-mcp-server
```

Configure a stdio MCP client with the executable and Pine credentials. For
example:

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

If installed with pip, use `pine-mcp-server` as `command` and omit `args`.
Alternatively, authenticate with the `pine_auth_request_code` and
`pine_auth_verify_code` tools. Do not put access tokens in plugin files.

### Environment

| Variable | Required | Description |
| --- | --- | --- |
| `PINE_ACCESS_TOKEN` | Yes* | Pine AI access token |
| `PINE_USER_ID` | Yes* | Pine AI user ID |
| `PINE_BASE_URL` | No | Pine AI backend URL (default: `https://www.19pine.ai`) |
| `PINE_DEVICE_ID` | No | Stable device identifier for subprocess clients; otherwise a new ID may be generated when `~/.pine/device_id` is unwritable. |

\* Not required when authenticating at runtime with the auth tools.

### Tools

| Area | Tools |
| --- | --- |
| Authentication | `pine_auth_request_code`, `pine_auth_verify_code` |
| Sessions | `pine_session_create`, `pine_session_list`, `pine_session_get`, `pine_session_delete`, `pine_session_url` |
| Conversation | `pine_get_history`, `pine_send_message`, `pine_send_form_response`, `pine_send_auth_confirmation`, `pine_send_location_response`, `pine_send_location_selection` |
| Tasks | `pine_task_start`, `pine_task_stop` |
| Attachments | `pine_upload_attachment`, `pine_delete_attachment` |
| Social and scheduling | `pine_social_share`, `pine_update_call_reminder` |

The local server follows a load-conversation model: create or select a
session, send a message, and read history for subsequent questions and
results. It does not stream real-time updates.

## Releases

Plugin releases use immutable `plugin-vX.Y.Z` tags. The Python package uses
`vX.Y.Z` tags and is published independently to PyPI. Keep all plugin manifest
versions synchronized before creating a plugin tag. Plugin tags run validation
without publishing to PyPI. Python tags must match the version in
`pyproject.toml` before publication.

The installation commands track `main`. Merge and validate a release before
tagging it, bump plugin versions when changing the package, and never move an
existing release tag. To pin a plugin release in Codex, add the repository with
`--ref plugin-vX.Y.Z` instead of `--ref main`. After updating a plugin, start a
new client conversation (or reload the client) to load its changes.

## Development

For plugin testing, clone this repository and edit `plugins/pine/.mcp.json` in
that working copy to point at the endpoint under test. Do not commit a local
endpoint or credentials. Use separate client configuration directories so the
local marketplace does not collide with your normal Pine installation.

From the repository root, test Codex:

```bash
PINE_CODEX_TEST_CONFIG="$(mktemp -d)"
CODEX_HOME="$PINE_CODEX_TEST_CONFIG" codex plugin marketplace add .
CODEX_HOME="$PINE_CODEX_TEST_CONFIG" codex plugin add pine@pine-ai
CODEX_HOME="$PINE_CODEX_TEST_CONFIG" codex
```

Or Claude Code:

```bash
PINE_CLAUDE_TEST_CONFIG="$(mktemp -d)"
CLAUDE_CONFIG_DIR="$PINE_CLAUDE_TEST_CONFIG" claude plugin marketplace add .
CLAUDE_CONFIG_DIR="$PINE_CLAUDE_TEST_CONFIG" claude plugin install pine@pine-ai
CLAUDE_CONFIG_DIR="$PINE_CLAUDE_TEST_CONFIG" claude
```

Keep the same temporary directory while testing. Each isolated client may
require its own client login and Pine authorization. Remove the temporary
configuration after testing; do not copy credentials into the repository.

Validate the Claude package and marketplace with:

```bash
claude plugin validate plugins/pine --strict
claude plugin validate . --strict
```

CI also checks cross-client metadata and bundled paths. For the legacy Python
server's development dependencies:

```bash
pip install -e ".[dev]"
```

## License

MIT
