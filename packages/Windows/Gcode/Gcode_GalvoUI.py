from PyQt6.QtWidgets import QPushButton, QSlider, QComboBox, QFrame, QLineEdit
from packages.Windows.View2D.AxeBlockUI import AxesController
from PyQt6.QtGui import QIcon
from Icon.IconName import *

from PyQt6.QtCore import QTimer
from packages.core.units.UnitManager import *


class GcodeGalvoUI:
    """
    Класс для управления всего, что относится к работе с гальвосканером в окне Gcode
    """
    name = "GcodeGalvoUI"

    def __init__(self, frame: QFrame, Controller=None, event_bus=None):
        name = "galvo"
        self.__frame = frame
        self.__Controller = Controller
        self.__event_bus = event_bus
        
        # Находим виджеты внутри frame
        self.__x_label = UnitLineEdit(frame.findChild(QLineEdit, name + "_x_label"), device=name)
        self.__y_label = UnitLineEdit(frame.findChild(QLineEdit, name + "_y_label"), device=name)

        self.scan_start = frame.findChild(QPushButton, name + "_scan_start")
        self.__go_y_plus = frame.findChild(QPushButton, name + "_go_y_plus")
        self.__go_x_plus = frame.findChild(QPushButton, name + "_go_x_plus")
        self.__go_y_minus = frame.findChild(QPushButton, name + "_go_y_minus")
        self.__go_x_minus = frame.findChild(QPushButton, name + "_go_x_minus")
        self.__go_home = frame.findChild(QPushButton, name + "_go_home")

        self.__x_slider = frame.findChild(QSlider, name + "_x_slider")
        self.__y_slider = frame.findChild(QSlider, name + "_y_slider")

        self.__step_to_go = frame.findChild(QComboBox, name + "_step_to_go")

        self.__TIM_Init()

        # Инициализация UI
        self.__init_widget_settings()
        AxesBorder = self.__Controller.AxesBorder
        # Создание объектов классов управления UI
        self.axes = AxesController([self.__x_label, self.__y_label], [self.__x_slider, self.__y_slider],
                                [self.__go_x_plus, self.__go_y_plus], [self.__go_x_minus, self.__go_y_minus],
                                         self.__go_home, AxesBorder, self.__step_to_go)

        self.update()

    def __TIM_Init(self):
        """ Инициализация таймер """
        self.TIM1 = QTimer()
        self.TIM1.timeout.connect(lambda: self.__TIM_Interruption())
        self.TIM1.start(100)

    def __TIM_Interruption(self):
        """ Обработка прерываний по таймеру """
        if self.axes.is_cord_changed():
            self.__event_bus.GalvoControl.emit(self.name, "GalvoControlClass", "set_cord", self.axes.get_cord())

    def __init_widget_settings(self):
        """ Инициализирует параметры виджетов, такие, как иконки кнопок и валидаторы для LineEdit """
        self.__go_y_plus.setIcon(QIcon(arrow_top_Icon))
        self.__go_x_plus.setIcon(QIcon(arrow_right_Icon))
        self.__go_y_minus.setIcon(QIcon(arrow_down_Icon))
        self.__go_x_minus.setIcon(QIcon(arrow_left_Icon))
        self.__go_home.setIcon(QIcon(home_Icon))

        for line_edit in self.__frame.findChildren(QLineEdit):
            line_edit.editingFinished.connect(line_edit.clearFocus)
            line_edit.editingFinished.connect(lambda checked=False, line=line_edit: line.setText(calc_str(line.text(), 0)))
            line_edit.setValidator(IntCalcValidator)

        self.__event_bus.GalvoControl.connect(self.__event_process)

    def __event_process(self, transmitter, receiver, command, data):
        """ Обработчик emit в выбранном канале """
        if transmitter == self.name:
            return

        if receiver == self.name or receiver == "All":
            if transmitter == "GalvoControlClass":
                if command == "update_AxesBorder":
                    self.update_AxesBorder(data)

                elif command == "update_cord":
                    self.update_cord(data)

    def update(self):
        """ Выполнение действия для сбора информации для обновления виджетов """
        self.__event_bus.GalvoControl.emit(self.name, "GalvoControlClass", "get_cord", [])

    def update_cord(self, cord):
        """ Обновление состояния виджетов осей на новые координаты """
        self.axes.set_cord(cord)

    def stop_scan(self):
        """ Действия при завершении сканирования """
        self.enable_for_scan(True)
        self.__event_bus.GalvoControl.emit(self.name, "GalvoControlClass", "G00", self.axes.get_cord())

    def update_AxesBorder(self, AxesBorder: list):
        """ Обновление границ виджетов осей """
        self.axes.set_AxesBorder(AxesBorder)

    def enable_frame(self, status):
        """ Блокирует корневой фрейм, тем самым делая недоступным все виджеты """
        self.__frame.setEnabled(status)

    def enable_for_scan(self, status):
        """ Блокирует все виджеты, кроме прогресс бара и кнопки сканирования """
        self.axes.enable_widgets(status)
