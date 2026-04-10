from __future__ import annotations

import os
import textwrap
from datetime import datetime

import _pytest.helpconfig as pytest_helpconfig
import pytest
from _pytest.config import ExitCode

from heeg_auto.config.settings import ensure_artifact_dirs
from heeg_auto.core.driver import UIADriver
from heeg_auto.core.logger import build_logger
from tests.support.case_catalog import CASE_DIR_FILTER_ENV, CASE_FILE_FILTER_ENV, CASE_FILTER_ENV

GROUP_TITLE_MAP = {
    "general": "通用参数",
    "terminal reporting": "报告输出",
    "pytest-warnings": "pytest 警告",
    "collect": "收集控制",
    "debugconfig": "调试与配置",
    "logging": "日志参数",
    "pytest-metadata": "pytest 元数据",
}

ARGPARSE_GROUP_TITLE_MAP = {
    "positional arguments": "位置参数",
    "options": "可选参数",
    "general": "通用参数",
    "Reporting": "报告输出",
    "pytest-warnings": "pytest 警告",
    "collection": "收集控制",
    "test session debugging and configuration": "调试与配置",
    "logging": "日志参数",
    "pytest-metadata": "pytest 元数据",
}

OPTION_HELP_MAP = {
    "-k": "仅运行名称或关键字匹配表达式的测试项。",
    "-m": "仅运行匹配指定标签表达式的测试项。",
    "--markers": "显示所有可用标记，包括内置、插件和项目标记。",
    "--exitfirst": "在首个错误或失败后立即停止。",
    "--maxfail": "达到指定失败或错误次数后停止。",
    "--strict-config": "启用严格配置校验。",
    "--strict-markers": "启用严格标记校验。",
    "--strict": "启用全部严格模式选项。",
    "--fixtures": "显示可用夹具；使用 -v 可显示以下划线开头的夹具。",
    "--fixtures-per-test": "显示每个测试项实际会使用到的夹具。",
    "--pdb": "发生错误或中断时进入 Python 调试器。",
    "--pdbcls": "指定自定义 Python 调试器类。",
    "--trace": "执行每个测试项前立即进入调试。",
    "--capture": "设置输出捕获方式：fd、sys、no 或 tee-sys。",
    "-s": "不捕获标准输出，直接显示 print 和日志。",
    "--runxfail": "将 xfail 测试按普通测试结果处理。",
    "--last-failed": "仅重跑上次失败的测试；若没有失败则按配置处理。",
    "--failed-first": "先运行上次失败的测试，再运行其余测试。",
    "--new-first": "优先运行新文件中的测试。",
    "--cache-show": "显示 pytest 缓存内容，不执行测试。",
    "--cache-clear": "运行开始前清空 pytest 缓存。",
    "--last-failed-no-failures": "控制在没有历史失败记录时的行为。",
    "--stepwise": "遇到失败即停止，下次从失败处继续。",
    "--stepwise-skip": "忽略首个失败项，在下一个失败处停止。",
    "--stepwise-reset": "重置 stepwise 状态并重新开始。",
    "--durations": "显示最慢的 N 个 setup 或 test 耗时；N=0 表示全部。",
    "--durations-min": "仅显示耗时不低于该秒数的慢测试。",
    "--verbose": "提高输出详细程度。",
    "--no-header": "不显示 pytest 头部信息。",
    "--no-summary": "不显示测试总结。",
    "--no-fold-skipped": "短摘要中不折叠跳过项。",
    "--force-short-summary": "强制使用精简摘要输出。",
    "--quiet": "降低输出详细程度。",
    "--verbosity": "显式设置输出详细级别。",
    "-r": "设置额外测试摘要显示内容。",
    "--disable-warnings": "不显示警告摘要。",
    "--showlocals": "失败时显示本地变量。",
    "--no-showlocals": "失败时不显示本地变量。",
    "--tb": "设置 traceback 显示风格。",
    "--xfail-tb": "显示 xfail 用例的 traceback。",
    "--show-capture": "控制失败时展示 stdout、stderr、log 的方式。",
    "--full-trace": "显示完整 traceback，不做裁剪。",
    "--color": "设置终端颜色输出：yes、no 或 auto。",
    "--code-highlight": "设置是否高亮代码输出。",
    "--pastebin": "将失败信息发送到 pastebin。",
    "--junit-xml": "将结果输出为 junit-xml 文件。",
    "--junit-prefix": "为 junit-xml 中的类名前添加前缀。",
    "--html": "生成 HTML 报告文件。",
    "--self-contained-html": "生成包含全部样式与资源的单文件 HTML 报告。",
    "--css": "向 HTML 报告附加额外 CSS。",
    "--pythonwarnings": "设置 Python warnings 过滤规则。",
    "--collect-only": "仅收集测试项，不真正执行。",
    "--pyargs": "将输入路径按 Python 包名解释。",
    "--ignore": "忽略指定路径，可重复传入。",
    "--ignore-glob": "按通配模式忽略路径，可重复传入。",
    "--deselect": "按节点前缀取消收集测试项，可重复传入。",
    "--confcutdir": "只加载指定目录之下的 conftest.py。",
    "--noconftest": "不加载任何 conftest.py 文件。",
    "--keep-duplicates": "收集时保留重复测试项。",
    "--collect-in-virtualenv": "收集本地虚拟环境目录中的测试。",
    "--continue-on-collection-errors": "即使收集阶段有错误也继续执行。",
    "--import-mode": "设置测试模块导入模式。",
    "--doctest-modules": "对所有 Python 模块执行 doctest。",
    "--doctest-report": "设置 doctest 失败差异显示格式。",
    "--doctest-glob": "指定 doctest 文件匹配模式。",
    "--doctest-ignore-import-errors": "忽略 doctest 导入错误。",
    "--doctest-continue-on-failure": "doctest 失败后继续执行后续项。",
    "--config-file": "使用指定配置文件，而不是自动查找默认配置。",
    "--rootdir": "指定测试根目录。",
    "--basetemp": "指定本次运行的临时目录基路径。",
    "--version": "显示 pytest 版本和插件信息。",
    "--help": "显示帮助信息和配置说明。",
    "-p": "预加载指定插件；使用 no: 前缀可禁用插件。",
    "--disable-plugin-autoload": "禁用通过入口点自动加载插件。",
    "--trace-config": "跟踪 conftest 与配置加载过程。",
    "--debug": "将 pytest 内部调试信息写入日志文件。",
    "--override-ini": "用 option=value 形式覆盖 ini 配置项。",
    "--assert": "设置断言重写模式。",
    "--setup-only": "只执行夹具 setup，不运行测试体。",
    "--setup-show": "显示夹具 setup 过程。",
    "--setup-plan": "显示将要执行的夹具和测试计划，但不真正执行。",
    "--log-level": "设置日志捕获或显示级别。",
    "--log-format": "设置日志输出格式。",
    "--log-date-format": "设置日志时间格式。",
    "--log-cli-level": "设置命令行实时日志级别。",
    "--log-cli-format": "设置命令行实时日志格式。",
    "--log-cli-date-format": "设置命令行实时日志时间格式。",
    "--log-file": "指定日志文件输出路径。",
    "--log-file-mode": "设置日志文件打开模式。",
    "--log-file-level": "设置日志文件记录级别。",
    "--log-file-format": "设置日志文件输出格式。",
    "--log-file-date-format": "设置日志文件时间格式。",
    "--log-auto-indent": "设置多行日志的自动缩进方式。",
    "--log-disable": "按名称禁用某个日志记录器，可重复传入。",
    "--metadata": "向报告附加键值元数据。",
    "--metadata-from-json": "从 JSON 字符串附加元数据。",
    "--metadata-from-json-file": "从 JSON 文件附加元数据。",
}

