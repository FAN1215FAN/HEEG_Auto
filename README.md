# HEEG Auto

HEEG Auto 是一个面向特定 WPF 软件的 Python + pywinauto 自动化测试工程。当前主线采用“中文正式用例 + 可编辑大模块 + pytest 执行治理层”。

## 当前主线

项目当前按 5 层模型组织：

- 动作层：固定自然语言动作与代码实现映射
- 元素层：固定模块元素清单与定位信息
- 大模块层：可编辑的大模块定义文件 + 稳定执行实现
- 用例层：带编号的正式用例，支持一个 case 串多个大模块
- pytest 执行层：负责收集、展示、筛选、运行和汇总报告

## 当前样板

- 大模块：`新建患者` -> `patient.create`
- 正式用例：`TC_PATIENT_001`、`TC_PATIENT_002`
- 会话策略样板：`TC_PATIENT_001 = 自动`，`TC_PATIENT_002 = 复用已有应用`

## 常用入口

- 单次演示：`python run_demo.py`
- 多 case 选择运行：`python run_case_suite.py`
- 结构与治理层测试：`python -m pytest`
- 真实 UI 套件：`python -m pytest -m ui --run-ui`
- 控件树导出：`python run_inspector.py`

## 文档索引

- 运行说明：`docs/run_guide.md`
- 架构说明：`docs/architecture.md`
- 映射说明：`docs/mapping_guide.md`
- 目录说明：`docs/folder_guide.md`
- 维护流程：`docs/maintenance_workflow.md`
- 控件与元素清单说明：`docs/control_inventory.md`

## 当前固定约束

- 正式用例继续使用中文 YAML，并采用模块调用式结构
- 一个 case 可以串多个大模块
- 动作映射、元素清单、模块注册与自然语言对应关系属于长期资产，必须持续维护
- 历史原型统一归档到 `src/heeg_auto/legacy/`，不再作为主线入口