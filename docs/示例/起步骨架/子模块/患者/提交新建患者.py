from __future__ import annotations


def submit_create_patient(actions, elements) -> None:
    """执行提交动作。

    后续如果“点击确定”前后需要扩展等待、截图或异常捕获，
    建议优先在这里扩展，而不是把逻辑散落到完整用例里。
    """

    actions.click(elements["confirm_button"])
