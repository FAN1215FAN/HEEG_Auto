from __future__ import annotations

import time

from heeg_auto.core.base_page import BasePage


class CreatePatientDialogPage(BasePage):
    def __init__(self, driver, logger) -> None:
        super().__init__(driver=driver, logger=logger, root=None)
        self.marker_text: str | None = None

    def wait_open(self, marker_text: str = "创建患者", timeout: int = 15):
        self.marker_text = marker_text
        deadline = time.time() + timeout
        while time.time() < deadline:
            candidate = self._resolve_dialog_root(marker_text)
            if candidate is not None:
                self.root = candidate
                return self.root
            time.sleep(0.5)
        raise TimeoutError(f"弹窗在 {timeout}s 内未出现，marker={marker_text!r}")

    def wait_closed(self, timeout: int = 15):
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.root is None:
                if not self._marker_still_visible():
                    return
                time.sleep(0.5)
                continue

            handle = getattr(self.root, "handle", None)
            if handle:
                try:
                    window = self.driver.desktop.window(handle=handle)
                    if not window.exists(timeout=0.2):
                        self.root = None
                        return
                except Exception:
                    self.root = None
                    return

            if not self._marker_still_visible():
                self.root = None
                return
            time.sleep(0.5)

        raise TimeoutError(
            f"弹窗在 {timeout}s 内未关闭，marker={self.marker_text!r}, "
            f"handle={getattr(self.root, 'handle', None)}"
        )

    def _marker_still_visible(self) -> bool:
        if not self.marker_text:
            return False
        for candidate in self._iter_visible_texts_from_roots():
            if self.marker_text in candidate:
                return True
        return False

    def _candidate_contains_marker(self, candidate, marker_text: str) -> bool:
        for wrapper in [candidate, *self._safe_descendants(candidate)]:
            text = self._visible_text_from_wrapper(wrapper)
            if marker_text and marker_text in text:
                return True
        return False

    @staticmethod
    def _safe_descendants(candidate):
        try:
            return list(candidate.descendants())
        except Exception:
            return []

    @staticmethod
    def _safe_parent(candidate):
        try:
            return candidate.parent()
        except Exception:
            return None

    def _resolve_from_main_descendants(self, marker_text: str, main_handle: int | None):
        root = getattr(self.driver, 'main_window_wrapper', None) or getattr(self.driver, 'main_window', None)
        if root is None:
            return None
        for descendant in self._safe_descendants(root):
            text = self._visible_text_from_wrapper(descendant)
            if not text or marker_text not in text:
                continue
            candidate = descendant
            parent = self._safe_parent(candidate)
            while parent is not None:
                parent_handle = getattr(parent, 'handle', None)
                if not parent_handle or parent_handle == main_handle:
                    break
                candidate = parent
                parent = self._safe_parent(candidate)
            candidate_handle = getattr(candidate, 'handle', None)
            if candidate_handle and candidate_handle != main_handle:
                return candidate
        return None

    def _resolve_dialog_root(self, marker_text: str):
        candidates = []
        main_handle = getattr(self.driver.main_window_wrapper, "handle", None)
        for getter in (self.driver.top_window, lambda: self.driver.desktop.top_window()):
            try:
                candidate = getter()
                if hasattr(candidate, "wrapper_object"):
                    candidate = candidate.wrapper_object()
            except Exception:
                candidate = None
            if candidate is None:
                continue
            handle = getattr(candidate, "handle", None)
            if any(getattr(existing, "handle", None) == handle for existing in candidates):
                continue
            candidates.append(candidate)

        for candidate in candidates:
            candidate_handle = getattr(candidate, "handle", None)
            if not candidate_handle or candidate_handle == main_handle:
                continue
            if self._candidate_contains_marker(candidate, marker_text):
                return candidate

        return self._resolve_from_main_descendants(marker_text, main_handle)
