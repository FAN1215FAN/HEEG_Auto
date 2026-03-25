from __future__ import annotations

from heeg_auto.config.locators import get_locator
from heeg_auto.core.base_page import BasePage


class MainPage(BasePage):
    def wait_ready(self, timeout: int = 30):
        return self.driver.main_window.wait("ready", timeout=timeout)

    def open_create_patient_dialog(self):
        self.click(get_locator("NewPatient"))
        from heeg_auto.pages.create_patient_dialog import CreatePatientDialogPage

        dialog_page = CreatePatientDialogPage(driver=self.driver, logger=self.logger)
        dialog_page.wait_open()
        return dialog_page

    def wait_patient_visible(self, patient_name: str, timeout: int = 20) -> None:
        self.assert_text_visible(text=patient_name, timeout=timeout)
