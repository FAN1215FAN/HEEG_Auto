from __future__ import annotations

import shlex


class LineDslCompiler:
    def compile_to_case(self, script_content: str, default_case_name: str) -> dict:
        case_name = default_case_name
        description = "使用中文行式脚本描述的自动化用例。"
        data: dict[str, str] = {}
        steps: list[dict] = []

        for line_number, raw_line in enumerate(script_content.splitlines(), start=1):
            line = raw_line.strip()
            if not line or line.startswith("#") or line.startswith("//"):
                continue

            tokens = shlex.split(line, posix=True)
            if not tokens:
                continue

            command = tokens[0]
            if command == "用例":
                self._ensure_min_args(tokens, 2, line_number, "用例 需要名称")
                case_name = tokens[1]
                continue
            if command == "说明":
                self._ensure_min_args(tokens, 2, line_number, "说明 需要内容")
                description = " ".join(tokens[1:])
                continue
            if command == "变量":
                self._ensure_min_args(tokens, 3, line_number, "变量 需要键和值")
                data[tokens[1]] = " ".join(tokens[2:])
                continue

            steps.append(self._compile_action(tokens, line_number))

        if not steps:
            raise ValueError("中文行式脚本中没有可执行步骤")

        return {
            "case_name": case_name,
            "description": description,
            "data": data,
            "steps": steps,
        }

    def _compile_action(self, tokens: list[str], line_number: int) -> dict:
        action = tokens[0]

        if action == "启动应用":
            self._ensure_exact_args(tokens, 1, line_number, "启动应用 不需要参数")
            return {"action": action}
        if action in {"点击", "双击", "右键", "等待窗口", "等待可见", "断言存在", "选择单选", "断言窗口关闭"}:
            self._ensure_exact_args(tokens, 2, line_number, f"{action} 需要 1 个参数")
            return {"action": action, "target": tokens[1]}
        if action in {"输入", "下拉选择", "设置勾选"}:
            self._ensure_min_args(tokens, 3, line_number, f"{action} 需要目标和值")
            return {"action": action, "target": tokens[1], "value": " ".join(tokens[2:])}
        if action == "断言文本可见":
            self._ensure_min_args(tokens, 2, line_number, "断言文本可见 需要文本")
            return {"action": action, "text": " ".join(tokens[1:])}
        if action == "截图":
            if len(tokens) == 1:
                return {"action": action}
            if len(tokens) == 2:
                return {"action": action, "file_name": tokens[1]}
            raise ValueError(f"第 {line_number} 行：截图 最多支持 1 个参数")

        raise ValueError(f"第 {line_number} 行无法识别动作：{action}")

    @staticmethod
    def _ensure_min_args(tokens: list[str], minimum: int, line_number: int, message: str) -> None:
        if len(tokens) < minimum:
            raise ValueError(f"第 {line_number} 行：{message}")

    @staticmethod
    def _ensure_exact_args(tokens: list[str], expected: int, line_number: int, message: str) -> None:
        if len(tokens) != expected:
            raise ValueError(f"第 {line_number} 行：{message}")