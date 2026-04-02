from __future__ import annotations

from pathlib import Path

import pytest

from heeg_auto.runner.case_loader import FormalCaseLoader
from tests.support.case_catalog import build_case_params


@pytest.mark.smoke
@pytest.mark.parametrize("case_file", build_case_params(ui=False))
def test_formal_cases_are_loadable(case_file: Path):
    payload = FormalCaseLoader().load(case_file)

    assert payload["case_id"]
    assert payload["case_name"]
    assert payload["module_chain"]
    assert payload["module_chain_labels"]
    assert all(module_label for module_label in payload["module_chain_labels"])
