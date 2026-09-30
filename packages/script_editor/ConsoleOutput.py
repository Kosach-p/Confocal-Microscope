import sys
import ast
import operator
import inspect
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QPlainTextEdit, QApplication, QSplitter)
from PyQt6.QtCore import Qt, QObject, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut, QFont


class ConsoleOutput(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setFont(QFont("Consolas", 10))
        self.setMaximumBlockCount(1000)
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1d1d1d; color: #cccccc;
                border: 1px solid #353535; border-radius: 4px; padding: 6px;
            }
        """)
    def write(self, text):
        self.appendPlainText(str(text).rstrip())
