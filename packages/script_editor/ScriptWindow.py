from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QSplitter, QFileDialog)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut, QAction

from packages.Floating_window.ParentFloatingWindow import ParentFloatingWindow
from .ScriptEditor import SimpleCodeEditor
from .ScriptExecutor import ScriptExecutor
from .ConsoleOutput import ConsoleOutput
from .ScriptAPI import build_script_context


class ScriptWindow(ParentFloatingWindow):
    """Окно скриптового редактора"""
    name = "ScriptWindow"

    def __init__(self, controllers, devices, event_bus):
        super().__init__()

        self._controllers = controllers or {}
        self._devices = devices or {}
        self._file_path = None
        self.event_bus = event_bus
        self._post_init()

    def _post_init(self):
        self.setWindowTitle("Script Editor")
        self.resize(900, 600)
        self.setStyleSheet("""
            QMainWindow { background-color: #1d1d1d; }
            QPushButton {
                background-color: #545454; border: 1px solid #353535; color: #fff;
                border-radius: 4px; padding: 6px 16px; min-height: 24px;
            }
            QPushButton:hover { border-color: #6c7d9d; }
            QPushButton:pressed { background-color: #303030; border-color: #4d6490; }
            QMenuBar { background-color: #1d1d1d; color: #ffffff; border-bottom: 1px solid #353535; }
            QMenuBar::item:selected { background-color: #353535; }
            QMenu { background-color: #303030; color: #ffffff; border: 1px solid #353535; padding: 5px; }
            QMenu::item:selected { background-color: #4d6490; }
        """)

        self._context = build_script_context(self._controllers, self._devices)

        self.executor = ScriptExecutor(self._context, self.event_bus)
        self.editor = SimpleCodeEditor(self._context, self.executor)
        self.console = ConsoleOutput()

        self._setup_menu()

        btn_layout = QHBoxLayout()
        self.btn_run = QPushButton("▶ Выполнить")
        self.btn_stop = QPushButton("■ Стоп")
        self.btn_pause = QPushButton("⏸ Пауза")
        btn_layout.addWidget(self.btn_run)
        btn_layout.addWidget(self.btn_pause)
        btn_layout.addWidget(self.btn_stop)
        btn_layout.addStretch()

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(self.editor)
        splitter.addWidget(self.console)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        central = QWidget()
        central_layout = QVBoxLayout()
        central_layout.setContentsMargins(8, 8, 8, 8)
        central_layout.setSpacing(6)
        central_layout.addLayout(btn_layout)
        central_layout.addWidget(splitter)
        central.setLayout(central_layout)
        self.setCentralWidget(central)

        self.btn_run.clicked.connect(self.editor.execute)
        QShortcut(QKeySequence("Ctrl+Return"), self).activated.connect(self.editor.execute)
        QShortcut(QKeySequence("Ctrl+R"), self).activated.connect(self.editor.execute)

    def _setup_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("Файл")

        save_action = QAction("Сохранить", self)
        save_action.setShortcut(QKeySequence("Ctrl+S"))
        save_action.triggered.connect(self.saveFile)
        file_menu.addAction(save_action)

        open_action = QAction("Открыть", self)
        open_action.setShortcut(QKeySequence("Ctrl+O"))
        open_action.triggered.connect(self.openFile)
        file_menu.addAction(open_action)

    def saveFile(self):
        if self._file_path:
            with open(self._file_path, 'w', encoding='utf-8') as f:
                f.write(self.editor.toPlainText())
        else:
            self._save_as()

    def openFile(self):
        path, _ = QFileDialog.getOpenFileName(self, "Открыть скрипт", "", "Python (*.py);;Все файлы (*)")
        if path:
            self._file_path = path
            with open(path, 'r', encoding='utf-8') as f:
                self.editor.setPlainText(f.read())

    def _save_as(self):
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить скрипт", "", "Python (*.py);;Все файлы (*)")
        if path:
            self._file_path = path
            self.saveFile()