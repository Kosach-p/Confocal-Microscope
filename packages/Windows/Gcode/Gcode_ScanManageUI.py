from PyQt6.QtWidgets import QPushButton, QFrame, QCheckBox, QProgressBar
from PyQt6.QtGui import QIcon
from Icon.IconName import *


class GcodeScanManageUI:
    """
    Класс для управления всего, что относится к работе с гальвосканером в окне Gcode
    """
    name = "GcodeScanManageUI"

    def __init__(self, frame: QFrame, Controller=None, event_bus=None):
        name = "gcode_"

        self.__frame = frame
        self.__Controller = Controller
        self.__event_bus = event_bus

        # Находим виджеты внутри frame
        self.__loop_checkBox = frame.findChild(QCheckBox, name + "loop_checkBox")
        self.__laser_state_checkBox = frame.findChild(QCheckBox, name + "laser_state_checkBox")

        self.__pause_button = frame.findChild(QPushButton, name + "pause_button")
        self.__stop_button = frame.findChild(QPushButton, name + "stop_button")
        self.__start_button = frame.findChild(QPushButton, name + "start_button")

        self.__progressBar = frame.findChild(QProgressBar, name + "progressBar")

        # Инициализация UI
        self.__init_widget_settings()

    def __init_widget_settings(self):
        """ Инициализирует параметры виджетов, такие, как иконки кнопок и прерывания от них """
        self.__pause_button.setIcon(QIcon(pause_Icon))
        self.__stop_button.setIcon(QIcon(stop_Icon))
        self.__start_button.setIcon(QIcon(play_Icon))

        self.__pause_button.clicked.connect(lambda: self.__event_bus.GcodeUI.emit(self.name, "GcodeWindowClass", "pause", [True]))
        self.__stop_button.clicked.connect(lambda: self.__event_bus.GcodeUI.emit(self.name, "GcodeWindowClass", "stop", [True]))
        self.__start_button.clicked.connect(lambda: self.__event_bus.GcodeUI.emit(self.name, "GcodeWindowClass", "start", [True]))

        self.__laser_state_checkBox.toggled.connect(self.__laser_state_checkBox_changed)

        self.__event_bus.GalvoControl.connect(self.__event_process)

    def __event_process(self, transmitter, receiver, command, data):
        """ Обработчик emit в выбранном канале """
        if transmitter == self.name:
            return
        pass

    def __laser_state_checkBox_changed(self):
        """ При изменении CheckBox, контроллеру гальвосканера посылается сигнал о включении (выключении) лазера  """
        if self.__laser_state_checkBox.isChecked():
            self.__event_bus.GalvoControl.emit(self.name, "GalvoControlClass", "M3", [])
        else:
            self.__event_bus.GalvoControl.emit(self.name, "GalvoControlClass", "M5", [])

    def enable_frame(self, status):
        """ Блокирует корневой фрейм, тем самым делая недоступным все виджеты """
        self.__frame.setEnabled(status)

    def is_looped(self):
        """ Метод возващает состояние checkBox о том, включено ли зацикливание Gcode """
        return self.__loop_checkBox.isChecked()

    def progressBar_setValue(self, Value):
        """ Устанавливает значение прогресс бара """
        self.__progressBar.setValue(int(Value))

    def progressBar_Value(self):
        """ Устанавливает значение прогресс бара """
        return self.__progressBar.value()

    def laser_checkBox_set(self, state):
        self.__laser_state_checkBox.setChecked(state)

