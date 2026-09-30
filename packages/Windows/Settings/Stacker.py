from PyQt6.QtWidgets import QListWidget, QStackedWidget, QFrame, QVBoxLayout, QWidget
from packages.core.widgets.ElementsListWidget import ListWidget
from PyQt6.uic import loadUi
from PyQt6.QtCore import Qt, pyqtSignal


def DeviceConnectionSettings():
    return loadUi("ui/DeviceConnectionSettings.ui")


class ProfilePage(QFrame):
    page_activated = pyqtSignal()  # сигнал при активации страницы
    page_deactivated = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContentsMargins(0, 0, 0, 0)
        self._active = False

    def showEvent(self, event):
        super().showEvent(event)
        if not self._active:
            self._active = True
            self.page_activated.emit()

    def hideEvent(self, event):
        super().hideEvent(event)
        if self._active:
            self._active = False
            self.page_deactivated.emit()


class SettingsSwitcher:
    """Связывает QListWidget и QStackedWidget для навигации по настройкам устройств"""

    def __init__(self, frame: QFrame, widget_name='widget', enable_radio=False):
        self.frame = frame
        self.list_widget = None
        self.stack_widget = None
        self.profiles_page = {}
        widget = self.frame.findChild(QWidget, widget_name)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        self.list_widget = ListWidget(parent=widget, enable_radio=enable_radio)
        layout.addWidget(self.list_widget)

        for child in self.frame.findChildren(QStackedWidget):
            self.stack_widget = child
            break

        self.stack_widget.setContentsMargins(0, 0, 0, 0)

        self.list_widget.tree_widget.currentItemChanged.connect(self.on_current_item_changed)
        if self.list_widget.tree_widget.topLevelItemCount() > 0:
            self.list_widget.tree_widget.setCurrentItem(self.list_widget.tree_widget.topLevelItem(0))

        self.id_item_to = {}

    def on_current_item_changed(self, current, previous):
        if current and current.parent():  # Только для листьев
            item_id = current.data(0, Qt.ItemDataRole.UserRole)
            self.stack_widget.setCurrentWidget(self.profiles_page[item_id])

    def append_page(self, prof_name, id, branch_name='default'):
        page = ProfilePage()
        self.stack_widget.addWidget(page)
        self.profiles_page[id] = page

        self.stack_widget.setCurrentWidget(page)

        self.list_widget.create_item(prof_name, id, branch_name)

    def set_active_page_by_id(self, id, branch_name):
        self.list_widget.set_active_item_by_id(id, branch_name)

    def remove_page(self, id):
        """Удаляет страницу под профиль"""
        self.stack_widget.removeWidget(self.profiles_page[id])

    def get_page(self, id) -> QFrame:
        """Возвращает страницу для указанного устройства"""
        return self.profiles_page.get(id)
