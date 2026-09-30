from PyQt6.QtWidgets import (QTableWidget, QTableWidgetItem, QHeaderView,
                             QVBoxLayout, QFrame, QApplication)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QColor
from packages.core.services.HotKey import HotKeyConverter


class HotkeyTable(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(2)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.verticalHeader().setVisible(False)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.setShowGrid(False)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._editing = None
        self._editing_text_buff = None

        self.codeConverter = HotKeyConverter()

        self.setHorizontalHeaderLabels(["Действие", "Горячие клавиши"])

        self.cellClicked.connect(self._on_cell_clicked)

        if parent:
            if parent.layout() is None:
                QVBoxLayout(parent)
            parent.layout().addWidget(self)
        self.current_keys = list()

    def add_row(self, action: str, shortcut: str = ""):
        row = self.rowCount()
        self.insertRow(row)

        item_action = QTableWidgetItem(action)
        item_action.setFlags(Qt.ItemFlag.NoItemFlags)
        item_action.setForeground(Qt.GlobalColor.white)
        self.setItem(row, 0, item_action)

        item_key = QTableWidgetItem(shortcut)
        item_key.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        item_key.setForeground(Qt.GlobalColor.lightGray)
        item_key.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setItem(row, 1, item_key)

    def add_category(self, name: str):
        row = self.rowCount()
        self.insertRow(row)
        item = QTableWidgetItem(name)
        item.setFlags(Qt.ItemFlag.NoItemFlags)
        item.setForeground(Qt.GlobalColor.white)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        font = item.font()
        font.setBold(True)
        font.setPointSize(10)
        item.setFont(font)
        self.setItem(row, 0, item)
        self.setSpan(row, 0, 1, 2)

        # Фон строки-категории
        self.item(row, 0).setBackground(QColor("#3a3a3a"))

    def _on_cell_clicked(self, row, col):
        if col == 1:
            if self._editing == row:
                return
            if self._editing is not None and self._editing != row:
                self._finish_editing()
            self._editing_text_buff = self.item(row, 1).text()
            self._editing = row
        elif col == 0:
            self._finish_editing()

    def _finish_editing(self):
        if self._editing is not None:
            self.item(self._editing, 1).setText(self._editing_text_buff)
            self._editing = None
            self._editing_text_buff = ""
            self.clearSelection()
            self.setFocus()

    def keyPressEvent(self, event):
        if self._editing is not None:
            if event.key() == Qt.Key.Key_Escape:
                self._finish_editing()
                return

            native_code = event.nativeScanCode()
            key_name = self.codeConverter.get_key_by_physical_code(native_code)

            if key_name:
                if key_name not in self.current_keys:
                    self.current_keys.append(key_name)
                combination_text = self.codeConverter.nativeCodeCombination2str(self.current_keys)
                self.item(self._editing, 1).setText(combination_text)
            else:
                return

            if key_name in ["Ctrl", "Alt", "Shift"]:
                return

            self.item(self._editing, 1).setData(Qt.ItemDataRole.UserRole, combination_text)
            self.clearSelection()
            self._editing = None
            return
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        native_code = event.nativeScanCode()
        key_name = self.codeConverter.get_key_by_physical_code(native_code)

        if key_name and key_name in self.current_keys:
            self.current_keys.remove(key_name)
            if self._editing is not None:
                combination_text = self.codeConverter.nativeCodeCombination2str(self.current_keys)
                self.item(self._editing, 1).setText(combination_text)

        event.accept()

    def get_shortcuts(self) -> dict:
        result = {}
        for row in range(self.rowCount()):
            action = self.item(row, 0).text()
            shortcut = self.item(row, 1).text()
            result[action] = shortcut
        return result

    def reset_defaults(self):
        """Сбрасывает таблицу к заводским настройкам"""
        self.setRowCount(0)