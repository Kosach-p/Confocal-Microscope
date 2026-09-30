from PyQt6.QtWidgets import QPushButton, QFrame, QLineEdit, QComboBox, QLabel
from PyQt6.QtCore import QTimer
from Icon.IconName import *

from packages.core.validators.numeric_validator import *
# 1317.5 Самая интенсивная частота


class ODMRSpectrometerGeneratorUI:
    """
    Класс для управления всего, что относится к работе с шаговым мотором в окне SpectrometerWindowClass
    """
    name = "ODMRSpectrometerGeneratorUI"

    def __init__(self, frame: QFrame, Controller=None, event_bus=None):
        name = "generator_"
        self.__frame = frame
        self.__Controller = Controller
        self.__event_bus = event_bus
        # Находим виджеты внутри frame
        self.__frq_LineEdit = self.__frame.findChild(QLineEdit, name + "frq_LineEdit")
        self.__connect_btn = self.__frame.findChild(QPushButton, name + "connect_btn")
        self.__COM_comboBox = self.__frame.findChild(QComboBox, name + "COM_comboBox")
        self.__connection_state_label = self.__frame.findChild(QLabel, name + "connection_state_label")

        # Инициализация UI
        self.__init_widget_settings()

    def __init_widget_settings(self):
        self.__COM_comboBox.setStyleSheet(f"QComboBox::down-arrow {{ image: url({arrow_down_Icon}); }}")

        self.__frq_LineEdit.editingFinished.connect(self.__frq_LineEdit.clearFocus)
        self.__frq_LineEdit.editingFinished.connect(lambda checked=False, line=self.__frq_LineEdit: line.setText(calc_str(line.text(), 0)))
        self.__frq_LineEdit.setValidator(FloatCalcValidator)
        self.__frq_LineEdit.editingFinished.connect(self.__frq_changed)

        self.__frq_LineEdit.setText(str(self.__Controller.frq_1_MHZ))

    def __apply_connection_state(self, connected):
        """ Меняет состояние UI в зависимости от статуса подключения к устройству """
        if connected is False:
            self.__event_bus.StatusBar.emit("Удалось подключиться, но нет ответа ❗", 3, "warning")
            self.__connection_state_label.setText("Устройство не подключено ❌")
        elif connected is None:
            self.__event_bus.StatusBar.emit("Не удалось подключиться ❌", 3, "error")
            self.__connection_state_label.setText("Устройство не подключено ❌")
        else:
            self.__event_bus.StatusBar.emit("Успешно подключено ✅", 3, "success")
            self.__connection_state_label.setText("Устройство подключено ✅")
            com_port_list = self.__Controller.com_port_list()
            self.__COM_comboBox.clear()
            self.__COM_comboBox.addItems(com_port_list)
            self.__COM_comboBox.setCurrentText(connected)

    def __frq_changed(self):
        """ Реагирует на изменение частоты в строке ввода """
        target_frq = float(self.__frq_LineEdit.text())
        self.__Controller.set_frq_1_MHZ(target_frq)

    def enable_widgets(self, status):
        """ Блокирует и разблокирует все доступные классу виджеты """
        self.__frame.setEnabled(status)