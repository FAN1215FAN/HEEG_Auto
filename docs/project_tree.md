# 当前目录树

```text
HEEG_Auto/
├─ artifacts/
│  ├─ inspectors/
│  ├─ logs/
│  ├─ reports/
│  └─ screenshots/
├─ docs/
│  └─ project_briefing.md
├─ scripts/
├─ src/
│  └─ heeg_auto/
│     ├─ config/
│     │  └─ cases/
│     ├─ core/
│     │  └─ reporting.py
│     └─ pages/
├─ tests/
├─ tools/
│  └─ inspectors/
├─ CHANGELOG.md
├─ README.md
├─ pyproject.toml
├─ requirements.txt
├─ run_demo.py
└─ run_inspector.py
```

`src/heeg_auto/config/cases/` 当前同时包含 `create_patient.yaml` 和 `create_patient.zh`。

`artifacts/reports/` 当前同时用于保存 `pytest-report.html` 以及单次运行生成的 `.json/.docx` 报告。
