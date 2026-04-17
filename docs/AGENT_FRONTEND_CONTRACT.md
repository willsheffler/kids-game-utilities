# Agent–Frontend Contract

Status: working
Created: 2026-04-17
Purpose: Document the stable tags and conventions the agent can use to interact with the kids-game-utilities frontend.

## Screenshot suggestions

The agent can suggest screenshots by including a tag in its reply text:

```
[suggest-screenshot: "description of what to capture"]
```

The frontend interprets this as a toast notification: "📷 Screenshot: description — ✓ Capture / ✕ Dismiss"

If the user accepts:
1. The game canvas is captured
2. The agent's suggested label is pre-filled (user can edit)
3. The screenshot is uploaded as an artifact via POST /api/artifacts
4. The artifact appears in the artifact tray

If the user dismisses:
- The suggestion is recorded in the manifest with status "dismissed"
- It remains visible in history but not in the active tray

### When to suggest screenshots

- After a visible UI change the user just made
- When the user describes a bug or visual issue
- At natural session breakpoints (before moving to a new feature)
- When generating a session report (to ensure evidence is captured)

### Example

```
That jump physics looks great! The arc feels much more natural now.
[suggest-screenshot: "improved jump arc with gravity tweaks"]
```

## Report generation

The agent can trigger report creation by including:

```
[save-report]
# Session Report: 2026-04-17

## What was built
- Added jump physics with configurable gravity
- Fixed collision detection on platforms

## Screenshots
![improved jump arc](session-logs/assets/2026-04-17/jump_arc_ab12.png)

## Quiz
Q: What parameter controls how fast the character falls?
A: The gravity constant (higher = faster fall)
[/save-report]
```

The frontend extracts the markdown between `[save-report]` and `[/save-report]` and sends it to POST /api/reports.

## Trigger mode

The current trigger mode affects whether user messages are sent to the agent:

- `auto`: every message triggers the agent (default)
- `mention`: only messages containing @agent trigger
- `manual`: messages are displayed but never sent to the agent automatically

The agent can check the current mode in the system note, but should not try to change it.

## Project context

When the user switches projects, the agent receives a system message:

```
[project-switched: rpsbattle]
```

The agent should adjust its working directory context accordingly.

## Artifact references in chat

When referencing artifacts, use the artifact path:

```
Looking at the screenshot you took earlier (session-logs/assets/2026-04-17/jump_arc_ab12.png),
I can see the collision box is slightly off...
```

The frontend may render artifact paths as clickable thumbnails in a future version.
