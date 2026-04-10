# HEEG Auto

HEEG Auto 是一个面向 WPF 上位机软件的 Python + pywinauto 自动化项目。
当前主线已经切到 V2 步骤式 case，formal case 编写统一采用中文 YAML 的 `步骤` 结构，目录级 `init.yaml` 继续负责启动和环境恢复。

## 当前状态

- 当前 formal case 已统一迁移到 V2 推荐结构。
- 目录级 `init.yaml` 已改为 V2，负责启动软件和恢复主界面。
- `cleanup.yaml` 仍保留为目录支持文件，占位清理不承载业务动作。
- V2 已支持 `点击 / 双击 / 右键 / 输入 / 下拉选择 / 选择单选 / 设置勾选 / 等待窗口 / 断言窗口关闭 / 断言存在 / 断言文本可见`。
- V2 断言继续采用命名断言，当前以窗口资产、元素资产、断言资产三套 YAML 管理。

## 推荐 V2 结构

```yaml
用例编号:
用例名称:
标签:
变参:
循环次数:
失败即停:
步骤:
  - 名称:
    窗口:
    参数:
    元素:
    按钮:
    动作:
    断言:
    超时:
    可选:
```

关键约束：
- 业务 case 不再写启动软件步骤。
- `窗口` 是当前步骤作用域。
- `按钮` 走点击简写。
- `参数` 按元素控件类型自动推断动作。
- `断言` 继续走命名断言资产。

## 当前 formal case

- [启动软件.yaml](/D:/AI_project/AI_Auto/HEEG_Auto/src/heeg_auto/cases/启动/启动软件.yaml)
- [新建患者_正常创建.yaml](/D:/AI_project/AI_Auto/HEEG_Auto/src/heeg_auto/cases/患者检查管理/患者管理/新建患者_正常创建.yaml)
- [新建患者_V2_点击关闭.yaml](/D:/AI_project/AI_Auto/HEEG_Auto/src/heeg_auto/cases/患者检查管理/患者管理/新建患者_V2_点击关闭.yaml)
- [设备设置循环.yaml](/D:/AI_project/AI_Auto/HEEG_Auto/src/heeg_auto/cases/系统设置/设备设置/设备设置循环.yaml)
- [设备设置_V2_采样率校验.yaml](/D:/AI_project/AI_Auto/HEEG_Auto/src/heeg_auto/cases/系统设置/设备设置/设备设置_V2_采样率校验.yaml)

## 常用入口

- `python run_demo.py`
- `python run_case.py`
- `python -m pytest --run-formal --run-ui -s`
- `python -m pytest`
- `python run_inspector.py`

## 文档索引

- [架构说明.md](/D:/AI_project/AI_Auto/HEEG_Auto/docs/架构说明.md)
- [目录说明.md](/D:/AI_project/AI_Auto/HEEG_Auto/docs/目录说明.md)
- [运行指南.md](/D:/AI_project/AI_Auto/HEEG_Auto/docs/运行指南.md)
- [V2执行器设计说明.md](/D:/AI_project/AI_Auto/HEEG_Auto/docs/V2执行器设计说明.md)
- [V2窗口资产规范.md](/D:/AI_project/AI_Auto/HEEG_Auto/docs/V2窗口资产规范.md)
- [V2元素资产规范.md](/D:/AI_project/AI_Auto/HEEG_Auto/docs/V2元素资产规范.md)
- [V2断言资产规范.md](/D:/AI_project/AI_Auto/HEEG_Auto/docs/V2断言资产规范.md)
- [V2资产总表.md](/D:/AI_project/AI_Auto/HEEG_Auto/docs/V2资产总表.md)
- [V2资产缺口清单.md](/D:/AI_project/AI_Auto/HEEG_Auto/docs/V2资产缺口清单.md)