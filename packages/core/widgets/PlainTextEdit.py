from PyQt6.QtWidgets import QPlainTextEdit
from PyQt6.QtCore import pyqtSignal


class PlainTextEdit(QPlainTextEdit):
    valueChanged = pyqtSignal(dict)
    valueSet = pyqtSignal(dict)

    def __init__(self, label=''):
        super().__init__()

        self.name = label
        self.textChanged.connect(lambda: self.valueChanged.emit({}))
        self.textChanged.connect(lambda: self.valueSet.emit({}))

    def value(self) -> str:
        return self.toPlainText()

    def get_name(self):
        return self.name