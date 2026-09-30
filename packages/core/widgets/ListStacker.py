from PyQt6.QtWidgets import QListWidget, QStackedWidget, QFrame, QWidget
from PyQt6.QtCore import Qt


class ListStacker:
    """Связывает QListWidget и QStackedWidget для навигации """

    def __init__(self, frame: QFrame):
        self.frame = frame
        self.list_widget = None
        self.stack_widget = None
        self.pages = {}

        for child in self.frame.findChildren(QStackedWidget):
            self.stack_widget = child
            break

        for child in self.frame.findChildren(QListWidget):
            self.list_widget = child
            break

        self.stack_widget.setContentsMargins(0, 0, 0, 0)
        self._connect_signals()

    def append_page(self, name: str, widget: QWidget):
        """Добавляет страницу в стек и в список"""
        self.stack_widget.addWidget(widget)
        self.list_widget.addItem(name)
        self.pages[name] = widget

        if self.stack_widget.count() == 1:
            self.list_widget.setCurrentRow(0)
            self.stack_widget.setCurrentIndex(0)

    def _connect_signals(self):
        """Подключение сигнала переключения"""
        self.list_widget.currentRowChanged.connect(self.stack_widget.setCurrentIndex)

    def get_current_page(self) -> QWidget:
        """Возвращает текущую активную страницу"""
        return self.stack_widget.currentWidget()

    def get_current_name(self) -> str:
        """Возвращает имя текущей страницы"""
        current_row = self.list_widget.currentRow()
        if current_row >= 0:
            return self.list_widget.item(current_row).text()
        return None
