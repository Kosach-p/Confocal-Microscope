import numpy as np
from packages.core.math.timeGen import *


class ScanFSM:
    display_frequency = 25

    def __init__(self):
        self.x1 = 0
        self.y1 = 0
        self.z1 = 0

        self.x2 = 65535
        self.y2 = 65535
        self.z2 = 4095

        self.step_x = 4096
        self.step_y = 4096
        self.step_z = 1024

        self.accum_time = 1000

        self.Np_x = 0
        self.Np_y = 0
        self.Np_z = 0
        self.Np_slice = 0
        self.Np_total = 0
        self.display_interval = None

        self.__RouteMatrix = None
        self.__DataMatrix = None

        self.__RoutePoint = 0

    def __generate_DataMatrix(self):
        """ Генерирует нулевую матрицу необходимы для, данных скана, размеров """
        self.__DataMatrix = np.full((self.Np_z, self.Np_y, self.Np_x), np.nan)

    def load_scan_parameters(self, params: dict):
        """
        Принимает параметры сканирования в виде списка
        list: [x1, x2, step_x, y1, y2, step_y, z1, z2, step_z, accum_time]
        """

        self.x1 = int(params['x']['origin'])
        self.x2 = int(params['x']['size'])
        self.step_x = int(params['x']['step'])

        self.y1 = int(params['y']['origin'])
        self.y2 = int(params['y']['size'])
        self.step_y = int(params['y']['step'])

        self.z1 = int(params['z']['origin'])
        self.z2 = int(params['z']['size'])
        self.step_z = int(params['z']['step'])

        self.accum_time = int(params['accum_time'])
        self.progressive_scan = params['progressive_scan']

        if self.step_x != 0 and (self.x2 - self.x1) != 0:
            self.Np_x = round((self.x2 - self.x1) / self.step_x)
        else:
            self.Np_x = 1
        if self.step_y != 0 and (self.y2 - self.y1) != 0:
            self.Np_y = round((self.y2 - self.y1) / self.step_y)
        else:
            self.Np_y = 1
        if self.step_z != 0 and (self.z2 - self.z1) != 0:
            self.Np_z = round((self.z2 - self.z1) / self.step_z)
        else:
            self.Np_z = 1

        if self.Np_x == 0:
            self.Np_x = 1
        if self.Np_y == 0:
            self.Np_y = 1
        if self.Np_z == 0:
            self.Np_z = 1

        self.Np_slice = self.Np_x * self.Np_y
        self.Np_total = self.Np_x * self.Np_y * self.Np_z
        self.display_interval = self.Np_total / self.display_frequency

        self.__RoutePoint = 0

        self.__generate_DataMatrix()

    @property
    def matrix_index(self):
        if self.progressive_scan:
            rp = self.__RoutePoint

            level = 0
            step = 2
            total_at_level = 0

            while True:
                points_at_level = ((self.Np_x + step - 1) // step) * ((self.Np_y + step - 1) // step) * self.Np_z
                if rp < total_at_level + points_at_level:
                    break
                total_at_level += points_at_level
                level += 1
                step = 2 ** (level + 1)

            offset = rp - total_at_level

            # Координаты на текущем уровне
            pixels_x = (self.Np_x + step - 1) // step
            pixels_y = (self.Np_y + step - 1) // step

            y_idx = offset // pixels_x
            if y_idx % 2 == 0:
                x_idx = offset % pixels_x
            else:
                x_idx = pixels_x - 1 - (offset % pixels_x)

            z_idx = offset // (pixels_x * pixels_y)
        else:
            rp = self.__RoutePoint
            y_idx = rp // self.Np_x
            if y_idx % 2 == 0:
                x_idx = rp % self.Np_x
            else:
                x_idx = self.Np_x - 1 - (rp % self.Np_x)
            z_idx = rp // self.Np_slice

        return z_idx, y_idx, x_idx

    @property
    def matrix_cord(self):
        z_idx, x_idx, y_idx = self.matrix_index
        x_cord = self.x1 + x_idx * self.step_x + self.step_x // 2
        y_cord = self.y1 + y_idx * self.step_y + self.step_y // 2
        z_cord = self.z1 + z_idx * self.step_z + self.step_z // 2
        return z_cord, x_cord, y_cord

    @property
    def percentage(self) -> int:
        """ Возвращает в процентах, число уже полученных через next_cord точек """
        return int((self.__RoutePoint / self.Np_total) * 100)

    def get_first_cord(self):
        """ Возвращает первую координату сканирования """
        mem_point = self.__RoutePoint
        self.__RoutePoint = 0
        first_cord = self.matrix_cord
        self.__RoutePoint = mem_point
        return first_cord

    def get_next_cord(self):
        """ Возвращает следующую координату сканирования (x, y, z) """
        self.__RoutePoint += 1

        if self.__RoutePoint >= self.Np_total:
            self.__RoutePoint = self.Np_total
            return None, None, None

        return self.matrix_cord

    def append_point(self, data):
        """ Добавляет точку в массив на место, которое соответствует последнему вызову get_next_cord """
        if self.__RoutePoint < self.Np_total:
            self.__DataMatrix[self.matrix_index] = data

    @property
    def DataMatrix(self):
        """ Возвращает DataMatrix """
        return self.__DataMatrix

    @property
    def inf_file(self):
        """ Создаёт inf файл для последнего скана """
        inf_file = {
            "comment": "",
            "name": None,
            "metadata": {
                "created": get_date_time(),
                "description": "3D scan",
            },
            "parameters": {
                "x1": self.x1,
                "y1": self.y1,
                "z1": self.z1,
                "x2": self.x2,
                "y2": self.y2,
                "z2": self.z2,
                "step_x": self.step_x,
                "step_y": self.step_y,
                "step_z": self.step_z,
                "accum_time": self.accum_time,
                "Np_x": self.Np_x,
                "Np_y": self.Np_y,
                "Np_z": self.Np_z,
                "Np_slice": self.Np_slice,
                "Np_total": self.Np_total
            },
            "units": {
                "cord": "LSB",
                "accum_time_ms": "ms",
            }
        }

        return inf_file

    def inf_file_from_dat(self, dat, name='3D scan'):
        if dat is not None:
            first_slice = dat[0]
            if isinstance(first_slice, np.ndarray):
                rows, cols = first_slice.shape
                num_slices = len(dat)

                inf_file = {
                    "comment": "",
                    "name": name,
                    "metadata": {
                        "created": None,
                        "description": "3D scan",
                    },
                    "parameters": {
                        "x1": 0,
                        "y1": 0,
                        "z1": 0,
                        "x2": cols,
                        "y2": rows,
                        "z2": num_slices,
                        "step_x": 1,
                        "step_y": 1,
                        "step_z": 1,
                        "accum_time": None,
                        "Np_x": cols,
                        "Np_y": rows,
                        "Np_z": num_slices,
                        "Np_slice": num_slices,
                        "Np_total": rows * cols * num_slices
                    },
                    "units": {
                        "cord": "LSB",
                        "accum_time_ms": "ms",
                    }
                }
                return inf_file

        return None

    @property
    def time_to_show(self):
        """ Возвращает True или False, в зависимости от того, пора ли показывать данные на ImageView """
        return (int(self.__RoutePoint % self.display_interval)) == 0
