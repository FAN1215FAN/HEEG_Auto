# 映射关系说明

本文用于说明“自然语言 -> 内部标识 -> 代码实现”的固定映射关系。这部分属于长期资产，后续新增动作、元素或业务模块时必须同步维护。

## 1. 动作映射

动作注册位置：`src/heeg_auto/actions/registry.py`

动作执行实现：`src/heeg_auto/core/actions.py`

当前主线的典型动作包括：

- `启动应用` -> `launch_app`
- `单击` -> `click`
- `输入` -> `input_text`
- `下拉选择` -> `select_combo`
- `选择单选` -> `select_radio`
- `等待窗口` -> `wait_for_window`
- `断言存在` -> `assert_exists`
- `断言窗口关闭` -> `assert_window_closed`
- `断言文本可见` -> `assert_text_visible`

这意味着业务模块 YAML 里写的是中文动作，但运行时会被稳定映射到内部 action id，再落到 `ActionExecutor` 的对应方法。

## 2. 元素映射

元素目录：`src/heeg_auto/elements/`

元素解析：`src/heeg_auto/elements/loader.py`

元素层负责维护稳定控件资产，例如：

- 业务中文标签
- 页面归属 `page`
- `automation_id`
- `control_type`
- `title`
- 兼容别名 `aliases`

### `patient.create`

典型映射示例：

- `新增按钮` -> `open_button`
- `创建患者标题` -> `dialog_marker`
- `姓名输入框` -> `name_input`
- `性别下拉框` -> `gender_combo`
- `病历号输入框` -> `patient_id_input`
- `脑电号输入框` -> `eeg_id_input`
- `确认按钮` -> `confirm_button`

### `device.settings`

典型映射示例：

- `设备设置按钮` -> `open_button`
- `设备设置标题` -> `dialog_marker`
- `设备类型下拉框` -> `device_type_combo`
- `采样率下拉框` -> `sample_rate_combo`
- `IP地址输入框` -> `ip_address_input`
- `设备增益下拉框` -> `gain_combo`
- `设备设置确认按钮` -> `confirm_button`

## 3. 模块映射

模块注册位置：`src/heeg_auto/modules/registry.py`

模块定义目录：`src/heeg_auto/modules/`

模块加载位置：`src/heeg_auto/modules/loader.py`

模块执行位置：`src/heeg_auto/runner/module_runner.py`

当前主线模块包括：

- `启动软件` -> `system.launch`
- `新建患者` -> `patient.create`
- `设备设置` -> `device.settings`

模块层的作用不是存零散动作，而是定义完整业务过程。模块 YAML 会引用元素清单，并用中文动作描述步骤和断言。

## 4. case 映射

case 目录：`src/heeg_auto/cases/`

case 加载位置：`src/heeg_auto/runner/case_loader.py`

pytest 展示支撑：`tests/support/case_catalog.py`

正式 case 当前使用中文 YAML，并以 `模块链` 为核心结构。例如：

- `TC_PATIENT_001`
- `TC_PATIENT_002`
- `TC_DEVICE_001`
- `TC_LONG_001`

`case_loader` 负责把中文字段映射为内部稳定字段，例如：

- `患者姓名` -> `patient_name`
- `性别` -> `gender`
- `利手` -> `habit_hand`
- `设备类型` -> `device_type`
- `采样率` -> `sample_rate`
- `软件路径` -> `exe_path`
- `会话模式` -> `session_mode`

同时它还负责：

- 解析可选 `数据` 层
- 处理 `${timestamp}` 这类动态变量
- 把中文模块名映射为稳定模块 id

## 5. 从自然语言到执行的转化逻辑

当前项目的关键链路可以概括为：

1. 用户在正式 case YAML 中写中文业务场景
2. `FormalCaseLoader` 标准化 case 字段、参数和变量
3. `ModuleRunner` 读取模块 YAML 并构建步骤上下文
4. `ElementStore` 把模块里的元素引用解析为真实 locator
5. `ActionExecutor` 通过动作 id 调用底层 UI 操作
6. `UIADriver` 和页面对象负责实际驱动 WPF 界面
7. `FormalCaseRunner` 汇总模块结果、失败工件与最终 case 结果

## 6. pytest 与映射链路的关系

pytest 不直接负责“把中文转代码”，但它负责承接这条映射链路的治理与执行：

- 收集正式 case
- 展示模块链
- 触发 UI smoke 套件
- 校验 loader / registry / 结构完整性
- 输出 HTML 报告

因此当前项目不是“pytest 外挂几个脚本”，而是把 pytest 放在主线治理层统一承接。

## 7. 维护要求

- 新增动作时，同时更新动作注册与底层实现。
- 新增元素时，同时更新元素清单与 `docs/control_inventory.md`。
- 新增模块时，同时更新模块注册、正式 case、pytest 治理测试和本文档。
- 中文展示名可以继续使用中文，但内部模块 id、元素 key、文件名应保持稳定可维护。
