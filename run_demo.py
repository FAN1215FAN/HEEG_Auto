from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from heeg_auto.config.settings import DEFAULT_CASE_PATH
from heeg_auto.core.reporting import generate_reports
from heeg_auto.runner.formal_case_runner import FormalCaseRunner


def main() -> int:
    runner = FormalCaseRunner()
    result = runner.run_case(DEFAULT_CASE_PATH, raise_on_failure=False, close_after_run=False)
    report_files = generate_reports(result)

    print(f"Case ID: {result['case_id']}")
    print(f"Case: {result['case_name']}")
    print(f"Modules: {' -> '.join(result.get('module_chain_labels', [])) or '-'}")
    print(f"Status: {result['status']}")
    print(
        "Runs: "
        f"planned={result['summary'].get('planned_runs', 0)}, "
        f"executed={result['summary'].get('executed_runs', 0)}, "
        f"passed={result['summary'].get('passed_runs', 0)}, "
        f"failed={result['summary'].get('failed_runs', 0)}, "
        f"interrupted={result['summary'].get('interrupted_runs', 0)}, "
        f"not_run={result['summary'].get('not_run_runs', 0)}"
    )
    print(f"HTML Report: {report_files['html_path']}")

    if not result["passed"]:
        print(f"Error Summary: {result.get('error_summary', '-')}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
