from packages.Controllers.ParentController import ParentController
from packages.Controllers.ParentController import ControllerSettings


class GalvoSettings(ControllerSettings):
    def _post_init(self):
        self._parameters = {'ID': 101, 'x_min': 0, 'y_min': 0, 'x_max': 0xFFFF, 'y_max': 0xFFFF, 'x_um_to_pixel': 0.00278,
                            'y_um_to_pixel': 0.00278, 'x': 0, 'y': 0, 'x_backlash': 0, 'y_backlash': 0, 'x_hysteresis': 0,
                            'y_hysteresis': 0, 'xsqr_hysteresis': 0, 'ysqr_hysteresis': 0}

        self._load_settings()

    def load_AxesBorder(self):
        """ Выгрузить только границы осей """
        self._load_settings()
        return [[self.x_min, self.x_max], [self.y_min, self.y_max]]

    def compensation_settings(self):
        s = self.load_settings_dict()['parameters']
        compensation_settings = {'x_backlash': s["x_backlash"], 'y_backlash': s["y_backlash"], 'x_hysteresis': s["x_hysteresis"],
                                 'y_hysteresis': s["y_hysteresis"], 'xsqr_hysteresis': s["xsqr_hysteresis"], 'ysqr_hysteresis': s["ysqr_hysteresis"]}
        return compensation_settings


