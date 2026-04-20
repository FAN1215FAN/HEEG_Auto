from __future__ import annotations

import html
from datetime import datetime
from pathlib import Path
from typing import Any

from heeg_auto.config.settings import REPORT_DIR, ensure_artifact_dirs

REPORT_TITLE = "HEEG 自动化测试执行报告"
STATUS_LABELS = {
    "PASS": "成功",
    "FAIL": "失败",
    "INTERRUPTED": "异常中断",
    "NOT_RUN": "未执行",
}
STATUS_COLORS = {
    "PASS": ("#1f8f4e", "#edf8f1", "#b7e4c5"),
    "FAIL": ("#d4380d", "#fff2f0", "#ffccc7"),
    "INTERRUPTED": ("#c27c00", "#fff7e6", "#ffe0a3"),
    "NOT_RUN": ("#8c8c8c", "#f5f5f5", "#d9d9d9"),
}


def build_report_base_name(report_timestamp: str) -> str:
    return f"HEEG_Auto_Report_{report_timestamp}"


def generate_reports(result: dict[str, Any]) -> dict[str, str]:
    return generate_suite_reports([result])


def generate_suite_reports(results: list[dict[str, Any]]) -> dict[str, str]:
    ensure_artifact_dirs()
    report_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    html_path = REPORT_DIR / f"{build_report_base_name(report_timestamp)}.html"
    payload = _build_suite_payload(results=results, html_path=html_path, report_timestamp=report_timestamp)
    html_path.write_text(_render_suite_html(payload), encoding="utf-8")
    return {"html": str(html_path), "html_path": str(html_path)}


def _build_suite_payload(results: list[dict[str, Any]], html_path: Path, report_timestamp: str) -> dict[str, Any]:
    cases = [_build_case_payload(item) for item in results]
    return {
        "report_title": REPORT_TITLE,
        "report_timestamp": report_timestamp,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "report_files": {"html": str(html_path)},
        "summary": {
            "case_count": len(cases),
            "passed_cases": sum(1 for item in cases if item.get("status") == "PASS"),
            "failed_cases": sum(1 for item in cases if item.get("status") == "FAIL"),
            "interrupted_cases": sum(1 for item in cases if item.get("status") == "INTERRUPTED"),
            "not_run_cases": sum(1 for item in cases if item.get("status") == "NOT_RUN"),
            "total_duration_seconds": round(sum(float(item.get("duration_seconds", 0) or 0) for item in cases), 3),
        },
        "cases": cases,
    }


def _build_case_payload(result: dict[str, Any]) -> dict[str, Any]:
    execution_results = result.get("execution_results") or []
    summary = result.get("summary") or _build_execution_summary(execution_results)
    first_abnormal = _find_first_abnormal(execution_results)
    return {
        "case_id": result.get("case_id", ""),
        "case_name": result.get("case_name", ""),
        "relative_dir": result.get("relative_dir", ""),
        "status": result.get("status", "FAIL"),
        "status_label": _status_label(result.get("status", "FAIL")),
        "duration_seconds": result.get("duration_seconds", 0),
        "started_at": result.get("started_at", ""),
        "finished_at": result.get("finished_at", ""),
        "module_chain_labels": result.get("module_chain_labels", []),
        "variant": result.get("variant"),
        "loop_count": result.get("loop_count", 1),
        "stop_on_failure": result.get("stop_on_failure", True),
        "summary": summary,
        "error_summary": result.get("error_summary", ""),
        "execution_results": execution_results,
        "first_abnormal": first_abnormal or {},
        "artifact_paths": _collect_case_artifact_paths(result),
    }


def _collect_case_artifact_paths(result: dict[str, Any]) -> list[str]:
    paths: list[str] = []
    seen: set[str] = set()
    for path in result.get("artifact_paths", []):
        text = str(path)
        if text not in seen:
            paths.append(text)
            seen.add(text)
    for execution in result.get("execution_results", []):
        for path in execution.get("artifact_paths", []):
            text = str(path)
            if text not in seen:
                paths.append(text)
                seen.add(text)
    return paths


def _build_execution_summary(execution_results: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "planned_runs": len(execution_results),
        "executed_runs": sum(1 for item in execution_results if item.get("status") in {"PASS", "FAIL", "INTERRUPTED"}),
        "passed_runs": sum(1 for item in execution_results if item.get("status") == "PASS"),
        "failed_runs": sum(1 for item in execution_results if item.get("status") == "FAIL"),
        "interrupted_runs": sum(1 for item in execution_results if item.get("status") == "INTERRUPTED"),
        "not_run_runs": sum(1 for item in execution_results if item.get("status") == "NOT_RUN"),
    }


