# Overnight Autonomy Setup V1

Status: active reference
Created: 2026-04-17
Maintainer: Will + Lattice

## Purpose

Record the exact overnight autonomy setup used for Loom and Rivet on the first kids-game-utilities implementation push.

This doc is intended to be refined/reused if the pattern works well.

## Targets

- Loom: frontend / UI / shell
- Rivet: backend / API / persistence / contracts

## Source docs

- `docs/IMPLEMENTATION_ARCHITECTURE_V1.md`
- `docs/IMPLEMENTATION_PLAN_V1.md`

## Work logs

Use:

- `docs/WORKLOG_LOOM.md`
- `docs/WORKLOG_RIVET.md`

Expected update moments:

- starting a chunk
- changing a contract assumption
- finishing a chunk
- tests run
- blocker encountered
- next intended step

Keep logs lightweight.

## Coordination rules

1. Work in lane by default.
2. If blocked on a seam, update the work log first.
3. Then message the other agent directly with:
   - the concrete seam question
   - current assumption
   - proposed resolution
4. If still unresolved, escalate to Lattice.

Use Lattice for:

- shared-vs-app boundary disputes
- contract changes with broader implications
- uncertainty about whether to defer or extract a surface

## Current babysitter reality

Current harness babysitter is useful, but limited.

What it does now:

- periodic re-prompts
- quiet-period suppression via `minQuietSeconds`
- bounded duration
- prompt count tracking
- event logging around pokes and suppression

What it does **not** yet do:

- true target-idle/stall detection before re-prompting
- consult current target busy/mid-turn state before prompting
- direct effectiveness scoring for each re-prompt

So for now:

- use a moderate interval
- use quiet-period suppression
- log prompt counts and suppression events
- infer effectiveness later from work logs and subsequent activity

## Suggested overnight prompt pattern

Common intent:

- continue autonomously until blocked or until the current phase is genuinely complete
- prefer implementation + tests over more speculation
- do not stop just because chat is quiet
- update the work log as you go
- message the other agent on seam issues
- escalate to Lattice only for real unresolved blockers

## Suggested babysitter settings

Recommended starting point:

- interval: 20 minutes
- min quiet: 20 minutes
- duration: overnight window or bounded prompt count equivalent
- operator context:
  - availability: unavailable
  - current context: asleep
  - preferred escalation surface: tui
  - escalation threshold: blockers only

This is conservative enough to keep momentum without spamming.

## What to inspect next morning

1. Loom/Rivet work logs
2. babysitter run status / prompt counts
3. babysitter poke and suppression events
4. messages exchanged between Loom and Rivet
5. tests added/run
6. real code progress in frontend/backend areas

## How to judge effectiveness

Because babysitter is not yet true idle-aware, effectiveness is inferred rather than directly measured.

Useful signals:

- did prompts correspond to resumed work-log entries soon after?
- did the agents keep moving without human nudges?
- did seam issues get resolved agent-to-agent rather than waiting?
- was the overnight progress mostly implementation and testing rather than speculation?

## Next refinement ideas

If this pattern works, likely improvements are:

- better idle-aware babysitter behavior
- suppress babysitter pokes when hook-derived agent status is `busy`
- add tests for “do not poke mid-turn/busy target”
- explicit babysitter history/status inspection helpers
- stronger automatic logging of reprompt -> subsequent activity correlation
- reusable prompt templates for frontend/backend paired work
