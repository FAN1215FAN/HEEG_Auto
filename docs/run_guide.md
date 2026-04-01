# 运行指南

## 环境准备
### YAML 编写提醒

- 同一个层级里不要重复写同名字段。例如 `参数` 里不能连续写两次 `采样率`；现在加载阶段会直接报“重复键”错误。
- 设备设置、创建患者这类弹窗模块已经按“优先绑定实际弹窗”处理，case 层不需要额外写主界面点击后的等待补丁。


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

## 正式用例结构

当前正式用例采用“模块调用式”结构，推荐直接写中文字段：

```yaml
用例编号: TC_DEVICE_001
用例名称: 设备设置+新建患者
标签:
  - smoke
  - device
  - patient

模块链:
  - 模块: 启动软件
    参数:
      软件路径: F:/neuracle/HEEG_project/HEEG/NSH-R/Neuracle.EEGRecorder.Viewer.HEEG.exe
      会话模式: 自动

  - 模块: 设备设置
    参数:
      设备类型: Neusen HEEG
      采样率: "2000"
      设备增益: "6"
      IP地址: "192.168.1.100"
      预期状态: PASS

  - 模块: 新建患者
    参数:
      患者姓名: 张三
      性别: 女
      利手: 左手
      病历号: "123"
      脑电号: "456"
      预期状态: PASS
```

## 数据层说明

`数据` 现在是**可选层**。

### 推荐默认写法

如果某个值只在一个模块里使用一次，推荐直接写在该模块 `参数` 中，不要额外包一层 `数据`。

### 适合使用 `数据` 的场景

只有在下面两种情况，才建议增加 `数据`：

1. 同一个值需要跨多个模块复用
2. 需要动态变量，例如 `${timestamp}`

例如：

```yaml
数据:
  软件路径: F:/.../Neuracle.EEGRecorder.Viewer.HEEG.exe
  患者姓名: autopatient${timestamp}
  病历号: PID${timestamp}
  脑电号: EEG${timestamp}

模块链:
  - 模块: 启动软件
    参数:
      软件路径: ${软件路径}
      会话模式: 自动
  - 模块: 新建患者
    参数:
      患者姓名: ${患者姓名}
      性别: 女
      利手: 右手
      病历号: ${病历号}
      脑电号: ${脑电号}
      预期状态: PASS
```

如果只是固定文本，请直接写文本，不要写成 `${...}`。

## 主要编辑位置

测试同事后续主要编辑的是：
- 正式 case YAML：`src/heeg_auto/cases/`
- 大模块定义 YAML：`src/heeg_auto/modules/`
- 元素清单 YAML：`src/heeg_auto/elements/`

底层 Python 文件主要负责稳定执行，不建议频繁直接修改。

## 启动软件系统模块

当前启动软件不再隐藏在 runner 外层，而是作为显式系统模块写在 case 的 `模块链` 中。

推荐参数：
- `软件路径`
- `会话模式`

当前支持的会话模式：
- `自动`：允许启动新应用，若已有可复用会话则直接复用/连接
- `复用已有应用`：要求复用当前已打开应用，如果未检测到则直接报错

## run_case_suite.py

可以在 VS Code 中直接运行 `run_case_suite.py`。
运行后会先列出所有正式 case，例如：

- `TC_PATIENT_001 | 新建患者_正常创建 | 模块链: 启动软件 -> 新建患者`
- `TC_PATIENT_002 | 新建患者_姓名含特殊字符 | 模块链: 启动软件 -> 新建患者`
- `TC_DEVICE_001 | 设备设置+新建患者 | 模块链: 启动软件 -> 设备设置 -> 新建患者`

支持输入：
- `all` 或 `全部`：运行全部 case
- `1,2`：按序号选择多个 case
- `TC_PATIENT_001,TC_DEVICE_001`：按用例编号选择多个 case

执行顺序以你的输入顺序为准。例如输入 `2,1,3`，就按 `2 -> 1 -> 3` 运行。

## pytest 用途

pytest 当前负责执行与治理层，而不是业务用例编辑层。它主要承担：
- 收集正式 case，并在测试名中展示 `用例编号 | 用例名称 | 模块链`
- 收集注册的大模块，并展示 `模块标识 | 模块名称`
- 校验 case、元素清单、模块定义和报告结构
- 驱动真实 UI 套件连续运行
- 输出 HTML 报告
