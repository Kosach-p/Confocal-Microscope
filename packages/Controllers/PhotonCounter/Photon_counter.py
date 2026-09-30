from packages.Controllers.ParentController import ParentController
from packages.Controllers.ParentController import ControllerSettings
from PyQt6.QtCore import QTimer
import time


class PhotonCounterSettings(ControllerSettings):
    def _post_init(self):
        self._parameters = {'accum_time_ms': 100, 'period_of_polling': 100, 'comp_level': 649}
        self._load_settings()


class PhotonCounterControlClass(ParentController):
    name = "PhotonCounterControlClass"
    name_ru = "Счётчик фотонов"
    group = 'detectors'
    device_name = 'PhotonCounter'

    def __init__(self, parent=None):
        self.settings = PhotonCounterSettings(name=self.name)
        super().__init__(parent.event_bus, parent.event_bus.PhotonCounterControl, self.settings, self.device_name)

        self.event_bus_waiting_subscriber = None

        self.__GetCounting_wait = False
        self.__counting = False
        self.settings_updated = False

        self.__current_accum_time = self.settings.accum_time_ms

        self.__TIM_Init()

    def __update_client_settings(self):
        self.settings_updated = False
        client_method = [self.client.SetAccumTime, self.client.SetComparatorLevel]
        commands = ['SetAccumTime', 'SetComparatorLevel']
        comp_level = max(600, min(self.settings.comp_level, 700))
        data = [{"accum_time": self.settings.accum_time_ms * 1000}, {"CompLevel": comp_level}]
        self.event_bus.DialUp.emit(self.name, "DialUpService", "DualUp", [self.client.device_id, client_method, commands, data, False])

    def event_process(self, transmitter, receiver, command, data):
        """ Обработка emit на линии event_bus """
        if transmitter == self.name:
            return

        if receiver == self.name or receiver == "All":
            if command == "get_polling_time":
                self.__Start_TIM1(self.settings.period_of_polling)

            elif transmitter == "DialUpService":
                self.event_bus.StatusBar.emit("Настройки счётчика фотонов обновлены ✅", True, "success")
                self.settings_updated = True

            elif command == "get_settings":
                self.event_bus.PhotonCounterControl.emit(self.name, transmitter, "set_settings", [self.settings.load_settings_dict()])

            elif command == "simple_send":
                self.client.simple_send(data[0], 'ascii', False, False, self.name)

    def __TIM_Init(self):
        """ Инициализация таймеров """
        self.TIM1 = QTimer()
        self.TIM1.timeout.connect(lambda: self.__TIM_Interruption(TIMx="TIM1"))
        if self.settings.period_of_polling < 1:
            self.settings.period_of_polling = 1

        self.__Start_TIM1(self.settings.period_of_polling)

        self.TIM2 = QTimer()
        self.TIM2.timeout.connect(lambda: self.__TIM_Interruption(TIMx="TIM2"))

        self.TIM3 = QTimer()
        self.TIM3.timeout.connect(lambda: self.__TIM_Interruption(TIMx="TIM3"))

    def __Start_TIM1(self, time_ms):
        """ особый метод запуск таймера TIM1, который сообщает всем подписчикам, что было выбрано новое время опроса """
        self.TIM1.stop()
        self.TIM1.start(time_ms)

        self.event_bus.PhotonCounterControl.emit(self.name, "All", "new_polling_time_ms", [time_ms])

    def __Start_TIM2(self, time_ms):
        """ особый метод запуск таймера TIM2 """
        self.TIM2.stop()
        self.TIM3.stop()
        self.TIM2.start(time_ms)
        self.TIM3.start(self.settings.accum_time_ms)

    def __TIM_Interruption(self, TIMx):
        """ Обработчик прерываний от таймеров """
        if TIMx == "TIM1":
            if not self.event_bus.ProgramBusy:
                self.GetCurrentCount(receive_marker=self.name)

        if TIMx == "TIM2":
            self.GetCounting(receive_marker=self.name)

        if TIMx == "TIM3":
            self.__GetCounting_wait = False

    def __set_accum_time_us(self, accum_time, receive_marker=None):
        """ Установка времени накопления в мкс """
        self.__counting = False
        if receive_marker is None:
            receive_marker = self.name
        self.client.SetAccumTime(accum_time=int(accum_time), receive_marker=receive_marker)

    @property
    def is_ready(self):
        """ Возвращает состояние готовности к работе """
        return self.client.state

    def set_accum_time_ms(self, accum_time, receive_marker=None):
        """ Установка времени накопления в мс """
        self.__current_accum_time = accum_time
        self.__set_accum_time_us(accum_time=int(accum_time * 1000), receive_marker=receive_marker)

    def SetComparatorLevel(self, CompLevel, receive_marker=None):
        """ Установка уровня дискретизации """
        CompLevel = max(600, min(CompLevel, 700))
        self.client.SetComparatorLevel(CompLevel=CompLevel, receive_marker=receive_marker)

    def StartCounting(self, receive_marker=""):
        """ Начать счёт фотонов с нуля """
        self.client.StartCounting(receive_marker=receive_marker)

    def GetCounting(self, receive_marker=""):
        """ Получить значение фотонов насчитанное после StartCounting """
        if self.__GetCounting_wait:
            return False
        else:
            self.client.GetCounting(receive_marker=receive_marker)
            self.__GetCounting_wait = True

    def GetCurrentCount(self, receive_marker=""):
        """ Получить текущее значение фотонов от счётчика """
        self.client.GetCurrentCount(receive_marker=receive_marker)

    def set_normal_accum_time_ms(self):
        """ Установить время накопления как в настройках """
        self.set_accum_time_ms(accum_time=self.settings.accum_time_ms, receive_marker=self.name)

    def get_normal_accum_time_ms(self):
        """ Вернуть время накопления как в настройках """
        return self.settings.accum_time_ms

    def StartGetCounting(self, receive_marker=""):
        """ Начать счёт фотонов с нуля, а затем вернуть через emit по receive_marker насчитанное значение
            с командой StartGetCounting. Это довольно медленно, из-за emit, не рекомендуется для быстрой работы """
        if self.__counting is False:
            self.__counting = True
            self.event_bus_waiting_subscriber = receive_marker
            self.client.StartCounting(receive_marker=self.name)
            self.__Start_TIM2(self.__current_accum_time // 5)

    def update_settings(self, dict):
        self.__Start_TIM1(self.settings.period_of_polling)
        self.__update_client_settings()

    def save_settings(self):
        """ Сохранение всех настроек, что записаны в settings на текущий момент """
        self.settings.save_current_settings()

    def Process_ModBus_Packet(self, cmd_name, params):
        """ Обработчик ModBus пакетов """
        if cmd_name == 'GetCurrentCount':
            self.event_bus.PhotonCounterControl.emit(self.name, "All", "RegularPhotonCount", [params])

        if cmd_name == 'GetCounting':
            self.__GetCounting_wait = False

            if params['status'] != 1:
                self.GetCounting(receive_marker=self.name)
            elif self.__counting:
                self.TIM2.stop()
                self.__counting = False
                self.event_bus.PhotonCounterControl.emit(self.name, self.event_bus_waiting_subscriber, "StartGetCounting", [params['count']])

