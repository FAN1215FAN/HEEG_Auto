from __future__ import annotations

from heeg_auto.core.base_page import BasePage


class _FakeWrapper:
    def __init__(self, handle: int = 1, automation_id: str = 'IPAddress1', control_type: str = 'Edit', name: str = 'fake') -> None:
        self.handle = handle
        self.element_info = type('Info', (), {'name': name, 'automation_id': automation_id, 'control_type': control_type})()


class _FakeRoot:
    def __init__(self, name: str, should_match=False) -> None:
        self.name = name
        self.handle = hash(name)
        self._should_match = should_match
        self.calls: list[dict] = []

    def child_window(self, **criteria):
        self.calls.append(criteria)
        if self._should_match and criteria.get('auto_id') == 'IPAddress1' and criteria.get('control_type') in {'Edit', 'TextBox', None}:
            return type('Spec', (), {'wrapper_object': lambda self: _FakeWrapper()})()
        raise RuntimeError(f'{self.name}:not found')

    def descendants(self):
        return []


class _FakeDriver:
    def __init__(self) -> None:
        self.main_window = _FakeRoot('main', should_match=False)
        self.main_window_wrapper = _FakeRoot('main_wrapper', should_match=False)
        self._top = _FakeRoot('top', should_match=True)
        self.app = None
        self.desktop = type('Desktop', (), {'top_window': lambda self: _FakeRoot('desktop_top', should_match=False)})()

    def top_window(self):
        return self._top


def test_find_falls_back_between_edit_and_textbox():
    class _TypeRoot(_FakeRoot):
        def child_window(self, **criteria):
            self.calls.append(criteria)
            if criteria.get('control_type') == 'Edit':
                raise RuntimeError('edit mismatch')
            if criteria.get('control_type') == 'TextBox':
                return type('Spec', (), {'wrapper_object': lambda self: _FakeWrapper()})()
            raise RuntimeError('unexpected')

    driver = _FakeDriver()
    driver.main_window = _TypeRoot('main')
    page = BasePage(driver=driver, logger=None, root=driver.main_window)

    wrapper = page.find({'automation_id': 'IPAddress1', 'control_type': 'Edit'}, timeout=1)

    assert wrapper.element_info.automation_id == 'IPAddress1'
    assert driver.main_window.calls[0] == {'auto_id': 'IPAddress1', 'control_type': 'Edit'}
    assert driver.main_window.calls[1] == {'auto_id': 'IPAddress1', 'control_type': 'TextBox'}


def test_find_falls_back_to_active_top_window_when_primary_root_misses():
    driver = _FakeDriver()
    page = BasePage(driver=driver, logger=None, root=driver.main_window)

    wrapper = page.find({'automation_id': 'IPAddress1', 'control_type': 'Edit'}, timeout=1)

    assert wrapper.element_info.automation_id == 'IPAddress1'
    assert driver.main_window.calls
    assert driver._top.calls


def test_find_falls_back_to_descendants_when_child_window_misses():
    class _DescRoot(_FakeRoot):
        def child_window(self, **criteria):
            self.calls.append(criteria)
            raise RuntimeError('child_window miss')

        def descendants(self):
            return [
                _FakeWrapper(handle=2, automation_id='Other', control_type='Button', name='其他按钮'),
                _FakeWrapper(handle=3, automation_id='SetDeviceSetting', control_type='Button', name='设备设置'),
            ]

    driver = _FakeDriver()
    root = _DescRoot('main')
    driver.main_window = root
    page = BasePage(driver=driver, logger=type('L', (), {'info': lambda *args, **kwargs: None})(), root=root)

    wrapper = page.find({'automation_id': 'SetDeviceSetting', 'control_type': 'Button'}, timeout=1)

    assert wrapper.element_info.automation_id == 'SetDeviceSetting'
    assert wrapper.element_info.control_type == 'Button'


