# HEEG Auto

HEEG Auto 是一个面向特定 WPF 上位机软件的 Python + pywinauto 自动化项目。当前主线不是通用低代码平台，而是一个可持续扩展、可交付、可治理的桌面 UI 自动化工程。

当前项目采用“中文正式用例 + 元素清单 + 可编辑模块 YAML + runner 编排 + pytest 治理”的主线结构，并已支持变参展开、断言组命名、失败即停、统一启动路径配置，以及面向汇报的单一 HTML 报告；报告默认保留执行概览、开始/结束时间、模块参数快照、异常/未执行轮次与截图链接，不再展开成功步骤明细。

## 当前项目定位

- 面向真实 WPF 客户端软件的自动化执行与验证
- 用中文 YAML 编写正式业务 case，降低维护门槛
- 用稳定的动作映射、元素清单和模块定义承接自然语言与代码执行
- 用 pytest 做治理测试与可选 UI smoke，用 run_case_suite.py 承接日常正式 case 执行与汇报报告输出
- 让项目具备再次演示、交付和后续接手能力

## 当前主线结构

项目当前围绕 6 个核心层次组织：

- `actions`：自然语言动作与底层实现的固定映射
- `elements`：稳定控件定位资产
- `modules`：可编辑业务模块 YAML
- `cases`：中文正式用例 YAML
- `runner`：case 加载、参数解析、多轮执行编排
- `tests`：pytest 治理测试与真实 UI smoke 入口

## 当前已支持的用例能力

- 顶层 `变参` 定义区：同一 case 可按候选值展开为多轮独立执行
- 顶层 `循环次数`：同一 case 可按 N 次循环执行
- `失败即停`：任意一轮失败后，后续轮次标记为 `NOT_RUN`
- 模块级 `断言组`：case 中显式指定 `创建成功`、`创建失败`、`设置成功` 等业务判定组
- 启动软件路径从 case 中抽离，统一由 `src/heeg_auto/config/app_config.yaml` 管理
- 参数默认不加双引号；如果值本身需要输入双引号，使用单引号包裹整段文本

## 已接入主线的模块与样板

- `启动软件` -> `system.launch`
- `新建患者` -> `patient.create`
- `设备设置` -> `device.settings`

已存在正式 case 示例：

- `启动软件_01`
- `患者管理_01`
- `患者管理_02`
- `设备设置_02`
- `设备设置_01`

## 常用入口

- 单次演示：`python run_demo.py`
- 多 case 选择运行：`python run_case_suite.py`（输出 `artifacts/reports/HEEG_Auto_Report_时间戳.html`）
- 结构与治理层测试：`python -m pytest`
- 真实 UI 套件：`python -m pytest -m ui --run-ui`（治理/联调用）
- 导出控件树：`python run_inspector.py`

## 文档索引

- 项目交付说明：[docs/项目交付说明.md](docs/项目交付说明.md)
- 架构说明：[docs/架构说明.md](docs/架构说明.md)
- 目录说明：[docs/目录说明.md](docs/目录说明.md)
- 映射说明：[docs/映射说明.md](docs/映射说明.md)
- 控件与元素清单：[docs/控件清单.md](docs/控件清单.md)
- 运行指南：[docs/运行指南.md](docs/运行指南.md)
- YAML 编写规范：[docs/YAML编写规范.md](docs/YAML编写规范.md)
- 断言目录：[docs/断言目录.md](docs/断言目录.md)
- 维护流程：[docs/维护流程.md](docs/维护流程.md)
- 需求范围：[docs/需求说明.md](docs/需求说明.md)

## 当前固定约束

- 正式用例继续使用中文 YAML，并以 `模块链` 为核心结构
- 启动软件作为显式系统模块写入 `模块链`
- 一个 case 可以串接多个业务模块
- 变参在一个 case 中原则上只保留一组核心参数
- 所有多次执行场景统一遵循失败即停
- case 中不再使用 `预期状态: PASS/FAIL`，改为显式 `断言组`
- 动作映射、元素清单、模块注册、断言目录和自然语言对应关系属于长期资产
- 历史原型统一归档到 `src/heeg_auto/legacy/`，不再作为主线入口
- 下拉框等重选择控件，优先在元素层存控件本体，在 case 层写具体业务值





