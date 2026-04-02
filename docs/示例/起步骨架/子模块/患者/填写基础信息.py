from __future__ import annotations


def fill_basic_info(actions, elements, *, name: str, gender: str, habit_hand: str = "右利手") -> None:
    """填写患者基础信息。

    这个样板用于说明：
    - 子模块负责“小业务单元”
    - 子模块内部可以调用多个基础动作
    - 子模块对外只暴露业务参数，不暴露 locator 细节
    """

    actions.input_text(elements["name_input"], name)
    actions.select_combo(elements["gender_combo"], gender)
    actions.select_radio(elements[habit_hand])
