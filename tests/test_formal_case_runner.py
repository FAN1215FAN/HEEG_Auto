from __future__ import annotations

import pytest

from heeg_auto.runner.formal_case_runner import FormalCaseRunner


def test_run_case_uses_step_executor_plan(monkeypatch, tmp_path):
    case_file = tmp_path / "step_case.yaml"
    case_file.write_text(
        "用例编号: STEP_001\n用例名称: 步骤式用例\n步骤:\n  - 名称: 启动\n    动作: 启动应用\n",
        encoding="utf-8",
    )

    runner = FormalCaseRunner()
    monkeypatch.setattr(
        runner.step_case_loader,
        "load",
        lambda path: {
            "case_id": "STEP_001",
            "case_name": "步骤式用例",
            "case_path": str(path),
            "context": {"timestamp": "20260409130000"},
            "steps": [{"step_name": "启动", "action": "启动应用", "params": {}, "assertions": []}],
        },
    )
    monkeypatch.setattr(
        runner.step_case_executor,
        "run_case",
        lambda actions, case_data, progress_callback=None: {
            "case_id": case_data["case_id"],
            "case_name": case_data["case_name"],
            "case_path": case_data["case_path"],
            "status": "PASS",
            "passed": True,
            "execution_results": [],
            "summary": {
                "planned_runs": 1,
                "executed_runs": 1,
                "passed_runs": 1,
                "failed_runs": 0,
                "interrupted_runs": 0,
                "not_run_runs": 0,
            },
        },
    )

    result = runner.run_case(case_file, raise_on_failure=False, close_after_run=False)

    assert result["case_id"] == "STEP_001"
    assert result["status"] == "PASS"
    assert result["module_chain_labels"] == ["步骤式"]


def test_run_case_raises_on_step_failure(monkeypatch, tmp_path):
    case_file = tmp_path / "step_case.yaml"
    case_file.write_text(
        "用例编号: STEP_002\n用例名称: 失败用例\n步骤:\n  - 名称: 启动\n    动作: 启动应用\n",
        encoding="utf-8",
    )

    runner = FormalCaseRunner()
    monkeypatch.setattr(
        runner.step_case_loader,
        "load",
        lambda path: {
            "case_id": "STEP_002",
            "case_name": "失败用例",
            "case_path": str(path),
            "context": {"timestamp": "20260409130000"},
            "steps": [{"step_name": "启动", "action": "启动应用", "params": {}, "assertions": []}],
        },
    )
    monkeypatch.setattr(
        runner.step_case_executor,
        "run_case",
        lambda actions, case_data, progress_callback=None: {
            "case_id": case_data["case_id"],
            "case_name": case_data["case_name"],
            "case_path": case_data["case_path"],
            "status": "FAIL",
            "passed": False,
            "execution_results": [{"sequence": 1, "status": "FAIL", "error_summary": "断言失败", "step_results": []}],
            "summary": {
                "planned_runs": 1,
                "executed_runs": 1,
                "passed_runs": 0,
                "failed_runs": 1,
                "interrupted_runs": 0,
                "not_run_runs": 0,
            },
        },
    )
    monkeypatch.setattr(runner, "_attach_step_case_failure_artifacts", lambda *args, **kwargs: None)

    with pytest.raises(RuntimeError, match="断言失败"):
        runner.run_case(case_file, raise_on_failure=True, close_after_run=False)
