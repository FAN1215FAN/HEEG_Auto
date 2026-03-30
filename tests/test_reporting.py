from __future__ import annotations

import json
from pathlib import Path

from docx import Document
from PIL import Image

from heeg_auto.core import reporting


def test_generate_reports_creates_same_name_json_and_docx(tmp_path):
    screenshot_dir = tmp_path / "screenshots"
    screenshot_dir.mkdir()

    screen_path = screenshot_dir / "demo_screen.png"
    active_path = screenshot_dir / "demo_active.png"

    for path, color in ((screen_path, "red"), (active_path, "blue")):
        Image.new("RGB", (120, 80), color=color).save(path)

    reporting.REPORT_DIR = tmp_path
    reporting.ensure_artifact_dirs = lambda: tmp_path.mkdir(parents=True, exist_ok=True)

    result = {
        "case_id": "TC_PATIENT_002",
        "case_name": "新建患者_姓名含特殊字符",
        "case_path": "D:/AI_project/AI_Auto/HEEG_Auto/src/heeg_auto/cases/patient/TC_PATIENT_002.yaml",
        "tags": ["regression", "patient"],
        "module_chain_labels": ["新建患者"],
        "passed": False,
        "status": "FAIL",
        "context": {"patient_name": "张三@123"},
        "started_at": "2026-03-25 10:30:00",
        "finished_at": "2026-03-25 10:30:05",
        "duration_seconds": 5.0,
        "report_timestamp": "20260325_103000",
        "module_results": [
            {
                "module_id": "system.launch",
                "module_label": "系统启动",
                "expected_status": "PASS",
                "status": "PASS",
                "duration_seconds": 1.2,
                "failed_step": "",
            },
            {
                "module_id": "patient.create",
                "module_label": "新建患者",
                "expected_status": "FAIL",
                "status": "FAIL",
                "duration_seconds": 2.5,
                "failed_step": "看到预期错误文本",
            },
        ],
        "error_summary": "患者姓名不能包含特殊字符",
        "error_detail": "Traceback (most recent call last): ...",
        "failure": {
            "module_id": "patient.create",
            "failed_step": "看到预期错误文本",
        },
        "artifact_paths": [str(screen_path), str(active_path)],
        "environment": {
            "app_path": "F:/neuracle/HEEG_project/HEEG/NSH-R/Neuracle.EEGRecorder.Viewer.HEEG.exe",
            "case_path": "D:/AI_project/AI_Auto/HEEG_Auto/src/heeg_auto/cases/patient/TC_PATIENT_002.yaml",
            "cwd": "D:/AI_project/AI_Auto/HEEG_Auto",
            "python_version": "3.11.0",
        },
    }

    report_files = reporting.generate_reports(result)
    json_path = Path(report_files["json_path"])
    docx_path = Path(report_files["docx_path"])

    assert json_path.exists()
    assert docx_path.exists()
    assert json_path.stem == docx_path.stem

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["case_id"] == "TC_PATIENT_002"
    assert payload["body_screenshot_paths"] == [str(screen_path), str(active_path)]
    assert payload["module_chain_labels"] == ["新建患者"]

    document = Document(docx_path)
    text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    assert "用例执行结果" in text
    assert "失败模块：patient.create" in text
    assert "患者姓名不能包含特殊字符" in text