import os
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

_CORE = Path(__file__).resolve().parent.parent / "core"
if str(_CORE) not in sys.path:
    sys.path.insert(0, str(_CORE))

import scheduler as scheduler_module  # noqa: E402


class _FakeResponse:
    def __init__(self, text: str = "ok", *, status_code: int = 200, payload: dict | None = None) -> None:
        self.text = text
        self.status_code = status_code
        self._payload = payload if payload is not None else {"ok": True}

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self) -> dict:
        return self._payload


class _FakeAsyncClient:
    calls = []

    def __init__(self, timeout: int) -> None:
        self.timeout = timeout

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url: str, json: dict):
        _FakeAsyncClient.calls.append((url, json, self.timeout))
        if url.endswith("/chat"):
            return _FakeResponse("agent-result")
        return _FakeResponse("", payload={"ok": True})


class SchedulerTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        scheduler_module.get_settings.cache_clear()
        os.environ["AGENT_URL"] = "http://agent-service:8092"
        os.environ["TELEGRAM_URL"] = "http://telegram:8094"

    async def test_run_skill_validates_and_sends(self) -> None:
        original_client = scheduler_module.httpx.AsyncClient
        _FakeAsyncClient.calls = []
        scheduler_module.httpx.AsyncClient = _FakeAsyncClient
        try:
            await scheduler_module._run_skill({"name": "daily", "prompt": "hello"})
        finally:
            scheduler_module.httpx.AsyncClient = original_client

        self.assertEqual(len(_FakeAsyncClient.calls), 2)
        self.assertEqual(_FakeAsyncClient.calls[0][0], "http://agent-service:8092/chat")
        self.assertEqual(_FakeAsyncClient.calls[0][1], {"message": "hello", "history": [], "mode": "skill"})
        self.assertEqual(
            _FakeAsyncClient.calls[1][1],
            {"text": "[daily]\nagent-result"},
        )

    async def test_run_skill_rejects_invalid_payload(self) -> None:
        original_client = scheduler_module.httpx.AsyncClient
        _FakeAsyncClient.calls = []
        scheduler_module.httpx.AsyncClient = _FakeAsyncClient
        try:
            await scheduler_module._run_skill({"name": "daily"})
        finally:
            scheduler_module.httpx.AsyncClient = original_client
        self.assertEqual(_FakeAsyncClient.calls, [])

    def test_load_skills_validates_yaml(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            jobs = tmp_path / "jobs"
            jobs.mkdir(parents=True)
            (jobs / "valid.yaml").write_text(
                "name: morning\ncron: '0 9 * * *'\nprompt: ping\n",
                encoding="utf-8",
            )
            (jobs / "disabled.yaml").write_text(
                "name: off\ncron: '0 10 * * *'\nprompt: ignore\nenabled: false\n",
                encoding="utf-8",
            )
            (jobs / "invalid.yaml").write_text("name: bad\n", encoding="utf-8")

            skills = scheduler_module._load_skills(tmp_path)

        self.assertEqual(len(skills), 1)
        self.assertEqual(skills[0].name, "morning")


    async def test_run_skill_returns_result(self) -> None:
        original_client = scheduler_module.httpx.AsyncClient
        _FakeAsyncClient.calls = []
        scheduler_module.httpx.AsyncClient = _FakeAsyncClient
        try:
            result = await scheduler_module._run_skill({"name": "daily", "prompt": "hello"})
        finally:
            scheduler_module.httpx.AsyncClient = original_client
        self.assertEqual(result, "agent-result")

    async def test_run_skill_shell_skips_agent_chat(self) -> None:
        original_client = scheduler_module.httpx.AsyncClient
        original_shell = scheduler_module._run_shell_command

        async def fake_shell(cmd: str, *, trace_id: str, job_name: str) -> str:
            return f"shell:{job_name}:{cmd}"

        _FakeAsyncClient.calls = []
        scheduler_module.httpx.AsyncClient = _FakeAsyncClient
        scheduler_module._run_shell_command = fake_shell
        try:
            result = await scheduler_module._run_skill(
                {"name": "hub-refresh", "prompt": "ignored", "command": "bash /x.sh"},
            )
        finally:
            scheduler_module.httpx.AsyncClient = original_client
            scheduler_module._run_shell_command = original_shell

        self.assertIn("shell:hub-refresh", result)
        chat_urls = [c[0] for c in _FakeAsyncClient.calls if c[0].endswith("/chat")]
        self.assertEqual(chat_urls, [])
        self.assertTrue(any(c[0].endswith("/send") for c in _FakeAsyncClient.calls))

    async def test_run_workflow_sequential(self) -> None:
        import tempfile
        import yaml as _yaml

        called = []

        async def fake_run_skill(skill_data: dict) -> str:
            called.append(skill_data["name"])
            return "ok"

        original = scheduler_module._run_skill
        scheduler_module._run_skill = fake_run_skill

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            jobs = tmp_path / "jobs"
            jobs.mkdir(parents=True)
            for job_name in ("job-a", "job-b", "job-c"):
                (jobs / f"{job_name}.yaml").write_text(
                    _yaml.dump({"name": job_name, "prompt": f"run {job_name}", "enabled": True}),
                    encoding="utf-8",
                )
            scheduler_module._skills_dir = tmp_path
            try:
                await scheduler_module._run_workflow({
                    "name": "my-workflow",
                    "jobs": ["job-a", "job-b", "job-c"],
                })
            finally:
                scheduler_module._run_skill = original
                scheduler_module._skills_dir = None

        self.assertEqual(called, ["job-a", "job-b", "job-c"])

    async def test_run_workflow_stops_on_failure(self) -> None:
        import tempfile
        import yaml as _yaml

        called = []

        async def fake_run_skill(skill_data: dict) -> str:
            called.append(skill_data["name"])
            if skill_data["name"] == "job-b":
                return "[agent error: something went wrong]"
            return "ok"

        original = scheduler_module._run_skill
        scheduler_module._run_skill = fake_run_skill

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            jobs = tmp_path / "jobs"
            jobs.mkdir(parents=True)
            for job_name in ("job-a", "job-b", "job-c"):
                (jobs / f"{job_name}.yaml").write_text(
                    _yaml.dump({"name": job_name, "prompt": f"run {job_name}", "enabled": True}),
                    encoding="utf-8",
                )
            scheduler_module._skills_dir = tmp_path
            try:
                await scheduler_module._run_workflow({
                    "name": "my-workflow",
                    "jobs": ["job-a", "job-b", "job-c"],
                })
            finally:
                scheduler_module._run_skill = original
                scheduler_module._skills_dir = None

        self.assertEqual(called, ["job-a", "job-b"])

    async def test_run_shell_command_respects_clawvis_root_alternate_paths(self) -> None:
        """Shell cwd + CLAWVIS_ROOT env must follow any absolute checkout path (not hardcoded /clawvis)."""
        for label, suffix in (("alpha", "nest-a"), ("beta", "other/b")):
            with self.subTest(label=label):
                with TemporaryDirectory() as tmp:
                    root = Path(tmp).resolve() / suffix
                    root.mkdir(parents=True)
                    (root / ".probe").write_text(label, encoding="utf-8")
                    old = os.environ.get("CLAWVIS_ROOT")
                    os.environ["CLAWVIS_ROOT"] = str(root)
                    try:
                        out = await scheduler_module._run_shell_command(
                            'pwd; echo "ENV=$CLAWVIS_ROOT"; cat .probe',
                            trace_id="t",
                            job_name="probe",
                        )
                    finally:
                        if old is None:
                            os.environ.pop("CLAWVIS_ROOT", None)
                        else:
                            os.environ["CLAWVIS_ROOT"] = old
                lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
                self.assertEqual(lines[0], str(root), msg="pwd should match CLAWVIS_ROOT cwd")
                self.assertIn(f"ENV={root}", out)
                self.assertIn(label, out)

    async def test_run_shell_command_real_repo_layout(self) -> None:
        """Smoke: current checkout path sees hub-core + skills (same as Docker mount /clawvis)."""
        repo = Path(__file__).resolve().parents[3]
        if not (repo / "hub-core").is_dir() or not (repo / "skills" / "hub-refresh").is_dir():
            self.skipTest("not a full clawvis repo root")
        old = os.environ.get("CLAWVIS_ROOT")
        os.environ["CLAWVIS_ROOT"] = str(repo)
        try:
            out = await scheduler_module._run_shell_command(
                "test -d hub-core && test -d skills/hub-refresh && echo LAYOUT_OK",
                trace_id="t",
                job_name="layout-check",
            )
        finally:
            if old is None:
                os.environ.pop("CLAWVIS_ROOT", None)
            else:
                os.environ["CLAWVIS_ROOT"] = old
        self.assertEqual(out.strip(), "LAYOUT_OK")


class TelegramFormatTests(unittest.TestCase):
    def test_strips_bold_markdown(self) -> None:
        import telegram_format as tf

        raw = "**Phase 1** — ok\n\n• **tech** — 5 items"
        self.assertEqual(
            tf.format_job_telegram_body(raw),
            "Phase 1 — ok\n\n• tech — 5 items",
        )


if __name__ == "__main__":
    unittest.main()
