# Changelog

## 2026-04-09

- formal case 已统一迁移到 V2 步骤式结构，当前仓库中的正式业务 case 全部改为 `步骤 / 窗口 / 参数 / 元素 / 按钮 / 动作 / 断言` 写法。
- `启动软件.yaml`、患者管理目录 `init.yaml`、设备设置目录 `init.yaml` 已迁为 V2；目录 `cleanup.yaml` 继续保留空支持文件语义。
- 重写 `src/heeg_auto/v2/asset_store.py`、`src/heeg_auto/v2/case_loader.py`、`src/heeg_auto/v2/executor.py`，清理乱码并补上步骤级上下文回填，支持断言内引用前序填写值。
- 补齐 `双击 / 右键 / CheckBox` 能力到 `src/heeg_auto/core/base_page.py`、`src/heeg_auto/core/actions.py`、`src/heeg_auto/actions/registry.py`、`src/heeg_auto/core/line_dsl.py` 与 V2 执行器。
- 重建 V2 资产：窗口资产、元素资产、断言资产改为干净中文口径，并补了患者列表第一行、标题栏关闭按钮、脑电工作模式等治理项。
- 更新 `README.md`、`docs/架构说明.md`、`docs/目录说明.md`、`docs/运行指南.md`、`docs/V2*.md`、`docs/V2资产总表.md`、`docs/V2资产缺口清单.md`、`docs/维护流程.md`。
- 重写 `tests/test_v2_asset_store.py`、`tests/test_v2_case_loader.py`、`tests/test_v2_executor.py`、`tests/test_case_loader.py`、`tests/test_case_catalog.py` 和 `tests/support/case_catalog.py`，校正到当前 case 集合与 V2 行为。

## 2026-04-07

- 新增 `docs/V1参数设计说明.md`，固化第一版基于 `pytest` 的参数机制与命令行口径。
- 正式 case 的 `变参` 数据模型升级为“多参数手工枚举参数行”，支持单参数旧写法和多参数括号/逗号行写法并存。
- `FormalCaseRunner` 改为支持按参数行展开执行，并在执行时按整条 case 作用域解析变参占位符。
- `失败即停` 的默认值调整为关闭，单 case 内默认改为失败记录后继续后续参数行；若显式声明 `失败即停: 是`，仍保留中断后续轮次能力。
- 新增 `src/heeg_auto/runner/directory_lifecycle.py`，重新引入目录级 `init.yaml` / `cleanup.yaml` 环境管理机制，并在真实 UI formal 执行中支持按目录初始化、清理和失败后恢复。
- `pytest` 现已支持 `--run-formal`、`--case-id`、`--case-dir`、`--case-file` 等正式 case 执行参数，并通过 `pytest -h` 可见。

## 2026-04-02

- `run_case_suite.py` 改为直接调用 `FormalCaseRunner` 执行所选 case，不再通过 `pytest.main(...)` 间接执行日常正式用例。
- 报告结果模型升级为多轮执行摘要，新增 `PASS / FAIL / INTERRUPTED / NOT_RUN` 结果统计。
- `src/heeg_auto/core/reporting.py` 改为输出单一 HTML 报告。