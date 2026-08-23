import tempfile
import unittest
from pathlib import Path

from governed_agent_plane import ControlPlane


class ControlPlaneTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.plane = ControlPlane(root / "state", root / "workspace")

    def tearDown(self):
        self.temp.cleanup()

    def test_preview_approve_execute_and_audit(self):
        action = self.plane.propose("write_text", {"path": "reports/demo.txt", "text": "verified\n"}, "agent", action_id="a1")
        self.assertEqual("pending_approval", action["status"])
        self.assertIn("9 bytes", self.plane.preview("a1")["effect"])
        self.plane.approve("a1", "human")
        executed = self.plane.execute("a1", "local-executor")
        self.assertEqual("executed", executed["status"])
        self.assertEqual("verified\n", (self.plane.workspace / "reports/demo.txt").read_text())
        self.assertEqual(["proposed", "approved", "executed"], [event["event"] for event in self.plane.audit()])

    def test_execution_requires_approval_and_is_single_use(self):
        self.plane.propose("make_directory", {"path": "safe"}, "agent", action_id="a2")
        with self.assertRaisesRegex(ValueError, "must be approved"):
            self.plane.execute("a2", "executor")
        self.plane.approve("a2", "human")
        self.plane.execute("a2", "executor")
        with self.assertRaisesRegex(ValueError, "must be approved"):
            self.plane.execute("a2", "executor")

    def test_workspace_escape_is_blocked_during_preview(self):
        self.plane.propose("write_text", {"path": "../outside.txt", "text": "no"}, "agent", action_id="a3")
        with self.assertRaisesRegex(ValueError, "escapes"):
            self.plane.preview("a3")

    def test_payload_tampering_breaks_approval(self):
        action = self.plane.propose("write_text", {"path": "one.txt", "text": "one"}, "agent", action_id="a4")
        self.plane.approve("a4", "human")
        path = self.plane.actions / "a4.json"
        changed = self.plane.get("a4")
        changed["payload"]["text"] = "changed"
        self.plane._save(path, changed)
        with self.assertRaisesRegex(ValueError, "no longer matches"):
            self.plane.execute("a4", "executor")


if __name__ == "__main__":
    unittest.main()
