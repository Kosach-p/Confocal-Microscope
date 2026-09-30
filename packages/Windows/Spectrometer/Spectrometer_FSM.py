from PyQt6.QtWidgets import QVBoxLayout, QSizePolicy
from PyQt6.QtWidgets import QFrame
from packages.core.widgets.SpectrumChartWidget import SpectrumChart
from datetime import datetime
import numpy as np


class SpectrumControllerClass:
    name = "SpectrumControllerClass"

    def __init__(self, frame: QFrame):
        self.left_edge = 0
        self.right_edge = 0
        self.step = 0
        self.accum_time = 0
        self.number_repetitions = 0

        self.N_points = 0

        self.__frame = frame
        self.__image = SpectrumChart(parent=self.__frame, user_name="Спектрометр")

        self.__RouteMatrix = None
        self.__DataMatrix = None

        self.fast_mode = True

        self.__RoutePoint = 0
        self.__RepeatStep = 0

        self.__start = self.left_edge
        self.__end = self.right_edge

        self.__current_curve = None

    def __calculate_Npoints(self):
        """ Расчёт число точек в спектре """
        self.N_points = int(abs(self.right_edge - self.left_edge) // self.step) + 1
        return self.N_points

    def __generate_DataMatrix(self):
        """ Генерирует нулевую матрицу необходимы для, данных скана, размеров """
        if self.fast_mode:
            self.__DataMatrix = []
        else:
            self.__DataMatrix = np.full(self.__calculate_Npoints(), np.nan)

    def __generate_RouteMatrix(self, current_wavelength):
        """ Рассчитывает матрицу, которая включает в себя маршрут движения для устройства """
        self.__RoutePoint = 0

        if self.fast_mode:
            self.__RouteMatrix = []
        else:
            self.__RouteMatrix = np.arange(self.left_edge, self.right_edge + self.step, self.step)

        if abs(self.left_edge - current_wavelength) <= abs(self.right_edge - current_wavelength):
            self.__start = self.left_edge
            self.__end = self.right_edge
        else:
            self.__start = self.right_edge
            self.__end = self.left_edge
            self.__RouteMatrix = self.__RouteMatrix[::-1]

    def load_scan_parameters(self, scan_parameters: list, current_wavelength):
        """
        Принимает параметры сканирования в виде списка
        list: [start, end, step, accum_time, number_repetitions]
        """
        self.left_edge = float(scan_parameters[0])
        self.right_edge = float(scan_parameters[1])
        self.step = float(scan_parameters[2])
        self.accum_time = int(scan_parameters[3])
        self.number_repetitions = int(scan_parameters[4])

        self.__RoutePoint = 0
        self.__RepeatStep = 0

        self.__generate_RouteMatrix(current_wavelength)
        self.__generate_DataMatrix()

    def generate_Matrices(self, current_wavelength):
        """ Генерирует новые матрицы, при тех же параметрах сканирования, но новом положении """
        self.__generate_RouteMatrix(current_wavelength)
        self.__generate_DataMatrix()

    def get_scan_parameters(self):
        """
        Возвращает параметры сканирования в виде списка
        list: [start, end, step, y0, accum_time, number_repetitions]
        """
        return [self.left_edge, self.right_edge, self.step, self.accum_time, self.number_repetitions]

    def show_data(self):
        """ Очищает экран и выводит текущие __DataMatrix """
        self.__image.clear_removable_curve()
        self.__image.add_curve_smart(self.__RouteMatrix, self.__DataMatrix, removable=True)

    def show_data_Tree(self, data, reason):
        """ Стандартный метод преобразования данных от TreeModule в X, Y координаты и проверку видимости данных """
        self.__image.show_TreeData(data, reason)

    def calculatePercentage(self) -> int:
        """ Возвращает в процентах, число уже полученных через next_cord точек """
        if self.fast_mode:
            return int(abs(self.__RouteMatrix[self.__RoutePoint] - self.__start) / (self.right_edge - self.left_edge) * 100)
        else:
            return int((self.__RoutePoint / self.__calculate_Npoints()) * 100)

    def get_first_cord(self):
        """ Возвращает первую координату сканирования """
        if self.fast_mode:
            return self.__start
        else:
            return self.__RouteMatrix[0]

    def get_next_cord(self, current_cord):
        """ Возвращает следующую координату сканирования """
        if self.fast_mode:
            self.__RoutePoint += 1
            return self.__end
        else:
            self.__RoutePoint += 1

            if self.__RoutePoint >= self.N_points:
                return None

            return self.__RouteMatrix[self.__RoutePoint]

    def append_point(self, data, wavelength=None):
        """ Добавляет точку в массив на место, которое соответствует последнему вызову get_next_cord """
        if self.fast_mode:
            if wavelength is not None:
                self.__DataMatrix.append(data)
                self.__RouteMatrix.append(wavelength)
                print(wavelength, data)
                self.show_data()
            else:
                print("Не указана длинна волны для точки")
        else:
            if self.__RoutePoint < self.N_points:
                self.__DataMatrix[self.__RoutePoint] = data
                self.show_data()

        return self.__RoutePoint

    @property
    def DataMatrix(self):
        """ Возвращает матрицу данных """
        return self.__DataMatrix

    @property
    def RouteMatrix(self):
        """ Возвращает матрицу пути """
        return self.__RouteMatrix

    @property
    def end(self):
        """ Возвращает конечную координату """
        return self.__end

    @property
    def repetition_completed(self):
        """ Увеличивается счётчик повторов на 1. True -> можно продолжать, False -> повторы кончились """
        self.__RepeatStep += 1
        if self.__RepeatStep >= self.number_repetitions:
            return False
        else:
            return True

    def dat_file(self):
        """ Создаёт dat файл для последнего скана """
        self.__RouteMatrix = np.array(self.__RouteMatrix)
        self.__DataMatrix = np.array(self.__DataMatrix)

        return [[self.__RouteMatrix, self.__DataMatrix]]

    def inf_file(self):
        """ Создаёт inf файл для последнего скана """
        inf_file = {
            "comment": "",
            "name": f"Spectrum measurement",
            "metadata": {
                "created": datetime.now().isoformat(timespec='seconds').replace(':', '_').replace('.', '_'),
                "description": "Spectrum measurement",
            },
            "parameters": {
                "start_nm": self.left_edge,
                "end_nm": self.right_edge,
                "step_nm": self.step,
                "accum_time_ms": self.accum_time,
                "number_repetitions": self.number_repetitions,
                "data_points": self.N_points
            },
            "units": {
                "start_nm": "nanometers",
                "end_nm": "nanometers",
                "step_nm": "nanometers",
                "accum_time_ms": "milliseconds"
            }
        }

        return inf_file
