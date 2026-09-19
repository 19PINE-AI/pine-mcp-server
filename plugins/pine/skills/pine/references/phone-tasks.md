# Phone tasks

Use this reference when preparing, continuing, or interpreting a Pine phone task. Follow the shared session, authorization, form, and recovery rules in [Pine Assistant](../SKILL.md).

## Prepare the instruction

Organize the task message using this short template. It guides the client's handoff to Pine; the user does not need to fill it out, and no new tool parameters are required.

```text
Goal:
Contact / phone number / search criteria:
Relevant background and requirements: (if available)
```

The goal and enough information to identify or find the contact are required. Use the current conversation first. For public businesses or organizations, pass a known number or enough information for Pine to find a public number. For private contacts, use a number provided by the user or obtained from an authorized, available source; do not assume it can be found through public search or guess it. Include the country code when known, and clarify ambiguous dialing information when needed.

Always carry over the user's known constraints and any relevant background. Omit an optional heading when it has no content. Ask about missing information only when it blocks progress; otherwise Pine can ask follow-up questions during the task. Do not invent personal facts, preferences, or authorization to fill the template.

## Continue the task

When Pine asks a question or presents a form, use the shared reply/form workflow in the original session. If Pine requires a verified phone number, direct the user to the returned Pine task page. Only treat a `phone_number` connector as requiring verification when its latest event requires action and is not connected. Typing a number in chat or submitting a form does not bind the account. After verification, query the same session again.

## Interpret call results

Use Pine's actual replies, history, and outcomes to report who was contacted and what happened. Message delivery, a session status, or a timestamp alone does not prove a call was placed, a person answered, or the objective succeeded. If the result is unclear, say what is known and retrieve the relevant history instead of inventing a successful outcome.

A request to end the task uses the shared `pine_end_task` workflow. Its response alone does not prove an ongoing call has disconnected.
