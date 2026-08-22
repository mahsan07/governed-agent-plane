# Product Definition

## One-sentence promise

A local-first control plane for previewing, approving, executing, and auditing agent actions.

## Problem

Agent systems can perform useful work across tools, but users often cannot see what will happen, stop unsafe actions, or reconstruct why an action occurred.

## Solution

Provide a durable action lifecycle: intent, preview, approval, execution, evidence, and rollback-aware status.

## Users

Builders operating multiple agents, tools, and local services who need explicit governance without giving up automation.

## Core workflow

- Receive a typed task
- Build an immutable action preview
- Apply policy and approval gates
- Execute exactly the approved action
- Record evidence and final state

## MVP acceptance criteria

- Typed task and action schemas
- Read-only preview mode
- Approval state machine
- Single-use action claim with expiry
- Append-only audit record
- Local JSON or SQLite state store

## Non-goals for the first release

- No hosted multi-tenant service
- No embedded credentials or provider accounts
- No irreversible external actions without a visible approval boundary
- No claim of production readiness before tests and evidence exist
