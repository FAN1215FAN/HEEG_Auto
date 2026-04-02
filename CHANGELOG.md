# Changelog

## 2026-04-02

- `run_case_suite.py` 改为直接调用 `FormalCaseRunner` 执行所选 case，不再通过 `pytest.main(...)` 间接执行日常正式用例。
- 日常执行默认不再追加非 case 指定的自动关软件动作，执行结束后界面状态以 case 本身为准；仅保留步骤卡住时的 watchdog 强制保护。
- 扩展执行结果模型，新增 `INTERRUPTED`（异常中断）结果，并在摘要中同时统计 `PASS / FAIL / INTERRUPTED / NOT_RUN`。
- `src/heeg_auto/core/reporting.py` 改为输出单一 HTML 报告，显式展示执行概览、开始/结束时间、用例名称、执行参数、执行结果、模块参数快照、失败原因/断言信息与截图产物链接，并去掉 Word/JSON 落盘。
- `run_case_suite.py` 现在每次只输出一份 `HEEG_Auto_Report_时间戳.html` 作为本次执行报告。
- `run_demo.py` 默认改为遵循 case 会话语义执行，不再在演示结束后自动关闭软件。
- 同步修正旧的治理测试假设，使 case 编号、物理目录层级和默认 case 路径与当前中文目录现状保持一致。

## 2026-04-01

- 正式 case 新增顶层 `变参`、`循环次数`、`失败即停` 配置，并支持按整条 case 展开为多轮独立执行。
- 模块调用改为显式 `断言组`，case 不再使用 `预期状态: PASS/FAIL`。
- 报告结果模型升级为多轮执行摘要，新增 `PASS / FAIL / NOT_RUN` 结果统计与首个失败详情。
- 启动软件路径从 case 中抽离，统一收敛到 `src/heeg_auto/config/app_config.yaml`。
- 新增 `src/heeg_auto/config/assertion_groups.yaml`、`docs/断言目录.md` 与 `docs/YAML编写规范.md`，用于维护断言目录与 YAML 编写规范。
- 现有正式 case 与模块 YAML 已整体迁移到新规范，并补充相应治理测试。
- 正式 case 目录与 YAML 文件名已改为中文描述，case 发现不再依赖 `TC_*.yaml` 文件名。
- `run_case_suite.py` 新增按目录批量选择能力，支持 `目录:患者` 这类输入方式。
- pytest smoke 执行新增目录级 before/after hook 基础设施，并在 UI 执行中启用“无进展 60 秒保护”。

## 2026-03-31

- 对齐 `wpf-module-importer` skill 与当前 HEEG 项目主线，使其生成骨架遵循 `actions / elements / modules / cases / runner / tests / docs` 结构。
- 新增 `docs/项目交付说明.md`，用于再次演示与交付说明，系统说明项目结构、pytest 作用、自然语言到代码的转化链路、主要目录与文档职责。
- 合并并收敛冗余文档口径：重写 README、目录说明、映射说明和维护流程，删除重复的 `docs/project_tree.md`。
- 修复弹窗关闭断言、dialog 根节点绑定和输入类控件查找问题，并补充对应回归测试。
- 正式用例 YAML 现在会拒绝重复键；例如同一个 `采样率` 写两次时，会在加载阶段直接报错，不再悄悄只保留最后一个值。
- 支持“数据层可选、直接参数优先”的正式 case 编写规则，并同步更新相关示例和说明。


