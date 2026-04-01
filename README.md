# HEEG Auto

HEEG Auto 是一个面向特定 WPF 上位机软件的 Python + pywinauto 自动化项目。当前主线不是通用低代码平台，而是一个可持续扩展、可交付、可治理的桌面 UI 自动化工程。

当前项目采用“中文正式用例 + 元素清单 + 可编辑模块 YAML + runner 编排 + pytest 治理与执行”的主线结构，用于持续扩展业务模块、正式 case、失败截图、日志和报告能力。

## 当前项目定位

- 面向真实 WPF 客户端软件的自动化执行与验证
- 用中文 YAML 编写正式业务 case，降低维护门槛
- 用稳定的动作映射、元素清单和模块定义承接自然语言与代码执行
- 用 pytest 统一做收集、治理、UI smoke 执行和报告输出
- 让项目具备再次演示、交付和后续接手能力

## 当前主线结构

项目当前围绕 6 个核心层次组织：

- `actions`：自然语言动作与底层实现的固定映射
- `elements`：稳定控件定位资产
- `modules`：可编辑业务模块 YAML
- `cases`：中文正式用例 YAML
- `runner`：case 加载、参数解析、模块调度、执行编排
- `tests`：pytest 治理测试与真实 UI smoke 入口

## 已接入主线的模块与样板

- `启动软件` -> `system.launch`
- `新建患者` -> `patient.create`
- `设备设置` -> `device.settings`

已存在正式 case 示例：

- `TC_PATIENT_001`
- `TC_PATIENT_002`
- `TC_DEVICE_001`
- `TC_LONG_001`

## 常用入口

- 单次演示：`python run_demo.py`
- 多 case 选择运行：`python run_case_suite.py`
- 结构与治理层测试：`python -m pytest`
- 真实 UI 套件：`python -m pytest -m ui --run-ui`
- 导出控件树：`python run_inspector.py`

## 文档索引

- 项目交付说明：[docs/project_delivery_overview.md](docs/project_delivery_overview.md)
- 架构说明：[docs/architecture.md](docs/architecture.md)
- 目录说明：[docs/folder_guide.md](docs/folder_guide.md)
- 映射说明：[docs/mapping_guide.md](docs/mapping_guide.md)
- 控件与元素清单：[docs/control_inventory.md](docs/control_inventory.md)
- 运行指南：[docs/run_guide.md](docs/run_guide.md)
- 维护流程：[docs/maintenance_workflow.md](docs/maintenance_workflow.md)
- 需求范围：[docs/requirements.md](docs/requirements.md)

## 当前固定约束

- 正式用例继续使用中文 YAML，并以 `模块链` 为核心结构
- 启动软件作为显式系统模块写入 `模块链`
- 一个 case 可以串接多个业务模块
- `数据` 是可选层，默认推荐“直接参数优先”
- 动作映射、元素清单、模块注册和自然语言对应关系属于长期资产
- 历史原型统一归档到 `src/heeg_auto/legacy/`，不再作为主线入口
- 下拉框等重选择控件，优先在元素层存控件本体，在 case 层写具体业务值
