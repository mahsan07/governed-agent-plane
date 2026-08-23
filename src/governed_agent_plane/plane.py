"""Local-first governed action lifecycle."""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

SUPPORTED_ACTIONS = {"write_text", "append_text", "make_directory"}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class ControlPlane:
    """Store action intent, approval, execution evidence, and audit events locally."""

    def __init__(self, state_dir: str | Path, workspace: str | Path):
        self.state_dir = Path(state_dir)
        self.workspace = Path(workspace).resolve()
        self.actions = self.state_dir / "actions"
        self.claims = self.state_dir / "claims"
        self.audit_path = self.state_dir / "audit.jsonl"

    def init(self) -> None:
        self.actions.mkdir(parents=True, exist_ok=True)
        self.claims.mkdir(parents=True, exist_ok=True)
        self.workspace.mkdir(parents=True, exist_ok=True)

    def propose(
        self,
        kind: str,
        payload: dict[str, Any],
        requested_by: str,
        *,
        ttl_seconds: int = 3600,
        action_id: str | None = None,
    ) -> dict[str, Any]:
        self.init()
        self._validate_payload(kind, payload)
        if ttl_seconds < 1:
            raise ValueError("ttl_seconds must be positive")
        created = utc_now()
        action_id = action_id or uuid.uuid4().hex[:12]
        action = {
            "schema_version": 1,
            "id": action_id,
            "kind": kind,
            "payload": payload,
            "requested_by": requested_by,
            "created_at": created.isoformat(),
            "expires_at": (created + timedelta(seconds=ttl_seconds)).isoformat(),
            "status": "pending_approval",
            "approval": None,
            "execution": None,
        }
        action["intent_digest"] = self._intent_digest(action)
        path = self._path(action_id)
        if path.exists():
            raise FileExistsError(f"action already exists: {action_id}")
        self._save(path, action)
        self._audit("proposed", action_id, requested_by, {"intent_digest": action["intent_digest"]})
        return action

    def preview(self, action_id: str) -> dict[str, Any]:
        action = self.get(action_id)
        target = action["payload"].get("path")
        return {
            "id": action_id,
            "kind": action["kind"],
            "status": action["status"],
            "expires_at": action["expires_at"],
            "requires_approval": True,
            "target": str(self._safe_target(target)) if target else None,
            "effect": self._effect(action),
            "intent_digest": action["intent_digest"],
        }

    def approve(self, action_id: str, approver: str) -> dict[str, Any]:
        action = self.get(action_id)
        self._require_status(action, "pending_approval")
        self._require_not_expired(action)
        action["status"] = "approved"
        action["approval"] = {
            "approved_by": approver,
            "approved_at": utc_now().isoformat(),
            "intent_digest": action["intent_digest"],
        }
        self._save(self._path(action_id), action)
        self._audit("approved", action_id, approver, {"intent_digest": action["intent_digest"]})
        return action

    def execute(self, action_id: str, executor: str) -> dict[str, Any]:
        action = self.get(action_id)
        self._require_status(action, "approved")
        self._require_not_expired(action)
        if action["approval"]["intent_digest"] != self._intent_digest(action):
            raise ValueError("approved intent no longer matches action payload")
        claim = self.claims / f"{action_id}.claim"
        try:
            with claim.open("x", encoding="utf-8") as stream:
                stream.write(executor + "\n")
        except FileExistsError as error:
            raise ValueError("action has already been claimed for execution") from error

        try:
            evidence = self._apply(action)
            action["status"] = "executed"
            action["execution"] = {
                "executed_by": executor,
                "executed_at": utc_now().isoformat(),
                "evidence": evidence,
            }
            self._save(self._path(action_id), action)
            self._audit("executed", action_id, executor, evidence)
            return action
        except Exception as error:
            action["status"] = "failed"
            action["execution"] = {
                "executed_by": executor,
                "executed_at": utc_now().isoformat(),
                "error": str(error),
            }
            self._save(self._path(action_id), action)
            self._audit("failed", action_id, executor, {"error": str(error)})
            raise

    def get(self, action_id: str) -> dict[str, Any]:
        path = self._path(action_id)
        if not path.exists():
            raise ValueError(f"unknown action: {action_id}")
        return json.loads(path.read_text(encoding="utf-8"))

    def list(self) -> list[dict[str, Any]]:
        self.init()
        return [json.loads(path.read_text(encoding="utf-8")) for path in sorted(self.actions.glob("*.json"))]

    def audit(self) -> list[dict[str, Any]]:
        if not self.audit_path.exists():
            return []
        return [json.loads(line) for line in self.audit_path.read_text(encoding="utf-8").splitlines() if line]

    def _apply(self, action: dict[str, Any]) -> dict[str, Any]:
        target = self._safe_target(action["payload"]["path"])
        if action["kind"] == "make_directory":
            target.mkdir(parents=True, exist_ok=True)
            return {"path": str(target), "created": True}
        target.parent.mkdir(parents=True, exist_ok=True)
        text = action["payload"]["text"]
        mode = "a" if action["kind"] == "append_text" else "w"
        with target.open(mode, encoding="utf-8") as stream:
            stream.write(text)
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        return {"path": str(target), "sha256": digest, "bytes": target.stat().st_size}

    def _safe_target(self, relative: str) -> Path:
        target = (self.workspace / relative).resolve()
        try:
            target.relative_to(self.workspace)
        except ValueError as error:
            raise ValueError("action path escapes the configured workspace") from error
        return target

    @staticmethod
    def _validate_payload(kind: str, payload: dict[str, Any]) -> None:
        if kind not in SUPPORTED_ACTIONS:
            raise ValueError(f"unsupported action kind: {kind}")
        if not isinstance(payload.get("path"), str) or not payload["path"]:
            raise ValueError("payload.path must be a non-empty relative path")
        if kind in {"write_text", "append_text"} and not isinstance(payload.get("text"), str):
            raise ValueError("payload.text must be a string")

    @staticmethod
    def _effect(action: dict[str, Any]) -> str:
        if action["kind"] == "make_directory":
            return "Create a directory inside the configured workspace"
        verb = "Append to" if action["kind"] == "append_text" else "Write"
        return f"{verb} {len(action['payload']['text'].encode('utf-8'))} bytes inside the configured workspace"

    @staticmethod
    def _intent_digest(action: dict[str, Any]) -> str:
        intent = {key: action[key] for key in ("id", "kind", "payload", "requested_by", "created_at", "expires_at")}
        return hashlib.sha256(canonical(intent).encode("utf-8")).hexdigest()

    @staticmethod
    def _require_status(action: dict[str, Any], status: str) -> None:
        if action["status"] != status:
            raise ValueError(f"action must be {status}; current status: {action['status']}")

    @staticmethod
    def _require_not_expired(action: dict[str, Any]) -> None:
        if utc_now() >= datetime.fromisoformat(action["expires_at"]):
            raise ValueError("action approval window has expired")

    def _path(self, action_id: str) -> Path:
        return self.actions / f"{action_id}.json"

    @staticmethod
    def _save(path: Path, value: dict[str, Any]) -> None:
        temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
        temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, path)

    def _audit(self, event: str, action_id: str, actor: str, details: dict[str, Any]) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        record = {
            "at": utc_now().isoformat(),
            "event": event,
            "action_id": action_id,
            "actor": actor,
            "details": details,
        }
        with self.audit_path.open("a", encoding="utf-8") as stream:
            stream.write(canonical(record) + "\n")
