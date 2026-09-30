import math

from PyQt6.QtWidgets import QPushButton, QCheckBox, QFrame, QProgressBar, QLineEdit

from packages.core.units.UnitManager import *


class SpectrometerSpectrumUI:
    """
    Класс для управления всего, что относится к работе со сканированием в окне SpectrometerWindowClass
    """
    name = "SpectrometerSpectrumUI"

    def __init__(self, frame: QFrame, event_bus=None, name="spectrum_"):

        self.__frame = frame
        self.__event_bus = event_bus
        name = "spectrum_"
        device = "Spectrometer"

        for label in frame.findChildren(QLabel):
            if "UnitLabel" in label.objectName():
                UnitLabel(label, device=device)

        self.MAX_speed = None
        self.MIN_speed = None
        self.accel_per_sec = None

        # Находим виджеты внутри frame
        self.__left_edge_LineEdit = self.__frame.findChild(QLineEdit, name + "left_edge")
        self.__right_edge_LineEdit = self.__frame.findChild(QLineEdit, name + "right_edge")
        self.__step_LineEdit = self.__frame.findChild(QLineEdit, name + "step")
        self.__accum_time_LineEdit = self.__frame.findChild(QLineEdit, name + "accum_time")
        self.__number_repeat_LineEdit = self.__frame.findChild(QLineEdit, name + "number_repeat")

        self.__fast_mode_scan = self.__frame.findChild(QCheckBox, name + "fast_mode_scan")
        self.__start_button = self.__frame.findChild(QPushButton, name + "button")

        self.__MotorSpeed_label = self.__frame.findChild(QLabel, name + "MotorSpeed")
        self.__WorkTime_label = self.__frame.findChild(QLabel, name + "WorkTime")

        self.__progressBar = self.__frame.findChild(QProgressBar, name + "progressBar")

        self.__LinesEdit = [self.__left_edge_LineEdit, self.__right_edge_LineEdit, self.__step_LineEdit, self.__accum_time_LineEdit, self.__number_repeat_LineEdit]
        self.__number_of_LineEdit = len(self.__LinesEdit)

        self.__scan_parameters = list(range(self.__number_of_LineEdit))

        self.scanning_flag = False
        # Инициализация UI
        self.__init_widget_settings()

        # Инициализация класса
        self.__lineEdit_changed()
        self.__event_bus.StepperMotorControl.connect(self.__event_process)
        self.__event_bus.SpectrometerUI.emit(self.name, "SpectrometerWindowClass", "get_settings", [])

    def __event_process(self, transmitter, receiver, command, data):
        """ Обработка emit на линии event_bus """
        if transmitter == self.name:
            return
        if receiver == self.name or receiver == "All":
            if transmitter == "StepperMotorControlClass":
                if command == "set_settings":
                    params = data[0]['parameters']
                    self.MAX_speed = params['MAX_speed']
                    self.MIN_speed = params['MIN_speed']
                    self.accel_per_sec = params['accel_per_sec']

    def __init_widget_settings(self):
        self.__start_button.clicked.connect(self.__start_button_clicked)
        for index in range(self.__number_of_LineEdit - 2):
            self.__LinesEdit[index].editingFinished.connect(self.__LinesEdit[index].clearFocus)
            self.__LinesEdit[index].editingFinished.connect(
                lambda checked=False, line=self.__LinesEdit[index]: line.setText(calc_str(line.text(), 2)))
            self.__LinesEdit[index].setValidator(FloatCalcValidator)
            self.__LinesEdit[index].editingFinished.connect(self.__lineEdit_changed)

        for index in range(self.__number_of_LineEdit - 2, self.__number_of_LineEdit):
            self.__LinesEdit[index].editingFinished.connect(self.__LinesEdit[index].clearFocus)
            self.__LinesEdit[index].editingFinished.connect(
                lambda checked=False, line=self.__LinesEdit[index]: line.setText(calc_str(line.text(), 0)))
            self.__LinesEdit[index].setValidator(IntCalcValidator)
            self.__LinesEdit[index].editingFinished.connect(self.__lineEdit_changed)

    def __lineEdit_changed(self):
        """ При вводе данных загружаем их в список скан параметров, проверяем и обновляем LineEdit """
        self.__get_scan_parameters()
        self.__check_scan_parameters()
        self.__update_widget()

    def __get_scan_parameters(self):
        """ Выгружает параметры сканирования в список __scan_parameters из LineEdit"""
        for index in range(0, self.__number_of_LineEdit - 2):
            self.__scan_parameters[index] = float(self.__LinesEdit[index].text())

        for index in range(self.__number_of_LineEdit - 2, self.__number_of_LineEdit):
            self.__scan_parameters[index] = int(float(self.__LinesEdit[index].text()))

    def __check_scan_parameters(self):
        """ Проверяем scan_parameters на соответствие требованиям (не завершено) """
        if not(self.MAX_speed is None or self.MIN_speed is None or self.accel_per_sec is None):
            params = []
            for index in range(0, self.__number_of_LineEdit):
                params.append(self.__scan_parameters[index])

            left_edge, right_edge, step, accum_time, number_repeat = params
            if self.fast_mode_CheckBox_state:
                MotorSpeed = step / (accum_time / 1000)
                if MotorSpeed > self.MAX_speed:
                    self.__scan_parameters[3] = int((step / self.MAX_speed) * 1000)

        if self.__scan_parameters[2] <= 0:
            self.__scan_parameters[2] = 1

    def __update_widget(self):
        params = []
        for index in range(0, self.__number_of_LineEdit):
            params.append(self.__scan_parameters[index])
            self.__LinesEdit[index].setText(str(self.__scan_parameters[index]))

        MotorSpeed = -1
        WorkTime = -1

        if not(self.MAX_speed is None or self.MIN_speed is None or self.accel_per_sec is None):
            left_edge, right_edge, step, accum_time, number_repeat = params
            if self.fast_mode_CheckBox_state:
                WorkTime = (abs(right_edge - left_edge) / step) * (accum_time / 1000)
                MotorSpeed = step / (accum_time / 1000)
            else:
                S_accel = (self.MAX_speed**2 - self.MIN_speed**2) / (2 * self.accel_per_sec)
                step_time = 0
                if step >= S_accel:
                    step_time = (self.MAX_speed - self.MIN_speed) / self.accel_per_sec + (step - S_accel) / self.MAX_speed
                else:
                    MAX = ((self.MIN_speed**2) + (2 * self.accel_per_sec * step))**0.5
                    if MAX >= self.MIN_speed:
                        step_time = (MAX - self.MIN_speed) / self.accel_per_sec
                    else:
                        step_time = step / self.MIN_speed
                step_time += (accum_time / 1000)

                WorkTime = (abs(right_edge - left_edge) / step) * step_time
                MotorSpeed = step / step_time

        self.__MotorSpeed_label.setText(f"{MotorSpeed:.2f} нм/с")
        self.__WorkTime_label.setText(f"{WorkTime:.1f} сек")

    def __start_button_clicked(self):
        """ Нажата кнопка сканирования """
        if self.scanning_flag:
            self.__stop_removing()
        else:
            self.__start_removing()

    def __start_removing(self):
        """ Метод класса, который при нажатии на кнопку посылает основному окну emit о том, что кнопка нажата """
        self.__event_bus.SpectrometerUI.emit(self.name, "SpectrometerWindowClass", "start_button", [True])

    def __stop_removing(self):
        """ Метод класса, который при нажатии на кнопку посылает основному окну emit о том, что кнопка отжата """
        self.__event_bus.SpectrometerUI.emit(self.name, "SpectrometerWindowClass", "start_button", [False])

    def start_removing(self):
        """ Публичный метод, который вызывается в случае, если окно подтвердило __start_removing """
        self.__get_scan_parameters()

        self.scanning_flag = True
        self.__start_button.setText("... Снятие спектра ...")
        self.progressBar_setValue(0)

    def stop_removing(self):
        """ Публичный метод, который вызывается в случае, если окно подтвердило __stop_removing """
        self.scanning_flag = False
        self.__start_button.setText("Спектр образца")
        self.progressBar_setValue(100)

    def get_scan_param(self):
        """ Публичный метод, возвращающий список параметров сканирования """
        self.__get_scan_parameters()
        return self.__scan_parameters

    def set_scan_param(self, scan_parameters):
        """ Публичный метод для загрузки списка параметров сканирования """
        self.__scan_parameters = scan_parameters
        self.__check_scan_parameters()
        self.__update_widget()

    def progressBar_setValue(self, Value):
        """ Устанавливает значение прогресс бара """
        self.__progressBar.setValue(int(max(0, min(100, Value))))

    def enable_widgets(self, status):
        """ Блокирует и разблокирует все доступные классу виджеты """

    @property
    def fast_mode_CheckBox_state(self):
        return self.__fast_mode_scan.isChecked()
