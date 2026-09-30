import time

import numpy as np
import pygcode
from packages.core.widgets.gcode_chart import GcodeChart
from packages.Windows.Gcode.Gcode_ParamUI import GcodeParamUI
from packages.Windows.Gcode.Gcode_Statistics import GcodeStatisticClass


class GcodeParser:
    def __init__(self):
        self.__handlers = {
            # Системные команды
            pygcode.gcodes.GCodeAbsoluteDistanceMode: self.handle_absolute_mode,
            pygcode.gcodes.GCodeIncrementalDistanceMode: self.handle_incremental_mode,

            # Команды движения
            pygcode.gcodes.GCodeRapidMove: self.handle_fast_move,  # G00
            pygcode.gcodes.GCodeLinearMove: self.handle_slow_move,  # G01

            # Команды управления шпинделем/лазером
            pygcode.gcodes.GCodeStartSpindleCW: self.handle_spindle_start,  # M03
            pygcode.gcodes.GCodeStopSpindle: self.handle_spindle_stop,  # M05
            pygcode.gcodes.GCodeSpindleSpeed: self.handle_spindle_speed,  # S (интенсивность лазера)

            # Команды управления подачей
            pygcode.gcodes.GCodeFeedRate: self.handle_feedrate,  # F

            # Команды ожидания
            pygcode.gcodes.GCodeDwell: self.handle_dwell,  # G04
        }

        self.__command_list_orig = list()
        self.__cord_list = list()
        self.__F_list = list()
        self.__Incremental_mode = False

        self.__X = 0
        self.__Y = 0
        self.__Z = 0

        self.__color = list()

    def parse_gcode(self, gcode_text):
        """ Парсит Gcode текст в список команд для устройства, список координат для отображения и список скоростей """
        self.__command_list_orig = list()
        self.__cord_list = list()
        self.__F_list = list()

        self.__X = 0
        self.__Y = 0
        self.__Z = 0

        self.__Incremental_mode = False

        for text_line in gcode_text:
            # Если это стандарт Gcode, где не ставится G01 и G00, ставим их самостоятельно
            if text_line.startswith("X") or text_line.startswith("Y") or text_line.startswith("Z"):
                text_line = "G01 " + text_line

            line = pygcode.Line(text_line)
            if len(line.block.gcodes) != 0:
                for block in reversed(line.block.gcodes):
                    handler = self.__handlers.get(type(block))
                    if handler:
                        handler(block)

        return self.__command_list_orig, self.__cord_list, self.__F_list, self.__color

    def get_handle_list(self):
        return self.__handlers

    def handle_absolute_mode(self, block):
        """ Преобразование строки Gcode к стандартизированному формату команды """
        self.__Incremental_mode = False

    def handle_incremental_mode(self, block):
        """ Преобразование строки Gcode к стандартизированному формату команды """
        self.__Incremental_mode = True

    def handle_fast_move(self, block):
        """ Преобразование строки Gcode к стандартизированному формату команды """
        # Плавное движение G00
        if block.X is not None:
            self.__X = float(self.__Incremental_mode * self.__X + block.X)
        if block.Y is not None:
            self.__Y = float(self.__Incremental_mode * self.__Y + block.Y)

        self.__command_list_orig.append(["G00", self.__X, self.__Y])
        self.__cord_list.append(np.array((self.__X, self.__Y, 1)))
        self.__color.append([0.5, 0.5, 0.5, 1])

    def handle_slow_move(self, block):
        """ Преобразование строки Gcode к стандартизированному формату команды """
        # Плавное движение G01
        if block.X is not None:
            self.__X = float(self.__Incremental_mode * self.__X + block.X)
        if block.Y is not None:
            self.__Y = float(self.__Incremental_mode * self.__Y + block.Y)

        self.__command_list_orig.append(["G01", self.__X, self.__Y])
        self.__cord_list.append(np.array((self.__X, self.__Y, 1)))
        self.__color.append([1, 1, 1, 1])

    def handle_spindle_start(self, block):
        """ Преобразование строки Gcode к стандартизированному формату команды """
        self.__command_list_orig.append(["M03", ])

    def handle_spindle_stop(self, block):
        """ Преобразование строки Gcode к стандартизированному формату команды """
        self.__command_list_orig.append(["M05", ])

    def handle_spindle_speed(self, block):
        """ Преобразование строки Gcode к стандартизированному формату команды """
        self.__command_list_orig.append(["S", float(str(block)[1:])])

    def handle_feedrate(self, block):
        """ Преобразование строки Gcode к стандартизированному формату команды """
        self.__F_list.append(float(str(block)[1:]))
        self.__command_list_orig.append(["F", float(str(block)[1:])])

    def handle_dwell(self, block):
        """ Преобразование строки Gcode к стандартизированному формату команды """
        self.__command_list_orig.append(["G04", block.P])


