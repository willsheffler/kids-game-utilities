# CAP Brief: Loom + Rivet V1 Architecture Review

Status: executed
Created: 2026-04-17
Coordinator: Lattice

## Participants

- Loom: frontend
- Rivet: backend

Both should review architecture and boundary decisions, not just their own lane.

## Purpose

Run a joint architecture/boundary CAP before implementation planning.

The goal is to pressure-test the frontend/backend split and the technical home for shared vs app-specific code.

## Inputs

Primary context:

- `docs/IMPLEMENTATION_ARCHITECTURE_V1.md`
- `sheffler-standards/KIDS_GAME_DEV_DOGFOOD_V1.md`

## Current coordinator assumptions

- first dogfood app is a flexible dev shell to exercise the tooling
- near-term usage will likely be light content annotation / image-picking style work with Madeira
- multi-project support should be exercised from the start
- shared timeline remains the default visible chat model
- screenshots are first-class artifacts, not just report attachments
- reports are agent-drafted, backend-persisted
- global artifact manifest per app/workspace is acceptable for now
- skip auth on first pass
- trigger mode is inline near the composer
- passive capture should be exposed as agent-facing tooling plus visible inspectability, not rich user-facing settings yet
- game-dev / learning-specific code should live in this repo
- common reusable components can live in `agent-common-base/components` for now
- service migration should remain a separate concern

## Questions for CAP

1. What should live in shared reusable code versus this repo’s app-specific shell/features?
2. What are the most important frontend/backend boundary cuts for:
   - chat/runtime
   - screenshot artifacts
   - report persistence
   - project context
3. Is multi-project-from-start still a good implementation choice given the current cut line, or is there a safer narrow version of it?
4. What should the global artifact manifest own in v1?
5. What is the minimum viable report-viewer/editor loop?
6. What would be materially wrong if shipped under the current assumptions?
7. After architecture review, what phased implementation plan would you recommend for Loom (frontend) and Rivet (backend)?

## Requested output shape

Please answer in two parts:

1. architecture / boundary review
2. phased implementation plan

Be explicit when recommending:

- keep
- move
- defer
- split

## Outcome

This CAP was run and converged enough to support implementation.

See:

- `docs/IMPLEMENTATION_ARCHITECTURE_V1.md`
- harness CAP artifacts under:
  - `~/.local/share/pensieve-harness/cap/kids_game_utilities_impl_v1/`
