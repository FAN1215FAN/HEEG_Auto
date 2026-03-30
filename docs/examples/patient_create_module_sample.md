# 新建患者模块样板拆分方案

## 1. 目标

本文件用于把当前“新建患者”这一个原型场景，进一步拆解成下一阶段可以复用的样板模块。

目的是回答三个问题：

- 新建患者这个大模块内部应该怎么拆
- 哪些属于元素，哪些属于子模块，哪些属于大模块
- 将来完整用例应该如何调用这个大模块

## 2. 当前大模块定义

### 模块名称

- 新建患者

### 建议模块标识

- `patient.create`

### 模块职责

- 打开创建患者区域
- 填写患者基础信息
- 提交创建动作
- 校验是否成功或是否出现预期失败

## 3. 元素层建议

建议将当前已掌握的控件拆为元素定义，而不是直接写在动作脚本里。

### 建议元素清单

- `new_button`
  - 新增按钮
- `name_input`
  - 姓名输入框
- `gender_combo`
  - 性别下拉框
- `patient_id_input`
  - 病历号输入框
- `eeg_id_input`
  - 脑电号输入框
- `note_input`
  - 备注输入框
- `confirm_button`
  - 确定按钮
- `cancel_button`
  - 关闭按钮
- `dialog_marker`
  - 创建患者标题或可见性标记

## 4. 子模块层建议

建议拆成以下子模块：

### 4.1 `open_create_patient`

职责：

- 点击主界面“新增”按钮
- 等待创建患者区域出现

### 4.2 `fill_basic_info`

职责：

- 输入姓名
- 选择性别
- 可扩展到年龄、出生日期等基础字段

### 4.3 `fill_identifiers`

职责：

- 输入病历号
- 输入脑电号

### 4.4 `fill_note`

职责：

- 输入备注

### 4.5 `submit_create_patient`

职责：

- 点击确定
- 返回提交结果或后续状态

### 4.6 `validate_create_patient`

职责：

- 成功场景：断言主界面出现患者信息
- 失败场景：断言窗口未关闭、保留错误信息和截图

## 5. 大模块对外参数建议

`patient.create` 建议对外暴露以下参数：

- `name`
- `gender`
- `patient_id`
- `eeg_id`
- `note`
- `expect_status`
- `expect_error_contains`

这样可以同时支持：

- 正向成功用例
- 负向失败用例

## 6. 正向调用示例

```yaml
module_chain:
  - module: patient.create
    params:
      name: 张三
      gender: 女
      patient_id: PID_001
      eeg_id: EEG_001
      note: 正向样板
      expect_status: PASS
```

## 7. 负向调用示例

```yaml
module_chain:
  - module: patient.create
    params:
      name: 张三@123
      gender: 女
      patient_id: PID_002
      eeg_id: EEG_002
      note: 负向样板
      expect_status: FAIL
      expect_error_contains: 患者姓名不能包含特殊字符
```

## 8. pytest 中的推荐接法

建议后续 pytest 测试函数不再直接写平铺动作，而是：

1. 读取正式用例
2. 获取 `module_chain`
3. 调用 `module_runner`
4. 收集模块结果
5. 汇总输出摘要或失败详情

也就是说，pytest 只负责“跑用例”，不再直接承担“拼动作”。

## 9. 推荐结论

“新建患者”应该作为下一阶段样板大模块优先重构。

原因是：

- 当前已经有真实可运行基础
- 元素已较完整
- 同时覆盖正向与负向测试需求
- 便于验证从平铺 DSL 向模块化结构迁移的完整路径
