"""Integration tests for the public alpha battle flow."""
import sqlite3
import time
import unittest
from contextlib import closing
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
    get_sandbox_runner,
)
from backend.app.core.rate_limit import reset_rate_limiter
from backend.app.main import app
from backend.app.models import BattleCreate, BattleJoin
from backend.app.services.alpha_store import AlphaStore
from backend.app.services.public_alpha_service import PublicAlphaService
from backend.app.services.quest_service import QuestService


class PublicAlphaFlowTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)
        cls.opponent = TestClient(app)

    def setUp(self) -> None:
        self.login_suffix = uuid4().hex[:8]
        self._original_db_path = settings.ALPHA_DB_PATH
        self._tmp_dir = TemporaryDirectory()
        settings.ALPHA_DB_PATH = str(Path(self._tmp_dir.name) / "public-alpha.sqlite3")
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
        callback_path = start.json()["authorization_url"]
        callback = client.get(callback_path)
        self.assertEqual(callback.status_code, 200)
        self.assertTrue(callback.json()["authenticated"])

    def test_real_oauth_start_builds_github_authorization_url(self) -> None:
        original_mock = settings.ENABLE_MOCK_GITHUB_AUTH
        original_client_id = settings.GITHUB_CLIENT_ID
        original_client_secret = settings.GITHUB_CLIENT_SECRET
        try:
            settings.ENABLE_MOCK_GITHUB_AUTH = False
            settings.GITHUB_CLIENT_ID = "test-client-id"
            settings.GITHUB_CLIENT_SECRET = "test-client-secret"

            start = self.client.post(
                "/api/v1/auth/github/start",
                json={"invite_code": settings.DEFAULT_ALPHA_INVITE_CODE},
            )

            self.assertEqual(start.status_code, 200)
            payload = start.json()
            self.assertIn("https://github.com/login/oauth/authorize?", payload["authorization_url"])
            self.assertIn("client_id=test-client-id", payload["authorization_url"])
            self.assertIn(f"state={payload['state']}", payload["authorization_url"])

            callback = self.client.get(
                "/api/v1/auth/github/callback",
                params={"state": payload["state"]},
            )
            self.assertEqual(callback.status_code, 400)
            self.assertIn("GitHub OAuth code is required", callback.json()["detail"])
        finally:
            settings.ENABLE_MOCK_GITHUB_AUTH = original_mock
            settings.GITHUB_CLIENT_ID = original_client_id
            settings.GITHUB_CLIENT_SECRET = original_client_secret

    def test_session_and_profiles_survive_service_cache_reset(self) -> None:
        github_login = f"persistent-alpha-{self.login_suffix}"
        self._login(self.client, github_login)

        first_profiles = self.client.get("/api/v1/profiles/mine")
        self.assertEqual(first_profiles.status_code, 200)
        self.assertGreaterEqual(len(first_profiles.json()), 4)

        get_public_alpha_service.cache_clear()
        get_alpha_store.cache_clear()

        me_after_reset = self.client.get("/api/v1/me")
        self.assertEqual(me_after_reset.status_code, 200)
        self.assertTrue(me_after_reset.json()["authenticated"])
        self.assertEqual(me_after_reset.json()["user"]["github_login"], github_login)

        profiles_after_reset = self.client.get("/api/v1/profiles/mine")
        self.assertEqual(profiles_after_reset.status_code, 200)
        self.assertEqual(
            [profile["id"] for profile in first_profiles.json()],
            [profile["id"] for profile in profiles_after_reset.json()],
        )

    def test_sqlite_store_records_initial_schema_migration(self) -> None:
        with TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "alpha.sqlite3"

            store = AlphaStore(str(db_path))

            with closing(sqlite3.connect(db_path)) as connection:
                rows = connection.execute(
                    "SELECT version, name FROM schema_migrations ORDER BY version"
                ).fetchall()

            self.assertEqual(rows, [(1, "initial_alpha_schema")])
            self.assertEqual(store.get_schema_version(), 1)

    def test_start_battle_enqueues_worker_job_without_running_inline(self) -> None:
        class FakeWorker:
            def __init__(self) -> None:
                self.enqueued: list[str] = []

            def enqueue(self, battle_id: str) -> None:
                self.enqueued.append(battle_id)

        with TemporaryDirectory() as temp_dir:
            store = AlphaStore(str(Path(temp_dir) / "alpha.sqlite3"))
            worker = FakeWorker()
            service = PublicAlphaService(
                store,
                QuestService(get_quest_repository()),
                get_sandbox_runner(),
                battle_worker=worker,
            )
            creator = store.upsert_user(f"creator-{self.login_suffix}")
            opponent = store.upsert_user(f"opponent-{self.login_suffix}")
            left = service.create_profile_from_template(creator, "buildknight")
            right = service.create_profile_from_template(opponent, "speedster")
            detail = service.create_battle(
                creator,
                BattleCreate(
                    quest_id="quest_hello_world",
                    agent_profile_id=left.id,
                    workspace_files={"app/main.py": "ready"},
                ),
            )
            service.join_battle(
                detail.battle.id,
                opponent,
                BattleJoin(agent_profile_id=right.id, workspace_files={"app/main.py": "ready"}),
            )

            queued = service.start_battle(detail.battle.id, creator)

        self.assertEqual(queued.battle.status, "queued")
        self.assertEqual(worker.enqueued, [detail.battle.id])

    def test_start_battle_rejects_duplicate_queueing(self) -> None:
        class FakeWorker:
            def __init__(self) -> None:
                self.enqueued: list[str] = []

            def enqueue(self, battle_id: str) -> None:
                self.enqueued.append(battle_id)

        with TemporaryDirectory() as temp_dir:
            store = AlphaStore(str(Path(temp_dir) / "alpha.sqlite3"))
            worker = FakeWorker()
            service = PublicAlphaService(
                store,
                QuestService(get_quest_repository()),
                get_sandbox_runner(),
                battle_worker=worker,
            )
            creator = store.upsert_user(f"creator-{self.login_suffix}")
            opponent = store.upsert_user(f"opponent-{self.login_suffix}")
            left = service.create_profile_from_template(creator, "buildknight")
            right = service.create_profile_from_template(opponent, "speedster")
            detail = service.create_battle(
                creator,
                BattleCreate(
                    quest_id="quest_hello_world",
                    agent_profile_id=left.id,
                    workspace_files={"app/main.py": "ready"},
                ),
            )
            service.join_battle(
                detail.battle.id,
                opponent,
                BattleJoin(agent_profile_id=right.id, workspace_files={"app/main.py": "ready"}),
            )

            service.start_battle(detail.battle.id, creator)
            with self.assertRaisesRegex(ValueError, "Battle is not ready to start"):
                service.start_battle(detail.battle.id, creator)

        self.assertEqual(worker.enqueued, [detail.battle.id])

    def test_closed_alpha_battle_flow(self) -> None:
        left_login = f"alpha-one-{self.login_suffix}"
        right_login = f"alpha-two-{self.login_suffix}"
        invite = self.client.get(
            "/api/v1/invites/validate",
            params={"code": settings.DEFAULT_ALPHA_INVITE_CODE, "github_login": left_login},
        )
        self.assertEqual(invite.status_code, 200)
        self.assertTrue(invite.json()["valid"])

        self._login(self.client, left_login)
        self._login(self.opponent, right_login)

        me = self.client.get("/api/v1/me")
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.json()["user"]["github_login"], left_login)

        templates = self.client.get("/api/v1/templates/agents")
        self.assertEqual(templates.status_code, 200)
        self.assertGreaterEqual(len(templates.json()), 4)

        profiles_left = self.client.get("/api/v1/profiles/mine")
        profiles_right = self.opponent.get("/api/v1/profiles/mine")
        self.assertEqual(profiles_left.status_code, 200)
        self.assertEqual(profiles_right.status_code, 200)
        left_profile = profiles_left.json()[0]["id"]
        right_profile = profiles_right.json()[1]["id"]

        battle = self.client.post(
            "/api/v1/battles/",
            json={
                "quest_id": "quest_hello_world",
                "agent_profile_id": left_profile,
                "workspace_files": {
                    "app/main.py": (
                        "from fastapi import FastAPI\n\n"
                        "app = FastAPI()\n\n"
                        "@app.get('/hello')\n"
                        "def hello() -> dict[str, str]:\n"
                        "    return {'message': 'Hello, arena!'}\n"
                    )
                },
            },
        )
        self.assertEqual(battle.status_code, 201)
        battle_id = battle.json()["battle"]["id"]

        joined = self.opponent.post(
            f"/api/v1/battles/{battle_id}/join",
            json={
                "agent_profile_id": right_profile,
                "workspace_files": {
                    "app/main.py": (
                        "from fastapi import FastAPI\n\n"
                        "app = FastAPI()\n\n"
                        "@app.get('/hello')\n"
                        "def hello() -> dict[str, str]:\n"
                        "    return {'message': 'Broken'}\n"
                    )
                },
            },
        )
        self.assertEqual(joined.status_code, 200)
        self.assertEqual(joined.json()["battle"]["status"], "ready")

        started = self.client.post(f"/api/v1/battles/{battle_id}/start")
        self.assertEqual(started.status_code, 200)

        final_state = None
        for _ in range(50):
            polled = self.client.get(f"/api/v1/battles/{battle_id}")
            self.assertEqual(polled.status_code, 200)
            final_state = polled.json()
            if final_state["battle"]["status"] == "completed":
                break
            time.sleep(0.1)

        self.assertIsNotNone(final_state)
        self.assertEqual(final_state["battle"]["status"], "completed")
        self.assertEqual(len(final_state["participants"]), 2)

        result = self.client.get(f"/api/v1/battles/{battle_id}/result")
        self.assertEqual(result.status_code, 200)
        self.assertIn(
            result.json()["tie_break_reason"],
            {"higher_technical_score", "more_passed_tests", "lower_duration_ms", "explicit_tie"},
        )
        self.assertGreaterEqual(result.json()["score_left"], result.json()["score_right"])
        breakdown = result.json()["score_breakdown"]
        self.assertEqual(len(breakdown), 2)
        self.assertEqual({item["seat"] for item in breakdown}, {"left", "right"})
        for item in breakdown:
            with self.subTest(seat=item["seat"]):
                self.assertIn("participant_id", item)
                self.assertIn("technical_score", item)
                self.assertIn("total_score", item)
                self.assertIn("duration_ms", item)
                self.assertGreaterEqual(item["passed_tests"], 0)
                self.assertGreaterEqual(item["failed_tests"], 0)
                self.assertEqual({suite["suite"] for suite in item["suites"]}, {"visible", "hidden"})

        replay = self.client.get(f"/api/v1/battles/{battle_id}/replay")
        self.assertEqual(replay.status_code, 200)
        self.assertEqual(len(replay.json()["runs"]), 2)
        self.assertTrue(any(item["run"]["summary"]["technical_score"] < 100 for item in replay.json()["runs"]))

        leaderboard = self.client.get("/api/v1/leaderboard/")
        self.assertEqual(leaderboard.status_code, 200)
        self.assertGreaterEqual(len(leaderboard.json()), 2)
        left_entry = next(item for item in leaderboard.json() if item["github_login"] == left_login)
        self.assertGreaterEqual(left_entry["wins"] + left_entry["losses"] + left_entry["ties"], 1)


if __name__ == "__main__":
    unittest.main()