def _find_first_abnormal(execution_results: list[dict[str, Any]]) -> dict[str, Any] | None:
    return next((item for item in execution_results if item.get("status") in {"FAIL", "INTERRUPTED"}), None)


def _status_label(status: str) -> str:
    return STATUS_LABELS.get(status, status or "-")


def _status_badge(status: str, large: bool = False) -> str:
    status_key = status if status in STATUS_COLORS else "NOT_RUN"
    color, background, border = STATUS_COLORS[status_key]
    size = " large" if large else ""
    return (
        f"<span class=\"status-badge{size}\" style=\"color:{color};background:{background};border-color:{border};\">"
        f"{html.escape(_status_label(status))}</span>"
    )


def _format_execution_param_text(execution: dict[str, Any]) -> str:
    parts = []
    variant = execution.get("variant") or {}
    if variant:
        variant_params = variant.get("params", [])
        if variant_params:
            parts.extend(f"{item.get('param_label', '-')}={item.get('value', '-')}" for item in variant_params)
        elif variant.get("param_label"):
            parts.append(f"{variant.get('param_label', '-')}={variant.get('value', '-')}" )
    if execution.get("loop_total", 1) > 1:
        parts.append(f"?{execution.get('loop_index', 1)}/{execution.get('loop_total', 1)}?")
    return " | ".join(parts) if parts else "-"


def _format_variant_target(variant: dict[str, Any] | None) -> str:
    if not variant:
        return "-"
    params = variant.get("params", [])
    if params:
        joined = "?".join(item.get("param_label", "-") for item in params)
        return f"{variant.get('module_label', '-')} -> {joined}"
    return f"{variant.get('module_label', '-')} -> {variant.get('param_label', '-')}"


def _format_failure_location(failure: dict[str, Any]) -> str:
    if not failure:
        return "-"
    return f"{failure.get('module_id') or '-'} / {failure.get('failed_step') or '-'}"


def _visible_step_results(module_result: dict[str, Any]) -> list[dict[str, Any]]:
    return [step for step in module_result.get("step_results", []) if step.get("status") != "PASS"]


def _visible_execution_steps(execution: dict[str, Any]) -> list[dict[str, Any]]:
    return [step for step in execution.get("step_results", []) if step.get("status") != "PASS"]


