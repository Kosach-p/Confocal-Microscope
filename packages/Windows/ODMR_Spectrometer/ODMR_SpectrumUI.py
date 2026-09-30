from PyQt6.QtWidgets import QPushButton, QCheckBox, QFrame, QProgressBar, QLineEdit

from packages.core.units.UnitManager import *


class ODMRSpectrometerSpectrumUI:
    """
    Класс для управления всего, что относится к работе со сканированием в окне ODMRSpectrometerWindowClass
    """
    name = "ODMRSpectrometerSpectrumUI"

    def __init__(self, frame: QFrame, event_bus=None):
        self.__frame = frame
        self.__event_bus = event_bus
        name = "ODMR_spectrum_"
        device = "Spectrometer"

        for label in frame.findChildren(QLabel):
            if "UnitLabel" in label.objectName():
                UnitLabel(label, device=device)

        # Находим виджеты внутри frame
        self.__left_edge_LineEdit = self.__frame.findChild(QLineEdit, name + "left_edge")
        self.__right_edge_LineEdit = self.__frame.findChild(QLineEdit, name + "right_edge")
        self.__step_LineEdit = self.__frame.findChild(QLineEdit, name + "step")
        self.__accum_time_LineEdit = self.__frame.findChild(QLineEdit, name + "accum_time")
        self.__number_repeat_LineEdit = self.__frame.findChild(QLineEdit, name + "number_repeat")

        self.__random_scan = self.__frame.findChild(QCheckBox, "random_checkBox")
        self.__start_button = self.__frame.findChild(QPushButton, name + "button")

        self.__progressBar = self.__frame.findChild(QProgressBar, name + "progressBar")

        self.__LinesEdit = [self.__left_edge_LineEdit, self.__right_edge_LineEdit, self.__step_LineEdit, self.__accum_time_LineEdit, self.__number_repeat_LineEdit]
        self.__number_of_LineEdit = len(self.__LinesEdit)

        self.__scan_parameters = list(range(self.__number_of_LineEdit))

        self.scanning_flag = False
        # Инициализация UI
        self.__init_widget_settings()

        # Инициализация класса
        self.__lineEdit_changed()

    def __init_widget_settings(self):
        self.__start_button.clicked.connect(self.__start_button_clicked)

        for index in range(self.__number_of_LineEdit - 2):
            self.__LinesEdit[index].editingFinished.connect(self.__LinesEdit[index].clearFocus)
            self.__LinesEdit[index].editingFinished.connect(
                lambda checked=False, line=self.__LinesEdit[index]: line.setText(calc_str(line.text(), 2)))
            self.__LinesEdit[index].setValidator(FloatCalcValidator)

        for index in range(self.__number_of_LineEdit - 2, self.__number_of_LineEdit):
            self.__LinesEdit[index].editingFinished.connect(self.__LinesEdit[index].clearFocus)
            self.__LinesEdit[index].editingFinished.connect(
                lambda checked=False, line=self.__LinesEdit[index]: line.setText(calc_str(line.text(), 0)))
            self.__LinesEdit[index].setValidator(IntCalcValidator)

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
            self.__scan_parameters[index] = int(self.__LinesEdit[index].text())

        self.__check_scan_parameters()
        self.__update_widget()

    def __check_scan_parameters(self):
        """ Проверяем scan_parameters на соответствие требованиям (не завершено) """
        self.__scan_parameters[0] = min(self.__scan_parameters[0], self.__scan_parameters[1])
        self.__scan_parameters[2] = min(self.__scan_parameters[1] - self.__scan_parameters[0], self.__scan_parameters[2])
        if self.__scan_parameters[2] == 0:
            self.__scan_parameters[2] = 1

    def __update_widget(self):
        for index in range(0, self.__number_of_LineEdit):
            self.__LinesEdit[index].setText(str(self.__scan_parameters[index]))

    def __start_button_clicked(self):
        """ Нажата кнопка сканирования """
        if self.scanning_flag:
            self.__stop_removing()
        else:
            self.__start_removing()

    def __start_reference_button_clicked(self):
        """ Нажата кнопка сканирования """
        if self.scanning_flag:
            self.__stop_removing()
        else:
            self.__start_removing()

    def __start_removing(self):
        """ Метод класса, который при нажатии на кнопку посылает основному окну emit о том, что кнопка нажата """
        self.__event_bus.ODMRSpectrometerUI.emit(self.name, "ODMRSpectrometerWindowClass", "start_button", [True])

    def __stop_removing(self):
        """ Метод класса, который при нажатии на кнопку посылает основному окну emit о том, что кнопка отжата """
        self.__event_bus.ODMRSpectrometerUI.emit(self.name, "ODMRSpectrometerWindowClass", "start_button", [False])

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
        self.__update_widget()

    def progressBar_setValue(self, Value):
        """ Устанавливает значение прогресс бара """
        self.__progressBar.setValue(int(max(0, min(100, Value))))

    def enable_widgets(self, status):
        """ Блокирует и разблокирует все доступные классу виджеты """

    @property
    def random_scan(self):
        return self.__random_scan.isChecked()
