"""Contract tests for the battle SSE stream endpoint.

Cobre o contrato do SSE do Battle Room (Issue #3):
1. GET /battles/{id}/stream responde 404 para battle inexistente.
2. O response tem os headers de SSE esperados (text/event-stream, no-cache).
3. O stream emite eventos JSON no formato SSE (`data: {json}\n\n`).
4. O stream fecha ao atingir o terminal (bus.close() ~ sentinela).
"""
import json
import threading
import time
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
    get_sandbox_runner,
)
from backend.app.core.rate_limit import reset_rate_limiter
from backend.app.main import app
from backend.app.services.battle_event_bus import get_bus


class SseContractTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)
        cls.opponent = TestClient(app)

    def setUp(self) -> None:
        self.login_suffix = uuid4().hex[:8]
        self._original_db_path = settings.ALPHA_DB_PATH
        self._tmp_dir = TemporaryDirectory()
        settings.ALPHA_DB_PATH = str(Path(self._tmp_dir.name) / "sse-contract.sqlite3")
        get_quest_repository.cache_clear()
        get_agent_profile_repository.cache_clear()
        get_run_repository.cache_clear()
        get_replay_event_repository.cache_clear()
        get_post_mortem_repository.cache_clear()
        get_ranking_repository.cache_clear()
        get_public_alpha_service.cache_clear()
        get_alpha_store.cache_clear()
        reset_rate_limiter()
        # Cada teste usa um battle_id único para não misturar filas do bus.
        self.battle_id = f"battle-contract-{self.login_suffix}"

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
        self.assertTrue(callback.json()["authenticated"])

    def _create_ready_battle(self) -> str:
        """Cria uma battle com 2 participantes no status ready e devolve o id."""
        left_login = f"sse-left-{self.login_suffix}"
        right_login = f"sse-right-{self.login_suffix}"
        self._login(self.client, left_login)
        self._login(self.opponent, right_login)

        profiles_left = self.client.get("/api/v1/profiles/mine").json()
        profiles_right = self.opponent.get("/api/v1/profiles/mine").json()
        left_profile = profiles_left[0]["id"]
        right_profile = profiles_right[1]["id"]

        battle = self.client.post(
            "/api/v1/battles/",
            json={
                "quest_id": "quest_hello_world",
                "agent_profile_id": left_profile,
                "workspace_files": {"app/main.py": "app = __import__('fastapi').FastAPI()"},
            },
        )
        self.assertEqual(battle.status_code, 201)
        battle_id = battle.json()["battle"]["id"]

        joined = self.opponent.post(
            f"/api/v1/battles/{battle_id}/join",
            json={
                "agent_profile_id": right_profile,
                "workspace_files": {"app/main.py": "app = __import__('fastapi').FastAPI()"},
            },
        )
        self.assertEqual(joined.status_code, 200)
        self.assertEqual(joined.json()["battle"]["status"], "ready")
        return battle_id

    def test_stream_returns_404_for_unknown_battle(self) -> None:
        response = self.client.get(f"/api/v1/battles/{self.battle_id}/stream")
        self.assertEqual(response.status_code, 404)

    def test_stream_endpoint_has_sse_headers(self) -> None:
        battle_id = self._create_ready_battle()

        try:
            with self.client.stream("GET", f"/api/v1/battles/{battle_id}/stream") as response:
                self.assertEqual(response.status_code, 200)
                self.assertTrue(
                    response.headers["content-type"].startswith("text/event-stream"),
                    msg=f"content-type inesperado: {response.headers['content-type']}",
                )
                self.assertEqual(response.headers["cache-control"], "no-cache")
                self.assertEqual(response.headers["x-accel-buffering"], "no")
                # Fecha o stream de forma limpa para o teste não depender do worker.
                get_bus().close(battle_id)
                for _ in response.iter_text():
                    break
        except StopIteration:
            pass  # stream já vazio/fechado: contrato de headers foi validado acima

    def test_stream_emits_running_then_completed_and_closes(self) -> None:
        battle_id = self._create_ready_battle()
        bus = get_bus()
        events: list[dict] = []

        # Publica a sequência do contrato em thread e fecha (sentinela) no final.
        def publisher() -> None:
            time.sleep(0.2)
            bus.publish(battle_id, {"battle_id": battle_id, "status": "running"})
            time.sleep(0.05)
            bus.publish(
                battle_id,
                {
                    "battle_id": battle_id,
                    "status": "completed",
                    "winner_participant_id": "participant-x",
                },
            )
            bus.close(battle_id)

        thread = threading.Thread(target=publisher)
        thread.start()
        try:
            with self.client.stream("GET", f"/api/v1/battles/{battle_id}/stream") as response:
                self.assertEqual(response.status_code, 200)
                for chunk in response.iter_lines():
                    if not chunk.startswith("data:"):
                        continue
                    payload = chunk.removeprefix("data:").strip()
                    if not payload:
                        continue
                    events.append(json.loads(payload))
        finally:
            thread.join(timeout=5)

        self.assertEqual(
            [event["status"] for event in events],
            ["running", "completed"],
            msg=f"Contrato SSE violado: eventos recebidos {events}",
        )
        self.assertEqual(events[0]["battle_id"], battle_id)
        self.assertEqual(events[1]["winner_participant_id"], "participant-x")


if __name__ == "__main__":
    unittest.main()