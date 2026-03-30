from __future__ import annotations

import pytest


@pytest.mark.smoke
@pytest.mark.patient
def test_tc_patient_001(app_session, case_context):
    """pytest 只负责执行完整用例，不再直接平铺业务动作。"""

    case_context["current_case_id"] = "TC_PATIENT_001"

    # 后续建议流程：
    # 1. 读取 cases/patient/TC_PATIENT_001.yaml
    # 2. 解析 module_chain
    # 3. 调用 ModuleRunner 执行
    # 4. 汇总结果并断言
    assert app_session == "app_session_placeholder"
