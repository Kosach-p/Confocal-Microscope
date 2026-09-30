from PyQt6.QtWidgets import QPushButton, QFrame, QLineEdit, QCheckBox
from PyQt6.QtGui import QIcon
from Icon.IconName import *
from packages.core.validators.numeric_validator import *


class LockButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
            QPushButton:focus {outline: none;}
            QPushButton:pressed {
                margin: 0px;
                padding: 0px;
            }
        """)
        self.clicked.connect(self.__change_locked)
        self.locked = False
        self.setFixedSize(30, 26)
        self.setIconSize(self.size())
        self.__change_locked()

    def __change_locked(self):
        if self.locked:
            self.locked = False
            self.setIcon(QIcon(lock_open_Icon))
        else:
            self.locked = True
            self.setIcon(QIcon(lock_Icon))

    @property
    def isLocked(self):
        return self.locked


class GcodeParamUI:
    """
    Класс для управления всего, что относится к работе с параметрами Gcode в окне Gcode
    """
    name = "GcodeParamUI"

    def __init__(self, frame: QFrame, event_bus=None):
        name = "gcode_"
        self.__frame = frame
        self.__event_bus = event_bus

        # Находим виджеты внутри frame
        self.__origin_x_LineEdit = frame.findChild(QLineEdit, name + "origin_x")
        self.__origin_y_LineEdit = frame.findChild(QLineEdit, name + "origin_y")

        self.__scale_x_LineEdit = frame.findChild(QLineEdit, name + "scale_x")
        self.__scale_y_LineEdit = frame.findChild(QLineEdit, name + "scale_y")
        self.__angle_LineEdit = frame.findChild(QLineEdit, name + "angle")
        self.__size_x_LineEdit = frame.findChild(QLineEdit, name + "size_x")
        self.__size_y_LineEdit = frame.findChild(QLineEdit, name + "size_y")
        self.__F_scale_LineEdit = frame.findChild(QLineEdit, name + "F_scale")

        self.__lock = LockButton(frame.findChild(QPushButton, name + "lock_Button"))
        self.__centering = frame.findChild(QPushButton, name + "centering_Button")

        self.__interpolate_fastMove = frame.findChild(QCheckBox, "interpolate_fastMove_checkBox")

        self.__LinesEdit = [self.__origin_x_LineEdit, self.__origin_y_LineEdit, self.__size_x_LineEdit,
                            self.__size_y_LineEdit, self.__F_scale_LineEdit, self.__scale_x_LineEdit,
                            self.__scale_y_LineEdit, self.__angle_LineEdit]
        self.__LinesEdit_val_prev = [0] * len(self.__LinesEdit)

        self.__change_dict = {
            'origin_x': False,
            'origin_y': False,
            'size_x': False,
            'size_y': False,
            'F_scale': False,
            'scale_x': False,
            'scale_y': False,
            'angle': False
        }

        self.__edit_names = ['origin_x', 'origin_y', 'size_x', 'size_y',
                             'F_scale', 'scale_x', 'scale_y', 'angle']

        self.__number_of_LineEdit = len(self.__LinesEdit)
        # Инициализация UI
        self.__init_widget_settings()
        self.set_linesEdit_value()
        self.enable_frame(False)

    def __init_widget_settings(self):
        """ Инициализирует параметры виджетов, такие, как валидаторы для LineEdit """
        for index in range(0, self.__number_of_LineEdit):
            line_edit = self.__LinesEdit[index]
            line_edit.editingFinished.connect(line_edit.clearFocus)
            line_edit.editingFinished.connect(lambda checked=False, line=line_edit: line.setText(calc_str(line.text(), 4)))
            line_edit.setValidator(FloatCalcValidator)

        self.__origin_x_LineEdit.editingFinished.connect(self.__origin_changed)
        self.__origin_y_LineEdit.editingFinished.connect(self.__origin_changed)
        self.__scale_x_LineEdit.editingFinished.connect(lambda: self.__scale_changed("x"))
        self.__scale_y_LineEdit.editingFinished.connect(lambda: self.__scale_changed("y"))
        self.__size_x_LineEdit.editingFinished.connect(lambda: self.__size_changed("x"))
        self.__size_y_LineEdit.editingFinished.connect(lambda: self.__size_changed("y"))
        self.__angle_LineEdit.editingFinished.connect(self.__angle_changed)
        self.__F_scale_LineEdit.editingFinished.connect(self.__F_scale_changed)

        self.__angle_changed()

        self.__centering.clicked.connect(self.__on_centering)
        self.__centering.setFixedSize(30, 26)
        self.__centering.setIconSize(self.__centering.size())
        self.__centering.setIcon(QIcon(centering_Icon))

        self.__event_bus.GcodeUI.connect(self.__event_process)

    def __on_centering(self):
        """ Перемещаем объект в центр """
        self.__event_bus.GcodeUI.emit(self.name, "GcodeProcessorClass", "Gcode_centering", [])

    def __origin_changed(self):
        """ Ориджин изменился """
        self.__event_bus.GcodeUI.emit(self.name, "GcodeProcessorClass", "Gcode_param_changed", [])

    def __angle_changed(self):
        """ Угол поворота изменился """
        angle_val = float(self.__angle_LineEdit.text()) % 360
        self.__angle_LineEdit.setText(str(angle_val))

        self.__event_bus.GcodeUI.emit(self.name, "GcodeProcessorClass", "Gcode_param_changed", [])

    def __scale_changed(self, axe):
        """ Масштаб изменился """
        scale_x_val = float(self.__scale_x_LineEdit.text())
        scale_y_val = float(self.__scale_y_LineEdit.text())

        if abs(scale_x_val) < 1e-3:
            sgn = (scale_x_val >= 0) - (scale_x_val < 0)
            scale_x_val = sgn * 1e-3
            self.__scale_x_LineEdit.setText(f"{sgn * 1e-3:.3f}")

        if abs(scale_y_val) < 1e-3:
            sgn = (scale_y_val >= 0) - (scale_y_val < 0)
            __scale_y_LineEdit = sgn * 1e-3
            self.__scale_y_LineEdit.setText(f"{sgn * 1e-3:.3f}")

        self.__event_bus.GcodeUI.emit(self.name, "GcodeProcessorClass", "Gcode_param_changed", [])

    def __size_changed(self, axe):
        """ Размер изменился """
        self.__event_bus.GcodeUI.emit(self.name, "GcodeProcessorClass", "Gcode_param_changed", [])

    def __F_scale_changed(self):
        """ Скорость изменилась """
        self.__change_dict['F'] = True
        self.__event_bus.GcodeUI.emit(self.name, "GcodeProcessorClass", "Gcode_param_changed", [])

    def __event_process(self, transmitter, receiver, command, data):
        """ Обработчик emit в выбранном канале """
        if transmitter == self.name:
            return

    def set_linesEdit_value(self, lines_edit_val=None):
        """
        Вставляет все значения из списка в LineEdit
        :param lines_edit_val: Список значений |origin_x|origin_y|size_x|size_y|F|scale|angle|
        :return: 
        """
        for index in range(self.__number_of_LineEdit):
            self.__LinesEdit[index].blockSignals(True)
            if lines_edit_val is None:
                self.__LinesEdit[index].setText("")
            else:
                self.__LinesEdit_val_prev[index] = round(lines_edit_val[index], 3)
                self.__LinesEdit[index].setText(f"{round(lines_edit_val[index], 3)}")

            self.__LinesEdit[index].blockSignals(False)

    def get_linesEdit_value(self) -> (dict, dict):
        """
        Возвращает все значения, записанные в LineEdit списком
        :return: Список значений |origin_x|origin_y|size_x|size_y|F|scale_x|scale_y|angle|
        """
        lines_edit_val = dict()

        self.__change_dict = {name: False for name in self.__edit_names}

        for index in range(self.__number_of_LineEdit):
            val = float(self.__LinesEdit[index].text())
            lines_edit_val[self.__edit_names[index]] = val

            if self.__LinesEdit_val_prev[index] != val:
                self.__change_dict[self.__edit_names[index]] = True
                self.__LinesEdit_val_prev[index] = val

        return lines_edit_val, self.__change_dict

    def enable_frame(self, status):
        """ Блокирует корневой фрейм, тем самым делая недоступным все виджеты """
        self.__frame.setEnabled(status)

    @property
    def scaling_isLocked(self):
        return self.__lock.isLocked

    @property
    def interpolate_fastMove(self):
        return self.__interpolate_fastMove.isChecked()
