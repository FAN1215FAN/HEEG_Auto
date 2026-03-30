# 当前目录树

```text
HEEG_Auto/
├─ artifacts/
│  ├─ inspectors/
│  ├─ logs/
│  ├─ reports/
│  └─ screenshots/
├─ docs/
│  ├─ examples/
│  ├─ templates/
│  ├─ architecture.md
│  ├─ control_inventory.md
│  ├─ mapping_guide.md
│  └─ run_guide.md
├─ src/
│  └─ heeg_auto/
│     ├─ actions/
│     ├─ cases/
│     │  └─ patient/
│     ├─ config/
│     ├─ core/
│     ├─ elements/
│     │  └─ patient/
│     ├─ legacy/
│     │  ├─ phase1_cases/
│     │  └─ phase2_transition/
│     ├─ modules/
│     │  └─ patient/
│     ├─ pages/
│     └─ runner/
├─ tests/
│  ├─ smoke/
│  ├─ support/
│  ├─ conftest.py
│  ├─ test_case_loader.py
│  ├─ test_elements_loader.py
│  ├─ test_module_loader.py
│  ├─ test_reporting.py
│  └─ test_runtime_locator_sanitization.py
├─ tools/
│  └─ inspectors/
├─ CHANGELOG.md
├─ README.md
├─ pyproject.toml
├─ requirements.txt
├─ run_demo.py
└─ run_inspector.py
```

说明：

- `src/heeg_auto/cases/` 是当前正式用例主目录。
- `src/heeg_auto/modules/` 是当前大模块定义主目录。
- `src/heeg_auto/legacy/` 用于存放已退出主线的历史原型。
- `tests/smoke/` 当前直接体现 pytest 的 case 视图和 UI 套件视图。