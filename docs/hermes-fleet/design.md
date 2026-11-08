# Bot fleet redesign — decisions

Terms are defined in [CONTEXT.md](CONTEXT.md). Settled with the owner, 2026-11-08. Numbers are the order the questions were settled in.

## Findings behind the design

- Each bot has one canonical session; peer DMs and watchdog wakes run as turns in it.
- Headless turns use `approvals.single_query_mode: deny`, so a command the smart judge approves in a Bot Chat turn is refused there (one Worker: 766 approved vs 36 blocked for `script execution via heredoc`). Bots then report "cannot".
- Compaction summaries reach 40–90k characters and drop text; earlier tool results shrink to one-line stubs. The bots had no `session_search` toolset to look them up.
- Every bot memory sat at the 2,200-character cap; 475 queued memory writes from Hermes's review were stale. `/memory approve all` stops trying after 3 failures (`_MAX_CONSOLIDATION_FAILURES_PER_TURN`). One approval removed the most needed lesson.
- One game PR: 756 posts, 1.1M characters, one of them from the owner. Manager's posts there were mostly build-slot scheduling.
- `skills.auto_load` is rendered once per agent and survives compaction unchanged; it does not see later edits.

## Decisions

| # | Topic | Decision |
|---|---|---|
| 2 | Headless-turn approvals | Keep `single_query_mode: deny`; teach bots the route around a block. |
| 3 | Lesson storage | Layered: procedures become tools, lessons go to shared homes, bot memory keeps only self-facts. Memory cap may rise only a little. |
| 4 | Old queue | All queued memory writes moved out of the queues into a dated backup folder. |
| 6 | Advisor authority | Merges on its own unless the PR needs eye review. |
| 7 | Eye review | Required when the game's output differs in any way; not when output is shown identical. |
| 8 | Merge proof | Red on base, green on head, identical-output comparison and criteria evidence, all from runs the Advisor starts itself. |
| 9 | Advisor model | Opus 5.5, effort `high`, no fallback of any kind. |
| 10 | Pro limit | Advisor wakes on events only; at the limit it does nothing and the watchdog says so once. |
| 11 | Reviewer | Keeps diff rounds. Advisor takes final review, the main clone and merging, and audits Reviewer (reviewer misses). |
| 12 | Findings | One Worker-facing list, Issues to Fix; each item names a criterion, repo rule or shown breakage. Anything else is a spec question for the Advisor. Enforced in `review.py`. |
| 13 | PR posts | Only state changes: PR body as summary, Issues to Fix, `Fixed #N at <sha>`, label lines, merge proof or eye-review request. No acks or progress. Scheduling leaves PRs. `comment.py` enforces a length cap. |
| 14 | Error reports | Self-check required by `label.py` / `comment.py`; routed per #27. |
| 15–16 | Homes | Specific → the project directory (`.memory/lessons/`, `tools/`, …). General → this repository, `memory/shared/<domain>/` (repos to merge later). |
| 17 | Reading lessons | `INDEX.md` of both homes in the prompt; fresh `lesson.py search` at the self-check, before writing a lesson, and on a matching symptom. |
| 18 | Upkeep | Advisor re-checks a lesson when it fails in use, and merges/retires when an index passes ~60 lines. Each lesson carries `Verified: <date> at <sha>`. Retired lessons move to `lessons/retired/`. |
| 19 | Lesson pipeline | Watchdog detects; the bot that erred writes a draft lesson with evidence; Advisor reviews; owner gets a daily digest and corrects or retires. Hermes memory review off (`memory.nudge_interval: 0`). |
| 20 | Advisor review timing | Daily batch, just before the digest. |
| 21 | Measuring | Watchdog counts per bot, role, PR and day, against a baseline from history; shown in the digest with the Advisor's own weekly token use. |
| 22–23 | Analysis | Advisor wakes when a rate is ≥1.5× baseline over 7 days with ≥5 events, held 2 days, 7-day cooldown; margins calibrated on history first. |
| 24 | Advisor's fleet authority | On its own: lessons, tools, one-rule SOUL edits for other bots (reverted if the count does not move in 7 days). Owner: its own SOUL, every `config.yaml` change, authority changes, deletions. |
| 25 | Rollout | Baseline → lesson homes → enforcing tools → Advisor → watchdog → seat and tool moves; counts checked after each step. |
| 26 | Manager | Keeps planning, issues, docs and relaying Worker questions. An item has one holder; once with the Advisor, only the Advisor pings the owner. |
| 27 | Routing | Spec questions: Reviewer → Advisor. Self-check reports: Worker → Manager → Advisor, Manager forwarding the report unchanged plus its own analysis and proposed fix. Other questions: first line answers when a source covers it, quoting it; otherwise escalates. Every Advisor answer carries a draft lesson; a repeat escalation means the teaching failed. Advisor escalations per week go in the digest. |
| 28 | Supervision | Advisor checks every first-line item at first, per bot and category (Manager self-check analyses, Manager answers, Reviewer Issues to Fix, Reviewer passes). At 90% agreement over the last 20, that category drops to a 1-in-5 spot check; a spot-check disagreement restores full checking. Each disagreement carries a draft lesson. Agreement rates go in the digest. |
| 29 | Check timing | Gate (before effect): spec questions, self-check escalations, Reviewer PR passes, Manager answers that change an issue's ask. Daily-batch audit (after): Reviewer Issues to Fix, explanatory Manager answers; a disagreement returns as an Issue to Fix the next morning. |
| 30 | Ready for review | The Worker puts its own merge proof in the PR body: per criterion, red-on-base/green-on-head evidence, probe reading or output comparison with command and result; identical-output comparison for "no visible change"; results pass `unity-test-failures.py --stale`. `label.py` refuses `waits-for-review` without an evidence line per criterion. A proof that does not reproduce for the Advisor is a reviewer miss and a lesson for the Worker. |
| 31 | Compaction recovery | Add `session_search` to every bot's `platform_toolsets` (owner's config change). The self-check "tried" line searches the bot's own session for the failing command and quotes whether it worked before. |
| 32 | Merge right | Fallback providers stay; `fallback_model` removed from every bot. `approvals.deny` blocks merging (`*gh pr merge*`, `*pulls/*/merge*`) on every bot except the Advisor, proven with `deny_check.py`. |
| 33 | Manager's docs push | `docs_push.py` pushes only markdown on Manager's paths after the repo's doc validator and the privacy grep, fast-forward only. Manager denies `*git push*`; Reviewer and Workers deny pushes to `main`. |
| 34 | Tool homes | Specific (game probes, play/join/latency scripts, board tool) → the game repo's `tools/`, moved in one Worker PR. General (GitHub/Discord/Hermes/lint helpers, Unity process and build helpers, `.meta` integrity) → this repository's `tools/<area>/`. Other projects' tools → their own folders. Toolbox-first rule checks the project index, then the General one. |
| 35 | Unity seat | `seat.py take/renew/release/status` with leases (N min + 10 min grace). Seat needed for player/server builds, player runs and Editor play runs; not for compiles or EditMode. Priority: owner's Editor (detected, preempts) > Advisor merge proofs > Workers in arrival order. Build and play scripts refuse without the caller's lease. Watchdog reads seat state. |
| 36 | Advisor on Discord | Advisor takes Reviewer's Discord account and thread, digest included; Reviewer reaches the owner only through the Advisor. Manager's `config.yaml` `platforms.discord.home_channel` must point at Manager's own thread. No `run_script.py`: General lesson 1 is "write the script with `write_file` into `.scratch/`, run `python <file>`". |
| 37 | This document | Lives here, as General. Project-specific pointers go in the game repo's `AGENTS.md` once built. |

