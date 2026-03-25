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
    main_path = screenshot_dir / "demo_main.png"

    for path, color in ((screen_path, "red"), (active_path, "blue"), (main_path, "green")):
        Image.new("RGB", (120, 80), color=color).save(path)

    reporting.REPORT_DIR = tmp_path
    reporting.ensure_artifact_dirs = lambda: tmp_path.mkdir(parents=True, exist_ok=True)

    result = {
        "case_name": "create_patient_line_smoke",
        "case_path": "D:/AI_project/AI_Auto/HEEG_Auto/src/heeg_auto/config/cases/create_patient.zh",
        "description": "新增患者冒烟测试",
        "passed": False,
        "status": "FAIL",
        "context": {"patient_name": "张三"},
        "started_at": "2026-03-25 10:30:00",
        "finished_at": "2026-03-25 10:30:05",
        "duration_seconds": 5.0,
        "report_timestamp": "20260325_103000",
        "steps": [
            {
                "index": 1,
                "action": "启动应用",
                "target": "-",
                "parameters": "-",
                "status": "PASS",
                "duration_seconds": 1.2,
                "error_summary": "",
            },
            {
                "index": 2,
                "action": "断言窗口关闭",
                "target": "创建患者",
                "parameters": "-",
                "status": "FAIL",
                "duration_seconds": 2.5,
                "error_summary": "text still visible in main window after timeout=15s: 创建患者",
            },
        ],
        "error_summary": "text still visible in main window after timeout=15s: 创建患者",
        "error_detail": "Traceback (most recent call last): ...",
        "artifact_paths": [str(screen_path), str(active_path), str(main_path)],
        "environment": {
            "app_path": "F:/neuracle/HEEG_project/HEEG/NSH-R/Neuracle.EEGRecorder.Viewer.HEEG.exe",
            "case_path": "D:/AI_project/AI_Auto/HEEG_Auto/src/heeg_auto/config/cases/create_patient.zh",
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
    assert payload["report_title"] == "HEEG 自动化测试执行报告"
    assert payload["report_files"]["json"] == str(json_path)
    assert payload["report_files"]["docx"] == str(docx_path)
    assert payload["body_screenshot_paths"] == [str(screen_path), str(active_path)]

    document = Document(docx_path)
    text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    assert "HEEG 自动化测试执行报告" in text
    assert "失败信息" in text
    assert "完整错误堆栈" in text
