# Use Pine MCP from your own agent with a Pine Platform API key

This guide is for a Pine Platform API partner whose product is an LLM agent. Your agent gives a task to Pine for one of your end users, for example a phone call to a business. Then it follows the progress and results through the hosted Pine MCP server.

Each of your end users is a separate Pine user, called a *managed user*. Your agent acts for one managed user at a time, with your secret key and that user's Pine user ID.

## Choose MCP or the Python SDK

Both use the same key and the same managed users. Use one of them; you do not need both.

| | Pine MCP | [Python SDK](https://github.com/19PINE-AI/pine-assistant-python) |
| --- | --- | --- |
| Language | Any language with an MCP client | Python |
| Who decides what to call | Your LLM, from the tool descriptions | Your code |
| Replies from Pine | Read with a tool call | Real-time event stream |
| Good for | An agent that decides when to use Pine | A fixed flow, for example "a button starts a booking call" |

## Before you start

Get a key from Pine, and create a managed user for each end user. Store the managed user's `id` (its Pine user ID) with your own user record. See [Platform API for partners](https://github.com/19PINE-AI/pine-assistant-python#platform-api-for-partners) in the Python SDK, or the [HTTP API for managed users](https://github.com/19PINE-AI/pine-assistant-python/blob/main/docs/http-api.md) for other languages.

The Pine MCP server is at `https://mcp.pine.im/mcp`.

## Step 1: connect to Pine MCP for one managed user

Every request to Pine MCP carries two headers:

```text
Authorization: Bearer <your secret key>
Pine-Managed-User-Id: <the managed user's Pine user ID>
```

The header selects the user, so **one MCP connection acts for one managed user**. Build the MCP client in code, for the user of the current request. A static configuration file with one fixed user does not work for a product with many users.

- The server is stateless. A new connection for each request is fine.
- Use an MCP client that supports custom headers on Streamable HTTP. Plugin installs and consumer apps that only offer browser login cannot use key mode.

Example with the Claude Agent SDK (Python):

```python
import asyncio
import os

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, create_sdk_mcp_server, query, tool

PINE_MCP_URL = "https://mcp.pine.im/mcp"
PINE_API_KEY = os.environ["PINE_API_KEY"]
SYSTEM_PROMPT = open("pine_system_prompt.txt").read()  # see step 2


@tool("wait", "Wait the given number of seconds (1-60) before continuing.", {"seconds": int})
async def wait(args):
    seconds = max(1, min(60, int(args["seconds"])))
    await asyncio.sleep(seconds)
    return {"content": [{"type": "text", "text": f"waited {seconds} seconds"}]}


def pine_options(pine_user_id: str) -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        mcp_servers={
            "pine": {
                "type": "http",
                "url": PINE_MCP_URL,
                "headers": {"Authorization": f"Bearer {PINE_API_KEY}", "Pine-Managed-User-Id": pine_user_id},
            },
            "agent": create_sdk_mcp_server("agent", tools=[wait]),
        },
        tools=[],
        allowed_tools=["mcp__pine__*", "mcp__agent__wait"],
        max_turns=20,
    )


async def run(pine_user_id: str, user_message: str) -> str | None:
    async for message in query(prompt=user_message, options=pine_options(pine_user_id)):
        if isinstance(message, ResultMessage):
            return message.result
    return None


print(asyncio.run(run("<the managed user's Pine user ID>", "Ask Pine what it needs from me to send flowers to my mom next Friday.")))
```

The `wait` tool is your own. It lets the model pause between reads of Pine's history (see step 3).

## Step 2: give your agent a system prompt

Pine MCP sends tool descriptions, but no usage policy. Add Pine guidance to your agent's system prompt, and change it to fit your product. For example:

```text
Pine AI carries out real-world tasks for the user, such as phone calls to businesses. You hand a task to Pine, then follow its progress and results through these tools.

Start or continue work
- When the user follows up on earlier work, list sessions and reuse the matching one. If several could match, ask which one; do not create a replacement session.
- For a new task, create one session, then send one clear instruction. Creating a session does not start work; Pine continues after it gets the instruction, and no separate start call exists.
- Write the instruction with: Goal; Contact, phone number or search criteria; Relevant background and requirements. Carry over every constraint the user gave. For a public business, give its number or enough detail for Pine to find it. For a private contact, use only a number the user gave; never guess one. Ask the user only for details that block progress, and never invent personal facts.
- A clear task request is the user's authorization; do not ask a separate "start?" question.

Follow progress
- Read the session history for Pine's questions, forms, state changes, replies and task completion. The result is in the task_finished event and Pine's last messages. Outcomes are shareable results; read them when you need them.
- Pine works asynchronously. A reply to a question usually takes seconds; a phone task can take minutes or longer.
  - If you have a tool to wait, wait about 10-30 seconds between history reads while the user is waiting for a reply.
  - If you have no way to wait, read the history at most twice. If Pine is still working, tell the user and end your turn. Check again when the user returns or when your system asks you to.
- A delivered message, a session state or a timestamp does not prove that a call happened or that the task succeeded. Report only what Pine's replies and history say. If the result is unclear, say what is known.

Answer Pine
- When Pine asks a question, get the answer from the conversation or from the user, and send it to the same session.
- When history contains a form, submit it with the form-response tool, using that form's message_id and its exact field names.
- Do not show Pine links (session_url, task_url) to the user; they cannot open them. Collect answers in this conversation and submit them yourself.

Uncertain writes
- Creating sessions, sending messages and submitting forms are not idempotent. After a timeout or unknown result, do not retry blindly: list recent sessions or read the session history first, then decide.

Ending tasks
- Call pine_end_task only when the user asks to end a task. Pine decides whether it can end; if it refuses, explain the returned reason. Ending a task does not prove that an ongoing call has stopped.
- With a Pine Platform API key, a task ends by itself when it produces its result, and pine_end_task is refused. Continue later work in a new session.

Do not repeat sensitive form values without need.
```

Parts you will often change:
- **Waiting.** Keep the branch that matches your agent: a wait tool, or "end your turn".
- **Forms.** Decide whether the agent fills a form from the conversation, or asks the end user first.

## Step 3: follow the result after the conversation

A phone task can take minutes or hours. Pine MCP does not call you back, and there is no webhook. So:

1. When your agent creates a session, store the `session_id` with the end user and the conversation.
2. Run a background job that, for each open session, connects as that managed user and calls `pine_get_history` every few minutes.
3. When the history has a `session:task_finished` event, tell the end user through your own product: a chat message, a push notification or an email.

The result of a task is in the `session:task_finished` event and in Pine's last messages. `pine_get_outcomes` returns the shareable results of a session.

A managed user's task ends by itself when it produces its result. Later work for the same user goes in a new session.

## Tools

| Tool | What it does | Notes for managed users |
| --- | --- | --- |
| `pine_session_create` | Creates a session. Does not start work. | |
| `pine_session_list` | Lists the user's sessions. | Use it to find earlier work. |
| `pine_session_get` | Reads one session's metadata. | |
| `pine_send_message` | Sends an instruction or an answer to Pine. Pine may then start work, including phone calls. | Not idempotent. |
| `pine_get_history` | Reads messages and events: Pine's replies, questions, forms, state, completion. | Opens a short real-time connection for each call. |
| `pine_send_form_response` | Answers a form from Pine. | Not idempotent. |
| `pine_get_outcomes` | Reads the session's shareable results. | |
| `pine_end_task` | Ends a task on request. | Always refused with 409 `session_close_not_eligible`. |

Results contain `session_url` and sometimes `task_url`. These are Pine web pages. A managed user has no Pine login, so do not show them to your end users.

## Errors

Rejected before any work, as an HTTP status on the MCP request:

| HTTP | Error | Cause |
| --- | --- | --- |
| 400 | `invalid_request` | `Pine-Managed-User-Id` is missing, repeated or not a valid user ID. |
| 401 | `invalid_token` | The bearer is not a Pine secret key. |

Returned as a tool error (`isError: true`, with `error.code` and `error.status_code`):

| Status | `error.code` | Cause | What to do |
| --- | --- | --- | --- |
| 401 | `unauthorized` | Unknown or revoked key, or a key of the other environment. | Check the key and the environment. |
| 403 | `platform_access_suspended` | Your access is suspended. | Contact Pine. |
| 403 | `platform_managed_user_unavailable` | The managed user is banned or archived. | Do not retry for this user. |
| 404 | `platform_managed_user_not_found` | The ID is not one of your managed users. | Check the stored ID. |
| 402 | `platform_spend_limit_reached` | Your monthly credit limit is used up. | Contact Pine, or wait for the next month. |
| 409 | `platform_session_limit_reached` | Your running-task limit is reached. | Retry later, when a task has finished. |
| 409 | `platform_session_state_conflict` | The session no longer accepts input. | Continue in a new session. |
| 409 | `session_close_not_eligible` | `pine_end_task` for a managed user. | Do not call it. |
| 429 | `too_many_requests` | Your request quota is used up. | Retry with exponential backoff and jitter. |
| — | `connection_error` | The real-time connection was refused or failed. | Check the key and ID; retry later. |

Tool errors never contain your key or the upstream response body.

## Checklist

- [ ] Key stored on the server only, never in prompts or logs.
- [ ] Pine user ID stored for each end user.
- [ ] One MCP connection per request, with that user's headers.
- [ ] Pine guidance in the system prompt, adapted to your product.
- [ ] Pine links not shown to end users.
- [ ] `session_id` stored, and a background job to follow open sessions.
- [ ] Tool errors handled by `error.code`.
