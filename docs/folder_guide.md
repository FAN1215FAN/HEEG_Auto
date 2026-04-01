# 目录说明

## 主代码目录

### `src/heeg_auto/actions/`

维护动作注册表，负责把中文动作名映射到稳定的内部 action id 与代码实现。

### `src/heeg_auto/elements/`

维护元素清单，按业务域存放稳定控件定位资产，例如 `patient/`、`device/`。

### `src/heeg_auto/modules/`

维护业务模块 YAML，按业务域存放可编辑模块定义，例如：

- `system/launch_application.yaml`
- `patient/create_patient.yaml`
- `device/device_settings.yaml`

### `src/heeg_auto/cases/`

维护正式 case，按业务域归档正式业务场景，例如：

- `patient/TC_PATIENT_001.yaml`
- `device/TC_DEVICE_001.yaml`
- `long/TC_LONG_001.yaml`

### `src/heeg_auto/runner/`

维护正式 case 的执行链路，负责 case 加载、模块调度、结果汇总。

### `src/heeg_auto/core/`

维护底层驱动、基础页面能力、动作执行器、报告等共用底座。

### `src/heeg_auto/pages/`

维护页面对象和弹窗辅助定位能力，用于承接复杂页面/对话框逻辑。

### `src/heeg_auto/config/`

维护默认路径、超时、定位兼容等底层配置。

### `src/heeg_auto/legacy/`

归档历史原型和过渡代码，不再作为当前主线入口。

## 测试目录

### `tests/`

pytest 治理层所在目录，负责：

- 正式 case 收集与展示
- loader / registry / 结构校验
- 真实 UI smoke 执行入口

### `tests/support/`

pytest 支持代码，例如 case 目录扫描、测试项显示名构造等。

### `tests/smoke/`

真实 UI 套件入口，基于正式 case 驱动 UI smoke 执行。

## 运行产物目录

### `artifacts/`

统一存放自动化运行产物，例如：

- `logs/`
- `screenshots/`
- `reports/`

## 说明文档目录

### `docs/`

存放项目文档，包括：

- 交付说明
- 架构说明
- 目录说明
- 映射说明
- 控件清单
- 运行指南
- 维护流程
- 需求范围

## 入口文件

### `run_demo.py`

单次默认 case 演示入口。

### `run_case_suite.py`

多 case 选择运行入口，可在 VS Code 中直接运行并按输入顺序执行所选 case。

### `run_inspector.py`

控件树导出入口。

## 新增模块时的落地顺序

建议固定按下面顺序新增资产：

1. `src/heeg_auto/elements/<domain>/...yaml`
2. `src/heeg_auto/modules/<domain>/...yaml`
3. `src/heeg_auto/cases/<domain>/TC_...yaml`
4. `src/heeg_auto/modules/registry.py`
5. `tests/` 中对应治理测试
6. `docs/mapping_guide.md` 与 `docs/control_inventory.md`
