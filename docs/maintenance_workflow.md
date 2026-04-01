# 维护流程

未来对本项目的任何修改，至少应遵守以下流程：

1. 修改前先阅读：
   - `README.md`
   - `CHANGELOG.md`
   - `docs/project_delivery_overview.md`
   - `docs/requirements.md`
   - `docs/architecture.md`
   - `docs/folder_guide.md`
   - `docs/run_guide.md`
   - `docs/control_inventory.md`
   - `docs/mapping_guide.md`
2. 优先沿当前主线结构修改：
   - `actions`
   - `elements`
   - `modules`
   - `cases`
   - `runner`
   - `tests`
3. 动作映射、元素清单、模块注册和自然语言对应关系属于长期资产，不做随意跳层改动。
4. 修改代码后必须同步更新相关 Markdown 文档。
5. 重要结构、运行方式或交付口径变化时，至少同步更新：
   - `README.md`
   - `docs/project_delivery_overview.md`
   - `docs/conversation_summary.md`
   - `CHANGELOG.md`
6. 正式用例优先使用带编号的模块调用式 YAML。
7. 历史原型统一归档到 `src/heeg_auto/legacy/`，不要重新拉回主线目录。

## 扩展业务模块的固定步骤

未来新增业务模块时，建议按下面顺序推进：

1. 整理控件信息表
2. 补元素清单 YAML
3. 补业务模块 YAML
4. 补模块注册
5. 补正式 case
6. 补 pytest 治理测试
7. 最后同步更新文档与清单

这样可以保证：

- 动作映射
- 元素清单
- 模块注册
- 正式 case
- pytest 治理层
- 文档说明

始终保持同一套主线口径。

## 启动软件系统模块约定

- 启动软件不再隐藏在 runner 外层，而是作为显式系统模块写入 `模块链`
- 推荐参数：`软件路径`、`会话模式`
- 业务 case 如需连续运行，可通过 `会话模式: 复用已有应用` 明确要求复用当前会话

## 下拉控件类模块约定

对于设备设置这类下拉较多的模块：

- 第一轮优先沉淀控件本体，而不是枚举全部下拉值
- 具体业务值默认写在 case 层参数中
- 纯展示字段在第一轮可以先不进入元素清单，除非用户明确要求断言它们
