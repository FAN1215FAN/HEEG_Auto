# 映射关系说明

本文件用于说明“自然语言 -> 内部标识 -> 代码文件”的固定映射关系。该部分属于长期资产，后续新增动作、元素或大模块时必须同步更新。

## 动作映射

动作映射定义位置：`src/heeg_auto/actions/registry.py`
底层实现位置：`src/heeg_auto/core/actions.py`

当前首批动作示例：

- `单击` -> `click`
- `输入` -> `input_text`
- `下拉选择` -> `select_combo`
- `选择单选` -> `select_radio`
- `等待窗口` -> `wait_for_window`
- `断言存在` -> `assert_exists`
- `断言窗口关闭` -> `assert_window_closed`
- `断言文本可见` -> `assert_text_visible`

## 元素映射

元素清单位置：`src/heeg_auto/elements/`
当前样板：`src/heeg_auto/elements/patient/create_patient.yaml`
解析位置：`src/heeg_auto/elements/loader.py`

当前样板元素示例：

- `新增按钮` -> `open_button`
- `创建患者标题` -> `dialog_marker`
- `姓名输入框` -> `name_input`
- `性别下拉框` -> `gender_combo`
- `右利手单选` -> `right_hand_radio`
- `病历号输入框` -> `patient_id_input`
- `脑电号输入框` -> `eeg_id_input`
- `备注输入框` -> `note_input`
- `确定按钮` -> `confirm_button`

## 大模块映射

模块注册位置：`src/heeg_auto/modules/registry.py`
模块定义位置：`src/heeg_auto/modules/`
模块加载位置：`src/heeg_auto/modules/loader.py`
模块执行位置：`src/heeg_auto/runner/module_runner.py`

当前样板模块：

- `新建患者` -> `patient.create`
- 模块定义文件：`src/heeg_auto/modules/patient/create_patient.yaml`

## case 映射

case 目录：`src/heeg_auto/cases/`
case 加载位置：`src/heeg_auto/runner/case_loader.py`
pytest case 展示位置：`tests/smoke/test_patient_cases.py`

当前样板 case：

- `TC_PATIENT_001` -> `新建患者_正常创建`
- `TC_PATIENT_002` -> `新建患者_姓名含特殊字符`

## 维护要求

- 新增动作时，同时更新动作映射与底层实现说明
- 新增元素时，同时更新元素清单与 `docs/control_inventory.md`
- 新增大模块时，同时更新模块注册和本文件
- 自然语言显示名可以中文，内部模块标识与文件名保持稳定 ASCII / 编号

## 会话策略映射

正式 case 可以通过 `会话策略` 字段控制应用会话复用方式，当前支持：

- `自动`
- `复用已有应用`

执行位置：

- `src/heeg_auto/runner/formal_case_runner.py`
- `src/heeg_auto/core/actions.py`
- `src/heeg_auto/core/driver.py`

## pytest 与总入口的关系

- `run_case_suite.py` 负责列出正式 case，并允许手动选择 case
- `tests/smoke/test_patient_ui_flow.py` 是 pytest 的真实 UI 套件入口
- `tests/support/case_catalog.py` 负责把正式 case 转成 pytest 可展示的测试项名称

也就是说，用户日常可以运行 Python 入口，而底层仍由 pytest 统一执行和治理。