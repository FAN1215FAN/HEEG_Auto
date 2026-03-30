# 目录说明

- `artifacts/inspectors`：控件树导出文本
- `artifacts/logs`：运行日志
- `artifacts/reports`：pytest HTML 报告、JSON 报告、Word 报告
- `artifacts/screenshots`：失败截图
- `docs`：项目文档、样板和模板
- `src/heeg_auto/actions`：动作映射定义
- `src/heeg_auto/elements`：元素清单
- `src/heeg_auto/modules`：大模块定义与注册
- `src/heeg_auto/cases`：正式用例
- `src/heeg_auto/runner`：case 加载、模块调度、正式 runner
- `src/heeg_auto/core`：driver、基础动作实现、报告
- `src/heeg_auto/pages`：页面对象
- `src/heeg_auto/legacy`：历史原型归档
- `tests`：pytest 用例与公共 fixture
- `tools/inspectors`：控件树导出工具

## 功能代码定位

- 启动入口：`run_demo.py`
  负责执行默认正式 case 并输出报告路径。
- 多 case 入口：`run_case_suite.py`
  负责列出正式 case，并允许在运行前手动选择 case。
- 控件树导出入口：`run_inspector.py`
  负责导出控件树，辅助定位 AutomationId。
- 项目配置：`src/heeg_auto/config/settings.py`
  保存应用路径、默认 case、产物目录等配置。
- 动作映射：`src/heeg_auto/actions/registry.py`
  固定自然语言动作与底层实现的对应关系。
- 元素清单：`src/heeg_auto/elements/patient/create_patient.yaml`
  定义“新建患者”模块使用的定位信息。
- 大模块定义：`src/heeg_auto/modules/patient/create_patient.yaml`
  定义“新建患者”模块的步骤、参数和断言。
- 模块注册：`src/heeg_auto/modules/registry.py`
  定义中文模块名与内部模块标识的对应关系。
- 用例文件：`src/heeg_auto/cases/patient`
  保存带编号的完整正式用例。
- 用例加载：`src/heeg_auto/runner/case_loader.py`
  负责加载中文 case YAML、变量替换和模块链解析。
- 模块调度：`src/heeg_auto/runner/module_runner.py`
  负责按模块定义执行步骤和断言。
- 正式 runner：`src/heeg_auto/runner/formal_case_runner.py`
  负责驱动应用会话、执行模块链并汇总结果。
- 基础动作实现：`src/heeg_auto/core/actions.py`
  提供点击、输入、下拉选择、断言、截图等底层能力。
- 驱动与会话复用：`src/heeg_auto/core/driver.py`
  负责启动/连接应用、主窗口识别、失败取证与关闭清理。
- 报告生成：`src/heeg_auto/core/reporting.py`
  负责生成 JSON / Word 报告。
- pytest case 目录：`tests/smoke/test_patient_cases.py`
  负责把正式 case 直观展示为 pytest 条目。
- pytest 模块目录：`tests/test_module_loader.py`
  负责把注册的大模块直观展示为 pytest 条目。
- pytest UI 套件：`tests/smoke/test_patient_ui_flow.py`
  负责连续运行真实 UI case，并复用同一应用会话。

## 新增大模块

新增大模块时，目录保持简单即可：

1. 在 `src/heeg_auto/elements/业务域/` 下新增元素清单 YAML
2. 在 `src/heeg_auto/modules/业务域/` 下新增模块定义 YAML
3. 在 `src/heeg_auto/cases/业务域/` 下新增正式 case
4. 同步更新 `src/heeg_auto/modules/registry.py` 与 `docs/mapping_guide.md`

详细变更顺序请继续参考 `docs/maintenance_workflow.md`。