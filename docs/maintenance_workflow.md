# 维护流程

未来对本项目的任何修改，至少应遵守以下流程：

1. 修改前先阅读：
   - `README.md`
   - `CHANGELOG.md`
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
3. 动作映射、元素清单、模块注册和自然语言对应关系属于长期资产，不做负向改动
4. 修改代码后同步更新相关 Markdown 文档
5. 重要结构或运行方式变化必须更新：
   - `docs/project_tree.md`
   - `docs/conversation_summary.md`
   - `CHANGELOG.md`
6. 正式用例优先使用带编号的模块调用式 YAML
7. 历史原型统一归档到 `src/heeg_auto/legacy/`，不要重新拉回主线目录

## 扩展大模块的固定步骤

未来新增大模块时，推荐固定按下面顺序推进：

- 先补元素清单
- 再补模块定义
- 再补模块注册
- 再补正式 case
- 最后补映射文档和测试

这样可以保证动作映射、元素清单和自然语言映射这三类长期资产始终同步更新。