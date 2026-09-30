# Импорты
from packages.Controllers.ParentController import ParentController
from packages.Controllers.ParentController import ControllerSettings
from packages.Сommunication.ClientRegistry import ClientRegistry


class PiezoSettings(ControllerSettings):
    def _post_init(self):
        self._parameters = {'x_min': 0, 'y_min': 0, 'z_min': 0, 'x_max': 4095, 'y_max': 4095, 'z_max': 4095,
                            'X_um_to_pixel': 1, 'Y_um_to_pixel': 1, 'Z_um_to_pixel': 1, 'rise_speed': 0,
                            'X': 0, 'Y': 0, 'Z': 0}

        self._load_settings()

    def load_AxesBorder(self):
        """ Выгрузить только границы осей """
        self._load_settings()
        return [[self.x_min, self.x_max], [self.y_min, self.y_max], [self.z_min, self.z_max]]


class PiezoControlClass(ParentController):
    """ Основной класс для управления Пьезоподвижкой """
    name = "PiezoControlClass"
    name_ru = "Пьезосканер"
    group = 'positioners'
    device_name = "Piezo"

    def __init__(self, parent=None):
        self.settings = PiezoSettings(self.name)
        super().__init__(parent.event_bus, parent.event_bus.PiezoControl, self.settings, self.device_name)

        # Координаты пьезо
        self.settings.X = self.settings.X
        self.settings.Y = self.settings.Y
        self.settings.Z = self.settings.Z

        # Проверка границ координат
        self.__check_cord_bound()

    def event_process(self, transmitter, receiver, command, data):
        """ Обработка emit на линии event_bus """
        if transmitter == self.name:
            return

        if receiver == self.name or receiver == "All":
            if command == "get_cord":
                self.event_bus.PiezoControl.emit(self.name, transmitter, "update_cord", self.get_cord())

            elif command == "update_settings":
                self.update_settings(data[0])

            elif command == "get_settings":
                self.event_bus.PiezoControl.emit(self.name, transmitter, "set_settings",
                                                         [self.settings.load_settings_dict()])

    def __check_cord_bound(self):
        """ Проверка выхода за границы координат """
        self.settings.X = max(self.settings.x_min, min(self.settings.x_max, self.settings.X))
        self.settings.Y = max(self.settings.y_min, min(self.settings.y_max, self.settings.Y))
        self.settings.Z = max(self.settings.z_min, min(self.settings.z_max, self.settings.Z))

    def __send_gcode_G01(self, X: int, Y: int, Z: int, receive_marker=None):
        """ Отправка G00 клиенту (плавное перемещение) """
        self.client.send_gcode_G01(X=X, Y=Y, Z=Z, receive_marker=receive_marker)

    def __send_gcode_F(self, F: int, receive_marker=None):
        """ Отправка F__ клиенту (число точек в миллисекунду) """
        self.client.send_gcode_F(F=F, receive_marker=receive_marker)

    # Публичные методы, для работы с координатами
    def set_cord(self, x: int, y: int, z: int, receive_marker=None):
        """ Привычный аналог G01 """
        self.G01(x, y, z, receive_marker)

    def G01(self, x: int, y: int, z: int, receive_marker=None):
        """ Установка требуемой координаты """
        self.settings.X = x
        self.settings.Y = y
        self.settings.Z = z
        self.__check_cord_bound()

        self.__send_gcode_G01(self.settings.X, self.settings.Y, self.settings.Z, receive_marker=receive_marker)

    def get_cord(self):
        """ Возвращает текущие координаты """
        return [self.settings.X, self.settings.Y, self.settings.Z]

    def set_cord_middle(self, receive_marker=None):
        """ Установка координаты по центру """
        self.settings.X = int((self.settings.x_max - self.settings.x_min) / 2)
        self.settings.Y = int((self.settings.y_max - self.settings.y_min) / 2)
        self.settings.Z = int((self.settings.z_max - self.settings.z_min) / 2)
        self.__check_cord_bound()

        self.__send_gcode_G01(self.settings.X, self.settings.Y, self.settings.Z, receive_marker=receive_marker)

    def displace_cord(self, dx: int, dy: int, dz: int, receive_marker=None):
        """ Смещение координаты на (dx, dy) """
        self.settings.X += dx
        self.settings.Y += dy
        self.settings.Z += dz
        self.__send_gcode_G01(self.settings.X, self.settings.Y, self.settings.Z, receive_marker=receive_marker)

    # Методы для работы с настройками
    def update_settings(self, dict):
        """ Сохранение всех настроек (и из списка настроек, и текущие координаты) """
        self.event_bus.PiezoControl.emit(self.name, "All", "update_AxesBorder", self.settings.load_AxesBorder())

    def get_AxesBorder(self):
        return self.settings.load_AxesBorder()

    # Метод, для обработки пакетов данных
    def Process_ModBus_Packet(self, cmd_name, data):
        return True
