"""Run a preview, approval, execution, and audit flow."""

import json
import tempfile
from pathlib import Path

from governed_agent_plane import ControlPlane

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    plane = ControlPlane(root / "state", root / "workspace")
    plane.propose("write_text", {"path": "report.txt", "text": "Evidence-backed output\n"},
                  "planner", action_id="demo-action")
    preview = plane.preview("demo-action")
    plane.approve("demo-action", "human")
    result = plane.execute("demo-action", "local-executor")
    print(json.dumps({"preview": preview, "status": result["status"],
                      "evidence": result["execution"]["evidence"],
                      "audit_events": [event["event"] for event in plane.audit()]}, indent=2))
