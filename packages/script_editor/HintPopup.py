import sys
import ast
import operator
import inspect
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QPlainTextEdit, QApplication, QSplitter)
from PyQt6.QtCore import Qt, QObject, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut, QFont


class HintPopup(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.ToolTip)
        self.setStyleSheet("""
            HintPopup { background-color: #2b2b2b; border: 1px solid #555; border-radius: 3px; }
        """)
        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(1, 1, 1, 1)
        self._layout.setSpacing(1)
        self.setLayout(self._layout)
        self._buttons = []
        self._selected_index = -1
        self._suffix = ""

    def show_hints(self, words: list):
        for btn in self._buttons:
            btn.deleteLater()
        self._buttons.clear()
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        if not words:
            self.hide()
            return
        self._selected_index = 0
        for word in words:
            suffix = word.get("suffix")
            word = word.get("name")
            btn = QPushButton(word+suffix)
            btn.clicked.connect(lambda checked, w=word+suffix: self._select(w))
            self._layout.addWidget(btn)
            self._buttons.append(btn)
        self._highlight()
        gp = self.editor.mapToGlobal(self.editor.cursorRect().bottomLeft())
        self.move(gp.x(), gp.y() + 2)
        self.show()
        self.raise_()
        self.adjustSize()

    def _highlight(self):
        for i, btn in enumerate(self._buttons):
            if i == self._selected_index:
                btn.setStyleSheet("QPushButton { background-color: #4d6490; color: white; border: none; padding: 5px 10px; text-align: left; min-width: 150px; min-height: 25px; }")
            else:
                btn.setStyleSheet("QPushButton { background-color: #3c3c3c; color: white; border: none; padding: 5px 10px; text-align: left; min-width: 150px; min-height: 25px; }")

    def _select(self, word_and_suffix: str):
        l = word_and_suffix.split("(")
        if len(l) == 1:
            self.editor.insert_word(l[0], "")
        elif len(l) == 2:
            self.editor.insert_word(l[0], "("+l[1])
        self.hide()

    def select_next(self):
        if self._buttons and self._selected_index < len(self._buttons) - 1:
            self._selected_index += 1
            self._highlight()

    def select_prev(self):
        if self._buttons and self._selected_index > 0:
            self._selected_index -= 1
            self._highlight()

    def select_current(self):
        if self._buttons and self._selected_index >= 0:
            self._select(self._buttons[self._selected_index].text())

    def is_visible(self):
        return self.isVisible()
