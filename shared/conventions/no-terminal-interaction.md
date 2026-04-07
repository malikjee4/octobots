# No Terminal Interaction

You run in an unattended tmux pane. **No human sees your terminal output.** Text you print goes nowhere. Questions you ask get no answer. Menus you present get no selection.

The user's only interface is **Telegram**.

## The Rule

**Never ask questions, present options, or wait for input in your terminal output.**

If you catch yourself writing "What do you think?", "Options:", "Awaiting direction", or anything that expects a human response — stop. Use the `notify` MCP tool instead.

## How to Reach the User

Any role can message the user directly via Telegram by calling the **`notify` MCP tool** (`mcp__notify__notify`):

```
notify(message="your message here")
```

The tool auto-tags your message with your role name: `[python-dev] your message here`. Messages support HTML formatting: `<b>bold</b>`, `<i>italic</i>`, `<code>inline code</code>`, `<pre>code block</pre>`.

**Long messages are auto-sent as documents.** If your message exceeds 4000 characters, `notify` automatically writes it to a temp `.md` file and sends it as a document attachment with a short caption preview. You don't need to do anything special.

## Sending Files

To send a file (epic document, screenshot, report, voice note, etc.) directly to the user, call the same tool with a `file` argument:

```
notify(message="Epic ready for review", file="/abs/path/to/epic-001.md")
notify(message="Login flow screenshot", file="/abs/path/to/login.png")
notify(message="Daily voice brief",     file="/abs/path/to/brief.ogg")
```

The transport is chosen automatically by file extension:

- `.jpg/.jpeg/.png/.webp/.gif` → photo
- `.ogg/.oga/.opus`            → voice note (voice-bubble UI)
- `.mp3/.m4a/.aac/.flac/.wav`  → audio player
- anything else                → document (raw bytes preserved)

**When to attach a file vs send text:**
- **Short status/question (< 10 lines):** plain `notify(message=...)` — appears inline in chat
- **Documents, reports, epics, stories, screenshots:** `notify(message=..., file=...)` — user gets a downloadable file with the message as caption
- **Long output you didn't plan for:** just plain `notify(message=...)` — it auto-converts to a document if over 4000 chars


## Writing Good Telegram Messages

Telegram messages arrive on a phone. They must be **self-contained, scannable, and actionable**.

### Structure

```
[Context] → [Key info] → [Action needed or status]
```

### Do

- **Lead with the point.** "Login endpoint done, PR #45 ready" — not "I've been working on the login endpoint and after analyzing the requirements..."
- **Include links.** Issue numbers, PR numbers, file paths — anything the user needs to follow up.
- **State what you did, what's next, or what you need.** Every message should answer one of these.
- **When asking a question:** give context, state your recommendation, ask for confirmation.
- **Keep it under 3-4 lines.** If it's longer, put the details on the GitHub issue and link to it.

### Don't

- Don't send empty status updates: "Working on it" with no detail.
- Don't send walls of text — that's what issue comments are for.
- Don't send raw error dumps — summarize the problem.
- Don't send multiple messages in rapid succession — batch them.

### Examples

**Status update (good):**
```
✅ TASK-003 done. Login endpoint with JWT + rate limiting.
PR #45: github.com/org/repo/pull/45
Tests pass. Notified QA via taskbox.
```

**Status update (bad):**
```
I've completed the implementation of the login endpoint.
```

**Question (good):**
```
❓ Auth approach for US-002: OAuth (GitHub/Google) or API keys?
OAuth is more work but better UX for end users.
I'd recommend OAuth. Want me to proceed, or go with API keys?
```

**Question (bad):**
```
What's the play?
1. Option A
2. Option B
3. Option C
```

**Blocked (good):**
```
🚫 Blocked on TASK-005: Stripe API key missing from .env.
Need STRIPE_SECRET_KEY to test payment flow.
Can you add it to .env.shared?
```

**Starting work (good):**
```
🔧 Starting TASK-003 (#103): login endpoint.
Approach: FastAPI + python-jose for JWT. ETA: this session.
```

## When the User Doesn't Respond

Telegram is async. The user may not reply immediately.

- **If you asked a question with a recommendation:** proceed with your recommendation. Note on the issue what you decided and why.
- **If you need a blocking decision** (credentials, access, scope change): notify, then move to the next available task. Don't idle.
- **If your inbox is empty and there's nothing to do:** send one "Standing by" message, then wait for taskbox. Don't spam.

## Summary

| Need | Channel | Who |
|------|---------|-----|
| Tell the user something | `notify` MCP tool | Any role |
| Ask the user something | `notify` MCP tool + your recommendation | Any role |
| Send a document/report/image/voice | `notify(message=..., file=...)` | Any role |
| Tell a teammate something | Taskbox | Any role |
| Record a decision/result | GitHub issue comment | Any role |
| Terminal output | **Nobody. Ever.** | — |
