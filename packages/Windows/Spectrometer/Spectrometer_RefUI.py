from PyQt6.QtWidgets import QPushButton, QCheckBox, QFrame, QLabel, QSpinBox
from PyQt6.QtGui import QIcon
from Icon.IconName import *


class SpectrometerRefUI:
    """
    Класс для управления всего, что относится к работе со сканированием в окне SpectrometerWindowClass
    """
    name = "SpectrometerRefUI"

    def __init__(self, frame: QFrame, event_bus=None):
        self.__frame = frame
        self.__event_bus = event_bus
        # Находим виджеты внутри frame
        self.__use_reference = self.__frame.findChild(QCheckBox, "use_reference")
        self.__show_reference = self.__frame.findChild(QCheckBox, "show_reference")

        self.__reference_Button = self.__frame.findChild(QPushButton, "reference_Button")
        self.__load_Button = self.__frame.findChild(QPushButton, "load_Button")
        self.__save_Button = self.__frame.findChild(QPushButton, "save_Button")

        self.__reference_label = self.__frame.findChild(QLabel, "reference_label")

        self.__transparency_spinBox = self.__frame.findChild(QLabel, "transparency_spinBox")

        self.ref_spectrum_param = None
        self.ref_spectrum_dat = None
        self.scanning_flag = False

        self.__init_widget_settings()

    def __init_widget_settings(self):
        self.__reference_Button.clicked.connect(self._start_reference_button_clicked)
        self.__load_Button.clicked.connect(self._load_ref_spectrum)
        self.__save_Button.clicked.connect(self._save_ref_spectrum)

        self.__save_Button.setIcon(QIcon(save_Icon))
        self.__load_Button.setIcon(QIcon(open_Icon))

        self.__use_reference.toggled.connect(self._on_ref_toggled)
        self.__show_reference.toggled.connect(self._on_show_toggled)

        self.label_update()

    def label_update(self):
        """ Обновляем надпись на лайбле, в зависимости от наличия опорного спектра """
        if self.ref_spectrum_dat is None:
            self.__reference_label.setText("Опорный спектр: не задан")
        else:
            self.__reference_label.setText(f"Опорный спектр: задан {min(self.ref_spectrum_dat[0])} нм - {max(self.ref_spectrum_dat[0])} нм")

    def _on_ref_toggled(self):
        """ Нажали на use_reference чек бокс """
        print(f"Используем референс {self.__use_reference.isChecked()}")

    def _on_show_toggled(self):
        """ Нажали на show_reference чек бокс """
        print(f"Показываем референс {self.__show_reference.isChecked()}")

    def _start_reference_button_clicked(self):
        """ Нажата кнопка сканирования """
        if self.scanning_flag:
            self.__stop_removing()
        else:
            self.__start_removing()

    def _save_ref_spectrum(self):
        """ Сохранить опорный спектр """
        print("save")

    def _load_ref_spectrum(self):
        """ Загрузить опорный спектр """
        print("load")

    def __start_removing(self):
        """ Метод класса, который при нажатии на кнопку посылает основному окну emit о том, что кнопка нажата """
        self.__event_bus.SpectrometerUI.emit(self.name, "SpectrometerWindowClass", "start_ref_button", [True])

    def __stop_removing(self):
        """ Метод класса, который при нажатии на кнопку посылает основному окну emit о том, что кнопка отжата """
        self.__event_bus.SpectrometerUI.emit(self.name, "SpectrometerWindowClass", "start_ref_button", [False])

    def setData(self, param, data):
        self.ref_spectrum_param = param
        self.ref_spectrum_dat = data
        self.label_update()

    def start_removing(self):
        """ Публичный метод, который вызывается в случае, если окно подтвердило __start_removing """
        self.scanning_flag = True
        self.__reference_Button.setText("... Снятие спектра ...")

    def stop_removing(self):
        """ Публичный метод, который вызывается в случае, если окно подтвердило __stop_removing """
        self.scanning_flag = False
        self.__reference_Button.setText("Опорный образца")

