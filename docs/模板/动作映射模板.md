# 动作映射表模板

用于固定“自然语言动作 -> 英文动作 ID -> 参数格式 -> 代码实现”的关系。

## 使用原则

- 一旦动作命名对外发布，原则上不随意修改
- 自然语言动作和英文动作 ID 必须一一对应
- 参数格式必须写清楚，避免脚本和代码解释不一致
- 对应代码文件要固定且可追踪

## 模板

| 自然语言动作 | 英文动作 ID | 参数格式 | 返回值 | 实现文件 | 备注 |
| --- | --- | --- | --- | --- | --- |
| 单击 | click | target | 无 | `src/heeg_auto/actions/click.py` | 固定动作 |
| 输入 | input_text | target, value | 无 | `src/heeg_auto/actions/input_text.py` | 固定动作 |
| 等待窗口 | wait_for_window | target, timeout | 无 | `src/heeg_auto/actions/wait_for_window.py` | 固定动作 |
| 断言存在 | assert_exists | target, timeout | bool/异常 | `src/heeg_auto/actions/assert_exists.py` | 固定动作 |

## 建议字段说明

- 自然语言动作：给测试同事或模块编排层使用的动作名
- 英文动作 ID：代码中的稳定动作标识
- 参数格式：固定参数顺序或参数名
- 返回值：动作执行后的结果约定
- 实现文件：最终代码落点
- 备注：版本说明、兼容性约定、是否废弃等