class GalvoControlClass(ParentController):
    """ Основной класс для управления гальвосканером """
    name = "GalvoControlClass"
    group = 'beam_steerers'
    device_name = "Galvo"

    def __init__(self, parent=None):
        self.settings = GalvoSettings(self.name)
        super().__init__(parent.event_bus, parent.event_bus.GalvoControl, self.settings, self.device_name)
        self.AxesBorder = self.settings.load_AxesBorder()

        self.settings.x = self.settings.x
        self.settings.y = self.settings.y
        self.__valid_x = None
        self.__valid_y = None

        self.set_cord_wait = None

        self.settings_updated = True
        self.__check_cord_bound()

    def event_process(self, transmitter, receiver, command, data):
        """ Обработка emit на линии event_bus """
        if transmitter == self.name:
            return

        if receiver == self.name or receiver == "All":
            if command == "get_cord":
                self.event_bus.GalvoControl.emit(self.name, transmitter, "update_cord", [self.settings.x, self.settings.y])

            elif command == "set_cord":
                self.set_cord(x=data[0], y=data[1], receive_marker=transmitter)

            elif command == "G00":
                self.G00(x=data[0], y=data[1], receive_marker=transmitter)

            elif command == "M03" or command == "M3":
                self.__send_gcode_M03()

            elif command == "M05" or command == "M5":
                self.__send_gcode_M05()

            elif command == "update_settings":
                self.update_settings(data[0])

            elif command == "get_settings":
                self.event_bus.GalvoControl.emit(self.name, transmitter, "set_settings", [self.settings.load_settings_dict()])

    def __check_cord_bound(self):
        """ Проверка выхода за границы координат """
        self.settings.x = max(self.AxesBorder[0][0], min(self.AxesBorder[0][1], self.settings.x))
        self.settings.y = max(self.AxesBorder[1][0], min(self.AxesBorder[1][1], self.settings.y))

    # Методы для отправки G-code команд
    def __send_gcode_M03(self, receive_marker=None):
        """ Отправка M03 клиенту (включить лазер) """
        self.client.send_gcode_M03(receive_marker=receive_marker)

    def __send_gcode_M05(self, receive_marker=None):
        """ Отправка M05 клиенту (выключить лазер) """
        self.client.send_gcode_M05(receive_marker=receive_marker)

    def __send_gcode_G00(self, x: int, y: int, receive_marker=None):
        """ Отправка G00 клиенту (быстрое перемещение) """
        self.client.send_gcode_G00(x=int(x), y=int(y), receive_marker=receive_marker)

    def __send_gcode_G01(self, x: int, y: int, receive_marker=None):
        """ Отправка G00 клиенту (плавное перемещение) """
        self.client.send_gcode_G01(x=int(x), y=int(y), receive_marker=receive_marker)

    def __send_gcode_G04(self, P, receive_marker=None):
        """ Отправка G04 клиенту (Ожидание) """
        print("GalvoControlClass::__send_gcode_G04::Функция не реализована")

    def __send_gcode_F(self, F: int, receive_marker=None):
        """ Отправка F__ клиенту (число точек в миллисекунду) """
        self.client.send_gcode_F(F=int(F), receive_marker=receive_marker)

    def __send_gcode_S(self, S: int, receive_marker=None):
        """ Отправка S клиенту (Мощность лазера) """
        self.client.send_gcode_S(S=int(S), receive_marker=receive_marker)  # Исправлено: было send_gcode_F

    # Публичные методы, для работы с координатами
    @property
    def is_ready(self):
        """ Возвращает состояние готовности к работе """
        return self.settings_updated * self.client.state

    def set_cord(self, x: int, y: int, receive_marker):
        """ Привычный аналог G00 """
        self.set_cord_wait = receive_marker
        self.settings.x = x
        self.settings.y = y
        self.client.set_cord(x=int(x), y=int(y), receive_marker=self.name)

    def M03(self, receive_marker=None):
        """ Включить лазер """
        self.__send_gcode_M03(receive_marker=receive_marker)

    def M05(self, receive_marker=None):
        """ Выключить лазер """
        self.__send_gcode_M05(receive_marker=receive_marker)

    def G00(self, x: int, y: int, receive_marker=None):
        """ Установка требуемой координаты """
        self.settings.x = x
        self.settings.y = y
        self.__check_cord_bound()

        self.__send_gcode_G00(int(self.settings.x), int(self.settings.y), receive_marker=receive_marker)

    def G01(self, x: int, y: int, receive_marker=None):
        """ Плавная установка требуемой координаты """
        self.settings.x = x
        self.settings.y = y
        self.__check_cord_bound()

        self.__send_gcode_G01(int(self.settings.x), int(self.settings.y), receive_marker=receive_marker)

    def G04(self, P: int, receive_marker=None):
        """ Задержка """
        self.__send_gcode_G04(int(P), receive_marker=receive_marker)

    def F(self, F: int, receive_marker=None):
        """ Установить скорость """
        self.__send_gcode_F(int(F), receive_marker=receive_marker)

    def S(self, S: int, receive_marker=None):
        """ Установить мощность лазера """
        self.__send_gcode_S(int(S), receive_marker=receive_marker)  # Исправлено: было send_gcode_F

    def get_cord(self):
        """ Возвращает текущие координаты """
        return int(self.settings.x), int(self.settings.y)

    def set_cord_middle(self, receive_marker=None):
        """ Установка координаты по центру """
        self.settings.x = int((self.settings.x_max - self.settings.x_min) / 2)
        self.settings.y = int((self.settings.y_max - self.settings.y_min) / 2)
        self.__check_cord_bound()

        self.__send_gcode_G00(int(self.settings.x), int(self.settings.y), receive_marker=receive_marker)

    def displace_cord(self, dx: int, dy: int, receive_marker=None):
        """ Смещение координаты на (dx, dy) """
        self.settings.x += dx
        self.settings.y += dy
        self.__send_gcode_G00(int(self.settings.x), int(self.settings.y), receive_marker=receive_marker)

    def save_settings(self):
        """ Сохранение всех настроек, что записаны в settings на текущий момент """
        self.settings.x = self.settings.x
        self.settings.y = self.settings.y
        self.settings.save_current_settings()

    def update_settings(self, dict):
        self.AxesBorder = self.settings.load_AxesBorder()
        self.event_bus.GalvoControl.emit(self.name, "All", "update_AxesBorder", self.AxesBorder)

    @property
    def compensation_settings(self):
        return self.settings.compensation_settings()

    @property
    def parameters_dict(self):
        return self.settings.load_settings_dict()['parameters']

    # Метод, для обработки пакетов данных
    def Process_ModBus_Packet(self, cmd_name, data) -> bool:
        if cmd_name == 'set_cord':
            if self.set_cord_wait is not None:
                self.event_bus_controller.emit(self.name, self.set_cord_wait, "movement_completed", [data])
            self.set_cord_wait = None


