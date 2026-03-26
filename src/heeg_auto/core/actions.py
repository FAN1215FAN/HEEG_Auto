from __future__ import annotations

from datetime import datetime

from heeg_auto.config.locators import resolve_locator
from heeg_auto.config.settings import DEFAULT_TIMEOUT
from heeg_auto.pages.create_patient_dialog import CreatePatientDialogPage
from heeg_auto.pages.main_page import MainPage


ACTION_ALIASES = {
    "launch_app": "launch_app",
    "启动应用": "launch_app",
    "click": "click",
    "单击": "click",
    "input_text": "input_text",
    "输入": "input_text",
    "select_combo": "select_combo",
    "下拉选择": "select_combo",
    "select_radio": "select_radio",
    "选择单选": "select_radio",
    "wait_for_window": "wait_for_window",
    "等待窗口": "wait_for_window",
    "wait_visible": "wait_visible",
    "等待可见": "wait_visible",
    "assert_exists": "assert_exists",
    "断言存在": "assert_exists",
    "assert_window_closed": "assert_window_closed",
    "断言窗口关闭": "assert_window_closed",
    "assert_text_visible": "assert_text_visible",
    "断言文本可见": "assert_text_visible",
    "screenshot": "screenshot",
    "截图": "screenshot",
}


class ActionExecutor:
    def __init__(self, driver, logger) -> None:
        self.driver = driver
        self.logger = logger
        self.main_page = MainPage(driver=driver, logger=logger)
        self.dialog_page = None

    def resolve_action_name(self, action_name: str) -> str:
        if action_name not in ACTION_ALIASES:
            raise KeyError(f"Unsupported action: {action_name}")
        return ACTION_ALIASES[action_name]

    def resolve_target(self, target, default_page: str | None = None) -> dict:
        # 统一把中文别名、AutomationId 写法和手写 locator 转成底层一致的定位结构。
        if default_page is None:
            default_page = "dialog" if self.dialog_page is not None else "main"
        locator = resolve_locator(target, default_page=default_page)
        self.logger.info("Resolved target %s -> %s", target, locator)
        return locator

    def launch_app(self, **_: dict) -> None:
        self.driver.launch()
        self.main_page = MainPage(driver=self.driver, logger=self.logger)

    def click(self, target, **_: dict) -> None:
        locator = self.resolve_target(target)
        page = self._page_for(locator)
        page.click(locator)

    def wait_for_window(self, target, timeout: int = DEFAULT_TIMEOUT, **_: dict) -> None:
        locator = self.resolve_target(target, default_page="main")
        if locator.get("title"):
            # “创建患者”当前是主窗口中的业务区域，不是独立顶层窗口，因此用标题文本作为出现标记。
            self.dialog_page = CreatePatientDialogPage(driver=self.driver, logger=self.logger)
            self.dialog_page.wait_open(marker_text=locator["title"], timeout=timeout)
            return
        self.main_page.find(locator, timeout=timeout)

    def wait_visible(self, target, timeout: int = DEFAULT_TIMEOUT, **_: dict) -> None:
        locator = self.resolve_target(target)
        page = self._page_for(locator)
        page.find(locator, timeout=timeout)

    def assert_exists(self, target, timeout: int = DEFAULT_TIMEOUT, **_: dict) -> None:
        locator = self.resolve_target(target)
        page = self._page_for(locator)
        page.find(locator, timeout=timeout)

    def input_text(self, target, value: str, **_: dict) -> None:
        locator = self.resolve_target(target)
        page = self._page_for(locator)
        page.input_text(locator, value)

    def select_combo(self, target, value: str, **_: dict) -> None:
        locator = self.resolve_target(target)
        page = self._page_for(locator)
        page.select_combo(locator, value)

    def select_radio(self, target, **_: dict) -> None:
        locator = self.resolve_target(target)
        page = self._page_for(locator)
        page.select_radio(locator)

    def assert_window_closed(self, target, timeout: int = DEFAULT_TIMEOUT, **_: dict) -> None:
        locator = self.resolve_target(target, default_page="main")
        if locator.get("title"):
            # 首版通过“标题文本消失”判断业务弹层关闭，避免依赖当前不稳定的顶层窗口结构。
            self.main_page.assert_text_not_visible(locator["title"], timeout=timeout)
            self.dialog_page = None
            return
        self.main_page.wait_closed(locator, timeout=timeout)

    def assert_text_visible(self, text: str, timeout: int = DEFAULT_TIMEOUT, **_: dict) -> None:
        self.main_page.assert_text_visible(text=text, timeout=timeout)

    def screenshot(self, file_name: str | None = None, **_: dict) -> None:
        if not file_name:
            file_name = f"manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        self.driver.capture_screenshot(file_name)

    def _page_for(self, locator: dict):
        page_name = locator.get("page")
        if page_name == "dialog":
            if self.dialog_page is None:
                # 当脚本先写“输入/选择”再写“等待窗口”时，这里补一次惰性初始化，降低步骤顺序耦合。
                self.dialog_page = CreatePatientDialogPage(driver=self.driver, logger=self.logger)
                self.dialog_page.wait_open()
            return self.dialog_page
        return self.main_page
