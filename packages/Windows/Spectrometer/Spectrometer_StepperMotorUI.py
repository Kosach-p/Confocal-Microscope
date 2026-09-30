from PyQt6.QtWidgets import QPushButton, QCheckBox, QFrame, QLineEdit
from PyQt6.QtGui import QIcon
from Icon.IconName import *

from packages.core.validators.numeric_validator import *


class SpectrometerStepperMotorUI:
    """
    Класс для управления всего, что относится к работе с шаговым мотором в окне SpectrometerWindowClass
    """
    name = "SpectrometerStepperMotorUI"

    def __init__(self, frame: QFrame, Controller=None, event_bus=None):
        name = "stepperMotor_"
        self.__frame = frame
        self.__Controller = Controller
        self.__event_bus = event_bus
        # Находим виджеты внутри frame
        self.__wave_length_LineEdit = self.__frame.findChild(QLineEdit, name + "wave_length")
        self.__step_LineEdit = self.__frame.findChild(QLineEdit, name + "step")
        self.__go_to_LineEdit = self.__frame.findChild(QLineEdit, name + "go_to")

        self.__wave_length_button = self.__frame.findChild(QPushButton, name + "wave_length_button")
        self.__go_to_button = self.__frame.findChild(QPushButton, name + "go_to_button")

        self.__go_minus = self.__frame.findChild(QPushButton, name + "go_minus")
        self.__stop = self.__frame.findChild(QPushButton, name + "stop")
        self.__go_plus = self.__frame.findChild(QPushButton, name + "go_plus")

        self.__hold_CheckBox = self.__frame.findChild(QCheckBox, name + "hold")

        # Инициализация UI
        self.__init_widget_settings()

        # Инициализация класса
        self.__connection_init()

        self.__min_waveLength = 0
        self.__max_waveLength = 0
        self.__waveLength = 0

    def __init_widget_settings(self):
        self.__go_minus.setIcon(QIcon(arrow_left_Icon))
        self.__stop.setIcon(QIcon(stop_Icon))
        self.__go_plus.setIcon(QIcon(arrow_right_Icon))

        for line_edit in self.__frame.findChildren(QLineEdit):
            line_edit.editingFinished.connect(line_edit.clearFocus)
            line_edit.editingFinished.connect(lambda checked=False, line=line_edit: line.setText(calc_str(line.text(), 2)))
            line_edit.setValidator(FloatCalcValidator)

        self.__hold_CheckBox_changed()

    def __connection_init(self):
        """ Подключение триггеров на действия с виджетами """
        self.__wave_length_button.setIcon(QIcon(check_mark_Icon))
        self.__go_to_button.setIcon(QIcon(check_mark_Icon))

        self.__wave_length_button.clicked.connect(self.__waveLength_changed)
        self.__go_to_button.clicked.connect(self.__go_to)

        self.__go_minus.clicked.connect(lambda: self.__button_clicked(-1))
        self.__stop.clicked.connect(lambda: self.__button_clicked(0))
        self.__go_plus.clicked.connect(lambda: self.__button_clicked(1))

        self.__hold_CheckBox.toggled.connect(self.__hold_CheckBox_changed)

        self.__event_bus.StepperMotorControl.connect(self.__event_process)
        self.__event_bus.StepperMotorControl.emit(self.name, "StepperMotorControlClass", "get_current_wave_length", [])

    def __event_process(self, transmitter, receiver, command, data):
        """ Обработчик emit в выбранном канале """
        if transmitter == self.name:
            return

        if receiver == self.name or receiver == "All":
            if command == "current_wave_length" or command == "movement_completed":
                self.__waveLength = data[0]
                self.__widget_update()

    def __waveLength_changed(self):
        """ Выгрузка текущей длины волны из LineEdit"""
        self.__waveLength = float(self.__wave_length_LineEdit.text())
        self.__event_bus.StepperMotorControl.emit(self.name, "StepperMotorControlClass", "waveLength_changed",
                                                  [self.__waveLength])

    def __go_to(self):
        """ Выгрузка целевой длинны волны и движение в неё """
        target_wave_length = float(self.__go_to_LineEdit.text())
        self.__event_bus.StepperMotorControl.emit(self.name, "StepperMotorControlClass", "go_to", [target_wave_length])

    def __button_clicked(self, direction):
        """ При нажатии на кнопку сообщает контроллеру о необходимости сместиться на shift """
        if direction == 0:
            self.__event_bus.StepperMotorControl.emit(self.name, "StepperMotorControlClass", "smooth_stop", [])
        else:
            shift = direction * float(self.__step_LineEdit.text())
            self.__event_bus.StepperMotorControl.emit(self.name, "StepperMotorControlClass", "shift", [shift])

    def __hold_CheckBox_changed(self):
        """ При переключении чекБокса удержания мотора сообщает о его состоянии контроллеру """
        self.__event_bus.StepperMotorControl.emit(self.name, "StepperMotorControlClass", "hold_StepperMotor",
                                                  [self.__hold_CheckBox.isChecked()])

    def __widget_update(self):
        """ Выводит в виджеты актуальные значения """
        self.__wave_length_LineEdit.setText(str(self.__waveLength))

    def set_StepperMotor_param(self, param_list):
        """ Принимает список параметров и загружает их в переменные """
        self.__waveLength = param_list[2]
        self.__widget_update()

    def enable_widgets(self, status):
        """ Блокирует и разблокирует все доступные классу виджеты """
        self.__frame.setEnabled(status)