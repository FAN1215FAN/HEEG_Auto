# 元素映射表模板

用于固定“模块元素名称 -> locator -> 页面 -> 引用代码位置”的关系。

## 使用原则

- 元素必须归属于某个明确的大模块
- 元素名称应在模块内唯一
- locator 信息与页面归属要一起保存
- 元素定义只负责说明和定位，不负责编排步骤

## 模板

| 所属模块 | 元素名称 | 人类说明 | 页面 | locator | ControlType | 引用子模块 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| patient.create | name_input | 姓名输入框 | dialog | `automation_id=PatientName` | Edit | `fill_basic_info` | 当前已接入 |
| patient.create | gender_combo | 性别下拉框 | dialog | `automation_id=PatientGender` | ComboBox | `fill_basic_info` | 当前已接入 |
| patient.create | confirm_button | 确定按钮 | dialog | `title=确定` | Button | `submit_create_patient` | 当前按标题定位 |

## 建议字段说明

- 所属模块：当前元素归属的大模块标识
- 元素名称：模块内部稳定名称
- 人类说明：方便测试同事和业务人员理解
- 页面：当前元素所在页面或区域
- locator：推荐统一写成结构化 locator 说明
- ControlType：当前元素控件类型
- 引用子模块：当前元素主要被哪些子模块使用
- 备注：定位策略、稳定性说明、备用定位方式等