class GcodeProcessorClass:
    name = "GcodeProcessorClass"

    def __init__(self, chart_frame, param_frame, statistic_frame, F_listWidget, event_bus, galvo_control):
        self.__chart_frame = chart_frame
        self.__param_frame = param_frame
        self.__statistic_frame = statistic_frame
        self.__F_listWidget = F_listWidget
        self.__event_bus = event_bus
        self.__galvo_control = galvo_control
        self.__workspace_size = {'x': self.__galvo_control.parameters_dict['x_max'], 'y': self.__galvo_control.parameters_dict['y_max']}

        self.__gcode_text = list()

        self.__origin_x = 0
        self.__origin_y = 0
        self.__scale_x = 1
        self.__scale_y = 1
        self.__F_scale = 1
        self.__angle = 0

        self.__size_x = 0
        self.__size_y = 0
        self.__workTime = 0

        self.__fileLoaded = False

        self.__gcode_parser = GcodeParser()
        self.__svg2paths = None
        self.__lasy_import()

        self.__Chart = GcodeChart(self.__chart_frame, workspace_size=self.__workspace_size)
        self.__paramUI = GcodeParamUI(self.__param_frame, self.__event_bus)
        self.__Statistic = GcodeStatisticClass(self.__statistic_frame, self.__event_bus)

        # Исходные
        self.__command_list_orig = list()
        self.__cord_array_orig = None
        self.__F_array_orig = None

        # Модифицированные
        self.__command_list_mod = list()
        self.__cord_array_mod = None
        self.__F_array_mod = None

        self.__command_list_index = 0
        self.__command_buffer = None
        self.__movement_prev = [0, 0]
        self.__direction_prev = [0, 0]
        self.__OneWay_disp = [0, 0]

        self.__event_bus.GcodeUI.connect(self.__event_process)

    def __lasy_import(self):
        from svgpathtools import svg2paths
        self.__svg2paths = svg2paths

    def __event_process(self, transmitter, receiver, command, data):
        """ Обработчик emit в выбранном канале """
        if transmitter == self.name:
            return

        if receiver == self.name or receiver == "All":
            if command == "Gcode_param_changed":
                self.__Gcode_param_changed()

            if command == "Gcode_centering":
                self.__Gcode_centering()

    def gcode_output(self, cord):
        """ Выводит координаты массивом для C """
        print("double FF[][3] = {")

        for point in cord:
            print(f"{{{point[0] / np.max(cord) - 0.5}, {point[1] / np.max(cord)- 0.5}, {int(point[2])}}},")
            point[2] = 1

        print("};")
        return cord

    def load_gcode_file(self, path):
        """ Загрузка текста gcode файла в память объекта """
        a = time.time()
        with open(path, 'r', encoding='utf-8') as file:
            self.__gcode_text = file.readlines()
        self.__scale_x = 1
        self.__scale_y = 1
        self.__F_scale = 1
        self.__angle = 0

        self.__command_list_orig, cord_list, F_list, color = self.__gcode_parser.parse_gcode(self.__gcode_text)
        #self.gcode_output(cord_list)

        self.__cord_array_orig = np.array(cord_list)
        self.__F_array_orig = np.array(F_list)

        self.__command_list_mod = self.__command_list_orig
        self.__cord_array_mod = np.copy(self.__cord_array_orig)
        self.__F_array_mod = np.copy(self.__F_array_orig)
        self.__Chart.show_data(self.__cord_array_mod[:, 0], self.__cord_array_mod[:, 1], color)
        self.__calc_gcode_param()

        self.__fileLoaded = True
        self.__paramUI.enable_frame(True)

        return self.__gcode_text

    def read_svg_file(self, path, max_x=50000, max_y=50000, speed=50, samples_per_segment=1):
        paths, attributes = self.__svg2paths(path)

        # Находим границы SVG
        all_points = []
        for path in paths:
            for segment in path:
                for t in np.linspace(0, 1, samples_per_segment):
                    point = segment.point(t)
                all_points.append((point.real, point.imag))

        # Находим min/max координаты
        points_array = np.array(all_points)
        min_x, min_y = np.min(points_array, axis=0)
        max_svg_x, max_svg_y = np.max(points_array, axis=0)

        # Масштабируем коэффициенты
        scale_x = max_x / (max_svg_x - min_x) if (max_svg_x - min_x) > 0 else 1
        scale_y = max_y / (max_svg_y - min_y) if (max_svg_y - min_y) > 0 else 1
        scale = min(scale_x, scale_y)  # Сохраняем пропорции

        # Генерируем GCode
        self.gcode_list = []

        first_point = True

        for path in paths:
            for segment in path:
                # Генерируем множество точек вдоль сегмента
                for t in np.linspace(0, 1, samples_per_segment):
                    point = segment.point(t)

                    # Масштабируем и смещаем координаты
                    x = (point.real - min_x) * scale
                    y = (point.imag - min_y) * scale

                    if first_point:
                        self.gcode_list.append((int(x) + 6000, int(y) + 6000))
                        first_point = False
                        continue

                    self.gcode_list.append((int(x) + 6000, int(y) + 6000))

    def __Gcode_param_changed(self):
        """ Изменяет Gcode, при изменении параметров в окне параметров """
        """ Список значений |origin_x|origin_y|size_x|size_y|F|scale_x|scale_y|angle|workTime| """
        lines_edit_value, change_list = self.__paramUI.get_linesEdit_value()
        if self.__fileLoaded is False:
            return

        self.__origin_x = np.min(self.__cord_array_mod[:, 0])
        self.__origin_y = np.min(self.__cord_array_mod[:, 1])
        self.__size_x = np.max(self.__cord_array_mod[:, 0]) - np.min(self.__cord_array_mod[:, 0])
        self.__size_y = np.max(self.__cord_array_mod[:, 1]) - np.min(self.__cord_array_mod[:, 1])

        if change_list['origin_x'] or change_list['origin_y']:
            self.__move(lines_edit_value['origin_x'], lines_edit_value['origin_y'])

        elif change_list['size_x'] or change_list['size_y']:
            self.__scale_to_size(lines_edit_value['size_x'], lines_edit_value['size_y'])

        elif change_list['scale_x'] or change_list['scale_y']:
            self.__scale_to_scale(lines_edit_value['scale_x'], lines_edit_value['scale_y'])

        elif change_list['angle']:
            self.__rotate(lines_edit_value['angle'])

        if self.__F_scale != lines_edit_value['F_scale']:
            self.__F_scaling(lines_edit_value['F_scale'] / self.__F_scale)

    def __Gcode_centering(self):
        """ Центрует Gcode на поле """
        self.__size_x = np.max(self.__cord_array_mod[:, 0]) - np.min(self.__cord_array_mod[:, 0])
        self.__size_y = np.max(self.__cord_array_mod[:, 1]) - np.min(self.__cord_array_mod[:, 1])

        new_origin_x = (self.__workspace_size['x'] - self.__size_x) / 2
        new_origin_y = (self.__workspace_size['y'] - self.__size_y) / 2

        self.__move(new_origin_x, new_origin_y)

    def __calc_gcode_param(self):
        self.__origin_x = np.min(self.__cord_array_mod[:, 0])
        self.__origin_y = np.min(self.__cord_array_mod[:, 1])
        self.__size_x = np.max(self.__cord_array_mod[:, 0]) - np.min(self.__cord_array_mod[:, 0])
        self.__size_y = np.max(self.__cord_array_mod[:, 1]) - np.min(self.__cord_array_mod[:, 1])
        self.__workTime = self.__get_workTime()

        lines_edit_value = [self.__origin_x, self.__origin_y, self.__size_x, self.__size_y, self.__F_scale,
                            self.__scale_x, self.__scale_y, self.__angle]

        self.__paramUI.set_linesEdit_value(lines_edit_value)
        self.__Statistic.display_statistics([self.__origin_x, self.__origin_y, self.__size_x, self.__size_y, self.__workTime])
        self.__F_listWidget.clear()
        self.__F_listWidget.addItems(self.__F_array_mod.astype(str))

    def __scale_to_size(self, new_size_x, new_size_y):
        scale_x = 1
        scale_y = 1
        if self.__paramUI.scaling_isLocked:
            if round(self.__size_x, 3) != new_size_x:
                scale_x = new_size_x / self.__size_x
                scale_y = scale_x
            elif round(self.__size_y, 3) != new_size_y:
                scale_y = new_size_y / self.__size_y
                scale_x = scale_y
        else:
            scale_x = new_size_x / self.__size_x
            scale_y = new_size_y / self.__size_y

        self.__scaling(scale_x, scale_y)

    def __scale_to_scale(self, new_scale_x, new_scale_y):
        scale_x = 1
        scale_y = 1

        if self.__paramUI.scaling_isLocked:
            if round(self.__scale_x, 3) != new_scale_x:
                scale_x = new_scale_x / self.__scale_x
                scale_y = scale_x
            if round(self.__scale_x, 3) != new_scale_y:
                scale_y = new_scale_y / self.__scale_y
                scale_x = scale_y
        else:
            scale_x = new_scale_x / self.__scale_x
            scale_y = new_scale_y / self.__scale_y

        self.__scaling(scale_x, scale_y)

    def __scaling(self, scale_x, scale_y):
        scaling_transformation_matrix = np.array([[scale_x, 0, self.__origin_x * (1 - scale_x)],
                                                  [0, scale_y, self.__origin_y * (1 - scale_y)],
                                                  [0, 0, 1]])

        self.__cord_array_mod = np.dot(self.__cord_array_mod, scaling_transformation_matrix.T)
        self.__apply_transformation_to_command_list(scaling_transformation_matrix)

        self.__scale_x *= scale_x
        self.__scale_y *= scale_y
        self.__Chart.show_data(self.__cord_array_mod[:, 0], self.__cord_array_mod[:, 1])
        self.__calc_gcode_param()

    def __displace(self, dx, dy):
        displace_transformation_matrix = np.array([ [1, 0, dx],
                                                [0, 1, dy],
                                                [0, 0, 1]])

        self.__cord_array_mod = np.dot(self.__cord_array_mod, displace_transformation_matrix.T)
        self.__apply_transformation_to_command_list(displace_transformation_matrix)
        self.__Chart.show_data(self.__cord_array_mod[:, 0], self.__cord_array_mod[:, 1])

    def __move(self, new_origin_x, new_origin_y):
        # Делаем матрицу преобразования перемещения
        dx = new_origin_x - self.__origin_x
        dy = new_origin_y - self.__origin_y

        self.__displace(dx, dy)
        self.__calc_gcode_param()
        self.__Chart.show_data(self.__cord_array_mod[:, 0], self.__cord_array_mod[:, 1])

    def __rotate(self, angle):
        # Делаем матрицу преобразования вращения
        d_angle_deg = angle - self.__angle
        d_angle_rad = d_angle_deg / 180 * np.pi

        self.__angle = angle

        origin_x = self.__origin_x
        origin_y = self.__origin_y

        rotation_transformation_matrix = np.array(
            [[np.cos(d_angle_rad), -np.sin(d_angle_rad), self.__origin_x * (1 - np.cos(d_angle_rad)) + self.__origin_y * np.sin(d_angle_rad)],
             [np.sin(d_angle_rad), np.cos(d_angle_rad), self.__origin_y * (1 - np.cos(d_angle_rad)) - self.__origin_x * np.sin(d_angle_rad)],
             [0, 0, 1]])

        self.__cord_array_mod = np.dot(self.__cord_array_mod, rotation_transformation_matrix.T)
        self.__apply_transformation_to_command_list(rotation_transformation_matrix)

        self.__calc_gcode_param()
        self.__move(origin_x, origin_y)
        self.__Chart.show_data(self.__cord_array_mod[:, 0], self.__cord_array_mod[:, 1])

    def __F_scaling(self, scale):
        """ Масштабируем скорость по коэффициенту """
        self.__F_array_mod *= scale
        F_array_index = 0

        self.transformed_command_list = list()
        for index in range(len(self.__command_list_mod)):
            if self.__command_list_mod[index][0] == "F":
                self.__command_list_mod[index][1] = self.__F_array_mod[F_array_index]
                F_array_index += 1

        self.__F_scale *= scale
        self.__calc_gcode_param()
        self.__Chart.show_data(self.__cord_array_mod[:, 0], self.__cord_array_mod[:, 1])

    def __apply_transformation_to_command_list(self, transformation_matrix):
        self.transformed_command_list = list()
        for command in self.__command_list_mod:
            if command[0] == "G00" or command[0] == "G01":
                x = command[1]
                y = command[2]

                point = np.array([x, y, 1])
                transformed_point = transformation_matrix @ point
                self.transformed_command_list.append([command[0], float(transformed_point[0]), float(transformed_point[1])])
            else:
                self.transformed_command_list.append(command)

            self.__command_list_mod = self.transformed_command_list

    def __get_workTime(self):
        x = 0
        y = 0
        time = 0
        speed = 1
        for command in self.__command_list_mod:
            if command[0] == "G01" or command[0] == "G1":
                time += np.sqrt((command[1] - x) ** 2 + (command[2] - y) ** 2) / speed
                x = command[1]
                y = command[2]

            elif command[0] == "F":
                speed = command[1]

        return time

    def enable_paramUI(self, state):
        self.__paramUI.enable_frame(state)

    @property
    def first_line(self):
        self.__command_list_index = 0
        return self.next_line

    @property
    def next_line(self):
        if self.__command_list_index >= len(self.__command_list_mod):
            return None

        comp_set = self.__galvo_control.compensation_settings

        line = self.__command_list_mod[self.__command_list_index].copy()
        if self.__paramUI.interpolate_fastMove:
            if line[0] == "G00" or line[0] == "G0":
                line[0] = "G01"

        if self.__command_list_index != 0:
            if line[0] == 'G00' or line[0] == 'G0' or line[0] == 'G01' or line[0] == 'G1':
                x, y = line[1:]
                x_prev, y_prev = self.__movement_prev
                dx_sign_prev, dy_sign_prev = self.__direction_prev

                dx = x - x_prev
                dy = y - y_prev

                comp_x = 0
                comp_y = 0

                if np.sign(dx) != dx_sign_prev:
                    comp_x += (np.sign(dx) * comp_set["x_backlash"])
                    self.__OneWay_disp[0] = dx
                else:
                    self.__OneWay_disp[0] += dx
                if np.sign(dy) != dy_sign_prev:
                    comp_y += (np.sign(dy) * comp_set["y_backlash"])
                    self.__OneWay_disp[1] = dy
                else:
                    self.__OneWay_disp[1] += dy

                nex_x = x + comp_x + (comp_set["x_hysteresis"] * self.__OneWay_disp[0] + comp_set["xsqr_hysteresis"] * self.__OneWay_disp[0]**2)
                nex_y = y + comp_y + (comp_set["y_hysteresis"] * self.__OneWay_disp[1] + comp_set["ysqr_hysteresis"] * self.__OneWay_disp[1]**2)

                self.__movement_prev = [x, y]
                self.__direction_prev = [np.sign(dx), np.sign(dy)]

                line[1:] = [nex_x, nex_y]

        self.__command_buffer = line

        self.__command_list_index += 1

        return line

    @property
    def last_used_line(self):
        return self.__command_buffer

    @property
    def progress(self):
        return int(self.__command_list_index / len(self.__command_list_mod) * 100)

    @property
    def isReady(self):
        if not self.__fileLoaded:
            print("Файл не загружен")
            return False

        return True
