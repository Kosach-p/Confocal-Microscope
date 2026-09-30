from PyQt6.QtWidgets import QFrame

from packages.core.widgets.SpectrumChartWidget import SpectrumChart

from datetime import datetime
import numpy as np


class ODMRSpectrumControllerClass:
    name = "SpectrumControllerClass"

    def __init__(self, frame: QFrame):
        self.left_edge = 0
        self.right_edge = 0
        self.step = 0
        self.accum_time = 0
        self.number_repetitions = 0

        self.N_points = 0

        self.__frame = frame
        self.__image = SpectrumChart(parent=self.__frame, user_name="ОДМР спектрометр")

        self.__RouteMatrix = None
        self.__RouteMatrixUnit = None
        self.__DataMatrix = None

        self.random_scan = False

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
        self.__DataMatrix = np.full(self.__calculate_Npoints(), np.nan)

    def nearby_shuffle(self, array, max_jump):
        """ Метод близкого перемешивания. То есть частоты перемешиваются, но шаг между соседями не слишком большой """
        result = [np.random.choice(array)]
        available = list(array)
        available.remove(result[0])

        while available:
            nearby = [x for x in available if abs(x - result[-1]) <= max_jump]
            result.append(np.random.choice(nearby) if nearby else min(available, key=lambda x: abs(x - result[-1])))
            available.remove(result[-1])

        return np.array(result)

    def __generate_RouteMatrix(self):
        """ Рассчитывает матрицу, которая включает в себя маршрут движения для устройства """
        self.__RoutePoint = 0
        self.__RouteMatrix = np.arange(0, self.__calculate_Npoints(), 1)
        np.random.shuffle(self.__RouteMatrix)
        self.__RouteMatrixUnit = self.__RouteMatrix * self.step + self.left_edge

        self.__start = self.left_edge
        self.__end = self.right_edge

    def load_scan_parameters(self, scan_parameters: list):
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

        self.__generate_RouteMatrix()
        self.__generate_DataMatrix()

    def generate_Matrices(self):
        """ Генерирует новые матрицы, при тех же параметрах сканирования, но новом положении """
        self.__generate_RouteMatrix()
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
        self.__image.add_curve_smart(self.__RouteMatrixUnit, self.__DataMatrix, removable=True)

    def show_data_Tree(self, data, reason):
        """ Стандартный метод преобразования данных от TreeModule в X, Y координаты и проверку видимости данных """
        self.__image.show_TreeData(data, reason)

    def calculatePercentage(self) -> int:
        """ Возвращает в процентах, число уже полученных через next_cord точек """
        return int((self.__RoutePoint / self.__calculate_Npoints()) * 100)

    def get_first_cord(self):
        """ Возвращает первую координату сканирования """
        return self.__RouteMatrixUnit[0]

    def get_next_cord(self, current_cord):
        """ Возвращает следующую координату сканирования """
        self.__RoutePoint += 1

        if self.__RoutePoint >= self.N_points:
            return None

        return self.__RouteMatrixUnit[self.__RoutePoint]

    def append_point(self, data, frq=None):
        """ Добавляет точку в массив на место, которое соответствует последнему вызову get_next_cord """
        if self.__RoutePoint < self.N_points:
            self.__DataMatrix[self.__RoutePoint] = data
            self.show_data()

        return self.__RoutePoint

    @property
    def DataMatrix(self):
        """ Возвращает матрицу данных """
        idx = np.argsort(self.__RouteMatrixUnit)
        data = self.__DataMatrix[idx]
        return data

    @property
    def RouteMatrix(self):
        """ Возвращает матрицу пути """
        return self.__RouteMatrixUnit

    @property
    def RoutePoint(self):
        """ Возвращает Точку """
        return self.__RoutePoint

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
        Route = np.array(self.__RouteMatrixUnit)
        return [[np.sort(Route), np.array(self.DataMatrix)]]

    def inf_file(self):
        """ Создаёт inf файл для последнего скана """
        inf_file = {
            "comment": "",
            "name": f"ODMR Spectrum measurement",
            "metadata": {
                "created": datetime.now().isoformat(timespec='seconds').replace(':', '_').replace('.', '_'),
                "description": "ODMR Spectrum measurement",
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
