# 架构设计

## 当前主架构

项目当前按以下 5 层组织：

- 动作层：`src/heeg_auto/actions`
- 元素层：`src/heeg_auto/elements`
- 大模块层：`src/heeg_auto/modules`
- 用例层：`src/heeg_auto/cases`
- pytest 执行层：`tests` + `src/heeg_auto/runner`

## 各层职责

### 动作层

职责：

- 固定自然语言动作与代码实现映射
- 保证自然语言到代码的映射长期稳定

当前位置：

- `src/heeg_auto/actions/registry.py`
- `src/heeg_auto/core/actions.py`

### 元素层

职责：

- 固定每个大模块内部使用的元素清单
- 沉淀 AutomationId、标题、控件类型等定位信息

当前位置：

- `src/heeg_auto/elements/patient/create_patient.yaml`
- `src/heeg_auto/elements/loader.py`

### 大模块层

职责：

- 定义一个完整可复用的业务模块
- 接收参数
- 内部组合动作与元素完成业务执行

当前位置：

- `src/heeg_auto/modules/patient/create_patient.yaml`
- `src/heeg_auto/modules/registry.py`
- `src/heeg_auto/modules/loader.py`

### 用例层

职责：

- 定义完整测试场景
- 一个 case 里可以串多个大模块
- 用例必须有编号

当前位置：

- `src/heeg_auto/cases/patient/TC_PATIENT_001.yaml`
- `src/heeg_auto/cases/patient/TC_PATIENT_002.yaml`

### pytest 执行层

职责：

- 收集 case
- 收集模块
- 展示 case 与模块链
- 筛选标签
- 执行真实 UI 套件
- 输出 HTML 报告

当前位置：

- `tests/smoke/test_patient_cases.py`
- `tests/test_module_loader.py`
- `tests/smoke/test_patient_ui_flow.py`
- `tests/conftest.py`

## 当前执行流

1. `run_demo.py` 读取默认正式 case
2. `FormalCaseLoader` 把中文字段转成内部稳定字段
3. `FormalCaseRunner` 负责驱动应用会话与模块链执行
4. `ModuleRunner` 读取大模块定义并执行步骤与断言
5. `reporting.py` 输出 JSON / Word 报告
6. `pytest` 收集和展示 case / 模块，并提供批量执行入口

## 关键设计约束

- 正式用例优先中文字段，内部模块标识保持稳定 ASCII
- 一个 case 可以串多个大模块
- 大模块可编辑，底层执行逻辑稳定
- 动作、元素、模块与代码的对应关系必须文档化并持续更新
- 成功报告精简，故障报告展开

## 当前样板模块

- 大模块：`新建患者` -> `patient.create`
- 正向用例：`TC_PATIENT_001`
- 负向用例：`TC_PATIENT_002`

## 当前真实联调状态

- `python run_demo.py` 已跑通
- `python -m pytest` 已通过
- `python -m pytest -m ui --run-ui` 已能连续执行两个 case，并复用同一应用会话