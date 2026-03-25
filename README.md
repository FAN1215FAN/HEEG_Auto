# HEEG Auto

HEEG Auto 是一个基于 Python + pywinauto 的 WPF 桌面 UI 自动化标准工程，当前第一版聚焦于 `Neuracle.EEGRecorder.Viewer.HEEG.exe` 的“新增患者”冒烟测试。

当前状态：

- 已按标准化工程结构创建目录、运行入口、检查器脚本、测试入口与文档
- 已实现首批通用动作：启动应用、点击、输入、组合框选择、单选框选择、窗口等待、文本断言、失败截图
- 已支持中文动作名、中文控件别名、`AutomationId` 定位和可见文本定位的混合手动搭建方式
- 已新增中文行式脚本最小原型，测试同事可以按“一行一个步骤”的方式描述自动化
- 已提供两种用例形式：中文行式脚本 `create_patient.zh` 和结构化 YAML `create_patient.yaml`
- `run_demo.py` 每次执行后会自动生成同名 JSON 报告和 Word 报告，便于向领导、测试和研发同步执行结果

推荐入口：

- 日常单次演示：`python run_demo.py`
- 控件树导出：`python run_inspector.py`
- 测试执行：`python -m pytest`

解释器要求：

- Python 3.10 及以上
- 建议在项目根目录创建 `.venv`

项目概览：

- `src/heeg_auto/config`：项目设置、控件定位、YAML 用例、中文行式脚本用例
- `src/heeg_auto/core`：驱动、基础页面、动作执行器、日志、行式脚本编译器、报告生成器
- `src/heeg_auto/pages`：主界面与创建患者弹窗页面对象
- `tests`：pytest 用例与失败截图钩子
- `tools/inspectors`：控件树导出脚本
- `artifacts`：日志、截图、JSON/Word 报告、pytest HTML 报告、控件树导出产物
