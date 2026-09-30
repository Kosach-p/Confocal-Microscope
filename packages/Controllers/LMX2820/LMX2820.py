import time

from packages.Controllers.ParentController import ParentController
from packages.Controllers.ParentController import ControllerSettings
import serial
import serial.tools.list_ports


class LMX2820Settings(ControllerSettings):
    def _post_init(self):
        self._parameters = {'COM_port': "COM5", 'frq': 0}

        self._load_settings()


class LMX2820ControlClass(ParentController):
    """ Основной класс для управления гальвосканером """
    name = "LMX2820ControlClass"
    device_name = 'LMX2820'
    group = 'modulators'

    def __init__(self, parent=None):
        self.settings = LMX2820Settings(self.name)
        super().__init__(parent.event_bus, parent.event_bus.LMX2820Control, self.settings, self.device_name)
        self.state = False

    def __event_process(self, transmitter, receiver, command, data):
        """ Обработка emit на линии event_bus """
        if transmitter == self.name:
            return

        if receiver == self.name or receiver == "All":
            pass

    def save_settings(self):
        """ Сохранение всех настроек """
        self.settings._save_settings()

    def update_frq(self):
        """ Установить частоту в МГц из той частоты, что в настройках запомнена """
        return self.set_frq_1(self.settings.frq)

    def set_frq_1_MHZ(self, frq_MHZ: float):
        """ Установить частоту в МГц """
        return self.set_frq_1(frq_MHZ * 1e3)

    def set_frq_2_MHZ(self, frq_MHZ: float):
        """ Установить частоту в МГц """
        return self.set_frq_1(frq_MHZ * 1e3)

    def set_frq_1(self, frq_1):
        """ Установка частоты 1 """
        self.client.set_frq_1(frq=frq_1, receive_marker=self.name)
        return True

    def set_frq_2(self, frq_2):
        """ Установка частоты 2 """
        self.client.set_frq_2(frq=frq_2, receive_marker=self.name)
        return True

    def set_power(self, power):
        self.client.set_power(power=power, receive_marker=self.name)
        return True

    def sweep_frq_time_ms(self, time_ms):
        self.client.sweep_frq_time_ms(time_ms=time_ms, receive_marker=self.name)
        return True

    def sweep_frq_step(self, step):
        self.client.sweep_frq_step(step=step, receive_marker=self.name)
        return True

    def sweep_frq_start(self):
        self.client.sweep_frq_start(receive_marker=self.name)
        return True

    def sweep_frq_stop(self):
        self.client.sweep_frq_stop(receive_marker=self.name)
        return True

    @property
    def frq_1_KHZ(self):
        return self.settings.frq

    @property
    def frq_1_MHZ(self):
        return self.settings.frq / 1e3

    @property
    def is_ready(self):
        return self.state

    def Process_ModBus_Packet(self, cmd_name, params):
        """ Обработчик ModBus пакетов """
        if cmd_name == "set_frq_1":
            self.event_bus_controller.emit(self.name, "All", "frq_1_cmpl", [True])
        elif cmd_name == "set_frq_2":
            self.event_bus_controller.emit(self.name, "All", "frq_2_cmpl", [True])
        elif cmd_name == "set_power":
            self.event_bus_controller.emit(self.name, "All", "set_power_cmpl", [True])
        elif cmd_name == "sweep_frq_time_ms":
            self.event_bus_controller.emit(self.name, "All", "sweep_frq_time_ms_cmpl", [True])
        elif cmd_name == "sweep_frq_step":
            self.event_bus_controller.emit(self.name, "All", "sweep_frq_step_cmpl", [True])
        elif cmd_name == "sweep_frq_start":
            self.event_bus_controller.emit(self.name, "All", "sweep_frq_start_cmpl", [True])
        elif cmd_name == "sweep_frq_stop":
            self.event_bus_controller.emit(self.name, "All", "sweep_frq_stop_cmpl", [True])
        pass

