from __future__ import annotations

import argparse
import json

from .plane import ControlPlane


def object_value(value: str) -> dict:
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise argparse.ArgumentTypeError("payload must be a JSON object")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="governed-agent-plane")
    root.add_argument("--state", default=".agent-plane")
    root.add_argument("--workspace", default=".agent-plane-workspace")
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("init")
    propose = commands.add_parser("propose")
    propose.add_argument("kind", choices=["write_text", "append_text", "make_directory"])
    propose.add_argument("--payload", type=object_value, required=True)
    propose.add_argument("--requested-by", required=True)
    propose.add_argument("--ttl", type=int, default=3600)
    propose.add_argument("--id")
    for name in ("preview", "get"):
        item = commands.add_parser(name)
        item.add_argument("action_id")
    approve = commands.add_parser("approve")
    approve.add_argument("action_id")
    approve.add_argument("--approver", required=True)
    execute = commands.add_parser("execute")
    execute.add_argument("action_id")
    execute.add_argument("--executor", required=True)
    commands.add_parser("list")
    commands.add_parser("audit")
    return root


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    plane = ControlPlane(args.state, args.workspace)
    try:
        if args.command == "init":
            plane.init()
            output = {"state": str(plane.state_dir), "workspace": str(plane.workspace)}
        elif args.command == "propose":
            output = plane.propose(args.kind, args.payload, args.requested_by, ttl_seconds=args.ttl, action_id=args.id)
        elif args.command == "preview":
            output = plane.preview(args.action_id)
        elif args.command == "get":
            output = plane.get(args.action_id)
        elif args.command == "approve":
            output = plane.approve(args.action_id, args.approver)
        elif args.command == "execute":
            output = plane.execute(args.action_id, args.executor)
        elif args.command == "list":
            output = plane.list()
        else:
            output = plane.audit()
    except (ValueError, FileExistsError, json.JSONDecodeError) as error:
        parser.error(str(error))
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0
