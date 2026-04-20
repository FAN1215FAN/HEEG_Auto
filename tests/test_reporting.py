from __future__ import annotations

from pathlib import Path

from heeg_auto.core import reporting


def _sample_case_result() -> dict:
    return {
        "case_id": "设备设置_01",
        "case_name": "设备设置_采样率校验",
        "relative_dir": "系统设置/设备设置",
        "module_chain_labels": ["启动软件", "设备设置"],
        "variant": {"module_label": "设备设置", "param_label": "采样率"},
        "loop_count": 1,
        "stop_on_failure": True,
        "status": "INTERRUPTED",
        "started_at": "2026-04-02 15:18:01",
        "finished_at": "2026-04-02 15:18:21",
        "duration_seconds": 20,
        "summary": {
            "planned_runs": 3,
            "executed_runs": 2,
            "passed_runs": 1,
            "failed_runs": 0,
            "interrupted_runs": 1,
            "not_run_runs": 1,
        },
        "execution_results": [
            {
                "sequence": 1,
                "execution_name": "设备设置_采样率校验 | 采样率=1000",
                "loop_index": 1,
                "loop_total": 1,
                "variant": {"param_label": "采样率", "value": "1000"},
                "status": "PASS",
                "started_at": "2026-04-02 15:18:01",
                "finished_at": "2026-04-02 15:18:08",
                "duration_seconds": 7,
                "error_summary": "",
                "failure": {},
                "artifact_paths": [],
                "parameter_snapshot": [
                    {
                        "module_label": "设备设置",
                        "assertion_group": "设置成功",
                        "params": [
                            {"label": "设备类型", "value": "Neusen HEEG"},
                            {"label": "采样率", "value": "1000"},
                        ],
                    }
                ],
                "module_results": [
                    {
                        "module_label": "设备设置",
                        "assertion_group": "设置成功",
                        "status": "PASS",
                        "failed_step": "",
                        "step_results": [
                            {"stage": "步骤", "step_name": "打开设置", "status": "PASS", "error_summary": ""}
                        ],
                    }
                ],
            },
            {
                "sequence": 2,
                "execution_name": "设备设置_采样率校验 | 采样率=2000",
                "loop_index": 1,
                "loop_total": 1,
                "variant": {"param_label": "采样率", "value": "2000"},
                "status": "INTERRUPTED",
                "started_at": "2026-04-02 15:18:08",
                "finished_at": "2026-04-02 15:18:21",
                "duration_seconds": 13,
                "error_summary": "步骤卡住超过 60 秒：采样率下拉框",
                "failure": {"module_id": "device.settings", "failed_step": "采样率下拉框"},
                "artifact_paths": ["D:/AI_project/AI_Auto/HEEG_Auto/artifacts/screenshots/demo.png"],
                "parameter_snapshot": [
                    {
                        "module_label": "设备设置",
                        "assertion_group": "设置成功",
                        "params": [
                            {"label": "设备类型", "value": "Neusen HEEG"},
                            {"label": "采样率", "value": "2000"},
                        ],
                    }
                ],
                "module_results": [
                    {
                        "module_label": "设备设置",
                        "assertion_group": "设置成功",
                        "status": "INTERRUPTED",
                        "failed_step": "采样率下拉框",
                        "step_results": [
                            {"stage": "步骤", "step_name": "打开设置", "status": "PASS", "error_summary": ""},
                            {"stage": "步骤", "step_name": "选择采样率", "status": "FAIL", "error_summary": "找不到目标选项"},
                        ],
                    }
                ],
            },
            {
                "sequence": 3,
                "execution_name": "设备设置_采样率校验 | 采样率=4000",
                "loop_index": 1,
                "loop_total": 1,
                "variant": {"param_label": "采样率", "value": "4000"},
                "status": "NOT_RUN",
                "started_at": "",
                "finished_at": "",
                "duration_seconds": 0,
                "error_summary": "前序执行失败或异常中断，后续轮次按失败即停标记为未执行。",
                "failure": {},
                "artifact_paths": [],
                "parameter_snapshot": [],
                "module_results": [],
            },
        ],
        "artifact_paths": ["D:/AI_project/AI_Auto/HEEG_Auto/artifacts/screenshots/demo.png"],
        "error_summary": "步骤卡住超过 60 秒：采样率下拉框",
    }


def test_generate_reports_only_outputs_html(tmp_path):
    reporting.REPORT_DIR = tmp_path
    reporting.ensure_artifact_dirs = lambda: tmp_path.mkdir(parents=True, exist_ok=True)

    report_files = reporting.generate_reports(_sample_case_result())
    html_path = Path(report_files["html_path"])

    assert html_path.exists()
    assert html_path.name.startswith("HEEG_Auto_Report_")
    assert set(report_files.keys()) == {"html", "html_path"}

    html_text = html_path.read_text(encoding="utf-8")
    assert "设备设置_采样率校验" in html_text
    assert "执行概览" in html_text
    assert "开始时间" in html_text
    assert "结束时间" in html_text
    assert "模块参数快照" in html_text
    assert "设备类型" in html_text
    assert "Neusen HEEG" in html_text
    assert "截图产物链接" in html_text
    assert "打开设置" not in html_text
    assert "选择采样率" in html_text


def test_generate_suite_reports_only_outputs_single_html(tmp_path):
    reporting.REPORT_DIR = tmp_path
    reporting.ensure_artifact_dirs = lambda: tmp_path.mkdir(parents=True, exist_ok=True)

    passed_case = {
        "case_id": "公共功能_01",
        "case_name": "主流程",
        "relative_dir": "公共功能",
        "status": "PASS",
        "duration_seconds": 32,
        "started_at": "2026-04-02 11:43:13",
        "finished_at": "2026-04-02 11:43:45",
        "module_chain_labels": ["启动软件", "新建患者", "设备设置"],
        "summary": {
            "planned_runs": 1,
            "executed_runs": 1,
            "passed_runs": 1,
            "failed_runs": 0,
            "interrupted_runs": 0,
            "not_run_runs": 0,
        },
        "execution_results": [
            {
                "sequence": 1,
                "execution_name": "主流程",
                "loop_index": 1,
                "loop_total": 1,
                "status": "PASS",
                "started_at": "2026-04-02 11:43:13",
                "finished_at": "2026-04-02 11:43:45",
                "duration_seconds": 32,
                "error_summary": "",
                "failure": {},
                "artifact_paths": [],
                "parameter_snapshot": [
                    {
                        "module_label": "新建患者",
                        "assertion_group": "创建成功",
                        "params": [{"label": "患者姓名", "value": "测试用户"}],
                    }
                ],
                "module_results": [],
            }
        ],
        "artifact_paths": [],
        "error_summary": "",
    }
    interrupted_case = _sample_case_result()

    report_files = reporting.generate_suite_reports([passed_case, interrupted_case])
    html_path = Path(report_files["html_path"])

    assert html_path.exists()
    assert html_path.name.startswith("HEEG_Auto_Report_")
    assert set(report_files.keys()) == {"html", "html_path"}

    html_text = html_path.read_text(encoding="utf-8")
    assert "主流程" in html_text
    assert "设备设置_采样率校验" in html_text
    assert "套件概览" in html_text
    assert "逐用例明细" in html_text
    assert "步骤卡住超过 60 秒：采样率下拉框" in html_text
    assert "模块参数快照" in html_text
    assert "截图产物链接" in html_text
    assert "打开设置" not in html_text
