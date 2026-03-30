# 控件清单

## 当前主线元素清单文件

- `src/heeg_auto/elements/patient/create_patient.yaml`

## 当前已确认控件

| 元素键 | 中文名称 | 当前工程使用定位 | 原始信息 | 所属区域 |
| --- | --- | --- | --- | --- |
| `open_button` | 新增 | `AutomationId=NewPatient` + `Button` | `NewPatient` / `Button` | 主界面 |
| `name_input` | 姓名 | `AutomationId=PatientName` + `Edit` | `PatientName` / `Edit` | 创建患者区域 |
| `gender_combo` | 性别 | `AutomationId=PatientGender` + `ComboBox` | `PatientGender` / `ComboBox` | 创建患者区域 |
| `right_hand_radio` | 右利手 | `AutomationId=PatientRightHand` + `RadioButton` | `PatientRightHand` / `RadioButton` | 创建患者区域 |
| `patient_id_input` | 病历号 | `AutomationId=PatientID` + `Edit` | `PatientID` / `Edit` | 创建患者区域 |
| `eeg_id_input` | 脑电号 | `AutomationId=PatientEEGID` + `Edit` | `PatientEEGID` / `Edit` | 创建患者区域 |
| `note_input` | 备注 | `AutomationId=PatientNote` + `Edit` | `PatientNote` / `Edit` | 创建患者区域 |
| `confirm_button` | 确定 | `title=确定` + `Button` | `Ok` / `Button` | 创建患者区域 |
| `dialog_marker` | 创建患者标题 | `title=创建患者` | 标题文本 | 创建患者区域 |

## 当前说明

- 当前正式用例和模块执行优先使用上述元素清单
- `config/locators.py` 当前仍保留，用于兼容底层动作执行器和历史原型
- 日期控件暂未纳入当前正式模块
- 主界面患者列表仍采用文本出现校验策略，后续可升级为表格级断言

## 后续建议补充

- 主界面患者列表容器及行控件的 AutomationId
- 新增成功后的提示消息控件信息
- 其他高频业务按钮和弹窗的 AutomationId