INI_HELP_MAP = {
    "markers": "注册项目可用的 pytest 标记。",
    "empty_parameter_set_mark": "为空参数集指定默认标记。",
    "strict_config": "解析 pytest 配置时遇到警告即报错。",
    "strict_markers": "未在 markers 中注册的标记将触发错误。",
    "strict": "启用全部严格模式选项。",
    "filterwarnings": "逐行配置 warnings.filterwarnings 规则。",
    "norecursedirs": "递归收集时需要忽略的目录模式。",
    "testpaths": "未显式传路径时默认搜索测试的目录。",
    "collect_imported_tests": "是否收集 testpaths 外被导入模块中的测试。",
    "consider_namespace_packages": "导入测试模块时是否考虑命名空间包。",
    "usefixtures": "默认启用的夹具列表。",
    "python_files": "测试文件匹配模式。",
    "python_classes": "测试类匹配模式。",
    "python_functions": "测试函数匹配模式。",
    "disable_test_id_escaping_and_forfeit_all_rights_to_community_support": "关闭非 ASCII 测试 ID 转义。",
    "strict_parametrization_ids": "参数化 ID 重复时直接报错。",
    "console_output_style": "控制终端输出风格。",
    "verbosity_test_cases": "单独设置测试项执行输出详细级别。",
    "strict_xfail": "未显式声明时 xfail 默认是否严格。",
    "tmp_path_retention_count": "保留的 tmp_path 会话目录数量。",
    "tmp_path_retention_policy": "按结果控制保留哪些 tmp_path 目录。",
    "enable_assertion_pass_hook": "启用 pytest_assertion_pass 钩子。",
    "truncation_limit_lines": "超过该行数后启用截断。",
    "truncation_limit_chars": "超过该字符数后启用截断。",
    "verbosity_assertions": "单独设置断言输出详细级别。",
    "junit_suite_name": "JUnit 报告中的测试套件名称。",
    "junit_logging": "控制日志写入 JUnit 报告的方式。",
    "junit_log_passing_tests": "是否为通过用例写入日志到 JUnit 报告。",
    "junit_duration_report": "JUnit 报告中记录耗时的粒度。",
    "junit_family": "设置 JUnit XML 的 schema 版本。",
    "doctest_optionflags": "doctest 使用的选项标志。",
    "doctest_encoding": "doctest 文件编码。",
    "cache_dir": "pytest 缓存目录路径。",
    "log_level": "--log-level 的默认值。",
    "log_format": "--log-format 的默认值。",
    "log_date_format": "--log-date-format 的默认值。",
    "log_cli": "是否启用命令行实时日志。",
    "log_cli_level": "--log-cli-level 的默认值。",
    "log_cli_format": "--log-cli-format 的默认值。",
    "log_cli_date_format": "--log-cli-date-format 的默认值。",
    "log_file": "--log-file 的默认值。",
    "log_file_mode": "--log-file-mode 的默认值。",
    "log_file_level": "--log-file-level 的默认值。",
    "log_file_format": "--log-file-format 的默认值。",
    "log_file_date_format": "--log-file-date-format 的默认值。",
    "log_auto_indent": "--log-auto-indent 的默认值。",
    "faulthandler_timeout": "测试超时后输出所有线程 traceback 的秒数。",
    "faulthandler_exit_on_timeout": "超时时是否直接退出测试进程。",
    "verbosity_subtests": "设置子测试输出详细级别。",
    "addopts": "附加默认命令行参数。",
    "minversion": "要求的最小 pytest 版本。",
    "pythonpath": "附加到 sys.path 的路径。",
    "required_plugins": "运行 pytest 所需的插件列表。",
    "anyio_mode": "AnyIO 插件运行模式。",
    "render_collapsed": "HTML 报告默认折叠的行。",
    "max_asset_filename_length": "HTML 报告附件文件名最大长度。",
    "environment_table_redact_list": "HTML 报告中需要脱敏的环境变量规则。",
    "initial_sort": "HTML 报告默认排序列。",
    "generate_report_on_test": "每个测试执行后都生成一次 HTML 报告。",
}

