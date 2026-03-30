# 会话结论

## 已达成一致

- 默认开发工具切换为 VS Code
- 放弃误听的 `PyText` 方向，保留并围绕 `pytest` 重构测试结构
- 正式用例不再平铺在 `.zh` 文件中
- 对外模型收敛为 5 层：动作、元素、大模块、用例、pytest 执行层
- 放弃“小模块”作为公开架构层
- 一个 case 可以串多个大模块
- 大模块采用“可编辑定义文件 + 稳定执行实现”的组合
- 动作、元素清单以及自然语言与代码映射必须保留并持续更新
- 报告改为“成功摘要 + 故障详情”

## 本阶段完成内容

- `pytest` 已经可以直接收集并展示正式 case：`用例编号｜用例名称｜模块链`
- `pytest` 已经可以直接收集并展示注册的大模块：`模块标识｜模块名称`
- 真实 UI 套件已改成“单次启动 / 连接 + 连续复用同一应用会话”
- 正向 case `TC_PATIENT_001` 已跑通
- 负向 case `TC_PATIENT_002` 已跑通
- `python -m pytest` 已通过
- `python -m pytest -m ui --run-ui` 已通过
- 历史原型已归档到 `src/heeg_auto/legacy/`

## 当前主线结构

- 动作映射：`src/heeg_auto/actions/registry.py`
- 元素清单：`src/heeg_auto/elements/patient/create_patient.yaml`
- 大模块定义：`src/heeg_auto/modules/patient/create_patient.yaml`
- 模块注册：`src/heeg_auto/modules/registry.py`
- 正式 case：`src/heeg_auto/cases/patient/TC_PATIENT_001.yaml`、`TC_PATIENT_002.yaml`
- 正式 runner：`src/heeg_auto/runner/formal_case_runner.py`
- pytest case 入口：`tests/smoke/test_patient_cases.py`
- pytest UI 入口：`tests/smoke/test_patient_ui_flow.py`

## 当前验证结果

- `python -m compileall src run_demo.py tests` 通过
- `python -m pytest` 通过，当前 `7 passed, 2 skipped`
- `python run_demo.py` 通过
- `python -m pytest -m ui --run-ui` 通过
- 新增正式 case 的 `会话策略` 设计：首个 case 可使用 `自动`，后续连续 case 可使用 `复用已有应用`，避免重复启动软件
