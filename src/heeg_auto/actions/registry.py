from __future__ import annotations


ACTION_DEFINITIONS = {
    "launch_app": {
        "label": "启动应用",
        "implementation": "heeg_auto.core.actions.ActionExecutor.launch_app",
        "parameters": [],
    },
    "click": {
        "label": "点击",
        "implementation": "heeg_auto.core.actions.ActionExecutor.click",
        "parameters": ["target"],
    },
    "double_click": {
        "label": "双击",
        "implementation": "heeg_auto.core.actions.ActionExecutor.double_click",
        "parameters": ["target"],
    },
    "right_click": {
        "label": "右键",
        "implementation": "heeg_auto.core.actions.ActionExecutor.right_click",
        "parameters": ["target"],
    },
    "input_text": {
        "label": "输入",
        "implementation": "heeg_auto.core.actions.ActionExecutor.input_text",
        "parameters": ["target", "value"],
    },
    "select_combo": {
        "label": "下拉选择",
        "implementation": "heeg_auto.core.actions.ActionExecutor.select_combo",
        "parameters": ["target", "value"],
    },
    "select_radio": {
        "label": "选择单选",
        "implementation": "heeg_auto.core.actions.ActionExecutor.select_radio",
        "parameters": ["target"],
    },
    "set_checkbox": {
        "label": "设置勾选",
        "implementation": "heeg_auto.core.actions.ActionExecutor.set_checkbox",
        "parameters": ["target", "value"],
    },
    "wait_for_window": {
        "label": "等待窗口",
        "implementation": "heeg_auto.core.actions.ActionExecutor.wait_for_window",
        "parameters": ["target", "timeout"],
    },
    "assert_exists": {
        "label": "断言存在",
        "implementation": "heeg_auto.core.actions.ActionExecutor.assert_exists",
        "parameters": ["target", "timeout"],
    },
    "assert_window_closed": {
        "label": "断言窗口关闭",
        "implementation": "heeg_auto.core.actions.ActionExecutor.assert_window_closed",
        "parameters": ["target", "timeout"],
    },
    "assert_text_visible": {
        "label": "断言文本可见",
        "implementation": "heeg_auto.core.actions.ActionExecutor.assert_text_visible",
        "parameters": ["text", "timeout"],
    },
    "screenshot": {
        "label": "截图",
        "implementation": "heeg_auto.core.actions.ActionExecutor.screenshot",
        "parameters": ["file_name"],
    },
}

ACTION_NAME_MAP = {
    definition["label"]: action_id for action_id, definition in ACTION_DEFINITIONS.items()
}