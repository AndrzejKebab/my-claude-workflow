# Context usage, and why you want to see it early

Claude Code shows a context indicator only when the window is nearly full. That is not a setting.
The component returns before it renders anything:

```js
if (BEv.level === "ok" || bDL) { return null }
```

While the level is `ok`, nothing is drawn. No setting, environment variable, or plugin moves that
threshold, so the first honest signal a session gives you arrives when it is almost too late to act
on. `cc-statusline` and `cc-context-warn` supply the earlier signal.

## Why it matters more than it looks

A running context is re-sent on every request. The number on screen is the *size* of the window, not
the volume you pay for. Measured on one real session:

| | |
|---|---|
| context at the end | 831k tokens |
| requests | 938 |
| average context re-read per request | 493k tokens |
| cache reads billed | 462.5M tokens |
| cache writes | 4.29M tokens |
| output | 0.89M tokens |
| cost | $168.34 |

The window held 831k tokens. The session billed 466.8M input-side tokens. The context you can see is
0.18% of the tokens you paid for.

The blended rate works out at $0.361 per million input-side tokens, which is cheap — cache reads bill
at a fraction of fresh input, and almost everything here was a cache read. Nothing was mispriced. The
cost came from volume, and the volume is the product of context size and request count. Both grow
together as a session runs, so the spend curve bends upward while the visible number moves slowly.
That is the case for watching the gauge from the start instead of from 90%.

## `cc-statusline`

Wired by `install.sh` as `statusLine.command`. Since 2.1.x the CLI hands the statusline the numbers
directly, so nothing has to parse a transcript:

```js
context_window: {
  total_input_tokens, total_output_tokens,
  context_window_size, current_usage,
  used_percentage, remaining_percentage
}
```

`used_percentage` is rounded to a whole number. On a 1M window one point is 10k tokens, so
`cc-statusline` recomputes from the raw counts and shows a decimal below 10%. It truncates rather
than rounds, so the figure never overstates and always agrees with the bar.

```
Opus 5 xhigh ░░░░░░░░░░ 4.2% 42k / 1.00M $1.23
Opus 5 xhigh ███░░░░░░░ 32% 328k / 1.00M $1.23
Opus 5 xhigh ████████░░ 84% 845k / 1.00M $1.23
```

Green below 50%, amber to 80%, red above. Window size comes from the payload, so a 200k session
reports against 200k without configuration.

Write it in shell, not in a runtime that needs a startup. The statusline re-renders constantly:
`cc-statusline` costs 13ms, and the `npx tsx` script it replaced cost 594ms and leaked `npm notice`
lines into the status text.

## `cc-context-warn`

A `UserPromptSubmit` hook. It announces each 10% band as the window fills:

```
context 30% used — 300k of 1.00M tokens
```

Hooks do not receive `context_window` — the statusline is the only consumer the CLI gives it to — so
this reads the newest main-thread `usage` record out of the transcript and applies the CLI's own
formula:

```
used = input_tokens + cache_creation_input_tokens + cache_read_input_tokens
```

Subagent turns carry `isSidechain`, and their usage belongs to their own window, so those records are
skipped. The transcript is read backwards and stops at the first match, which keeps the cost flat as
the file grows.

Output goes out as `{"systemMessage": ...}`. That reaches the terminal without being injected into
the model's context, which matters for a message whose whole purpose is to report that the context is
filling up.

Bands fire once, on the way up. State lives in `$XDG_RUNTIME_DIR/cc-ctx-band-<session_id>`, so a
session that compacts and climbs again re-announces from wherever it lands.

The window defaults to 1M. Export `CC_CONTEXT_WINDOW=200000` for a session that is not on the long
window.

## `cc-cost-tick`

Wired on `Stop` and on `UserPromptSubmit`. It announces what the turn cost and rings a cash
register:

```
+$0.42 — $179.07 this session
```

Hook payloads carry no cost field at all. `total_cost_usd` goes to the statusline and nowhere else,
so `cc-statusline` parks it in `$XDG_RUNTIME_DIR/cc-cost-<session_id>` and `cc-cost-tick` reads it
there. Install a different statusline and the ticker goes quiet rather than guessing at prices.

The figure the CLI gives is a running total, so the ticker reports the difference since it last
spoke. Both events are wired because either may be the first to see the money land, and whichever
does claims the delta — so a turn is announced once, not twice. Anything under a cent is held back.

First sight of a session is handled by its size. A young session has spent nearly nothing, so
counting from zero is right. An old one is being joined mid-flight, and announcing its accumulated
total as a single turn would be a lie, so the ticker adopts the figure quietly and starts counting
from there.

The bell is synthesised on first use into `$XDG_CACHE_HOME/cc-ca-ching.wav` rather than shipped as a
blob: two strikes on inharmonic partials with a noise transient at each onset, the second higher and
longer than the first. Generating it costs 78ms once; every tick after that is 11ms. Playback goes
through `pw-play`, `paplay`, or `aplay`, detached, so a stalled audio server never holds up a turn.

```
CC_CACHING=0            keep the figure, drop the sound
CC_CACHING_SOUND=<wav>  play your own
CC_CACHING_MIN=0.01     floor below which nothing is said
```

## A plugin cannot do the statusline half

A plugin can carry the hook. It cannot register a statusline — there is no plugin-statusline path in
the CLI, and `statusLine` is a settings key. That is why `install.sh` claims the slot directly, and
why it refuses to take the slot when something else already holds it.
