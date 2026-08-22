# Architecture

## Design summary

A small API and state store sit between agent clients and side-effecting tools. Policy evaluation happens before execution; the executor receives only the approved action payload.

## Main components

- Receive a typed task
- Build an immutable action preview
- Apply policy and approval gates
- Execute exactly the approved action
- Record evidence and final state

## Initial implementation boundary

Start with a local, inspectable implementation. Prefer plain files, small typed schemas, and deterministic commands before introducing a database, hosted service, or provider-specific adapter.

## Verification

Every MVP feature should have at least one fixture, one failure case, and one visible verification artifact. Keep inferred behavior separate from measured behavior.
