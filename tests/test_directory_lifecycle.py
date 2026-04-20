from __future__ import annotations

from pathlib import Path

from heeg_auto.runner.directory_lifecycle import DirectoryLifecycleManager


def _write_step_case(path: Path, case_id: str, case_name: str) -> None:
    path.write_text(
        f"用例编号: {case_id}\n用例名称: {case_name}\n步骤:\n  - 名称: 空步骤\n    窗口: 主窗口\n",
        encoding="utf-8",
    )


class _FakeDriver:
    def __init__(self) -> None:
        self.app = object()
        self.main_window_wrapper = type("W", (), {"handle": 1, "is_visible": lambda self: True})()
        self.force_close_calls: list[str] = []

    def force_close_running_app(self) -> None:
        self.force_close_calls.append("force_close")
        self.app = None
        self.main_window_wrapper = None


class _FakeRunner:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.logger = type(
            "Logger",
            (),
            {
                "info": lambda self, *args, **kwargs: None,
                "warning": lambda self, *args, **kwargs: None,
            },
        )()
        self.driver = _FakeDriver()
        self.driver.top_window = lambda: type("Top", (), {"handle": 1})()

    def run_case(self, case_path, raise_on_failure=False, close_after_run=False, stall_timeout_seconds=60):
        self.calls.append(Path(case_path).name)
        return {"passed": True, "error_summary": ""}


def test_directory_enter_runs_init_once(tmp_path):
    case_dir = tmp_path / "患者管理"
    case_dir.mkdir()
    _write_step_case(case_dir / "init.yaml", "INIT", "初始化")
    _write_step_case(case_dir / "case_a.yaml", "A", "A")

    manager = DirectoryLifecycleManager(_FakeRunner(), case_root=tmp_path)

    manager.prepare_for_case(case_dir / "case_a.yaml")
    manager.prepare_for_case(case_dir / "case_a.yaml")

    assert manager.runner.calls == ["init.yaml"]


def test_reuse_per_suite_switches_directory_without_forced_restart(tmp_path):
    dir_a = tmp_path / "患者管理"
    dir_b = tmp_path / "设备设置"
    dir_a.mkdir()
    dir_b.mkdir()
    _write_step_case(dir_a / "init.yaml", "INIT_A", "初始化A")
    _write_step_case(dir_a / "cleanup.yaml", "CLEAN_A", "清理A")
    _write_step_case(dir_b / "init.yaml", "INIT_B", "初始化B")

    runner = _FakeRunner()
    manager = DirectoryLifecycleManager(runner, case_root=tmp_path, environment_mode="reuse_per_suite")

    manager.prepare_for_case(dir_a / "case_a.yaml")
    manager.prepare_for_case(dir_b / "case_b.yaml")

    assert runner.calls == ["init.yaml", "cleanup.yaml", "init.yaml"]
    assert runner.driver.force_close_calls == []


def test_reset_per_directory_forces_restart_on_directory_switch(tmp_path):
    dir_a = tmp_path / "患者管理"
    dir_b = tmp_path / "设备设置"
    dir_a.mkdir()
    dir_b.mkdir()
    _write_step_case(dir_a / "init.yaml", "INIT_A", "初始化A")
    _write_step_case(dir_a / "cleanup.yaml", "CLEAN_A", "清理A")
    _write_step_case(dir_b / "init.yaml", "INIT_B", "初始化B")

    runner = _FakeRunner()
    manager = DirectoryLifecycleManager(runner, case_root=tmp_path, environment_mode="reset_per_directory")

    manager.prepare_for_case(dir_a / "case_a.yaml")
    runner.driver.app = object()
    runner.driver.main_window_wrapper = type("W", (), {"handle": 1, "is_visible": lambda self: True})()
    manager.prepare_for_case(dir_b / "case_b.yaml")

    assert runner.calls == ["init.yaml", "cleanup.yaml", "init.yaml"]
    assert runner.driver.force_close_calls == ["force_close"]


def test_directory_failure_marks_next_case_for_recovery(tmp_path):
    case_dir = tmp_path / "患者管理"
    case_dir.mkdir()
    _write_step_case(case_dir / "init.yaml", "INIT", "初始化")
    _write_step_case(case_dir / "cleanup.yaml", "CLEAN", "清理")

    runner = _FakeRunner()
    manager = DirectoryLifecycleManager(runner, case_root=tmp_path)

    manager.prepare_for_case(case_dir / "case_a.yaml")
    manager.record_case_result(case_dir / "case_a.yaml", {"status": "FAIL"})
    manager.prepare_for_case(case_dir / "case_b.yaml")

    assert runner.calls == ["init.yaml", "cleanup.yaml", "init.yaml"]
    assert runner.driver.force_close_calls == ["force_close"]


def test_suite_support_files_run_once(tmp_path):
    case_dir = tmp_path / "患者管理"
    case_dir.mkdir()
    _write_step_case(tmp_path / "suite_setup.yaml", "SUITE_SETUP", "套件初始化")
    _write_step_case(tmp_path / "suite_cleanup.yaml", "SUITE_CLEAN", "套件清理")
    _write_step_case(case_dir / "init.yaml", "INIT", "初始化")

    runner = _FakeRunner()
    manager = DirectoryLifecycleManager(runner, case_root=tmp_path)

    manager.prepare_for_case(case_dir / "case_a.yaml")
    manager.prepare_for_case(case_dir / "case_b.yaml")
    manager.finish()

    assert runner.calls == ["suite_setup.yaml", "init.yaml", "suite_cleanup.yaml"]


def test_directory_visible_main_window_does_not_trigger_recovery(tmp_path):
    case_dir = tmp_path / "设备设置"
    case_dir.mkdir()
    _write_step_case(case_dir / "init.yaml", "INIT", "初始化")

    runner = _FakeRunner()
    runner.driver.top_window = lambda: type("Top", (), {"handle": 99})()
    manager = DirectoryLifecycleManager(runner, case_root=tmp_path)

    manager.prepare_for_case(case_dir / "case_a.yaml")
    manager.prepare_for_case(case_dir / "case_b.yaml")

    assert runner.calls == ["init.yaml"]
