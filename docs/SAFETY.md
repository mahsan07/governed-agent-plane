# Safety and Trust Boundaries

This project is designed to be useful without silently taking control of external systems.

## Required boundaries

- Default to read-only
- Never infer approval from conversation context
- Bind execution to the exact approved payload
- Reject expired, replayed, or already-claimed actions
- Keep secrets outside task records

## Default posture

- Read-only and dry-run modes come first.
- Human approval is required for external communication, spending, publication, destructive changes, access changes, and merges.
- Logs and examples must not contain secrets, private endpoints, personal identifiers, or private source material.
- Every side effect must be attributable to an explicit request and a verifiable execution record.
