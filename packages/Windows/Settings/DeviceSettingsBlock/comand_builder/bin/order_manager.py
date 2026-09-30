from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QAbstractItemView
from PyQt6.QtCore import Qt, pyqtSignal, QObject


class OrderListManager(QObject):
    order_changed = pyqtSignal(list)

    def __init__(self, list_widget):
        super().__init__()
        self.list_widget = list_widget
        self.list_widget.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.list_widget.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        self.list_widget.model().rowsMoved.connect(self._on_order_changed)

    def _on_order_changed(self, parent, start, end, destination, row):
        """Вызывается при перемещении элементов"""
        self.order_changed.emit(self.get_order())

    def add_block(self, name, data=None):
        """Добавить блок"""
        # Проверяем, нет ли уже такого
        if self.get_block(name) is not None:
            return False

        item = QListWidgetItem(name)
        item.setData(Qt.ItemDataRole.UserRole, data)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsDragEnabled)
        self.list_widget.addItem(item)
        return True

    def remove_block(self, name):
        """Удалить блок по названию"""
        item = self.get_block(name)
        if item:
            row = self.list_widget.row(item)
            self.list_widget.takeItem(row)
            return True
        return False

    def get_block(self, name):
        """Найти блок по названию"""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.text() == name:
                return item
        return None

    def get_order(self):
        """Выгрузить текущую последовательность"""
        order = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            order.append({
                'name': item.text(),
                'data': item.data(Qt.ItemDataRole.UserRole)
            })
        return order

    def clear(self):
        """Очистить список"""
        self.list_widget.clear()