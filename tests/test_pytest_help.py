from __future__ import annotations

from tests import conftest


def test_render_minimal_help_focuses_on_project_parameters():
    help_text = conftest._render_minimal_help()

    assert "--run-formal" in help_text
    assert "--helpfull" in help_text
    assert "--maxfail" not in help_text
    assert "--collect-only" not in help_text
