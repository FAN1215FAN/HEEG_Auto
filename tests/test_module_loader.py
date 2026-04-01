from __future__ import annotations

import pytest

from heeg_auto.modules import ModuleStore
from tests.support.case_catalog import build_module_params


@pytest.mark.parametrize("module_id", build_module_params())
def test_registered_modules_are_loadable(module_id: str):
    payload = ModuleStore().load(module_id)

    assert payload["module_id"] == module_id
    assert payload["module_label"]
    assert payload["steps"]
    assert "PASS" in payload["assertions"]
