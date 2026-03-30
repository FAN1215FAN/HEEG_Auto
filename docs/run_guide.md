# 运行指南

## 环境准备

1. 在项目根目录创建虚拟环境：`python -m venv .venv`
2. 激活虚拟环境
3. 安装依赖：`pip install -r requirements.txt`
4. 推荐在 VS Code 中打开项目目录运行

## 推荐运行方式

- 单次演示：`python run_demo.py`
- 多 case 选择运行：`python run_case_suite.py`
- 结构与治理层测试：`python -m pytest`
- 真实 UI 套件：`python -m pytest -m ui --run-ui`
- 导出控件树：`python run_inspector.py`

## 当前默认运行内容

`run_demo.py` 当前默认执行：

- `src/heeg_auto/cases/patient/TC_PATIENT_001.yaml`

该入口会输出：

- 用例编号
- 用例名称
- 模块链
- 患者姓名
- 执行结果
- JSON / Word 报告路径

## 正式用例结构

当前正式用例采用“模块调用式”结构，推荐直接写中文字段：

```yaml
用例编号: TC_PATIENT_002
用例名称: 新建患者_姓名含特殊字符
标签:
  - regression
  - patient
数据:
  患者姓名: 张三@123
  病历号: PID${timestamp}
  脑电号: EEG${timestamp}
模块链:
  - 模块: 新建患者
    参数:
      姓名: ${患者姓名}
      性别: 女
      利手: right_hand_radio
      病历号: ${病历号}
      脑电号: ${脑电号}
      备注: 负向模块化样板
      预期状态: FAIL
      预期错误包含: 患者姓名不能包含特殊字符
```

## 主要编辑位置

测试同事后续主要编辑的是：

- 正式 case YAML：`src/heeg_auto/cases/`
- 大模块定义 YAML：`src/heeg_auto/modules/`
- 元素清单 YAML：`src/heeg_auto/elements/`

底层 Python 文件主要负责稳定执行，不建议频繁直接修改。

## 会话策略

case 支持 `会话策略` 字段：

- `自动`：允许启动应用或连接当前已打开应用
- `复用已有应用`：要求复用已打开应用

当前样板：

- `TC_PATIENT_001` = `自动`
- `TC_PATIENT_002` = `复用已有应用`

## run_case_suite.py

可以在 VS Code 中直接运行 `run_case_suite.py`。

运行后会先列出所有正式 case，例如：

- `TC_PATIENT_001 | 新建患者_正常创建 | 模块链: 新建患者`
- `TC_PATIENT_002 | 新建患者_姓名含特殊字符 | 模块链: 新建患者`

支持输入：

- `all` 或 `全部`：运行全部 case
- `1,2`：按序号选择多个 case
- `TC_PATIENT_001,TC_PATIENT_002`：按用例编号选择多个 case

默认规则：

- 第一个 case 使用 `自动`
- 后续连续 case 可使用 `复用已有应用`，避免重复启动软件

## pytest 用途

pytest 当前负责的是执行与治理层，而不是业务用例编辑层。它主要承担：

- 收集正式 case，并在测试名称中展示 `用例编号｜用例名称｜模块链`
- 收集注册的大模块，并展示 `模块标识｜模块名称`
- 校验 case、元素清单、模块定义和报告结构
- 驱动真实 UI 套件连续运行
- 输出 HTML 报告

## 报告与截图

### 当前报告策略

- 成功：输出用例摘要和模块执行摘要
- 失败：单独输出故障详情、失败模块、失败步骤、截图和堆栈

### 当前截图策略

- 运行异常自动截图
- 断言失败自动截图
- 尽量同时保留：全屏 / 活动窗口 / 主窗口
- 文件名包含：用例编号、失败位置、时间戳

## 历史原型说明

以下旧原型已降级到历史归档，不再作为当前主入口：

- `src/heeg_auto/legacy/phase1_cases/`
- `src/heeg_auto/legacy/phase2_transition/`