ENV_HELP_MAP = [
    ("CI", "设置为非空时，pytest 会识别当前运行在 CI 环境中，并避免截断摘要信息。"),
    ("BUILD_NUMBER", "与 CI 变量作用等价。"),
    ("PYTEST_ADDOPTS", "追加的命令行参数。"),
    ("PYTEST_PLUGINS", "启动时额外加载的插件，多个用逗号分隔。"),
    ("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "设置后禁用插件自动加载。"),
    ("PYTEST_DEBUG", "设置后输出 pytest 内部调试跟踪信息。"),
    ("PYTEST_DEBUG_TEMPROOT", "覆盖系统临时目录路径。"),
    ("PYTEST_THEME", "设置代码高亮所使用的 Pygments 主题。"),
    ("PYTEST_THEME_MODE", "设置主题模式为 dark 或 light。"),
]

MINIMAL_HELP_LINES = [
    "HEEG Auto pytest 最小帮助",
    "",
    "项目参数：",
    "  -h, --help                 显示当前最小帮助页",
    "  -s                         显示执行过程输出",
    "  --run-formal               仅运行正式 YAML case 主线",
    "  --run-ui                   运行真实桌面 UI 自动化用例",
    "  --case-dir 目录1,目录2      按业务目录筛选正式 case",
    "  --case-file 文件路径        按单个正式 case YAML 文件执行",
    "  --case-id 编号1,编号2       按 case 编号筛选正式 case",
    "  --stall-timeout 秒数        UI 无进展超时秒数，默认 60",
    "  --helpfull                 显示 pytest 原生完整帮助",
    "",
    "常用命令：",
    "  python -m pytest -h",
    "  python -m pytest --case-dir 设备设置 -s",
    "  python -m pytest --case-file src/heeg_auto/cases/系统设置/设备设置/采样率校验.yaml -s",
    "  python -m pytest --case-id 患者管理_01 -s",
    "  python -m pytest --run-formal --run-ui -s",
    "",
    "说明：",
    "  1. 当前项目只主支持上面列出的最小参数集。",
    "  2. pytest 原生日志、报告和其他参数能力仍然保留，但不在日常支持范围内。",
    "  3. 如需查看 pytest 原生完整帮助，请使用：python -m pytest --helpfull",
]


def _build_case_report_summary(result: dict) -> str:
    summary = result.get("summary", {})
    lines = [
        f"用例: {result.get('case_id', '-')} | {result.get('case_name', '-')}",
        f"状态: {result.get('status', '-')}",
        f"执行计划: planned={summary.get('planned_runs', 0)}, executed={summary.get('executed_runs', 0)}, passed={summary.get('passed_runs', 0)}, failed={summary.get('failed_runs', 0)}, interrupted={summary.get('interrupted_runs', 0)}, not_run={summary.get('not_run_runs', 0)}",
    ]
    first_abnormal = next(
        (item for item in result.get("execution_results", []) if item.get("status") in {"FAIL", "INTERRUPTED"}),
        None,
    )
    if first_abnormal:
        lines.append(f"首个异常轮次: {first_abnormal.get('execution_name', '-')}")
        lines.append(f"异常摘要: {first_abnormal.get('error_summary', '-')}")
    return "\n".join(lines)


def _set_or_clear_env(name: str, value: str | None) -> None:
    if value:
        os.environ[name] = value
    else:
        os.environ.pop(name, None)


def _has_explicit_case_filters(config) -> bool:
    return any(
        [
            bool((config.getoption("--case-id") or "").strip()),
            bool((config.getoption("--case-dir") or "").strip()),
            bool((config.getoption("--case-file") or "").strip()),
        ]
    )


def _is_formal_requested(config) -> bool:
    return bool(config.getoption("--run-formal")) or _has_explicit_case_filters(config)


def _is_ui_execution_requested(config) -> bool:
    return bool(config.getoption("--run-ui")) or _is_formal_requested(config)


def _canonical_option_key(option) -> str | None:
    for candidate in option._long_opts:
        if candidate in OPTION_HELP_MAP:
            return candidate
    for candidate in option._short_opts:
        if candidate in OPTION_HELP_MAP:
            return candidate
    if option._long_opts:
        return option._long_opts[0]
    if option._short_opts:
        return option._short_opts[0]
    return None


def _canonical_action_key(action) -> str | None:
    for candidate in getattr(action, "option_strings", []):
        if candidate in OPTION_HELP_MAP:
            return candidate
    option_strings = getattr(action, "option_strings", [])
    if option_strings:
        return option_strings[0]
    return None


def _localize_pytest_parser(parser) -> None:
    for group in parser._groups:
        translated_title = GROUP_TITLE_MAP.get(group.name)
        if translated_title:
            group.name = translated_title
            if getattr(group, "_arggroup", None) is not None:
                group._arggroup.title = translated_title
        for option in group.options:
            key = _canonical_option_key(option)
            translated_help = OPTION_HELP_MAP.get(key)
            if translated_help:
                option._attrs["help"] = translated_help
    for key, payload in list(parser._inidict.items()):
        translated_desc = INI_HELP_MAP.get(key)
        if translated_desc:
            parser._inidict[key] = (translated_desc, payload[1], payload[2])


def _localize_argparse_help(optparser) -> str:
    for group in getattr(optparser, "_action_groups", []):
        translated_title = ARGPARSE_GROUP_TITLE_MAP.get(group.title)
        if translated_title:
            group.title = translated_title
        for action in getattr(group, "_group_actions", []):
            key = _canonical_action_key(action)
            translated_help = OPTION_HELP_MAP.get(key)
            if translated_help:
                action.help = translated_help
            elif action.dest == "file_or_dir":
                action.help = "测试文件或目录。"

    help_text = optparser.format_help()
    help_text = help_text.replace("usage:", "用法：")
    help_text = help_text.replace("[options]", "[参数]")
    help_text = help_text.replace("positional arguments:", "位置参数:")
    help_text = help_text.replace("optional arguments:", "可选参数:")
    help_text = help_text.replace(
        "位置参数:\n  file_or_dir\n",
        "位置参数:\n  file_or_dir             测试文件或目录。\n",
    )
    return help_text


def _render_minimal_help() -> str:
    return "\n".join(MINIMAL_HELP_LINES) + "\n"


def _showhelp_minimal(config) -> None:
    reporter = config.pluginmanager.get_plugin("terminalreporter")
    assert reporter is not None
    reporter._tw.write(_render_minimal_help())


def _showhelp_full(config) -> None:
    reporter = config.pluginmanager.get_plugin("terminalreporter")
    assert reporter is not None
    tw = reporter._tw
    tw.write(_localize_argparse_help(config._parser.optparser))
    tw.line()
    tw.line("[pytest] 首个 pytest.toml|pytest.ini|tox.ini|setup.cfg|pyproject.toml 中发现的配置项：")
    tw.line()

    columns = tw.fullwidth
    indent_len = 24
    indent = " " * indent_len
    for name in config._parser._inidict:
        help_text, value_type, _default = config._parser._inidict[name]
        if help_text is None:
            raise TypeError(f"help argument cannot be None for {name}")
        spec = f"{name} ({value_type}):"
        tw.write(f"  {spec}")
        spec_len = len(spec)
        if spec_len > (indent_len - 3):
            tw.line()
            helplines = textwrap.wrap(
                help_text,
                columns,
                initial_indent=indent,
                subsequent_indent=indent,
                break_on_hyphens=False,
            )
            for line in helplines:
                tw.line(line)
        else:
            tw.write(" " * (indent_len - spec_len - 2))
            wrapped = textwrap.wrap(help_text, columns - indent_len, break_on_hyphens=False)
            if wrapped:
                tw.line(wrapped[0])
                for line in wrapped[1:]:
                    tw.line(indent + line)

    tw.line()
    tw.line("环境变量：")
    for name, help_text in ENV_HELP_MAP:
        tw.line(f"  {name:<24} {help_text}")
    tw.line()
    tw.line()
    tw.line("查看可用标记：pytest --markers")
    tw.line("查看可用夹具：pytest --fixtures")
    tw.line("夹具显示会根据指定的 file_or_dir 过滤；以下划线开头的夹具仅在使用 -v 时显示。")

    for warningreport in reporter.stats.get("warnings", []):
        tw.line("警告: " + warningreport.message, red=True)


pytest_helpconfig.showhelp = _showhelp_minimal


def pytest_addoption(parser):
    _localize_pytest_parser(parser)

    project_group = parser.getgroup("项目参数", description="正式 case 执行最小参数集")
    project_group.addoption(
        "--helpfull",
        action="store_true",
        default=False,
        help="显示 pytest 原生完整帮助",
    )
    project_group.addoption(
        "--run-ui",
        action="store_true",
        default=False,
        help="运行真实桌面 UI 自动化用例",
    )
    project_group.addoption(
        "--run-formal",
        action="store_true",
        default=False,
        help="仅运行正式 YAML case 主线",
    )
    project_group.addoption(
        "--stall-timeout",
        action="store",
        default="60",
        help="真实 UI 执行无进展超时秒数，默认 60 秒",
    )
    project_group.addoption(
        "--case-id",
        action="store",
        default="",
        help="按 case 编号筛选正式 case，多个用逗号分隔",
    )
    project_group.addoption(
        "--case-dir",
        action="store",
        default="",
        help="按业务目录筛选正式 case，多个用逗号分隔",
    )
    project_group.addoption(
        "--case-file",
        action="store",
        default="",
        help="按单个正式 case YAML 文件筛选执行",
    )


@pytest.hookimpl(tryfirst=True)
def pytest_cmdline_main(config):
    if not getattr(config.option, "helpfull", False):
        return None
    config._do_configure()
    _showhelp_full(config)
    config._ensure_unconfigure()
    return ExitCode.OK


def pytest_configure(config):
    ensure_artifact_dirs()
    config.addinivalue_line("markers", "formal: marks formal YAML case execution entry")
    config.addinivalue_line("markers", "v2: marks v2 step-based case tests")

    formal_requested = _is_formal_requested(config)
    case_id = (config.getoption("--case-id") or "").strip()
    case_dir = (config.getoption("--case-dir") or "").strip()
    case_file = (config.getoption("--case-file") or "").strip()

    if case_file and (case_id or case_dir):
        raise pytest.UsageError("--case-file 不能和 --case-id 或 --case-dir 同时使用")

    _set_or_clear_env(CASE_FILTER_ENV, case_id if formal_requested else None)
    _set_or_clear_env(CASE_DIR_FILTER_ENV, case_dir if formal_requested else None)
    _set_or_clear_env(CASE_FILE_FILTER_ENV, case_file if formal_requested else None)


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(config, items):
    if not _is_formal_requested(config):
        return
    selected = []
    deselected = []
    for item in items:
        if item.get_closest_marker("formal"):
            selected.append(item)
        else:
            deselected.append(item)
    if deselected:
        config.hook.pytest_deselected(items=deselected)
        items[:] = selected


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)
    if report.when != "call":
        return
    case_result = getattr(item, "case_result", None)
    if not case_result:
        return
    report.sections.append(("case-summary", _build_case_report_summary(case_result)))
    report.case_status = case_result.get("status", "-")
    report.case_directory = getattr(item, "case_directory", "-")
    report.failure_summary = case_result.get("error_summary", "")


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

