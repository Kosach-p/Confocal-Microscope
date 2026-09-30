from PyQt6.QtWidgets import QPushButton, QSlider, QProgressBar, QComboBox, QFrame, QLineEdit, QCheckBox
from packages.Windows.View2D.AxeBlockUI import AxesController
from packages.Windows.View2D.ScanBlockUI import ScanAxesParamController
from PyQt6.QtGui import QIcon
from Icon.IconName import *

from packages.core.units.UnitManager import *


class View2DPiezoUI:
    """
    Класс для управления всего, что относится к работе с гальвосканером в окне view2D
    """
    name = "View2DPiezoUI"

    def __init__(self, frame: QFrame, Controller=None, event_bus=None):
        self.__frame = frame
        self.__Controller = Controller
        self.__event_bus = event_bus
        name = "piezo"

        # Оборачиваем все label, в названии которых есть UnitLabel, в особый класс, который меняет единицы измерения
        for label in frame.findChildren(QLabel):
            if "UnitLabel" in label.objectName():
                label = UnitLabel(label, device=name)

        # Находим виджеты внутри frame
        self.progressive_scan_checkBox = frame.findChild(QCheckBox, name + "_progressive_scan_checkBox")
        self.scan_x0 = UnitLineEdit(frame.findChild(QLineEdit, name + "_scan_x0"), device=name)
        self.scan_y0 = UnitLineEdit(frame.findChild(QLineEdit, name + "_scan_y0"), device=name)
        self.scan_z0 = UnitLineEdit(frame.findChild(QLineEdit, name + "_scan_z0"), device=name)
        self.scan_size_x = UnitLineEdit(frame.findChild(QLineEdit, name + "_scan_size_x"), device=name)
        self.scan_size_y = UnitLineEdit(frame.findChild(QLineEdit, name + "_scan_size_y"), device=name)
        self.scan_size_z = UnitLineEdit(frame.findChild(QLineEdit, name + "_scan_size_z"), device=name)
        self.scan_step_x = UnitLineEdit(frame.findChild(QLineEdit, name + "_scan_step_x"), device=name)
        self.scan_step_y = UnitLineEdit(frame.findChild(QLineEdit, name + "_scan_step_y"), device=name)
        self.scan_step_z = UnitLineEdit(frame.findChild(QLineEdit, name + "_scan_step_z"), device=name)
        self.scan_accum_time = frame.findChild(QLineEdit, name + "_scan_accum_time")

        self.x_label = UnitLineEdit(frame.findChild(QLineEdit, name + "_x_label"))
        self.y_label = UnitLineEdit(frame.findChild(QLineEdit, name + "_y_label"))
        self.z_label = UnitLineEdit(frame.findChild(QLineEdit, name + "_z_label"))

        self.scan_start = frame.findChild(QPushButton, name + "_scan_start")
        self.go_z_plus = frame.findChild(QPushButton, name + "_go_z_plus")
        self.go_y_plus = frame.findChild(QPushButton, name + "_go_y_plus")
        self.go_x_plus = frame.findChild(QPushButton, name + "_go_x_plus")
        self.go_z_minus = frame.findChild(QPushButton, name + "_go_z_minus")
        self.go_y_minus = frame.findChild(QPushButton, name + "_go_y_minus")
        self.go_x_minus = frame.findChild(QPushButton, name + "_go_x_minus")
        self.go_home = frame.findChild(QPushButton, name + "_go_home")

        self.x_slider = frame.findChild(QSlider, name + "_x_slider")
        self.y_slider = frame.findChild(QSlider, name + "_y_slider")
        self.z_slider = frame.findChild(QSlider, name + "_z_slider")

        self.progressBar = frame.findChild(QProgressBar, name + "_progressBar")
        self.step_to_go = frame.findChild(QComboBox, name + "_step_to_go")

        self.step_to_go.setStyleSheet(f"QComboBox::down-arrow {{ image: url({arrow_down_Icon}); }}")

        # Инициализация UI
        self.__init_widget_settings()

        # Создание объектов классов управления UI
        self.axes = AxesController([self.x_label, self.y_label, self.z_label], [self.x_slider, self.y_slider, self.z_slider],
                                [self.go_x_plus, self.go_y_plus, self.go_z_plus], [self.go_x_minus, self.go_y_minus, self.go_z_minus],
                                         self.go_home,[[0, 4095], [0, 4095], [0, 4095]], self.step_to_go)

        self.scan = ScanAxesParamController(
            axes_config={
                'x': [self.scan_x0, self.scan_size_x, self.scan_step_x],
                'y': [self.scan_y0, self.scan_size_y, self.scan_step_y],
                'z': [self.scan_z0, self.scan_size_z, self.scan_step_z]
            },
            borders={'x': [0, 4095], 'y': [0, 4095], 'z': [0, 4095], 'accum': [1, 1000]},
            accum_time_lineedit=self.scan_accum_time,
            button=self.scan_start,
            progress_bar=self.progressBar,
            progressive_scan_checkbox=self.progressive_scan_checkBox
        )

    def __init_widget_settings(self):
        """ Инициализирует параметры виджетов, такие, как иконки кнопок и валидаторы для LineEdit """
        self.go_z_plus.setIcon(QIcon(arrow_top_Icon))
        self.go_y_plus.setIcon(QIcon(arrow_top_Icon))
        self.go_x_plus.setIcon(QIcon(arrow_right_Icon))
        self.go_z_minus.setIcon(QIcon(arrow_down_Icon))
        self.go_y_minus.setIcon(QIcon(arrow_down_Icon))
        self.go_x_minus.setIcon(QIcon(arrow_left_Icon))
        self.go_home.setIcon(QIcon(home_Icon))

        for line_edit in self.__frame.findChildren(QLineEdit):
            line_edit.editingFinished.connect(line_edit.clearFocus)
            line_edit.editingFinished.connect(lambda checked=False, line=line_edit: line.setText(calc_str(line.text(), 0)))
            line_edit.setValidator(IntCalcValidator)
            
        self.__event_bus.PiezoControl.connect(self.__event_process)

    def __event_process(self, transmitter, receiver, command, data):
        """ Обработчик emit в выбранном канале """
        if transmitter == self.name:
            return

        if receiver == self.name or receiver == "All":
            if transmitter == "PiezoControlClass":
                if command == "update_AxesBorder":
                    self.update_AxesBorder(data)

                elif command == "update_cord":
                    self.update_cord(data)

    def update(self):
        """ Выполнение действия для сбора информации для обновления виджетов """
        self.__event_bus.PiezoControl.emit(self.name, "PiezoControlClass", "get_cord", [])

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

    def get_scan_param(self):
        """ Возвращает параметры сканирования в виде объекта класса ScanParam """
        return self.scan.get_scan_param()

    def progressBar_setValue(self, Value):
        """ Устанавливает значение прогресс бара """
        self.scan.progressBar_setValue(Value=Value)