def test_find_returns_root_when_wrapper_itself_matches_window_locator():
    class _WindowWrapper:
        def __init__(self) -> None:
            self.handle = 88
            self.element_info = type(
                "Info",
                (),
                {"name": "历史回放", "automation_id": "", "control_type": "Window", "class_name": "Window"},
            )()

        def descendants(self):
            return []

    class _Driver:
        def __init__(self) -> None:
            self.main_window = _FakeRoot('main', should_match=False)
            self.main_window_wrapper = self.main_window
            self._top = _WindowWrapper()
            self.app = None
            self.desktop = type('Desktop', (), {'top_window': lambda self: None})()

        def top_window(self):
            return self._top

    driver = _Driver()
    page = BasePage(driver=driver, logger=type('L', (), {'info': lambda *args, **kwargs: None})())

    wrapper = page.find({'title': '历史回放', 'control_type': 'Window', 'class_name': 'Window'}, timeout=1)

    assert wrapper is driver._top


def test_find_uses_application_window_for_non_active_top_level_window():
    target_wrapper = _FakeWrapper(handle=99, automation_id='', control_type='Window', name='历史回放')
    app_calls: list[dict] = []

    class _WindowSpec:
        def exists(self, timeout=0.5):
            return True

        def wrapper_object(self):
            return target_wrapper

    class _App:
        def window(self, **criteria):
            app_calls.append(criteria)
            return _WindowSpec()

    driver = _FakeDriver()
    driver.app = _App()
    driver._top = _FakeRoot('top', should_match=False)
    page = BasePage(driver=driver, logger=None)

    wrapper = page.find({'title': '历史回放', 'control_type': 'Window', 'class_name': 'Window'}, timeout=1)

    assert wrapper is target_wrapper
    assert app_calls == [{'title': '历史回放', 'control_type': 'Window', 'class_name': 'Window'}]


def test_assert_text_visible_scans_all_application_top_level_windows():
    popup = _FakeWrapper(handle=101, automation_id='', control_type='Window', name='剪辑完成。')

    class _App:
        def windows(self):
            return [popup]

    driver = _FakeDriver()
    driver.app = _App()
    driver._top = _FakeRoot('other_app', should_match=False)
    page = BasePage(driver=driver, logger=type('L', (), {'info': lambda *args, **kwargs: None})())

    page.assert_text_visible('剪辑完成。', timeout=1)


def test_find_scans_all_application_top_level_windows_for_controls():
    class _PopupRoot(_FakeRoot):
        def descendants(self):
            return [_FakeWrapper(handle=202, automation_id='OKButton', control_type='Button', name='确定')]

    class _App:
        def windows(self):
            return [_PopupRoot('popup')]

    driver = _FakeDriver()
    driver.app = _App()
    driver._top = _FakeRoot('other_app', should_match=False)
    page = BasePage(driver=driver, logger=type('L', (), {'info': lambda *args, **kwargs: None})())

    wrapper = page.find({'automation_id': 'OKButton', 'control_type': 'Button'}, timeout=1)

    assert wrapper.element_info.automation_id == 'OKButton'


class _FakeDialogPage:
    def __init__(self) -> None:
        self.root = type("Root", (), {"handle": 123})()
        self.closed = False

    def wait_closed(self, timeout=15):
        self.closed = True
        self.root = None


def test_assert_window_closed_prefers_dialog_handle_over_text_match():
    from heeg_auto.core.actions import ActionExecutor

    class _FakeDriverForActions:
        def __init__(self) -> None:
            self.main_window = _FakeRoot('main', should_match=False)
            self.main_window_wrapper = self.main_window
            self.app = None
            self.desktop = type('Desktop', (), {'top_window': lambda self: None})()

        def top_window(self):
            return None

    logger = type('L', (), {'info': lambda *args, **kwargs: None})()
    driver = _FakeDriverForActions()
    executor = ActionExecutor(driver=driver, logger=logger)
    fake_dialog = _FakeDialogPage()
    executor.dialog_page = fake_dialog

    called = {"text_check": False}

    def _unexpected(*args, **kwargs):
        called["text_check"] = True
        raise AssertionError('should not fall back to main page text check')

    executor.main_page.assert_text_not_visible = _unexpected
    executor.assert_window_closed({'title': '????'}, timeout=1)

    assert fake_dialog.closed is True
    assert called["text_check"] is False
