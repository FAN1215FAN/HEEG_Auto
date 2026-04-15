# HEEG Auto

HEEG Auto 是面向公司 WPF 上位机软件的桌面 UI 自动化工程。当前正式方案已经收敛为 `Python + pywinauto + UIA + pytest`，正式 case 真源为中文步骤式 YAML，正式资产真源为 `windows / elements / assertions`。

## 当前正式口径

1. 对外不再区分 `V1 / V2`。
2. 正式 case 只认 `src/heeg_auto/cases/` 下的步骤式 YAML。
3. 正式资产只认 `src/heeg_auto/assets/`。
4. `run_case.py` 面向测试日常运行，`pytest` 面向研发治理与 CI。
5. 环境模式当前支持 `reuse_per_suite` 和 `reset_per_directory`。

## 当前目标

- 让测试同事可以维护正式 case
- 让研发可以用 `pytest` 跑正式回归
- 让窗口、元素、断言逐步沉淀成正式资产
- 让框架在需求持续变化下仍然保持稳定

## 常用入口

### 测试日常执行

```bash
python run_case.py
```

### 演示入口

```bash
python run_demo.py
```

### UI 检查辅助入口

```bash
python run_inspector.py
python run_ratio_picker.py
```

### pytest 执行

```bash
python -m pytest
python -m pytest --run-formal --run-ui -s
python -m pytest --run-formal --run-ui --environment-mode reuse_per_suite -s
python -m pytest --run-formal --run-ui --environment-mode reset_per_directory -s
```

## 正式目录

- `src/heeg_auto/assets/`：正式窗口、元素、断言资产
- `src/heeg_auto/cases/`：正式步骤式 case，按软件当前大分类区分组，后续允许继续新增同级分类和下级文件夹
- `src/heeg_auto/runner/`：正式 case 执行链路
- `src/heeg_auto/core/`：底层驱动、动作、报告等基础能力
- `tests/`：治理测试和 smoke 测试
- `docs/`：项目文档，当前分为主线、资产规范、治理、模板四层

## 先看哪些文档

1. [项目书](docs/01_主线/项目书.md)
2. [框架收敛方案](docs/01_主线/框架收敛方案.md)
3. [瘦身迁移清单](docs/01_主线/瘦身迁移清单.md)
4. [需求说明](docs/01_主线/需求说明.md)
5. [运行指南](docs/01_主线/运行指南.md)
6. [资产总表](docs/02_资产规范/资产总表.md)
7. [资产缺口清单](docs/02_资产规范/资产缺口清单.md)
8. [对话纪要](docs/03_治理/对话纪要.md)
9. [文档治理索引](docs/03_治理/文档治理索引.md)

## 当前注意事项

1. 主文档后续采用持续更新，不再压缩式重写。
2. `docs` 现已按“主线 / 资产规范 / 治理 / 模板”分组。
3. 图形和波形类断言仍是当前最需要继续建设的能力。
4. 每次结构、脚本或正式口径调整，都会同步更新主文档进度和治理记录。
5. `cases` 顶层目录表示当前软件设想的大分类区，不是封闭列表，后续可以继续增加新的同级分类。
6. 默认 `stall-timeout` 已收紧到 `20` 秒；出现 UI 无进展或异常等待时，会优先快速失败并记录报错，不再长时间挂起当前 case。
