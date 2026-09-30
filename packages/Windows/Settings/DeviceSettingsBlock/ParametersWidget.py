from PyQt6.uic import loadUi
from PyQt6.QtWidgets import QWidget, QCheckBox, QComboBox
from typing import Any

from packages.core.config.path import ui
from packages.core.validators.numeric_validator import (
    IntCalcValidator, IntValidator, FloatCalcValidator, FloatValidator,
    ReadOnlyIntValidator,
)


class ParametersWidget:
    """
    Таблица параметров устройства.

    Использование:
        params_widget = ParametersWidget()
        params_widget.set_parameters({"x_min": 0, "y_max": 100})
        values = params_widget.get_parameters()
    """

    # Маппинг валидатор → геттер/сеттер
    _GETTERS = {
        IntCalcValidator: lambda w: int(w.text() or 0),
        IntValidator: lambda w: int(w.text() or 0),
        FloatCalcValidator: lambda w: float(w.text() or 0.0),
        FloatValidator: lambda w: float(w.text() or 0.0),
        ReadOnlyIntValidator: lambda w: int(w.text() or 0),
        QCheckBox: lambda w: w.isChecked(),
        QComboBox: lambda w: w.currentText(),
    }

    _SETTERS = {
        IntCalcValidator: lambda w, v: w.setText(str(int(v))),
        IntValidator: lambda w, v: w.setText(str(int(v))),
        FloatCalcValidator: lambda w, v: w.setText(str(float(v))),
        FloatValidator: lambda w, v: w.setText(str(float(v))),
        ReadOnlyIntValidator: lambda w, v: w.setText(str(int(v))),
        QCheckBox: lambda w, v: w.setChecked(bool(v)),
        QComboBox: lambda w, v: w.setCurrentText(str(v)),
    }

    def __init__(self, ui_name: str, params_map: list[tuple[str, str, type]]):
        """
        Args:
            ui_name: имя .ui файла
            params_map: [(имя_параметра, имя_виджета, валидатор), ...]
        """
        self.init_cplt = False
        self.frame = loadUi(ui(ui_name))

        self._params_map = params_map
        self._ui_name = ui_name
        self._widgets: dict[str, QWidget] = {}
        self._validators: dict[str, Any] = {}

        self.data = None

    def setupUI(self):
        self.init_cplt = True

        for param_name, widget_name, validator in self._params_map:
            widget = self.frame.findChild(QWidget, widget_name)
            if widget is None:
                raise ValueError(f"Виджет '{widget_name}' не найден в {self._ui_name}")

            self._widgets[param_name] = widget
            self._validators[param_name] = validator

            if hasattr(widget, 'setValidator') and validator is not None:
                widget.setValidator(validator)

        self.set_parameters(self.data)

    def get_parameters(self) -> dict:
        """Возвращает словарь {имя_параметра: значение}"""
        if self.init_cplt is False:
            return self.data
        data = {}
        for param_name, widget in self._widgets.items():
            validator = self._validators.get(param_name)

            if validator and validator in self._GETTERS:
                data[param_name] = self._GETTERS[validator](widget)
            elif isinstance(widget, QCheckBox):
                data[param_name] = widget.isChecked()
            elif isinstance(widget, QComboBox):
                data[param_name] = widget.currentText()
            elif hasattr(widget, 'text'):
                data[param_name] = widget.text()
            elif hasattr(widget, 'value'):
                data[param_name] = widget.value()
        return data

    def set_parameters(self, data: dict) -> None:
        """Устанавливает значения параметров из словаря"""
        self.data = data
        if self.init_cplt is True:
            for param_name, value in data.items():
                if param_name not in self._widgets:
                    continue

                widget = self._widgets[param_name]
                validator = self._validators.get(param_name)

                if validator and validator in self._SETTERS:
                    self._SETTERS[validator](widget, value)
                elif isinstance(widget, QCheckBox):
                    widget.setChecked(bool(value))
                elif isinstance(widget, QComboBox):
                    widget.setCurrentText(str(value))
                elif hasattr(widget, 'setText'):
                    widget.setText(str(value))
                elif hasattr(widget, 'setValue'):
                    widget.setValue(value)