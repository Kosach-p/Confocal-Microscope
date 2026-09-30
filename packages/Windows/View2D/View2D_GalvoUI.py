from PyQt6.QtWidgets import QPushButton, QSlider, QProgressBar, QComboBox, QFrame, QLineEdit, QCheckBox, QGridLayout
from packages.Windows.View2D.AxeBlockUI import AxesController
from packages.Windows.View2D.ScanBlockUI import ScanAxesParamController
from PyQt6.QtGui import QIcon
from Icon.IconName import *
from packages.core.widgets.QLineEdit import DragButtonNumberInputStatic
from packages.Controllers.controllers_config import UNITS
from PyQt6.QtCore import QTimer
from packages.core.widgets.DataInAreaBuilder import DataInAreaBuilder
from PyQt6.QtCore import Qt
from packages.core.units.UnitManager import *


class View2DGalvoUI:
    """
    Класс для управления всего, что относится к работе с гальвосканером в окне view2D
    """
    name = "View2DGalvoUI"

    def __init__(self, frame: QFrame, Controller=None, event_bus=None):
        name = "galvo"
        self.__frame = frame
        self.__Controller = Controller
        self.__event_bus = event_bus

        # Оборачиваем все label, в названии которых есть UnitLabel, в особый класс, который меняет единицы измерения
        for label in frame.findChildren(QLabel):
            if "UnitLabel" in label.objectName():
                label = UnitLabel(label, device=name)

        # Находим виджеты внутри frame
        BeamScanGridLayout = frame.findChild(QGridLayout, "BeamScanGridLayout")

        self.progressive_scan_checkBox = frame.findChild(QCheckBox, name + "_progressive_scan_checkBox")
        self.scan_x0 = DragButtonNumberInputStatic(label='X', units_set_name='beam_steerers', units_set=UNITS)
        self.scan_y0 = DragButtonNumberInputStatic(label='Y', units_set_name='beam_steerers', units_set=UNITS)
        self.scan_z0 = DragButtonNumberInputStatic(label='Z', units_set_name='beam_steerers', units_set=UNITS)
        self.scan_size_x = DragButtonNumberInputStatic(label='X', units_set_name='beam_steerers', units_set=UNITS)
        self.scan_size_y = DragButtonNumberInputStatic(label='Y', units_set_name='beam_steerers', units_set=UNITS)
        self.scan_size_z = DragButtonNumberInputStatic(label='Z', units_set_name='beam_steerers', units_set=UNITS)
        self.scan_step_x = DragButtonNumberInputStatic(label='X', units_set_name='beam_steerers', units_set=UNITS)
        self.scan_step_y = DragButtonNumberInputStatic(label='Y', units_set_name='beam_steerers', units_set=UNITS)
        self.scan_step_z = DragButtonNumberInputStatic(label='Z', units_set_name='beam_steerers', units_set=UNITS)
        self.scan_accum_time = DragButtonNumberInputStatic(label='', units_set_name='time', units_set=UNITS, alignment='center')

        label = QLabel(text='Начало')
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        BeamScanGridLayout.addWidget(label, 0, 0)

        label = QLabel(text='Конец')
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        BeamScanGridLayout.addWidget(label, 0, 1)

        label = QLabel(text='Шаг')
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        BeamScanGridLayout.addWidget(label, 0, 2)

        BeamScanGridLayout.addWidget(self.scan_x0, 1, 0)
        BeamScanGridLayout.addWidget(self.scan_y0, 2, 0)
        BeamScanGridLayout.addWidget(self.scan_z0, 3, 0)
        BeamScanGridLayout.addWidget(self.scan_size_x, 1, 1)
        BeamScanGridLayout.addWidget(self.scan_size_y, 2, 1)
        BeamScanGridLayout.addWidget(self.scan_size_z, 3, 1)
        BeamScanGridLayout.addWidget(self.scan_step_x, 1, 2)
        BeamScanGridLayout.addWidget(self.scan_step_y, 2, 2)
        BeamScanGridLayout.addWidget(self.scan_step_z, 3, 2)

        label = QLabel(text='Время')
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        BeamScanGridLayout.addWidget(label, 4, 1)
        BeamScanGridLayout.addWidget(self.scan_accum_time, 5, 1)

        self.__x_label = UnitLineEdit(frame.findChild(QLineEdit, name + "_x_label"), device=name)
        self.__y_label = UnitLineEdit(frame.findChild(QLineEdit, name + "_y_label"), device=name)

        self.scan_start = frame.findChild(QPushButton, name + "_scan_start")
        self.go_y_plus = frame.findChild(QPushButton, name + "_go_y_plus")
        self.go_x_plus = frame.findChild(QPushButton, name + "_go_x_plus")
        self.go_y_minus = frame.findChild(QPushButton, name + "_go_y_minus")
        self.go_x_minus = frame.findChild(QPushButton, name + "_go_x_minus")
        self.go_home = frame.findChild(QPushButton, name + "_go_home")

        self.__x_slider = frame.findChild(QSlider, name + "_x_slider")
        self.__y_slider = frame.findChild(QSlider, name + "_y_slider")

        self.__progressBar = frame.findChild(QProgressBar, name + "_progressBar")
        self.__step_to_go = frame.findChild(QComboBox, name + "_step_to_go")

        self.__step_to_go.setStyleSheet(f"QComboBox::down-arrow {{ image: url({arrow_down_Icon}); }}")

        self.__TIM_Init()
        

    
    def __TIM_Init(self):
        """ Инициализация таймер """
        self.TIM1 = QTimer()
        self.TIM1.timeout.connect(lambda: self.__TIM_Interruption())
        self.TIM1.start(100)

    def __TIM_Interruption(self):
        """ Обработка прерываний по таймеру """
        if self.__event_bus.ProgramBusy:
            if self.is_waiting_scan_stop():
                self.__event_bus.View2DUI.emit(self.name, "View2DClass", "scan_stop", [])

        else:
            if self.axes.is_cord_changed():
                self.__event_bus.GalvoControl.emit(self.name, "GalvoControlClass", "set_cord", self.axes.get_cord())
            elif self.is_waiting_scan_start():
                self.__event_bus.View2DUI.emit(self.name, "View2DClass", "scan_start", [])
            
    def __init_widget_settings(self):
        """ Инициализирует параметры виджетов, такие, как иконки кнопок и валидаторы для LineEdit """
        self.go_y_plus.setIcon(QIcon(arrow_top_Icon))
        self.go_x_plus.setIcon(QIcon(arrow_right_Icon))
        self.go_y_minus.setIcon(QIcon(arrow_down_Icon))
        self.go_x_minus.setIcon(QIcon(arrow_left_Icon))
        self.go_home.setIcon(QIcon(home_Icon))

        for line_edit in self.__frame.findChildren(QLineEdit):
            line_edit.editingFinished.connect(line_edit.clearFocus)
            line_edit.editingFinished.connect(lambda checked=False, line=line_edit: line.setText(calc_str(line.text(), 0)))

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

    def update_AxesBorder(self, AxesBorder: list):
        """ Обновление границ виджетов осей """
        self.axes.set_AxesBorder(AxesBorder)

    def enable_frame(self, status):
        """ Блокирует корневой фрейм, тем самым делая недоступным все виджеты """
        self.__frame.setEnabled(status)

    def enable_for_scan(self, status):
        """ Блокирует все виджеты, кроме прогресс бара и кнопки сканирования """
        self.axes.enable_widgets(status)
        self.scan.enable_widgets(status)

    def is_waiting_scan_start(self):
        """ Возвращает флаг об ожидании начала сканирования """
        return self.scan.waiting_scan_start

    def is_waiting_scan_stop(self):
        """ Возвращает флаг об ожидании начала сканирования """
        return self.scan.waiting_scan_stop

    def reset_waiting_scan_start(self):
        """ Очистить флаг об ожидании начала сканирования """
        self.scan.waiting_scan_start = False

    def reset_waiting_scan_stop(self):
        """ Очистить флаг об ожидании окончания сканирования """
        self.scan.waiting_scan_stop = False
    
    def start_scan(self):
        """ Действия при начале сканирования """
        self.reset_waiting_scan_start()

        self.enable_for_scan(False)
        self.progressBar_setValue(0)

    def stop_scan(self):
        """ Действия при завершении сканирования """
        self.reset_waiting_scan_stop()

        self.enable_for_scan(True)
        self.progressBar_setValue(100)
        self.scan.button_status_reset()
        self.__event_bus.GalvoControl.emit(self.name, "GalvoControlClass", "set_cord", self.axes.get_cord())

    def get_scan_param(self):
        """ Возвращает параметры сканирования в виде объекта класса ScanParam """
        return self.scan.get_scan_param()

    def set_scan_param(self, scan_parameters):
        """ Устанавливает параметры сканирования """
        self.scan.set_scan_param(scan_parameters)

    def progressBar_setValue(self, Value):
        """ Устанавливает значение прогресс бара """
        self.scan.progressBar_setValue(Value=Value)



