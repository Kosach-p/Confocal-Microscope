import numpy as np
from PyQt6.QtCore import QTimer


class DialUpService:
    """ Класс службы дозвона """
    name = "DialUpService"

    def __init__(self, event_bus):
        self.__event_bus = event_bus
        self.__event_bus.DialUp.connect(self.__event_process)
        # Очередь из запросов - теперь каждый запрос это dict
        self.__queue = []
        self.__queue_number = 0
        self.__queue_completed = True

        self.__TIM_Init()

    def __TIM_Init(self):
        """ Инициализация таймер """
        self.TIM = QTimer()
        self.TIM.timeout.connect(lambda: self.__TIM_Interruption())
        self.TIM.start(500)

    def __TIM_Interruption(self):
        """ Обработка прерываний по таймеру """
        if self.__queue_completed and not self.__event_bus.ProgramBusy:
            self.__queue_processor()

    def __event_process(self, transmitter, receiver, command, data):
        """ Обработчик emit в выбранном канале """
        if transmitter == self.name:
            return
        if receiver == self.name:
            if command == "DualUp":
                # Удаляем старый запрос от этого transmitter если есть
                for element in self.__queue:
                    if element['transmitter'] == transmitter:
                        self.__queue.remove(element)
                        break

                # Создаем запрос в виде словаря
                request = {
                    'transmitter': transmitter,
                    'slave_id': data[0],
                    'methods': data[1],
                    'cmd_name': data[2],
                    'params': data[3],
                    'wait_response': data[4],
                    'completed': [False] * len(data[2]),  # флаги выполнения
                    'results': {}  # результаты по командам
                }

                self.__queue.append(request)

    def __queue_processor(self):
        state = False
        for request in self.__queue:
            for index in range(0, len(request['methods'])):
                if not request['completed'][index]:
                    command = request['methods'][index]
                    params = request['params'][index]
                    state = command(**params, receive_marker=self.name)

            if not request['wait_response'] and state:
                self.__event_bus.DialUp.emit(
                    self.name,
                    request['transmitter'],
                    "DualUp",
                    [request['slave_id'], request['methods'], request['wait_response'], request['params']]
                )
                self.__queue.remove(request)

        return True

    def Process_ModBus_Packet(self, cmd_name, params):
        state = True

        for request in self.__queue:
            if cmd_name in request['cmd_name']:
                for index, command_name in enumerate(request['cmd_name']):
                    if command_name == cmd_name:
                        request['completed'][index] = True
                        request['results'][cmd_name] = params

                    if not request['completed'][index]:
                        state = False

                if state:
                    self.__event_bus.DialUp.emit(
                        self.name,
                        request['transmitter'],
                        "DualUp",
                        [request['slave_id'], request['methods'], request['wait_response'], request['params'],
                         request['results']]
                    )
                    self.__event_bus.StatusBar.emit(
                        f"Параметры {request['transmitter']} установлены",
                        3,
                        "success"
                    )
                    self.__queue.remove(request)
