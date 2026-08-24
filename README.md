# Governed Agent Plane

A local-first control plane for previewing, approving, executing, and auditing agent actions.

## Why this exists

Agent systems can perform useful work across tools, but users often cannot see what will happen, stop unsafe actions, or reconstruct why an action occurred.

## What it provides

Provide a durable action lifecycle: intent, preview, approval, execution, evidence, and rollback-aware status.

## Intended users

Builders operating multiple agents, tools, and local services who need explicit governance without giving up automation.

## Example

Preview a file export, require approval, execute it once, and show the evidence trail.

## Visual overview

![Governed Agent Plane architecture flow](assets/architecture-flow.svg)

[Open the architecture and sequence diagrams](docs/DIAGRAMS.md).

## Current status

Public scaffold. The repository defines the product contract and MVP boundaries before implementation begins.

## Documentation

- [Product definition](docs/PRODUCT.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Flow and sequence diagrams](docs/DIAGRAMS.md)
- [Safety](docs/SAFETY.md)
- [Roadmap](docs/ROADMAP.md)

## License

MIT. See [LICENSE](LICENSE).
