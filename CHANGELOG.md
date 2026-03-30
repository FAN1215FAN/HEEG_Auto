# Changelog

## 2026-03-27

- 将公开架构层级收敛为 5 层：动作、元素、大模块、用例、pytest 执行层，不再对外保留“小模块”概念
- 正式确认 `pytest` 作为执行与治理层：直接收集 case、展示模块链、筛选标签、执行真实 UI 套件
- 调整 `tests/support/case_catalog.py`，让 pytest 用例名称直接显示 `用例编号｜用例名称｜模块链`
- 调整 `tests/test_module_loader.py`，让 pytest 直接展示注册的大模块列表
- 调整 `src/heeg_auto/core/driver.py`，支持连接已有应用、复用当前会话、优雅关闭与强制回收兜底
- 调整 `src/heeg_auto/core/actions.py` 与 `src/heeg_auto/runner/formal_case_runner.py`，支持 UI 套件连续运行多个 case 时复用同一应用会话
- 调整 `tests/smoke/test_patient_ui_flow.py`，真实 UI 套件改为单次启动 / 连续复用模式，避免第二个 case 再次启动软件
- 调整 `src/heeg_auto/core/base_page.py`，增强文本断言对主窗口、当前顶层窗口和桌面顶层窗口的可见文本搜索能力
- 调整 `src/heeg_auto/modules/patient/create_patient.yaml` 与 `src/heeg_auto/runner/module_runner.py`，将负向文案断言改为“可选证据”，提升复用会话下的稳定性
- 调整 `src/heeg_auto/core/reporting.py`，修复中文报告文案，统一为“成功摘要 + 故障详情”口径
- 新增 `docs/mapping_guide.md`，专门说明动作、元素、大模块和 case 的固定映射关系
- 更新 `README.md`、`docs/run_guide.md`、`docs/architecture.md`、`docs/folder_guide.md`、`docs/project_tree.md`、`docs/conversation_summary.md`、`docs/maintenance_workflow.md`、`docs/requirements.md`，同步当前主线结构
- 历史原型已归档到 `src/heeg_auto/legacy/`，并删除不再使用的 `submodules/` 目录与缓存文件
- 当前验证结果：`python -m pytest` 通过，`python run_demo.py` 通过，`python -m pytest -m ui --run-ui` 通过

## 2026-03-26

- 新增 `docs/project_briefing.md`，整理本次自动化项目的讲解口径、结构树、技术选型、路线取舍、当前成果与常见质疑回应
- 更新 `docs/folder_guide.md`，补充“各个功能代码在哪个文件夹/文件中”的定位说明，便于演示和后续维护
- 为核心执行链路补充简洁注释，覆盖动作执行、行式脚本编译、失败截图、用例运行和报告生成等关键模块

## 2026-03-25

- 新增 `src/heeg_auto/core/reporting.py`，将单次运行结果自动生成为全中文 JSON 报告和 Word 报告
- 调整 `CaseRunner` 返回结构化执行结果，包含步骤明细、环境信息、失败摘要、完整错误堆栈和失败截图路径
- 调整 `run_demo.py`：每次运行后自动输出同名 `.json/.docx` 报告，并在失败时返回非零退出码
- 新增 `tests/test_reporting.py`，校验报告文件生成、同名规则、正文截图选择和 Word 文本结构
- 在依赖中补充 `python-docx`，作为 Word 报告生成组件
- 文档同步更新：补充自动报告能力、报告目录说明、运行后产物说明和架构分层变化

## 2026-03-24

- 按 `windows-uia-project-standard` 创建新的 Python 标准化 WPF UIA 自动化工程
- 建立 `artifacts/`、`docs/`、`src/`、`tests/`、`tools/inspectors/` 等标准目录
- 实现首批通用动作与 YAML 用例运行器，支持创建患者场景的稳定最小闭环
- 新增 `run_demo.py`、`run_inspector.py`、`pytest` 配置、失败截图与 HTML 报告输出路径
- 补充项目说明、架构说明、控件清单、运行指南、维护流程等文档
- 修复 PyCharm 直接运行根目录入口脚本时无法导入 `src/heeg_auto` 包的问题
- 新增中文动作名、中文控件别名、手写可见文本定位和中文定位键支持，更接近手动搭建式自动化
- 根据真实运行结果调整默认患者名格式，避免触发“患者姓名不能包含特殊字符”的业务校验
- 修正 `timestamp` 上下文格式，避免时间戳自带下划线再次污染患者姓名
- 新增中文行式脚本最小原型，并让 `CaseRunner` 同时支持结构化 YAML 与行式脚本两种输入
- 优化中文行式脚本易用性：补充“直接文本 vs 变量引用”说明，并为未定义变量提供更直白的中文报错
- 升级失败取证：运行异常和断言失败都会自动保存全屏截图，并尽量补充活动窗口与主窗口截图，文件名包含失败步骤信息

- 修复 README 与多份文档尾部的乱码段落，统一恢复为可读中文说明。
- 收紧 README、运行指南和目录说明中的重复表述，按“总览 / 运行 / 目录”重新分工。
- 删除阶段性文档 `next_stage_architecture_draft.md`、`next_stage_blueprint.md`、`project_briefing.md`，并同步清理目录树说明。
- 更新 `docs/requirements.md`，同步当前主线需求：VS Code、会话策略、模块调用式 case 与 pytest 执行定位。
