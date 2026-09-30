from PyQt6.QtWidgets import QWidget, QLabel, QComboBox, QHBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal


class ComboBoxName(QWidget):
    valueChanged = pyqtSignal(dict)
    valueSet = pyqtSignal(dict)

    def __init__(self, label='', name_list=None, values=None, default_index=0):
        super().__init__()

        self.name = label
        self._name_list = name_list if name_list else []
        self._values = values if values else self._name_list.copy()

        # Проверка на соответствие длин
        if len(self._name_list) != len(self._values):
            raise ValueError("name_list and values must have the same length")

        self._current_index = min(default_index, len(self._name_list) - 1) if self._name_list else 0
        self._graphics_view = None

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._wrapper = QWidget()
        self._wrapper.setFixedHeight(25)

        # ComboBox внутри wrapper (занимает всю ширину)
        self._combo = QComboBox(self._wrapper)
        self._combo.addItems(self._name_list)
        self._combo.setCurrentIndex(self._current_index)

        self._label = None
        if label:
            self._label = QLabel(label, self._wrapper)
            self._label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            self._label.setProperty("dragLabel", True)
            self._label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
            self._label.setGeometry(0, 0, self._wrapper.width() - 6, self._wrapper.height())

        outer.addWidget(self._wrapper)

        # Properties для QSS
        self.setProperty("dragInput", True)
        self._wrapper.setProperty("dragWrapper", True)
        self._combo.setProperty("dragCombo", True)

        # Connect signal
        self._combo.currentIndexChanged.connect(self._onComboChanged)

    def _onComboChanged(self, index):
        if index >= 0 and index < len(self._values):
            self._current_index = index
            value = self._values[index]
            self.valueChanged.emit({"value": value})
            self.valueSet.emit({"value": value})

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # ComboBox занимает всю ширину wrapper
        self._combo.setGeometry(0, 2, self._wrapper.width(), self._wrapper.height() - 4)

        # Обновляем позицию label при изменении размера
        if self._label:
            self._label.move(self._wrapper.width() - self._label.width() - 6, 4)

    def value(self):
        """Возвращает текущее значение (данные)"""
        if self._current_index < len(self._values):
            return self._values[self._current_index]
        return None

    def setValue(self, value):
        """Устанавливает значение по данным"""
        if value in self._values:
            index = self._values.index(value)
            self._combo.setCurrentIndex(index)
            self._current_index = index

    def setCurrentIndex(self, index):
        """Устанавливает текущий индекс"""
        if 0 <= index < len(self._name_list):
            self._combo.setCurrentIndex(index)
            self._current_index = index

    def currentIndex(self):
        """Возвращает текущий индекс"""
        return self._current_index

    def currentText(self):
        """Возвращает текущий текст"""
        return self._combo.currentText()

    def get_name(self):
        return self.name