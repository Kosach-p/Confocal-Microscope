from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (QTreeWidgetItem, QSpinBox, QLineEdit,
                             QComboBox, QWidget, QHBoxLayout, QTreeWidget, QLabel, QHeaderView, QAbstractItemView)
from packages.core.widgets.SpinBox import upgradeSpinBox
from packages.core.widgets.ComboBox import upgradeComboBox
from PyQt6.QtWidgets import QSizePolicy
from packages.core.config.device_schema import ASCII_ALIGNMENT_NAMES_RU

class SmartSpinBox(QSpinBox):
    """Спинбокс, который показывает '-' для значения -1"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setSpecialValueText("∞")
        self.setMinimum(-1)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Выравнивание по центру
        self.setMinimumWidth(30)  # Минимальная ширина
        self.setSizePolicy(
            QSizePolicy.Policy.Minimum,  # Горизонтальная политика - минимальный
            QSizePolicy.Policy.Fixed  # Вертикальная политика - фиксированная
        )

    def valueFromText(self, text):
        if text == "∞":
            return -1
        return super().valueFromText(text)

    def textFromValue(self, value):
        if value == -1:
            return "∞"
        return super().textFromValue(value)


class FormatWidget(QWidget):
    """Виджет для настройки формата числа (до/после запятой)"""
    format_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        self.dot = QLabel()
        self.dot.setText(".")

        self.after_dot = upgradeSpinBox(SmartSpinBox())
        self.after_dot.setRange(-1, 20)
        self.after_dot.setValue(2)
        self.after_dot.valueChanged.connect(self.format_changed.emit)

        layout.addWidget(self.dot)
        layout.addWidget(self.after_dot)
        self.setLayout(layout)

    def get_format(self):
        after = self.after_dot.value()

        if after == -1:
            return f"f"
        else:
            return f".{after}f"

    def set_format(self, fmt_str):
        if not fmt_str or fmt_str == "s":
            self.after_dot.setValue(-1)
            return

        try:
            parts = fmt_str.replace('f', '').replace('d', '').replace('x', '').replace('X', '').split('.')
            after = int(parts[1]) if len(parts) > 1 else -1
            self.after_dot.setValue(after)
        except:
            self.after_dot.setValue(-1)


class SpaceWidget(QWidget):
    """Виджет для выбора пространства и выравнивания"""
    space_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        self.space_spin = upgradeSpinBox(SmartSpinBox())
        self.space_spin.setRange(-1, 100)
        self.space_spin.setValue(10)
        self.space_spin.valueChanged.connect(self.space_changed.emit)

        self.alignment = upgradeComboBox(QComboBox())
        for key, value in ASCII_ALIGNMENT_NAMES_RU.items():
            self.alignment.addItem(value, key)
        self.alignment.setCurrentIndex(0)
        self.alignment.currentIndexChanged.connect(self.space_changed.emit)

        layout.addWidget(self.space_spin)
        layout.addWidget(self.alignment)
        self.setLayout(layout)

    def get_alignment(self):
        return 'right' if self.alignment.currentIndex() == 0 else 'left'

    def set_alignment(self, alignment):
        self.alignment.setCurrentIndex(0 if alignment == 'right' else 1)

    def get_space(self):
        return self.space_spin.value()

    def set_space(self, space):
        self.space_spin.setValue(space)


class ParamsTreeWidget(QTreeWidget):
    """Класс-обёртка для дерева параметров"""
    params_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # Настройка заголовков
        self.setColumnCount(7)
        self.setHeaderLabels(["Переменная", "Значение", "Префикс", "Суффикс",
                              "Число знаков", "Заполняющий символ", "Пространство"])

        # Настройки дерева
        self.setRootIsDecorated(False)
        self.setIndentation(0)
        self.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # Включаем горизонтальный скролл, когда колонки не влезают
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Отключаем автоматический скролл по содержимому
        self.setAutoScroll(False)

        # Настройка заголовков
        header = self.header()
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStretchLastSection(False)  # Отключаем растягивание последней

        # Минимальные ширины колонок (чтобы не схлопывались)
        min_widths = {
            0: 120,  # Переменная
            1: 100,  # Значение
            2: 80,   # Префикс
            3: 80,   # Суффикс
            4: 80,   # Формат
            5: 100,  # Пространство
            6: 100,  # Пространство
        }

        for col, width in min_widths.items():
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)
            header.resizeSection(col, width)
            self.setColumnWidth(col, width)

        # Стилизация
        self.setStyleSheet("""
            QTreeWidget::item {
                padding: 4px 5px;
                margin: 2px 0px;
                min-height: 24px;
            }
        """)

        # Хранилище виджетов для каждой строки
        self.param_widgets = {}

        # Минимальная высота
        self.setMinimumHeight(150)

    def resizeEvent(self, event):
        """Автоматически растягивает колонки при изменении размера"""
        super().resizeEvent(event)
        total_width = self.viewport().width()
        if total_width > 0:
            # Распределяем ширину пропорционально
            self.setColumnWidth(0, int(total_width * 0.15))  # Переменная
            self.setColumnWidth(1, int(total_width * 0.10))  # Значение
            self.setColumnWidth(2, int(total_width * 0.10))  # Префикс
            self.setColumnWidth(3, int(total_width * 0.10))  # Суффикс
            self.setColumnWidth(4, int(total_width * 0.13))  # Число знаков
            self.setColumnWidth(5, int(total_width * 0.17))  # Заполняющий символ
            self.setColumnWidth(6, int(total_width * 0.25))  # Пространство

    def add_row(self, var_name, value=0, prefix="", suffix="",
                  fmt="", space=10, alignment='right', fill_symbol="0"):
        """Добавляет новый параметр в дерево"""

        if var_name in self.param_widgets:
            return False  # Параметр с таким именем уже существует

        item = QTreeWidgetItem(self)

        # Запрещаем дроп на этот элемент
        flags = item.flags()
        flags &= ~Qt.ItemFlag.ItemIsDropEnabled
        item.setFlags(flags)

        def _center_widget(widget):
            container = QWidget()
            container.setObjectName("centerContainer")
            container.setStyleSheet("QWidget#centerContainer {background-color: transparent;}")
            layout = QHBoxLayout(container)
            layout.addWidget(widget)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            return container

        # Колонка 0: Имя переменной
        item.setText(0, var_name)
        item.setTextAlignment(0, Qt.AlignmentFlag.AlignCenter)

        # Колонка 1: Значение (SpinBox)
        value_spin = upgradeSpinBox(SmartSpinBox())
        value_spin.setRange(-2147483648, 2147483647)
        value_spin.setValue(value)
        value_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_spin.valueChanged.connect(self._on_internal_change)
        self.setItemWidget(item, 1, _center_widget(value_spin))  # Оборачиваем

        # Колонка 2: Префикс (LineEdit)
        prefix_edit = QLineEdit()
        prefix_edit.setText(prefix)
        prefix_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        prefix_edit.setMaximumWidth(80)
        prefix_edit.textChanged.connect(self._on_internal_change)
        self.setItemWidget(item, 2, _center_widget(prefix_edit))  # Оборачиваем

        # Колонка 3: Суффикс (LineEdit)
        suffix_edit = QLineEdit()
        suffix_edit.setText(suffix)
        suffix_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        suffix_edit.setMaximumWidth(80)
        suffix_edit.textChanged.connect(self._on_internal_change)
        self.setItemWidget(item, 3, _center_widget(suffix_edit))  # Оборачиваем

        # Колонка 4: Формат (FormatWidget)
        format_widget = FormatWidget()
        format_widget.set_format(fmt)
        format_widget.format_changed.connect(self._on_internal_change)
        self.setItemWidget(item, 4, _center_widget(format_widget))  # Оборачиваем

        # Колонка 5: Заполняющий символ
        fill_symbol_edit = QLineEdit()
        fill_symbol_edit.setText(fill_symbol)
        fill_symbol_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fill_symbol_edit.setMaximumWidth(80)
        fill_symbol_edit.textChanged.connect(self._on_internal_change)
        self.setItemWidget(item, 5, _center_widget(fill_symbol_edit))

        # Колонка 6: Пространство (SpaceWidget)
        space_widget = SpaceWidget()
        space_widget.space_spin.setValue(space)
        space_widget.set_alignment(alignment)
        space_widget.space_changed.connect(self._on_internal_change)
        self.setItemWidget(item, 6, _center_widget(space_widget))  # Оборачиваем

        # Сохраняем виджеты
        self.param_widgets[var_name] = {
            'item': item,
            'value_spin': value_spin,
            'prefix_edit': prefix_edit,
            'suffix_edit': suffix_edit,
            'format_widget': format_widget,
            'space_widget': space_widget,
            'fill_symbol': fill_symbol_edit
        }

        self.params_changed.emit()
        return True

    def remove_param(self, var_name):
        """Удаляет параметр по имени"""
        if var_name not in self.param_widgets:
            return False

        widgets = self.param_widgets[var_name]
        root = self.invisibleRootItem()
        root.removeChild(widgets['item'])
        del self.param_widgets[var_name]

        self.params_changed.emit()
        return True

    def clear(self):
        """Удаляет параметр по имени"""
        for widgets in self.param_widgets.values():
            root = self.invisibleRootItem()
            root.removeChild(widgets['item'])
        self.param_widgets = {}
        self.params_changed.emit()
        return True

    def get_param_data(self, var_name):
        """Получает данные конкретного параметра"""
        if var_name not in self.param_widgets:
            return None

        widgets = self.param_widgets[var_name]
        fmt_widget = widgets['format_widget']
        space_widget = widgets['space_widget']

        return {
            'name': var_name,
            'value': widgets['value_spin'].value(),
            'param_prefix': widgets['prefix_edit'].text(),
            'param_suffix': widgets['suffix_edit'].text(),
            'param_fmt': fmt_widget.get_format(),
            'param_space': space_widget.get_space(),
            'param_alignment': space_widget.get_alignment(),
            'fill_symbol': widgets['fill_symbol'].text()
        }

    def get_all_params(self):
        """Получает данные всех параметров в порядке их следования"""
        params = []
        root = self.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            var_name = item.text(0)
            param_data = self.get_param_data(var_name)
            if param_data:
                params.append(param_data)

        return params

    def set_param_value(self, var_name, value):
        """Устанавливает значение параметра"""
        if var_name in self.param_widgets:
            self.param_widgets[var_name]['value_spin'].setValue(value)

    def set_param_prefix(self, var_name, prefix):
        """Устанавливает префикс параметра"""
        if var_name in self.param_widgets:
            self.param_widgets[var_name]['prefix_edit'].setText(prefix)

    def set_param_suffix(self, var_name, suffix):
        """Устанавливает суффикс параметра"""
        if var_name in self.param_widgets:
            self.param_widgets[var_name]['suffix_edit'].setText(suffix)

    def set_param_format(self, var_name, fmt):
        """Устанавливает формат параметра"""
        if var_name in self.param_widgets:
            self.param_widgets[var_name]['format_widget'].set_format(fmt)

    def set_param_space(self, var_name, space, alignment='right'):
        """Устанавливает пространство и выравнивание параметра"""
        if var_name in self.param_widgets:
            space_widget = self.param_widgets[var_name]['space_widget']
            space_widget.set_space(space)
            space_widget.set_alignment(alignment)

    def get_param_names(self):
        """Возвращает список имён параметров в порядке отображения"""
        names = []
        root = self.invisibleRootItem()
        for i in range(root.childCount()):
            names.append(root.child(i).text(0))
        return names

    def move_param_up(self, var_name):
        """Перемещает параметр вверх"""
        if var_name not in self.param_widgets:
            return

        item = self.param_widgets[var_name]['item']
        root = self.invisibleRootItem()
        index = root.indexOfChild(item)

        if index > 0:
            # Удаляем и вставляем на позицию выше
            root.removeChild(item)
            root.insertChild(index - 1, item)
            self.setCurrentItem(item)
            self.params_changed.emit()

    def move_param_down(self, var_name):
        """Перемещает параметр вниз"""
        if var_name not in self.param_widgets:
            return

        item = self.param_widgets[var_name]['item']
        root = self.invisibleRootItem()
        index = root.indexOfChild(item)

        if index < root.childCount() - 1:
            root.removeChild(item)
            root.insertChild(index + 1, item)
            self.setCurrentItem(item)
            self.params_changed.emit()

    def clear_params(self):
        """Очищает все параметры"""
        self.clear()
        self.param_widgets.clear()
        self.params_changed.emit()

    def _on_internal_change(self, *args):
        """Внутренний обработчик изменений"""
        self.params_changed.emit()

    def get_selected_param_name(self):
        """Возвращает имя выбранного параметра"""
        current = self.currentItem()
        if current:
            return current.text(0)
        return None