from __future__ import annotations

import pytest


@pytest.fixture(scope="session")
def app_session():
    """启动与关闭应用的 session 级 fixture 样板。"""

    yield "app_session_placeholder"


@pytest.fixture()
def case_context(tmp_path):
    """每个完整用例独立持有自己的执行上下文。"""

    return {
        "artifacts_dir": tmp_path,
        "current_case_id": None,
    }
