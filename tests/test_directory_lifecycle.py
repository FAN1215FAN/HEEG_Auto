from __future__ import annotations

from pathlib import Path

from heeg_auto.runner.directory_lifecycle import DirectoryLifecycleManager


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
        self.driver = type(
            "Driver",
            (),
            {
                "app": object(),
                "main_window_wrapper": type("W", (), {"handle": 1, "is_visible": lambda self: True})(),
            },
        )()
        self.driver.top_window = lambda: type("Top", (), {"handle": 1})()

    def run_case(self, case_path, raise_on_failure=False, close_after_run=False, stall_timeout_seconds=60):
        self.calls.append(Path(case_path).name)
        return {"passed": True, "error_summary": ""}


def test_directory_enter_runs_init_once(tmp_path):
    case_dir = tmp_path / "患者管理"
    case_dir.mkdir()
    (case_dir / "init.yaml").write_text("用例编号: INIT\n用例名称: 初始化\n模块链: []", encoding="utf-8")
    (case_dir / "case_a.yaml").write_text("用例编号: A\n用例名称: A\n模块链: []", encoding="utf-8")

    manager = DirectoryLifecycleManager(_FakeRunner())

    manager.prepare_for_case(case_dir / "case_a.yaml")
    manager.prepare_for_case(case_dir / "case_a.yaml")

    assert manager.runner.calls == ["init.yaml"]


def test_directory_switch_runs_cleanup_then_next_init(tmp_path):
    dir_a = tmp_path / "患者管理"
    dir_b = tmp_path / "设备设置"
    dir_a.mkdir()
    dir_b.mkdir()
    (dir_a / "init.yaml").write_text("用例编号: INIT_A\n用例名称: 初始化A\n模块链: []", encoding="utf-8")
    (dir_a / "cleanup.yaml").write_text("用例编号: CLEAN_A\n用例名称: 清理A\n模块链: []", encoding="utf-8")
    (dir_b / "init.yaml").write_text("用例编号: INIT_B\n用例名称: 初始化B\n模块链: []", encoding="utf-8")

    manager = DirectoryLifecycleManager(_FakeRunner())

    manager.prepare_for_case(dir_a / "case_a.yaml")
    manager.prepare_for_case(dir_b / "case_b.yaml")

    assert manager.runner.calls == ["init.yaml", "cleanup.yaml", "init.yaml"]


def test_directory_failure_marks_next_case_for_recovery(tmp_path):
    case_dir = tmp_path / "患者管理"
    case_dir.mkdir()
    (case_dir / "init.yaml").write_text("用例编号: INIT\n用例名称: 初始化\n模块链: []", encoding="utf-8")
    (case_dir / "cleanup.yaml").write_text("用例编号: CLEAN\n用例名称: 清理\n模块链: []", encoding="utf-8")

    manager = DirectoryLifecycleManager(_FakeRunner())

    manager.prepare_for_case(case_dir / "case_a.yaml")
    manager.record_case_result(case_dir / "case_a.yaml", {"status": "FAIL"})
    manager.prepare_for_case(case_dir / "case_b.yaml")

    assert manager.runner.calls == ["init.yaml", "cleanup.yaml", "init.yaml"]


def test_directory_visible_main_window_does_not_trigger_recovery(tmp_path):
    case_dir = tmp_path / "设备设置"
    case_dir.mkdir()
    (case_dir / "init.yaml").write_text("用例编号: INIT\n用例名称: 初始化\n模块链: []", encoding="utf-8")

    runner = _FakeRunner()
    runner.driver.top_window = lambda: type("Top", (), {"handle": 99})()
    manager = DirectoryLifecycleManager(runner)

    manager.prepare_for_case(case_dir / "case_a.yaml")
    manager.prepare_for_case(case_dir / "case_b.yaml")

    assert manager.runner.calls == ["init.yaml"]

