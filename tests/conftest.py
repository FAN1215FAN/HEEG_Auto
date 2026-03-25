from __future__ import annotations

from datetime import datetime

import pytest

from heeg_auto.config.settings import ensure_artifact_dirs
from heeg_auto.core.driver import UIADriver
from heeg_auto.core.logger import build_logger


def pytest_configure(config):
    ensure_artifact_dirs()


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)


@pytest.fixture
def app_driver(request):
    logger = build_logger(name="pytest_run")
    driver = UIADriver(logger=logger)
    request.node.app_driver = driver
    yield driver
    driver.close()


@pytest.fixture(autouse=True)
def failure_screenshot(request):
    yield
    rep_call = getattr(request.node, "rep_call", None)
    driver = getattr(request.node, "app_driver", None)
    if rep_call and rep_call.failed and driver:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        saved_paths = driver.capture_failure_artifacts(
            case_name=request.node.name,
            step_name=f"pytest_{rep_call.when}",
            timestamp=timestamp,
        )
        for path in saved_paths:
            logger = getattr(driver, "logger", None)
            if logger:
                logger.error("failure.artifact %s", path)
