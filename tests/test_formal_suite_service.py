from __future__ import annotations

from pathlib import Path

from heeg_auto.runner.formal_suite_service import FormalSuiteService


class _FakeDriver:
    def __init__(self) -> None:
        self.closed = 0

    def close(self) -> None:
        self.closed += 1


class _FakeRunner:
    def __init__(self, should_raise: bool = False) -> None:
        self.should_raise = should_raise
        self.driver = _FakeDriver()
        self.calls: list[Path] = []
        self.logger = type(
            "Logger",
            (),
            {
                "info": lambda self, *args, **kwargs: None,
                "warning": lambda self, *args, **kwargs: None,
            },
        )()

    def run_case(self, case_path, raise_on_failure=False, close_after_run=False, stall_timeout_seconds=60):
        case_path = Path(case_path)
        self.calls.append(case_path)
        if self.should_raise:
            raise RuntimeError("runner boom")
        return {
            "case_id": case_path.stem,
            "case_name": case_path.stem,
            "status": "PASS",
            "passed": True,
            "summary": {
                "planned_runs": 1,
                "executed_runs": 1,
                "passed_runs": 1,
                "failed_runs": 0,
                "interrupted_runs": 0,
                "not_run_runs": 0,
            },
        }


class _FakeLifecycle:
    def __init__(self, should_raise: bool = False) -> None:
        self.should_raise = should_raise
        self.prepared: list[Path] = []
        self.recorded: list[tuple[Path, str]] = []
        self.finished = 0

    def prepare_for_case(self, case_path) -> None:
        case_path = Path(case_path)
        self.prepared.append(case_path)
        if self.should_raise:
            raise RuntimeError("init boom")

    def record_case_result(self, case_path, result) -> None:
        self.recorded.append((Path(case_path), result["status"]))

    def finish(self) -> None:
        self.finished += 1


def test_run_case_item_uses_shared_lifecycle_and_runner():
    runner = _FakeRunner()
    lifecycle = _FakeLifecycle()
    service = FormalSuiteService(runner=runner, lifecycle=lifecycle, close_driver_on_finish=False)
    item = {
        "path": Path("src/heeg_auto/cases/系统设置/设备设置/采样率校验.yaml"),
        "relative_dir": "系统设置/设备设置",
        "case_id": "设备设置_01",
        "case_name": "采样率校验",
    }

    result = service.run_case_item(item)

    assert runner.calls == [item["path"]]
    assert lifecycle.prepared == [item["path"]]
    assert lifecycle.recorded == [(item["path"], "PASS")]
    assert result["relative_dir"] == "系统设置/设备设置"


def test_run_case_item_converts_prepare_or_runner_failure_to_interrupted_result():
    item = {
        "path": Path("src/heeg_auto/cases/系统设置/设备设置/采样率校验.yaml"),
        "relative_dir": "系统设置/设备设置",
        "case_id": "设备设置_01",
        "case_name": "采样率校验",
    }

    result = FormalSuiteService(
        runner=_FakeRunner(should_raise=True),
        lifecycle=_FakeLifecycle(),
        close_driver_on_finish=False,
    ).run_case_item(item)
    assert result["status"] == "INTERRUPTED"
    assert result["error_summary"] == "runner boom"

    result = FormalSuiteService(
        runner=_FakeRunner(),
        lifecycle=_FakeLifecycle(should_raise=True),
        close_driver_on_finish=False,
    ).run_case_item(item)
    assert result["status"] == "INTERRUPTED"
    assert result["error_summary"] == "init boom"


def test_execute_suite_and_finish_use_shared_service_resources(monkeypatch):
    runner = _FakeRunner()
    lifecycle = _FakeLifecycle()
    service = FormalSuiteService(runner=runner, lifecycle=lifecycle)
    items = [
        {
            "path": Path("a.yaml"),
            "relative_dir": "目录A",
            "case_id": "A",
            "case_name": "A",
        },
        {
            "path": Path("b.yaml"),
            "relative_dir": "目录B",
            "case_id": "B",
            "case_name": "B",
        },
    ]
    progress: list[tuple[int, str, str]] = []

    def capture(index, total, item, result):
        progress.append((index, item["case_id"], result["status"]))

    monkeypatch.setattr(
        "heeg_auto.runner.formal_suite_service.generate_suite_reports",
        lambda results: {"html_path": "artifacts/reports/demo.html", "html": "artifacts/reports/demo.html"},
    )

    results = service.execute_suite(items, progress_callback=capture)
    summary = service.finalize_suite(results)
    service.finish()
    service.finish()

    assert [item["case_id"] for item in results] == ["a", "b"]
    assert progress == [(1, "A", "PASS"), (2, "B", "PASS")]
    assert summary["passed_cases"] == 2
    assert summary["failed_cases"] == 0
    assert summary["report_files"]["html_path"] == "artifacts/reports/demo.html"
    assert lifecycle.finished == 1
    assert runner.driver.closed == 1


def test_service_accepts_environment_mode():
    service = FormalSuiteService(
        runner=_FakeRunner(),
        close_driver_on_finish=False,
        environment_mode="reset_per_directory",
    )

    assert service.environment_mode == "reset_per_directory"
    assert service.lifecycle.environment_mode == "reset_per_directory"