def _collect_snapshot_cards(execution_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for execution in execution_results:
        snapshots = execution.get("parameter_snapshot", []) or []
        if not snapshots:
            continue
        cards.append(
            {
                "execution_name": execution.get("execution_name", "-"),
                "status": execution.get("status", "-"),
                "params": snapshots,
            }
        )
    return cards


def _render_suite_html(payload: dict[str, Any]) -> str:
    summary = payload.get("summary", {})
    case_rows = "\n".join(_render_suite_case_row(item) for item in payload.get("cases", []))
    case_details = "\n".join(_render_suite_case_detail(item) for item in payload.get("cases", []))
    return f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>{html.escape(payload['report_title'])}</title>
  <style>{_base_report_css()}</style>
</head>
<body>
  <div class="page">
    <header class="hero">
      <div>
        <div class="eyebrow">HEEG AUTO</div>
        <h1>{html.escape(payload['report_title'])}</h1>
        <p class="meta">生成时间：{html.escape(payload.get('generated_at', '-'))}</p>
      </div>
      <div class="status-panel">
        <div class="duration">共 {summary.get('case_count', 0)} 条 case，累计耗时 {summary.get('total_duration_seconds', 0)} 秒</div>
      </div>
    </header>
    <section class="card-grid">
      {_metric_card('成功', summary.get('passed_cases', 0), 'PASS')}
      {_metric_card('失败', summary.get('failed_cases', 0), 'FAIL')}
      {_metric_card('异常中断', summary.get('interrupted_cases', 0), 'INTERRUPTED')}
      {_metric_card('未执行', summary.get('not_run_cases', 0), 'NOT_RUN')}
    </section>
    <section class="panel">
      <h2>套件概览</h2>
      <table>
        <thead><tr><th>用例编号</th><th>用例名称</th><th>目录</th><th>执行结果</th><th>耗时</th><th>执行计划</th><th>失败原因或断言信息</th></tr></thead>
        <tbody>{case_rows}</tbody>
      </table>
    </section>
    <section class="panel">
      <h2>逐用例明细</h2>
      {case_details}
    </section>
  </div>
</body>
</html>
"""


def _render_suite_case_row(item: dict[str, Any]) -> str:
    summary = item.get("summary", {})
    plan_text = (
        f"planned={summary.get('planned_runs', 0)} / executed={summary.get('executed_runs', 0)} / "
        f"pass={summary.get('passed_runs', 0)} / fail={summary.get('failed_runs', 0)} / "
        f"interrupted={summary.get('interrupted_runs', 0)} / not_run={summary.get('not_run_runs', 0)}"
    )
    reason = item.get("error_summary") or item.get("first_abnormal", {}).get("error_summary") or "-"
    return f"""
      <tr>
        <td>{html.escape(item.get('case_id', '-') or '-')}</td>
        <td>{html.escape(item.get('case_name', '-') or '-')}</td>
        <td>{html.escape(item.get('relative_dir', '-') or '-')}</td>
        <td>{_status_badge(item.get('status', '-'))}</td>
        <td>{item.get('duration_seconds', 0)} 秒</td>
        <td>{html.escape(plan_text)}</td>
        <td>{html.escape(reason)}</td>
      </tr>
    """


def _render_suite_case_detail(item: dict[str, Any]) -> str:
    modules = " -> ".join(item.get("module_chain_labels", [])) or "-"
    snapshots = _collect_snapshot_cards(item.get("execution_results", []))
    snapshot_html = "".join(_render_snapshot_card(card) for card in snapshots) or "<div class=\"empty\">当前用例无模块参数快照。</div>"
    abnormal_blocks = [execution for execution in item.get("execution_results", []) if execution.get("status") != "PASS"]
    abnormal_html = "".join(_render_execution_block(execution) for execution in abnormal_blocks) or "<div class=\"empty\">当前用例无失败、异常中断或未执行轮次。</div>"
    screenshot_html = "".join(
        f"<li><a href=\"{html.escape(path)}\">{html.escape(Path(path).name)}</a></li>" for path in item.get("artifact_paths", [])
    ) or "<li>无</li>"
    return f"""
    <details class="execution" open>
      <summary>
        <div class="summary-main">
          <span class="summary-title">{html.escape(item.get('case_id', '-') or '-')} | {html.escape(item.get('case_name', '-') or '-')}</span>
          <span class="summary-meta">{_status_badge(item.get('status', '-'))} <span class="soft">{item.get('duration_seconds', 0)} 秒</span></span>
        </div>
      </summary>
      <div class="execution-body">
        <section class="subsection">
          <h3>执行概览</h3>
          <div class="info-grid compact">
            <div><span class="label">目录</span><span>{html.escape(item.get('relative_dir', '-') or '-')}</span></div>
            <div><span class="label">执行标签</span><span>{html.escape(modules)}</span></div>
            <div><span class="label">开始时间</span><span>{html.escape(item.get('started_at', '-') or '-')}</span></div>
            <div><span class="label">结束时间</span><span>{html.escape(item.get('finished_at', '-') or '-')}</span></div>
            <div><span class="label">总耗时</span><span>{item.get('duration_seconds', 0)} 秒</span></div>
            <div><span class="label">变参目标</span><span>{html.escape(_format_variant_target(item.get('variant')))}</span></div>
            <div><span class="label">循环次数</span><span>{item.get('loop_count', 1)}</span></div>
            <div><span class="label">失败即停</span><span>{'是' if item.get('stop_on_failure', True) else '否'}</span></div>
            <div class="full"><span class="label">失败原因或断言信息</span><span>{html.escape(item.get('error_summary', '') or '-')}</span></div>
          </div>
        </section>
        <section class="subsection">
          <h3>模块参数快照</h3>
          <div class="snapshot-grid">{snapshot_html}</div>
        </section>
        <section class="subsection">
          <h3>异常/未执行轮次</h3>
          {abnormal_html}
        </section>
        <section class="subsection">
          <h3>截图产物链接</h3>
          <ul class="artifact-list">{screenshot_html}</ul>
        </section>
      </div>
    </details>
    """


def _render_snapshot_card(card: dict[str, Any]) -> str:
    groups = []
    for module in card.get("params", []):
        params = module.get("params", [])
        params_html = "".join(
            f"<li><span class=\"chip-key\">{html.escape(param.get('label', '-'))}</span><span class=\"chip-value\">{html.escape(str(param.get('value', '-')))}</span></li>"
            for param in params
        ) or "<li>无参数</li>"
        groups.append(
            f"<div class=\"module-snapshot\"><div class=\"module-head\"><strong>{html.escape(module.get('module_label', '-'))}</strong><span class=\"soft\">断言组：{html.escape(module.get('assertion_group', '') or '-')}</span></div><ul class=\"param-chips\">{params_html}</ul></div>"
        )
    return f"""
    <div class="snapshot-card">
      <div class="module-head"><strong>{html.escape(card.get('execution_name', '-'))}</strong><span>{_status_badge(card.get('status', '-'))}</span></div>
      {''.join(groups)}
    </div>
    """


def _render_execution_block(execution: dict[str, Any]) -> str:
    module_results = execution.get("module_results", [])
    if module_results:
        detail_sections = "".join(_render_module_result_block(item) for item in module_results)
        detail_title = "模块与断言结果"
    else:
        detail_sections = _render_step_result_block(execution)
        detail_title = "步骤与断言结果"
    artifact_html = "".join(
        f'<li><a href="{html.escape(path)}">{html.escape(Path(path).name)}</a></li>' for path in execution.get("artifact_paths", [])
    ) or "<li>无</li>"
    return f"""
    <div class="execution-card">
      <div class="summary-main">
        <span class="summary-title">{html.escape(execution.get('execution_name', '-') or '-')}</span>
        <span class="summary-meta">{_status_badge(execution.get('status', '-'))} <span class="soft">{execution.get('duration_seconds', 0)} ?</span></span>
      </div>
      <div class="info-grid compact execution-info">
        <div><span class="label">????</span><span>{html.escape(_format_execution_param_text(execution))}</span></div>
        <div><span class="label">????</span><span>{html.escape(execution.get('started_at', '-') or '-')}</span></div>
        <div><span class="label">????</span><span>{html.escape(execution.get('finished_at', '-') or '-')}</span></div>
        <div><span class="label">????/??</span><span>{html.escape(_format_failure_location(execution.get('failure', {})))}</span></div>
        <div class="full"><span class="label">?????????</span><span>{html.escape(execution.get('error_summary', '') or '-')}</span></div>
      </div>
      <div class="subsection"><h4>{detail_title}</h4>{detail_sections}</div>
      <div class="subsection"><h4>??????</h4><ul class="artifact-list">{artifact_html}</ul></div>
    </div>
    """


def _render_step_result_block(execution: dict[str, Any]) -> str:
    visible_steps = _visible_execution_steps(execution)
    if not visible_steps:
        return '<div class="empty">????????????</div>'
    step_rows = "".join(
        f"<tr><td>{html.escape(step.get('step_name', '-') or '-')}</td><td>{_status_badge(step.get('status', '-'))}</td><td>{html.escape(step.get('error_summary', '') or '-')}</td></tr>"
        for step in visible_steps
    )
    return f"<table><thead><tr><th>??</th><th>??</th><th>??</th></tr></thead><tbody>{step_rows}</tbody></table>"


def _render_module_result_block(item: dict[str, Any]) -> str:
    visible_steps = _visible_step_results(item)
    step_table = "<div class=\"empty\">当前模块无失败步骤明细。</div>"
    if visible_steps:
        step_rows = "".join(
            f"<tr><td>{html.escape(step.get('stage', '-') or '-')}</td><td>{html.escape(step.get('step_name', '-') or '-')}</td><td>{_status_badge(step.get('status', '-'))}</td><td>{html.escape(step.get('error_summary', '') or '-')}</td></tr>"
            for step in visible_steps
        )
        step_table = f"<table><thead><tr><th>阶段</th><th>步骤</th><th>结果</th><th>说明</th></tr></thead><tbody>{step_rows}</tbody></table>"
    return f"""
    <div class="module-block">
      <div class="module-head"><strong>{html.escape(item.get('module_label', '-') or '-')}</strong><span>{_status_badge(item.get('status', '-'))}</span></div>
      <div class="info-grid compact module-meta">
        <div><span class="label">断言组</span><span>{html.escape(item.get('assertion_group', '') or '-')}</span></div>
        <div><span class="label">失败步骤</span><span>{html.escape(item.get('failed_step', '') or '-')}</span></div>
      </div>
      {step_table}
    </div>
    """


def _metric_card(title: str, value: Any, status: str | None = None) -> str:
    style = ""
    if status:
        color, background, border = STATUS_COLORS[status]
        style = f" style=\"border-color:{border};background:{background};\""
    return f"<section class=\"metric\"{style}><div class=\"metric-title\">{html.escape(str(title))}</div><div class=\"metric-value\">{html.escape(str(value))}</div></section>"


def _base_report_css() -> str:
    return """
      :root { --bg:#f3f6fb; --panel:#ffffff; --text:#1f2937; --muted:#667085; --line:#dfe5ef; }
      * { box-sizing:border-box; }
      body { margin:0; font-family:"Microsoft YaHei","Segoe UI",sans-serif; background:radial-gradient(circle at top left,#e8f1ff,var(--bg) 42%); color:var(--text); }
      .page { max-width:1520px; margin:0 auto; padding:28px; }
      .hero,.panel,.metric,.execution,.execution-card,.snapshot-card,.module-snapshot { border:1px solid var(--line); border-radius:18px; background:var(--panel); box-shadow:0 12px 36px rgba(37,53,78,.08); }
      .hero { display:flex; justify-content:space-between; gap:24px; padding:28px 38px; margin-bottom:24px; align-items:flex-start; }
      .eyebrow { font-size:12px; letter-spacing:.12em; text-transform:uppercase; color:#6a84ad; margin-bottom:10px; }
      h1,h2,h3,h4 { margin:0; } h1 { font-size:54px; line-height:1.08; margin-bottom:28px; } h2 { font-size:24px; margin-bottom:18px; } h3 { font-size:20px; margin-bottom:14px; } h4 { font-size:16px; margin-bottom:12px; }
      .meta,.soft,.label,.metric-title { color:var(--muted); }
      .status-panel { text-align:right; min-width:280px; font-size:20px; color:#54657e; } .duration { margin-top:12px; }
      .card-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:18px; margin-bottom:24px; }
      .metric { padding:22px; } .metric-value { font-size:42px; font-weight:700; margin-top:16px; }
      .panel { padding:28px 30px; margin-bottom:24px; }
      .info-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:14px 18px; }
      .info-grid.compact { grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); } .info-grid .full { grid-column:1/-1; }
      .info-grid > div,.abnormal-grid > div { display:flex; flex-direction:column; gap:6px; padding:14px 16px; border:1px solid var(--line); border-radius:14px; background:#fbfcfe; }
      .summary-main { display:flex; justify-content:space-between; gap:16px; align-items:center; }
      .summary-title { font-weight:700; font-size:18px; } .summary-meta { display:flex; gap:12px; align-items:center; }
      details.execution { overflow:hidden; margin-top:18px; } details.execution > summary { list-style:none; cursor:pointer; padding:18px 22px; } details.execution > summary::-webkit-details-marker { display:none; }
      details.execution[open] > summary { border-bottom:1px solid var(--line); background:#f8fbff; }
      .execution-body { padding:22px; }
      .subsection { margin-top:20px; }
      .snapshot-grid { display:grid; gap:16px; }
      .snapshot-card,.execution-card,.module-snapshot,.module-block { padding:16px; margin-top:12px; background:#fcfdff; }
      .module-head { display:flex; justify-content:space-between; gap:12px; align-items:center; margin-bottom:12px; }
      .param-chips { list-style:none; margin:0; padding:0; display:flex; flex-wrap:wrap; gap:10px; }
      .param-chips li { display:inline-flex; align-items:center; gap:8px; padding:8px 10px; border-radius:999px; background:#eef4ff; border:1px solid #cfdbf5; }
      .chip-key { color:#4b5f88; } .chip-value { font-weight:700; }
      .artifact-list { margin:0; padding-left:18px; } a { color:#1456d9; text-decoration:none; } a:hover { text-decoration:underline; }
      table { width:100%; border-collapse:collapse; font-size:15px; } th,td { text-align:left; border-bottom:1px solid var(--line); padding:14px 12px; vertical-align:top; } th { background:#f7faff; color:#42526d; font-weight:700; }
      .empty { padding:18px; border:1px dashed var(--line); border-radius:14px; color:var(--muted); background:#fafcff; }
      .status-badge { display:inline-flex; align-items:center; justify-content:center; min-width:92px; padding:7px 14px; border-radius:999px; font-size:14px; font-weight:700; border:1px solid transparent; }
      .status-badge.large { padding:10px 18px; font-size:16px; }
      @media (max-width:900px) { .hero,.summary-main { flex-direction:column; align-items:flex-start; } .status-panel { text-align:left; min-width:auto; } h1 { font-size:40px; } }
    """