| 38 | Tool creation | Any bot drafts a tool in its worktree's `.scratch/` and may use it for its own task. Promotion needs `--help`, an index line, clean `loop_guard.py`, and one recorded example run (command and real output) in the header, enforced by `tool_check.py`; a draft duplicating an existing tool is refused (add a flag instead). Specific tools enter through the Worker's PR; General tools through the Advisor's daily batch. |
| 39 | Non-intrusive tools | Declare: the header lists every program the tool starts; `tool_check.py` refuses undeclared process starts and any GUI program. Contain: toolbox tools run through `fleet_run.py` (grown from `mem_guard.py`), one Windows Job Object per run with a deadline and memory cap, whole tree killed on exit, timeout or crash. Stop: `fleet-stop` kills fleet jobs only, never the owner's processes. Watchdog kills a spawn storm (same program started >5 times in 10 min inside fleet jobs) and reports once. Every stop prints one fixed line with its reason and a distinct exit code (finished, deadline, memory cap, spawn storm, stopped by owner); the self-check quotes that line, so a bot does not report a stop as a bug. |

| 40 | Tool use | Skill list in the prompt; a search runs before any new script is written. `fleet_run.py` logs tool, bot, exit reason and duration. A real failure in use goes to the Advisor's batch (fix the tool or record how to call it). Unused for 60 days → `retired/` with last use date, moved not deleted. Digest lists most-used, failed and promoted tools. |
| 41 | Tools as skills | Every tool is a skill (`SKILL.md` + `scripts/`), grouped by job, description written by symptom; body holds usage, `spawns:`, `fleet_run` stop lines and the example run. General → this repository's `skills/`; Specific → the game repo's `.agents/skills/` (repo added with `hermes skills trust`). The skill list replaces tool indexes; `tool_check.py` becomes `skill_check.py`. Toolbox skills are excluded from Hermes's curator. |
| 42 | Toolsets | Every bot, Advisor included: `terminal`, `file`, `skills`, `vision`, `delegation`, `memory`, `session_search`. Removed: `todo` (never called) and Manager's `cronjob` (never called; the watchdog cron runs without it). `skills.create_dir` per bot points at `profiles/<bot>/skill-drafts/`, so self-made skills stay drafts until promoted. No web or browser: no recorded need. |

## Still open

- Hundreds of one-off review drafts in `profiles/reviewer-tmp/`: owner decides on removal.
- Turns repeated word for word after a gateway outage (seen on one Worker): cause not yet found.
