"""Abuse-control tests for the public alpha hardening sprint."""
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.core.config import settings
from backend.app.core.dependencies import (
    get_agent_profile_repository,
    get_alpha_store,
    get_post_mortem_repository,
    get_public_alpha_service,
    get_quest_repository,
    get_ranking_repository,
    get_replay_event_repository,
    get_run_repository,
)
from backend.app.core.rate_limit import reset_rate_limiter
from backend.app.main import app
from backend.app.sandbox.runner import DockerSandboxProvider


class AbuseControlsTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._original_db_path = settings.ALPHA_DB_PATH
        self._tmp_dir = TemporaryDirectory()
        settings.ALPHA_DB_PATH = str(Path(self._tmp_dir.name) / "abuse-controls.sqlite3")
        self.client = TestClient(app)
        self.opponent = TestClient(app)
        self.login_suffix = uuid4().hex[:8]
        get_quest_repository.cache_clear()
        get_agent_profile_repository.cache_clear()
        get_run_repository.cache_clear()
        get_replay_event_repository.cache_clear()
        get_post_mortem_repository.cache_clear()
        get_ranking_repository.cache_clear()
        get_public_alpha_service.cache_clear()
        get_alpha_store.cache_clear()
        reset_rate_limiter()

    def tearDown(self) -> None:
        get_public_alpha_service.cache_clear()
        get_alpha_store.cache_clear()
        settings.ALPHA_DB_PATH = self._original_db_path
        self._tmp_dir.cleanup()

    def _login(self, client: TestClient, github_login: str) -> None:
        start = client.post(
            "/api/v1/auth/github/start",
            json={
                "github_login": github_login,
                "invite_code": settings.DEFAULT_ALPHA_INVITE_CODE,
            },
        )
        self.assertEqual(start.status_code, 200)
        callback = client.get(start.json()["authorization_url"])
        self.assertEqual(callback.status_code, 200)

    def _create_profile(self, profile_id: str = "abuse-profile") -> None:
        response = self.client.post(
            "/api/v1/profiles/",
            json={
                "id": profile_id,
                "name": "Abuse Profile",
                "archetype": "debugger",
                "planning_style": "tests_first",
                "preferred_stack": ["python"],
                "engineering_principles": ["Preservar contratos"],
                "modules": ["test_debugging"],
                "constraints": {
                    "allow_dependency_install": True,
                    "allow_external_network": False,
                    "allow_schema_change": True,
                    "max_runtime_minutes": 10,
                },
                "memory": {"slots": []},
                "limits": {"max_files_edited": 25, "max_runs": 5},
            },
        )
        self.assertEqual(response.status_code, 201)

    def _create_ready_battle(self) -> str:
        self._login(self.client, f"left-{self.login_suffix}")
        self._login(self.opponent, f"right-{self.login_suffix}")
        left_profiles = self.client.get("/api/v1/profiles/mine").json()
        right_profiles = self.opponent.get("/api/v1/profiles/mine").json()
        battle = self.client.post(
            "/api/v1/battles/",
            json={
                "quest_id": "quest_hello_world",
                "agent_profile_id": left_profiles[0]["id"],
                "workspace_files": {"app/main.py": "from fastapi import FastAPI\n"},
            },
        )
        self.assertEqual(battle.status_code, 201)
        battle_id = battle.json()["battle"]["id"]
        joined = self.opponent.post(
            f"/api/v1/battles/{battle_id}/join",
            json={
                "agent_profile_id": right_profiles[0]["id"],
                "workspace_files": {"app/main.py": "from fastapi import FastAPI\n"},
            },
        )
        self.assertEqual(joined.status_code, 200)
        return battle_id

    def test_auth_start_rate_limit_returns_429(self) -> None:
        original_enabled = getattr(settings, "RATE_LIMIT_ENABLED", True)
        original_limit = getattr(settings, "RATE_LIMIT_AUTH_REQUESTS_PER_MINUTE", 10)
        try:
            settings.RATE_LIMIT_ENABLED = True
            settings.RATE_LIMIT_AUTH_REQUESTS_PER_MINUTE = 2
            statuses = [
                self.client.post(
                    "/api/v1/auth/github/start",
                    json={
                        "github_login": f"limited-{index}-{self.login_suffix}",
                        "invite_code": settings.DEFAULT_ALPHA_INVITE_CODE,
                    },
                ).status_code
                for index in range(3)
            ]
        finally:
            settings.RATE_LIMIT_ENABLED = original_enabled
            settings.RATE_LIMIT_AUTH_REQUESTS_PER_MINUTE = original_limit

        self.assertEqual(statuses, [200, 200, 429])

    def test_secure_cookie_setting_is_honored(self) -> None:
        original_secure = getattr(settings, "SESSION_COOKIE_SECURE", False)
        try:
            settings.SESSION_COOKIE_SECURE = True
            start = self.client.post(
                "/api/v1/auth/github/start",
                json={
                    "github_login": f"secure-{self.login_suffix}",
                    "invite_code": settings.DEFAULT_ALPHA_INVITE_CODE,
                },
            )
            response = self.client.get(start.json()["authorization_url"])
        finally:
            settings.SESSION_COOKIE_SECURE = original_secure

        self.assertEqual(response.status_code, 200)
        self.assertIn("Secure", response.headers["set-cookie"])

    def test_run_rejects_parent_directory_workspace_path(self) -> None:
        self._create_profile()

        response = self.client.post(
            "/api/v1/runs/",
            json={
                "quest_id": "quest_hello_world",
                "agent_profile_id": "abuse-profile",
                "workspace_files": {"../app/main.py": "print('bad')"},
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid workspace path", response.json()["detail"])

    def test_battle_create_rejects_parent_directory_workspace_path(self) -> None:
        self._login(self.client, f"creator-{self.login_suffix}")
        profile_id = self.client.get("/api/v1/profiles/mine").json()[0]["id"]

        response = self.client.post(
            "/api/v1/battles/",
            json={
                "quest_id": "quest_hello_world",
                "agent_profile_id": profile_id,
                "workspace_files": {"../app/main.py": "print('bad')"},
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid workspace path", response.json()["detail"])

    def test_battle_submit_rejects_absolute_workspace_path(self) -> None:
        battle_id = self._create_ready_battle()

        response = self.client.post(
            f"/api/v1/battles/{battle_id}/submit",
            json={"workspace_files": {"/tmp/app/main.py": "print('bad')"}},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid workspace path", response.json()["detail"])

    def test_workspace_file_count_limit_is_enforced(self) -> None:
        original_limit = getattr(settings, "MAX_WORKSPACE_FILES", 25)
        try:
            settings.MAX_WORKSPACE_FILES = 1
            self._create_profile("count-limit-profile")
            response = self.client.post(
                "/api/v1/runs/",
                json={
                    "quest_id": "quest_hello_world",
                    "agent_profile_id": "count-limit-profile",
                    "workspace_files": {
                        "app/main.py": "print('one')",
                        "app/extra.py": "print('two')",
                    },
                },
            )
        finally:
            settings.MAX_WORKSPACE_FILES = original_limit

        self.assertEqual(response.status_code, 400)
        self.assertIn("Too many workspace files", response.json()["detail"])

    def test_workspace_total_bytes_limit_is_enforced(self) -> None:
        original_limit = getattr(settings, "MAX_WORKSPACE_TOTAL_BYTES", 150000)
        try:
            settings.MAX_WORKSPACE_TOTAL_BYTES = 10
            self._create_profile("bytes-limit-profile")
            response = self.client.post(
                "/api/v1/runs/",
                json={
                    "quest_id": "quest_hello_world",
                    "agent_profile_id": "bytes-limit-profile",
                    "workspace_files": {"app/main.py": "x" * 11},
                },
            )
        finally:
            settings.MAX_WORKSPACE_TOTAL_BYTES = original_limit

        self.assertEqual(response.status_code, 400)
        self.assertIn("Workspace payload is too large", response.json()["detail"])

    def test_docker_runner_command_uses_hardened_container_flags(self) -> None:
        command = DockerSandboxProvider().build_docker_command(
            temp_path="/tmp/cqa_runs/example",
            script="print('ok')",
            timeout_seconds=10,
        )

        self.assertIn("--network", command)
        self.assertIn("none", command)
        self.assertIn("--read-only", command)
        self.assertIn("--security-opt", command)
        self.assertIn("no-new-privileges", command)
        self.assertIn("--cap-drop", command)
        self.assertIn("ALL", command)
        self.assertIn("--tmpfs", command)
        self.assertIn("/tmp:rw,noexec,nosuid,size=64m", command)


if __name__ == "__main__":
    unittest.main()
