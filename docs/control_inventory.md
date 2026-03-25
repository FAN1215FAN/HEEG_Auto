# 控件清单

## 当前已确认控件

| 中文名称 | 当前工程使用定位 | 原始信息 | 所属区域 |
| --- | --- | --- | --- |
| 新增 | `AutomationId=NewPatient` + `Button` | `NewPatient` / `Button` | 主界面 |
| 姓名 | `AutomationId=PatientName` + `Edit` | `PatientName` / `Edit` | 创建患者弹窗 |
| 性别 | `AutomationId=PatientGender` + `ComboBox` | `PatientGender` / `ComboBox` | 创建患者弹窗 |
| 出生日期 | 暂未使用 | `PatientBirthDate` / `Custom` | 创建患者弹窗 |
| 年龄 | 暂未使用 | `PatientAge` / `Edit` | 创建患者弹窗 |
| 右利手 | `AutomationId=PatientRightHand` + `RadioButton` | `PatientRightHand` / `RadioButton` | 创建患者弹窗 |
| 左利手 | 已记录，当前未用 | `PatienLeftHand` / `RadioButton` | 创建患者弹窗 |
| 无利手 | 已记录，当前未用 | `PatienNoHabitHand` / `RadioButton` | 创建患者弹窗 |
| 双利手 | 已记录，当前未用 | `PatienPairHand` / `RadioButton` | 创建患者弹窗 |
| 病历号 | `AutomationId=PatientID` + `Edit` | `PatientID` / `Edit` | 创建患者弹窗 |
| 脑电号 | `AutomationId=PatientEEGID` + `Edit` | `PatientEEGID` / `Edit` | 创建患者弹窗 |
| 备注 | `AutomationId=PatientNote` + `Edit` | `PatientNote` / `Edit` | 创建患者弹窗 |
| 确定 | `title=确定` + `Button` | `Ok` / `Button` | 创建患者弹窗 |
| 关闭 | `title=关闭` + `Button` | `Cancel` / `Button` | 创建患者弹窗 |

## 当前中文别名

- `新增` -> `NewPatient`
- `姓名` -> `PatientName`
- `性别` -> `PatientGender`
- `右利手` -> `PatientRightHand`
- `病历号` -> `PatientID`
- `脑电号` -> `PatientEEGID`
- `备注` -> `PatientNote`
- `确定` -> `Ok`
- `关闭` -> `Cancel`
- `创建患者` -> `create_patient_dialog`

## 当前策略说明

- 第一版优先使用上述控件完成“新增患者”闭环
- 日期控件暂不纳入自动化动作范围
- 创建患者弹窗在当前 UIA 结构中按主窗口内嵌容器处理，不按独立顶层窗口处理
- 主界面患者列表尚未拿到稳定的列表级 AutomationId，因此当前断言采用“新增患者唯一姓名出现在主窗口文本树中”的方式

## 后续建议补充

- 主界面患者列表容器及行控件的 AutomationId
- 新增成功后的提示消息控件信息
- 其他高频业务按钮和弹窗的 AutomationId
