from __future__ import annotations

from heeg_auto.core.case_runner import CaseRunner
from heeg_auto.core.line_dsl import LineDslCompiler


def test_compile_line_dsl_to_case():
    script = """
    用例 smoke_case
    说明 这是一个最小原型
    变量 patient_name autopatient${timestamp}
    启动应用
    单击 新增
    输入 姓名 ${patient_name}
    断言文本可见 ${patient_name}
    """

    case = LineDslCompiler().compile_to_case(script, default_case_name="fallback")

    assert case["case_name"] == "smoke_case"
    assert case["description"] == "这是一个最小原型"
    assert case["data"]["patient_name"] == "autopatient${timestamp}"
    assert case["steps"] == [
        {"action": "启动应用"},
        {"action": "单击", "target": "新增"},
        {"action": "输入", "target": "姓名", "value": "${patient_name}"},
        {"action": "断言文本可见", "text": "${patient_name}"},
    ]


def test_compile_line_dsl_supports_quoted_values():
    script = '输入 备注 "hello world"\n截图 "manual shot.png"'
    case = LineDslCompiler().compile_to_case(script, default_case_name="quoted")

    assert case["steps"][0] == {"action": "输入", "target": "备注", "value": "hello world"}
    assert case["steps"][1] == {"action": "截图", "file_name": "manual shot.png"}


def test_resolve_text_reports_friendly_message_for_missing_variable():
    try:
        CaseRunner._resolve_text("${张三}", {})
        raise AssertionError("Expected missing variable error")
    except KeyError as exc:
        message = str(exc)

    assert "未定义变量：张三" in message
    assert "输入 姓名 张三" in message
