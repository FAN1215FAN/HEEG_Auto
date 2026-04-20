from __future__ import annotations

import time

from heeg_auto.config.locators import get_locator
from heeg_auto.core.base_page import BasePage
from heeg_auto.core.duration_utils import parse_duration_seconds

_GRID_FRAGMENT_CONTROL_TYPES = {"Custom", "DataItem", "Edit", "ListItem", "Pane", "Text", "TreeItem"}
_ROW_TOP_TOLERANCE = 10


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

    def assert_latest_clipped_record(
        self,
        record_name: str,
        expected_duration: str | None = None,
        min_duration: str | None = None,
        max_duration: str | None = None,
        original_duration: str | None = None,
        timeout: int = 20,
    ) -> None:
        if expected_duration:
            min_duration = min_duration or expected_duration
            max_duration = max_duration or expected_duration
        if not min_duration or not max_duration:
            raise ValueError("assert_latest_clipped_record requires expected_duration or min_duration/max_duration")
        deadline = time.time() + timeout
        while time.time() < deadline:
            rows = self._collect_grid_rows()
            if not rows:
                time.sleep(0.5)
                continue

            if original_duration:
                original_candidates = [
                    row
                    for row in rows
                    if self._row_contains_text(row, record_name) and self._row_contains_text(row, original_duration)
                ]
                if original_candidates:
                    original_row = sorted(original_candidates, key=lambda item: item["top"])[0]
                    child_candidates = [
                        row
                        for row in rows
                        if row["top"] > original_row["top"] and self._row_duration_in_range(row, min_duration, max_duration)
                    ]
                    named_child_candidates = [
                        row for row in child_candidates if self._row_contains_text(row, record_name)
                    ]
                    if named_child_candidates:
                        child_candidates = named_child_candidates
                    if child_candidates:
                        latest_child = sorted(child_candidates, key=lambda item: (item["top"], item["left"]))[0]
                        self.logger.info(
                            "Matched latest clipped child row: name=%s duration_range=%s~%s row_texts=%s",
                            record_name,
                            min_duration,
                            max_duration,
                            latest_child["texts"],
                        )
                        return
            else:
                clip_candidates = [
                    row
                    for row in rows
                    if self._row_contains_text(row, record_name) and self._row_duration_in_range(row, min_duration, max_duration)
                ]
                if clip_candidates:
                    clip_candidates.sort(key=lambda item: (item["top"], item["left"]))
                    self.logger.info(
                        "Matched latest clipped record without original anchor: name=%s duration_range=%s~%s row_texts=%s",
                        record_name,
                        min_duration,
                        max_duration,
                        clip_candidates[0]["texts"],
                    )
                    return

            time.sleep(0.5)

        snapshot = self._collect_grid_rows()[:8]
        summary = [" | ".join(row["texts"][:8]) for row in snapshot]
        raise AssertionError(
            f"主窗口未发现最新剪辑记录：记录名称={record_name}，时长范围={min_duration}~{max_duration}，原始时长={original_duration}，列表快照={summary}"
        )

    def _collect_grid_rows(self) -> list[dict]:
        root = getattr(self.driver, "main_window_wrapper", None)
        if root is None:
            return []
        fragments: list[dict] = []
        seen_fragments: set[tuple[str, int, int]] = set()
        try:
            descendants = root.descendants()
        except Exception:
            descendants = []
        for wrapper in descendants:
            info = getattr(wrapper, "element_info", None)
            control_type = str(getattr(info, "control_type", "") if info is not None else "").strip()
            if control_type not in _GRID_FRAGMENT_CONTROL_TYPES:
                continue
            text = self._visible_text_from_wrapper(wrapper)
            if not text:
                continue
            try:
                rect = wrapper.rectangle()
                top = int(rect.top)
                left = int(rect.left)
            except Exception:
                continue
            key = (text, top, left)
            if key in seen_fragments:
                continue
            seen_fragments.add(key)
            fragments.append({"text": text, "top": top, "left": left})
        fragments.sort(key=lambda item: (item["top"], item["left"]))
        return self._group_grid_fragments_by_row(fragments)

    def _group_grid_fragments_by_row(self, fragments: list[dict]) -> list[dict]:
        if not fragments:
            return []

        grouped_rows: list[list[dict]] = []
        current_row = [fragments[0]]
        current_top = fragments[0]["top"]

        for fragment in fragments[1:]:
            if abs(fragment["top"] - current_top) <= _ROW_TOP_TOLERANCE:
                current_row.append(fragment)
                current_top = round(sum(item["top"] for item in current_row) / len(current_row))
                continue
            grouped_rows.append(current_row)
            current_row = [fragment]
            current_top = fragment["top"]
        grouped_rows.append(current_row)

        rows: list[dict] = []
        for items in grouped_rows:
            ordered = sorted(items, key=lambda item: item["left"])
            texts: list[str] = []
            seen_texts: set[str] = set()
            for item in ordered:
                text = item["text"].strip()
                if not text or text in seen_texts:
                    continue
                seen_texts.add(text)
                texts.append(text)
            if not texts:
                continue
            rows.append({"texts": texts, "top": min(item["top"] for item in items), "left": min(item["left"] for item in items)})
        return rows

    @staticmethod
    def _row_contains_text(row: dict, expected: str | None) -> bool:
        if not expected:
            return False
        target = expected.strip()
        return any(target in text for text in row.get("texts", []))

    @staticmethod
    def _row_duration_in_range(row: dict, min_duration: str, max_duration: str) -> bool:
        min_seconds = parse_duration_seconds(min_duration, field_name="min_duration")
        max_seconds = parse_duration_seconds(max_duration, field_name="max_duration")
        for text in row.get("texts", []):
            try:
                seconds = parse_duration_seconds(text, field_name="row_duration")
            except ValueError:
                continue
            if min_seconds <= seconds <= max_seconds:
                return True
        return False
