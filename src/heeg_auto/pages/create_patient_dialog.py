from __future__ import annotations

from heeg_auto.core.base_page import BasePage


class CreatePatientDialogPage(BasePage):
    def __init__(self, driver, logger) -> None:
        super().__init__(driver=driver, logger=logger, root=driver.main_window)

    def wait_open(self, marker_text: str = "创建患者", timeout: int = 15):
        self.assert_text_visible(marker_text, timeout=timeout)
        self.root = self.driver.main_window
        return self.root
