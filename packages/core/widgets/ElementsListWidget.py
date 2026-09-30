from PyQt6.QtWidgets import (QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, QHBoxLayout,
                             QAbstractItemView, QHeaderView, QRadioButton,
                             QButtonGroup)
from PyQt6.QtCore import Qt, pyqtSignal
from Icon.IconName import *
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QPushButton


class HoverButton(QPushButton):
    def __init__(self, normal_icon, hover_icon, parent=None):
        super().__init__(parent)
        self.normal_icon = QIcon(normal_icon)
        self.hover_icon = QIcon(hover_icon)
        self.setIcon(self.normal_icon)
        self.setFixedSize(20, 20)
        self.setStyleSheet("""
            QPushButton {
                background: transparent;  
                border: none;  
            }
        """)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)

    def enterEvent(self, event):
        self.setIcon(self.hover_icon)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setIcon(self.normal_icon)
        super().leaveEvent(event)


class ListWidget(QWidget):
    itemRadioChanged = pyqtSignal(int, int)  # Сигнал: (branch_id, selected_item_id)

    # Константы для позиции radioButton
    RADIO_LEFT = 0  # Слева от текста
    RADIO_RIGHT = 1  # Справа от корзины

    def __init__(self, parent=None, enable_radio=False, radio_position=RADIO_RIGHT):
        super().__init__(parent)
        self.counter = 0
        self.item_height = 28
        self.on_item_selected = None
        self.enable_radio = enable_radio
        self.radio_position = radio_position  # Позиция radioButton
        self.branch_button_groups = {}
        self.setup_ui()

        self.icons = {
            'trash': QIcon(closed_trash_Icon),
            'trash_hover': QIcon(trash_Icon)
        }

    def set_radio_mode(self, enabled, position=None):
        """Включение/выключение режима с radioButton"""
        self.enable_radio = enabled
        if position is not None:
            self.radio_position = position

        # Обновляем существующие элементы
        for i in range(self.tree_widget.topLevelItemCount()):
            branch = self.tree_widget.topLevelItem(i)
            branch_name = branch.text(0)

            if enabled:
                # Создаем группу кнопок для этой ветки, если её нет
                if branch_name not in self.branch_button_groups:
                    self.branch_button_groups[branch_name] = QButtonGroup(self)
                    self.branch_button_groups[branch_name].setExclusive(True)
                    self.branch_button_groups[branch_name].buttonClicked.connect(
                        lambda btn, bn=branch_name: self._on_radio_toggled(bn, btn)
                    )

                # Обновляем виджеты в листьях этой ветки
                for j in range(branch.childCount()):
                    item = branch.child(j)
                    self._update_item_widget(item, branch_name)
            else:
                # Удаляем все группы кнопок
                for group in self.branch_button_groups.values():
                    group.deleteLater()
                self.branch_button_groups.clear()

                # Восстанавливаем исходные виджеты и снимаем disabled
                for j in range(branch.childCount()):
                    item = branch.child(j)
                    item.setDisabled(False)
                    self._update_item_widget(item, branch_name)

    def set_active_item_by_id(self, item_id, branch_name=None):
        """
        Установка активного элемента по ID.
        Если branch_name не указан, ищет по всем веткам.
        """
        if not self.enable_radio:
            return False

        for i in range(self.tree_widget.topLevelItemCount()):
            branch = self.tree_widget.topLevelItem(i)
            current_branch_name = branch.text(0)

            # Если указано имя ветки, проверяем только её
            if branch_name is not None and current_branch_name != branch_name:
                continue

            # Ищем элемент с нужным ID
            for j in range(branch.childCount()):
                item = branch.child(j)
                if item.data(0, Qt.ItemDataRole.UserRole) == item_id:
                    # Находим radioButton для этого элемента
                    widget = self.tree_widget.itemWidget(item, 1)
                    if widget and current_branch_name in self.branch_button_groups:
                        for radio_btn in widget.findChildren(QRadioButton):
                            radio_btn.setChecked(True)
                            # _on_radio_toggled вызовется автоматически
                            return True

        return False

    def get_active_id_in_branch(self, branch_name):
        """
        Возвращает ID активного элемента в указанной ветке.
        Если никто не активен - возвращает -1.
        """
        if branch_name in self.branch_button_groups:
            checked_button = self.branch_button_groups[branch_name].checkedButton()
            if checked_button:
                return checked_button.property("item_id")
        return -1

    def clear_active_items(self, branch_name=None):
        """
        Снятие всех активных элементов.
        Если branch_name указан, очищает только эту ветку.
        """
        if branch_name:
            # Очищаем конкретную ветку
            if branch_name in self.branch_button_groups:
                checked_button = self.branch_button_groups[branch_name].checkedButton()
                if checked_button:
                    # Временно отключаем эксклюзивность
                    self.branch_button_groups[branch_name].setExclusive(False)
                    checked_button.setChecked(False)
                    self.branch_button_groups[branch_name].setExclusive(True)

                    # Снимаем disabled со всех элементов в ветке
                    for i in range(self.tree_widget.topLevelItemCount()):
                        branch = self.tree_widget.topLevelItem(i)
                        if branch.text(0) == branch_name:
                            for j in range(branch.childCount()):
                                branch.child(j).setDisabled(False)
                            break
        else:
            # Очищаем все ветки
            for group_name, group in self.branch_button_groups.items():
                checked_button = group.checkedButton()
                if checked_button:
                    group.setExclusive(False)
                    checked_button.setChecked(False)
                    group.setExclusive(True)

            # Снимаем disabled со всех элементов
            for i in range(self.tree_widget.topLevelItemCount()):
                branch = self.tree_widget.topLevelItem(i)
                for j in range(branch.childCount()):
                    branch.child(j).setDisabled(False)

    def _create_item_widget(self, item, branch_name):
        """Создание виджета для элемента с учетом позиции radioButton"""
        btn_widget = QWidget()
        btn_widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        btn_widget.setStyleSheet("background: transparent; ")

        btn_layout = QHBoxLayout(btn_widget)
        btn_layout.setContentsMargins(4, 0, 4, 0)
        btn_layout.setSpacing(4)

        # Создаем radioButton если режим включен
        radio_btn = None
        if self.enable_radio and branch_name in self.branch_button_groups:
            radio_btn = QRadioButton()

            # Добавляем в группу кнопок
            self.branch_button_groups[branch_name].addButton(radio_btn)

            # Сохраняем ID элемента в radioButton для идентификации
            radio_btn.setProperty("item_id", item.data(0, Qt.ItemDataRole.UserRole))

        # Кнопка удаления
        delete_btn = HoverButton(self.icons['trash'], self.icons['trash_hover'])
        delete_btn.setFixedSize(20, 20)
        item_id = item.data(0, Qt.ItemDataRole.UserRole)
        delete_btn.clicked.connect(lambda checked, id=item_id: self.delete_item(id))

        # Располагаем элементы в зависимости от позиции
        if self.radio_position == self.RADIO_LEFT:
            # RadioButton слева, затем stretch, затем корзина справа
            if radio_btn:
                btn_layout.addWidget(radio_btn)
            btn_layout.addStretch()
            btn_layout.addWidget(delete_btn)
        else:  # RADIO_RIGHT
            # Корзина справа, затем radioButton ещё правее
            btn_layout.addStretch()
            btn_layout.addWidget(delete_btn)
            if radio_btn:
                btn_layout.addWidget(radio_btn)

        return btn_widget

    def _update_item_widget(self, item, branch_name):
        """Обновление виджета элемента"""
        # Удаляем старый виджет если есть
        old_widget = self.tree_widget.itemWidget(item, 1)
        if old_widget:
            old_widget.deleteLater()

        # Создаем новый виджет
        new_widget = self._create_item_widget(item, branch_name)
        self.tree_widget.setItemWidget(item, 1, new_widget)

    def _on_radio_toggled(self, branch_name, radio_btn):
        """Обработчик выбора radioButton"""
        if radio_btn.isChecked():
            item_id = radio_btn.property("item_id")

            # Находим ветку и обновляем состояние disabled для всех элементов
            for i in range(self.tree_widget.topLevelItemCount()):
                branch = self.tree_widget.topLevelItem(i)
                if branch.text(0) == branch_name:
                    # Обновляем состояние всех элементов в ветке
                    for j in range(branch.childCount()):
                        child_item = branch.child(j)
                        child_id = child_item.data(0, Qt.ItemDataRole.UserRole)
                        # Активный элемент разблокирован, остальные заблокированы
                        child_item.setDisabled(child_id != item_id)

                    self.itemRadioChanged.emit(i, item_id)
                    break

    def get_selected_radio_items(self):
        """Получение выбранных элементов по всем группам"""
        selected = {}
        for branch_name, group in self.branch_button_groups.items():
            checked_button = group.checkedButton()
            if checked_button:
                selected[branch_name] = checked_button.property("item_id")
        return selected

    def get_active_radio_ids(self):
        """
        Выгрузка состояния radioButton - возвращает список ID активных элементов.
        Возвращает список словарей с информацией о выбранных элементах.
        """
        active_items = []
        for i in range(self.tree_widget.topLevelItemCount()):
            branch = self.tree_widget.topLevelItem(i)
            branch_name = branch.text(0)

            if branch_name in self.branch_button_groups:
                checked_button = self.branch_button_groups[branch_name].checkedButton()
                if checked_button:
                    item_id = checked_button.property("item_id")

                    # Находим соответствующий элемент для получения дополнительной информации
                    for j in range(branch.childCount()):
                        item = branch.child(j)
                        if item.data(0, Qt.ItemDataRole.UserRole) == item_id:
                            active_items.append({
                                'id': item_id,
                                'name': item.text(0),
                                'branch': branch_name,
                                'branch_index': i,
                                'item_index': j
                            })
                            break

        return active_items

    def get_active_radio_ids_simple(self):
        """
        Упрощенная выгрузка - возвращает только словарь {branch_name: item_id}
        """
        return self.get_selected_radio_items()

    def get_item_name_by_id(self, item_id):
        """
        Возвращает имя элемента по его ID.
        Если элемент не найден - возвращает None.
        """
        for i in range(self.tree_widget.topLevelItemCount()):
            branch = self.tree_widget.topLevelItem(i)
            for j in range(branch.childCount()):
                item = branch.child(j)
                if item.data(0, Qt.ItemDataRole.UserRole) == item_id:
                    return item.text(0)
        return None

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Кнопка создания
        self.create_btn = QPushButton("+ Добавить")
        self.create_btn.setFixedHeight(32)
        layout.addWidget(self.create_btn)

        self.create_btn.setStyleSheet(f"""
            QPushButton {{background: transparent; color: white; border: 1px solid #555555; border-radius: 4px; padding: 4px 8px;}}
            QPushButton:hover {{background-color: #3d3d3d;}}
            QPushButton:pressed {{background-color: #2d2d2d;}}
        """)

        # Дерево
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.setColumnCount(2)
        # Увеличиваем ширину второй колонки если radioButton справа
        column_width = 120 if (self.enable_radio and self.radio_position == self.RADIO_RIGHT) else 80
        self.tree_widget.setColumnWidth(1, column_width)
        self.tree_widget.header().setStretchLastSection(False)
        self.tree_widget.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tree_widget.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.tree_widget.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.tree_widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.tree_widget.verticalScrollBar().setSingleStep(50)
        self.tree_widget.verticalScrollBar().setPageStep(50)
        self.tree_widget.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked |
            QAbstractItemView.EditTrigger.EditKeyPressed
        )

        # Стилизация с добавлением стиля для disabled элементов
        self.tree_widget.setStyleSheet(f"""
            QTreeWidget {{border: 1px solid #545454; border-radius: 0px; background: transparent;}}
            QTreeWidget:focus {{outline: none; border: 1px solid #545454; border-radius: 0px;}}
            QTreeWidget::item {{padding: 5px; height: 20px; color: white;}}
            QTreeWidget::item:selected {{background-color: #3a4a6b; color: white;}}
            QTreeWidget::item:hover {{background-color: #6c7d9d;}}
            QTreeWidget::item:disabled {{color: #666666; background-color: transparent;}}
            QTreeWidget::branch {{background-color: transparent;}}
            QTreeWidget::branch:hover {{background-color: transparent;}}
            QTreeWidget::branch:closed:has-children,
            QTreeWidget::branch:closed:has-children:has-siblings {{image: url({arrow_right_Icon});}}
            QTreeWidget::branch:open:has-children,
            QTreeWidget::branch:open:has-children:has-siblings {{image: url({arrow_down_Icon});}}
            QTreeWidget QLineEdit {{background-color: #2b2b2b; color: white; border: 1px solid #555555; border-radius: 2px; padding: 2px; selection-background-color: #3a4a6b;}}
            QScrollBar:vertical {{background-color: #303030; width: 12px; border: none;}}
            QScrollBar::handle:vertical {{background-color: #6c7d9d; border-radius: 6px; min-height: 30px;}}
            QScrollBar::handle:vertical:hover {{background-color: #8a9bb9;}}
            QScrollBar::handle:vertical:pressed {{background-color: #4d6490;}}
            QScrollBar:horizontal {{background-color: #303030; height: 12px; border: none;}}
            QScrollBar::handle:horizontal {{background-color: #6c7d9d; border-radius: 6px; min-width: 30px;}}
            QScrollBar::handle:horizontal:hover {{background-color: #8a9bb9;}}
            QScrollBar::handle:horizontal:pressed {{background-color: #4d6490;}}
        """)

        self.tree_widget.currentItemChanged.connect(self._on_item_selected)
        layout.addWidget(self.tree_widget)

    def create_item(self, name=None, id=-1, branch="Default"):
        # Ищем существующую ветвь
        branch_item = None
        for i in range(self.tree_widget.topLevelItemCount()):
            item = self.tree_widget.topLevelItem(i)
            if item.text(0) == branch and item.data(0, Qt.ItemDataRole.UserRole) == -1:
                branch_item = item
                break

        # Если ветвь не найдена - создаём новую
        if branch_item is None:
            branch_item = QTreeWidgetItem()
            branch_item.setText(0, branch)
            branch_item.setData(0, Qt.ItemDataRole.UserRole, -1)
            branch_item.setFlags(branch_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            branch_item.setChildIndicatorPolicy(QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator)
            self.tree_widget.addTopLevelItem(branch_item)
            branch_item.setExpanded(True)

            # Создаем группу кнопок для новой ветки если режим включен
            if self.enable_radio and branch not in self.branch_button_groups:
                self.branch_button_groups[branch] = QButtonGroup(self)
                self.branch_button_groups[branch].setExclusive(True)
                self.branch_button_groups[branch].buttonClicked.connect(
                    lambda btn, bn=branch: self._on_radio_toggled(bn, btn)
                )

        # Создаем лист (дочерний элемент)
        tree_item = QTreeWidgetItem(branch_item)
        tree_item.setText(0, name)
        tree_item.setData(0, Qt.ItemDataRole.UserRole, id)
        tree_item.setFlags(tree_item.flags() | Qt.ItemFlag.ItemIsEditable)

        # Создаем виджет для элемента
        btn_widget = self._create_item_widget(tree_item, branch)
        self.tree_widget.setItemWidget(tree_item, 1, btn_widget)

        # Если есть активный radioButton в этой ветке, новый элемент должен быть disabled
        if self.enable_radio and branch in self.branch_button_groups:
            checked_button = self.branch_button_groups[branch].checkedButton()
            if checked_button:
                tree_item.setDisabled(True)

        # Устанавливаем созданный элемент как текущий
        self.tree_widget.setCurrentItem(tree_item)

    def _on_item_selected(self, current, previous):
        if current and current.parent():
            item_id = current.data(0, Qt.ItemDataRole.UserRole)
            if self.on_item_selected:
                self.on_item_selected(item_id)
        elif current and self.on_item_selected:
            self.on_item_selected(None)

    def get_selected_item_id(self):
        current = self.tree_widget.currentItem()
        if current:
            return current.data(0, Qt.ItemDataRole.UserRole)
        return None

    def delete_item_ext(self, item_id):
        pass

    def delete_item(self, item_id):
        for i in range(self.tree_widget.topLevelItemCount()):
            branch = self.tree_widget.topLevelItem(i)
            branch_name = branch.text(0)
            for j in range(branch.childCount()):
                item = branch.child(j)
                if item.data(0, Qt.ItemDataRole.UserRole) == item_id:
                    # Проверяем, был ли удаляемый элемент активным
                    was_active = False
                    if branch_name in self.branch_button_groups:
                        widget = self.tree_widget.itemWidget(item, 1)
                        if widget:
                            for child in widget.findChildren(QRadioButton):
                                if child.isChecked():
                                    was_active = True
                                self.branch_button_groups[branch_name].removeButton(child)

                    # Удаляем виджет
                    widget = self.tree_widget.itemWidget(item, 1)
                    if widget:
                        widget.deleteLater()

                    branch.removeChild(item)
                    self.delete_item_ext(item_id)

                    # Если ветвь опустела - удаляем её и группу кнопок
                    if branch.childCount() == 0:
                        if branch_name in self.branch_button_groups:
                            self.branch_button_groups[branch_name].deleteLater()
                            del self.branch_button_groups[branch_name]
                        self.tree_widget.takeTopLevelItem(i)
                    elif was_active and branch_name in self.branch_button_groups:
                        # Если удалили активный элемент, снимаем disabled со всех оставшихся
                        for k in range(branch.childCount()):
                            branch.child(k).setDisabled(False)
                    return

    def get_all_items_data(self):
        items_data = []
        for i in range(self.tree_widget.topLevelItemCount()):
            branch = self.tree_widget.topLevelItem(i)
            branch_name = branch.text(0)
            for j in range(branch.childCount()):
                item = branch.child(j)
                item_data = {
                    'name': item.text(0),
                    'id': item.data(0, Qt.ItemDataRole.UserRole),
                    'branch': branch_name,
                    'index': j
                }
                items_data.append(item_data)
        return items_data