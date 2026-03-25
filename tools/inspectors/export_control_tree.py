from __future__ import annotations

import argparse
from contextlib import redirect_stdout
from datetime import datetime
from io import StringIO

from heeg_auto.config.settings import INSPECTOR_DIR, ensure_artifact_dirs
from heeg_auto.core.driver import UIADriver
from heeg_auto.core.logger import build_logger
from heeg_auto.pages.main_page import MainPage


def export_control_tree(open_create_patient: bool = False) -> str:
    ensure_artifact_dirs()
    logger = build_logger(name="inspector")
    driver = UIADriver(logger=logger)
    driver.launch()

    target = driver.main_window
    if open_create_patient:
        main_page = MainPage(driver=driver, logger=logger)
        dialog_page = main_page.open_create_patient_dialog()
        target = dialog_page.root

    buffer = StringIO()
    with redirect_stdout(buffer):
        target.print_control_identifiers()

    output_file = INSPECTOR_DIR / f"control_tree_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    output_file.write_text(buffer.getvalue(), encoding="utf-8")
    driver.close()
    return str(output_file)


def main() -> None:
    parser = argparse.ArgumentParser(description="Export WPF control tree for HEEG app.")
    parser.add_argument("--open-create-patient", action="store_true", help="Click the 新增 button before exporting.")
    args = parser.parse_args()
    output_path = export_control_tree(open_create_patient=args.open_create_patient)
    print(output_path)


if __name__ == "__main__":
    main()
