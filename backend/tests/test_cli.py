"""Tests for the local run CLI."""
import json
import subprocess
import sys
import unittest


class RunQuestCliTestCase(unittest.TestCase):
    def test_lists_quests(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-m", "backend.app.cli.run_quest", "--list-quests"],
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("quest_hello_world", completed.stdout)
        self.assertIn("quest_profile_settings", completed.stdout)

    def test_runs_with_inline_override(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "backend.app.cli.run_quest",
                "--quest-id",
                "quest_hello_world",
                "--profile-id",
                "cli-test",
                "--override-inline",
                "app/main.py=from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get('/hello')\ndef hello() -> dict[str, str]:\n    return {'message': 'Broken'}\n",
                "--print-json",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(completed.stdout)
        self.assertEqual(payload["quest_id"], "quest_hello_world")
        self.assertLess(payload["summary"]["technical_score"], 100.0)
        self.assertTrue(payload["workspace_files"])


if __name__ == "__main__":
    unittest.main()
