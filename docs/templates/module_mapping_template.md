# 大模块映射表模板

用于固定“大模块名称 -> 模块标识 -> 子模块 -> 实现文件 -> 元素文件”的关系。

## 使用原则

- 一个大模块必须有唯一模块标识
- 大模块是正式用例调用的最小业务编排单元
- 大模块内部可以拆多个子模块，但对外暴露统一接口
- 元素文件和模块实现文件需要清晰关联

## 模板

| 模块名称 | 模块标识 | 子模块列表 | 输入参数 | 实现文件 | 元素文件 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| 新建患者 | patient.create | `fill_basic_info`, `submit_create_patient` | `name, gender, patient_id, eeg_id` | `src/heeg_auto/modules/patient/create.py` | `src/heeg_auto/elements/patient/create_patient.yaml` | 样板模块 |
| 查看阻抗 | impedance.view | `open_impedance_panel`, `read_impedance_result` | `patient_id` | `src/heeg_auto/modules/impedance/view.py` | `src/heeg_auto/elements/impedance/view.yaml` | 待扩展 |

## 建议字段说明

- 模块名称：给业务和测试同事看的名称
- 模块标识：给代码、用例、报告使用的稳定标识
- 子模块列表：当前模块依赖的子模块清单
- 输入参数：模块对外暴露的参数
- 实现文件：最终代码落点
- 元素文件：当前模块依赖的元素清单
- 备注：状态说明、是否样板、是否废弃等
