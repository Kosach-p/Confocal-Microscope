import inspect
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QPlainTextEdit, QApplication, QSplitter)
from PyQt6.QtCore import Qt, QObject, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut, QFont
from .HintPopup import HintPopup


class SimpleCodeEditor(QPlainTextEdit):
    def __init__(self, context, executor=None):
        super().__init__()
        self.context = context
        self.executor = executor
        self.setFont(QFont("Consolas", 11))
        self.setTabStopDistance(24)
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e; color: #d4d4d4;
                border: 1px solid #353535; border-radius: 4px;
                padding: 8px; selection-background-color: #264f78;
            }
        """)
        self.cursorPositionChanged.connect(self._find_hints)
        self._split = set(' .()[]{}:,\n\t')
        self._top_words = list(context.keys())
        self.edited_word = ''
        self._popup = HintPopup(self)

    def keyPressEvent(self, event):
        if self._popup.is_visible():
            if event.key() == Qt.Key.Key_Down:
                self._popup.select_next()
                return
            elif event.key() == Qt.Key.Key_Up:
                self._popup.select_prev()
                return
            elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Tab):
                self._popup.select_current()
                return
            elif event.key() == Qt.Key.Key_Escape:
                self._popup.hide()
                return
        super().keyPressEvent(event)

    def _find_hints(self):
        line, col = self._current_line_col()
        if line is None or col < 0:
            self._popup.hide()
            return
        dot_found = (col < len(line) and line[col] == '.')
        self.edited_word = ''
        obj_name = ''
        if dot_found:
            obj_name = self._extract_word_before(line, col - 1)
        elif col >= 0 and col < len(line) and line[col] not in self._split:
            i = col
            while i >= 0 and line[i] not in self._split:
                self.edited_word = line[i] + self.edited_word
                i -= 1
            if i >= 0 and line[i] == '.':
                dot_found = True
                obj_name = self._extract_word_before(line, i - 1)
        obj = self.context.get(obj_name) if obj_name else None

        if obj and dot_found:
            self._show_methods(obj)
        elif not dot_found and self.edited_word:
            self._show_top_words()
        else:
            self._popup.hide()

    def _show_methods(self, obj):
        methods = [m for m in dir(obj) if not m.startswith('_') and callable(getattr(obj, m, None))]
        params = [m for m in dir(obj) if not m.startswith('_') and not callable(getattr(obj, m, None))]
        descs = []
        for name in params:
            descs.append({"name": name, "suffix": ""})

        for name in methods:
            try:
                sig = inspect.signature(getattr(obj, name))
                params = [n for n in sig.parameters if n != 'self']
                descs.append({"name": name, "suffix": f"({', '.join(params)})"})
            except:
                descs.append({"name": name, "suffix": "()"})
        self._popup.show_hints(descs)

    def _show_top_words(self):
        l = [w for w in self._top_words if w.startswith(self.edited_word)]
        descs = []
        for word in l:
            descs.append({"name": word, "suffix": ""})
        self._popup.show_hints(descs)

    def insert_word(self, word, suffix=""):
        cur = self.textCursor()
        cur.setPosition(cur.position() - len(self.edited_word))
        cur.movePosition(cur.MoveOperation.Right, cur.MoveMode.KeepAnchor, len(self.edited_word))
        cur.removeSelectedText()
        cur.insertText(word.split('(')[0] + suffix)

    def execute(self):
        if self.executor:
            self.executor.execute_script(self.toPlainText())

    def _current_line_col(self):
        text = self.toPlainText()
        if not text: return None, -1
        lines = text.split('\n')
        cur = self.textCursor()
        ln = cur.blockNumber()
        if ln >= len(lines): return None, -1
        return list(lines[ln]), cur.columnNumber() - 1

    def _extract_word_before(self, line, pos):
        word = []
        while pos >= 0 and line[pos] not in self._split:
            word.append(line[pos])
            pos -= 1
        return ''.join(word[::-1])
