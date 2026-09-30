# packages/core/services/ThemeManager.py
from PyQt6.QtWidgets import QApplication
import darkdetect


class ThemeManager:
    _instance = None
    _current = None

    def __init__(self):
        ThemeManager._instance = self

    @classmethod
    def get(cls):
        return cls._instance

    @classmethod
    def current(cls):
        return cls._current

    @classmethod
    def apply(cls, theme: str):
        change = False
        if theme == "system":
            if darkdetect.theme() != cls._current:
                cls._current = darkdetect.theme()
                change = True
        else:
            if theme != cls._current:
                cls._current = theme
                change = True

        if change:
            qss_path = f"service_files/themes/{cls._current}.qss"

            with open(qss_path, "r", encoding="utf-8") as f:
                QApplication.instance().setStyleSheet(f.read())
