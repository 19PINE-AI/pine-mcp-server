---
name: pine
description: Connect to Pine AI to delegate supported real-world tasks and check, continue, or end existing Pine tasks. See the skill instructions for the integration's currently supported scope.
---

# Pine Assistant

Pine AI is an assistant that carries out real-world tasks. This MCP integration currently supports starting phone tasks only. Pine can search for public business phone numbers and do the preparation needed to complete those phone tasks. This is the integration's current release scope, not a limit on Pine's overall capabilities. When a user's goal can be handled by phone, treat it as a phone task without requiring them to explicitly say “call.” If they explicitly request a new task through email, browser operation, fax, or another non-phone method, explain that this integration does not yet support starting that kind of task; do not silently change it to a phone call.

For a new or continuing phone task, read [Phone tasks](references/phone-tasks.md) before composing the task instruction or interpreting call results. Existing Pine tasks can still be queried, answered, or ended using the available tools; do not reject an existing task merely because it used another execution method. Ordinary informational questions can be answered in the user's client without delegating to Pine.

A clear task request is authorization: do not ask a separate “start?” question. Gather only information that is necessary to act.

Use the currently discovered Pine tools by their semantic purpose; clients can namespace their names differently. The current service provides capabilities to create, list, and get sessions; send a message; read history and outcomes; submit a form response; and end a task (`pine_end_task`). It does not require a separate task-start call.

## Start or continue work

1. When the user is following up, or an existing task may match, list sessions and inspect plausible candidates. Reuse the matching session. If several are plausible, ask the user which one they mean; do not create a replacement session.
2. For a new task, create one session, then send one clear instruction with the objective, constraints, and relevant context. Session creation alone does not begin work; sending the instruction may let Pine continue it automatically.
3. Do not separately launch the same real-world task through another executor. Keep execution of the delegated task with Pine; include any useful research the client has already gathered.

Do not claim an external action happened or the task is complete from a session state, timestamp, or a `received`/`delivered` message receipt. A delivered message only confirms dispatch. A `delivery_failed` receipt does not establish that nothing was saved; inspect history before sending again. A session can remain processing after Pine has replied.

## Read updates and respond

Read the same session's history for questions, forms, state, task-finished content, connection or payment requests, and Agent replies. Read outcomes as well when they are relevant. Present Pine's actual reply and result facts faithfully; explain them if useful, but do not manufacture a summary, outcome, or terminal status.

Fetch bounded history pages. Follow the returned cursor (`next_message_id`) through the history tool's `before` argument only while another page is needed, respect the returned `order`, and retain the latest revision of duplicate events. Do not poll in a tight loop. If the client supports native waiting, use it before another bounded query; do not promise that updates will be delivered after the client exits. A later conversation can recover by listing sessions and reading the chosen session's history/outcomes.

For an ordinary Pine question, collect the user's answer in this conversation and send it to the same session. Keep sensitive form values, especially L2/L3 values, out of unnecessary narration.

## Forms and web actions

When history contains a form, submit it structurally when possible. Use that form's `message_id` and an `answers` map keyed by its exact field names; follow its visible required fields and allowed choices. The form-response tool preserves the original form association, so do not invent IDs, request metadata, or alternate field names. Its receipt still does not mean the task is finished.

If Pine requests payment, account connection, a verified phone-number binding, or another web intervention, give the user the returned Pine task link and have them complete it there. For a natural-language web-action request without an action card or task link, use the session link. After the user finishes the web action, query the original session again; do not resend the task instruction or create a new session. Use Pine's browser authorization with the user's existing account and credits; never ask for Pine login tokens, Pine API keys, or manually supplied Pine login credentials.

## End a task

When the user asks to end or stop a Pine task, identify the matching session and call `pine_end_task` with its `session_id`. A clear request is sufficient; clarify only when the target is ambiguous. Pine decides whether that task can be ended. If it rejects the request, explain the returned reason rather than creating a replacement task or trying another execution path.

Report the returned state faithfully: a user-ended task is not proof its objective succeeded, and the response does not prove an external action has already stopped. Do not end other tasks merely to free a task slot unless the user has authorized ending those tasks.

If ending the task times out or returns an unknown result, query the same session and its history before deciding what to do next. The state may have changed before notification to the agent failed; do not blindly repeat the write or claim that downstream execution has stopped.

## Uncertain writes

Creating sessions, sending messages, and submitting forms are non-idempotent. Do not blindly retry when a write times out, has an unknown result, or reports a transport/server failure. For an uncertain creation, first list recent sessions; for an uncertain message or form submission, first read that session's history and reconcile the result. Ask for direction when recovery still cannot establish what happened.
