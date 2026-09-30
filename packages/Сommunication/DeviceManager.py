import time

from PyQt6.QtCore import QTimer
from packages.Сommunication.protocol_controller.ProcessCollector import *
from packages.Controllers.ParentController import ControllerRegistry
from packages.Сommunication.ClientRegistry import ClientRegistry
from multiprocessing import Process, Queue
import multiprocessing
from packages.Windows.ParentWindow import WindowRegistry
from packages.Сommunication.protocol_controller.DynamicModbusDevice import DeviceFactory
from packages.core.config.app_config import DEVICE_CONFIG
from packages.core.services.dial_up_service import DialUpService

from packages.Сommunication.interface_controllers.Serial.SerialInterfaceController import SerialInterfaceController
from packages.Сommunication.interface_configs import *
import pprint

DEVELOPER_MODE = False
GOOD_PRINT_MODE = True


def ppprint(values):
    if DEVELOPER_MODE:
        if GOOD_PRINT_MODE:
            pprint.pprint(values, indent=2)
        else:
            print(values)

class DeviceManager:
    """ Отвечает за работу с ядром передачи данных """
    name = "DeviceManager"

    def __init__(self, event_bus, statusBar):
        self.to_worker = Queue()
        self.l_p_input_q = Queue()
        self.from_worker = Queue()

        self.event_bus = event_bus
        self.init_devices()
        self.TIM_Init()
        self.statusBar = statusBar
        self.DualUp = DialUpService(self.event_bus)

        self.interface_class = {'ser': SerialInterfaceController,
                                'eth': SerialInterfaceController}

        self.get_info_timeout = 0

        self.event_bus.ModbusService.connect(self.__event_process)
        self.connection_dict = {}
        self.port_state_dict = {}
        self.profile_mapping = {}

        self.TIM = QTimer()
        self.TIM.timeout.connect(lambda: self.to_worker.put({"command": "pulse"}))
        self.TIM.start(1000)

    def __event_process(self, transmitter, receiver, command, data):
        """ Обработчик emit в выбранном канале """
        if transmitter == self.name:
            return

        if receiver == "All" or receiver == self.name:
            if command == "connect":
                response = data[0]
                self.connection_dict = {}
                self.connection_dict = response

                for key, value in self.connection_dict.items():
                    self.port_state_dict.setdefault(key, {'state': PORT_NOT_EXISTS, 'name': value.get('name'), 'queue': 0,
                                                          'ping': {'response_time': 0, 'request_time': 0, 'requested': False}})

                for profile in response.values():
                    self.to_worker.put({'command': 'open', 'id': profile['id'], 'params': None})
                    self.to_worker.put({'command': 'connect', 'id': profile['id'], 'params':
                        {'interface': self.interface_class[profile['type']], 'settings': profile}})

            elif command == "disconnect":
                response = data[0]
                self.connection_dict.pop(str(response['id']))

                for key, value in self.connection_dict.items():
                    self.port_state_dict.setdefault(key, {'state': PORT_NOT_EXISTS, 'name': value.get('name'), 'queue': 0,
                                                          'ping': {'response_time': 0, 'request_time': 0, 'requested': False}})
                self.to_worker.put({'command': 'close', 'id': response['id'], 'params': None})

            elif command == "active_ids":
                response = data[0]
                self.profile_mapping = {}
                name_list, controller_list = ControllerRegistry.get_all()
                for controller in controller_list:
                    if controller.client.device_id in response.values():
                        interface_id = controller.client.interface_id
                        if interface_id in self.profile_mapping:
                            self.profile_mapping[interface_id].append(controller)
                        else:
                            self.profile_mapping[interface_id] = [controller]

    def init_devices(self):
        self.worker_process = Process(
            target=CommunicationProcessCollector,
            args=(self.to_worker, self.l_p_input_q, self.from_worker),
            name='InterFace Manager'
        )

        self.worker_process.start()
        for group in DEVICE_CONFIG:
            client = DeviceFactory.create(self.l_p_input_q, group)
            ClientRegistry.register(client)
            client.interface_id = 0

    def TIM_Init(self):
        # Таймер Попытки подключиться к COM порту
        self.TIM_GET_INFO = QTimer()
        self.TIM_GET_INFO.timeout.connect(lambda: self.TIM_Interruption(TIMx="TIM_GET_INFO"))
        self.TIM_GET_INFO.start(500)  # 1000 мс

        # Проверка очереди COM порта
        self.TIM_MULTIPROCESSING = QTimer()
        self.TIM_MULTIPROCESSING.timeout.connect(lambda: self.TIM_Interruption(TIMx="TIM_MULTIPROCESSING"))
        self.TIM_MULTIPROCESSING.start(1)  # 1 мс

    def TIM_Interruption(self, TIMx):
        if TIMx == "TIM_MULTIPROCESSING":
            while not self.from_worker.empty():
                self.ModBus_answers_router(self.from_worker.get())

        if TIMx == "TIM_GET_INFO":
            self.to_worker.put({'command': 'get_info', 'id': -1, 'params': None})

            self.update_status_bar()

            for value in self.port_state_dict.values():
                ping = value['ping']
                if ping['requested'] is False:
                    ping['request_time'] = time.time()
                    ping['requested'] = True

    def update_status_bar(self):
        status_text = ''
        self.event_bus.ModbusService.emit(self.name, 'All', 'port_state', [self.port_state_dict])
        self.event_bus.DeviceSettings.emit(self.name, 'All', 'port_state', [self.port_state_dict])
        for key, value in self.port_state_dict.items():
            state = value['state']
            ping = value['ping']
            if state == PORT_EXISTS_AND_OPEN:
                dev_status_text = ""
                if self.connection_dict.get(key) is not None:
                    emoji = ["❌", "✅"]
                    if self.profile_mapping is not None:
                        for controller in self.profile_mapping.get(key, []):
                            name = controller.dev_name
                            if name is not None:
                                dev_status_text += f"{name} {emoji[controller.dev_state]}| "

                ping_state = '❌'
                if ping['requested'] is False:
                    time_out = (ping['response_time'] - ping['request_time']) * 1000
                    ping_state = f'ping: {int(time_out)} ms'

                status_text += f"{ping_state}: {self.connection_dict[key]['name']} ✅: " + dev_status_text + str(value["queue"]) + "\n"
            elif state == PORT_NOT_EXISTS:
                if self.connection_dict.get(key) is not None:
                    status_text += f" {self.connection_dict[key]['name']} :  Указанный порт не существует ❌\n"
            elif state == PORT_EXISTS_NOT_OPEN:
                if self.connection_dict.get(key) is not None:
                    status_text += f" {self.connection_dict[key]['name']} :  Подключение к порту ⌛️\n"

        if status_text == '':
            status_text = '... обновление ...'
        status_text = status_text.removesuffix('\n')

        self.statusBar.set_leftStatusBar_text(status_text)

    def ModBus_answers_router(self, response):
        if response is not None:
            if response['command'] == 'open':
                if response['params'] is True:
                    ppprint(f"Был успешно создан процесс с id = [{response['id']}]")
                else:
                    ppprint(f"Не был создан процесс с id = [{response['id']}]")
            elif response['command'] == 'close':
                if response['params'] is True:
                    ppprint(f"Был успешно закрыт процесс с id = [{response['id']}]")
                else:
                    ppprint(f"Не был закрыт процесс с id = [{response['id']}]")
            elif response['command'] == 'stop':
                if response['params'] is True:
                    ppprint(f"Были успешно остановлены все процессы коммуникации")
            elif response['command'] == 'get_info':
                self._process_get_info(response)
                self.event_bus.ModbusService.emit(self.name, "ConnectionSettings", "get_info", [response])
            elif response['command'] == 'send_receive':
                self._process_regular_packet(response)

    def _process_get_info(self, response):
        id = str(response['id'])
        if id == '-1':
            pass
        else:
            queue = str(response['queue'])
            state = response['params']['port_state']

            self.port_state_dict[id]['state'] = state
            self.port_state_dict[id]['queue'] = queue

            self.port_state_dict[id]['ping']['requested'] = False
            self.port_state_dict[id]['ping']['response_time'] = time.time()

    def _process_regular_packet(self, response):
        cmd_name = response.get("cmd_name")
        data = response['params']
        marker = data.get('receive_marker')
        answer = data.get('answer')
        report = data.get('report')

        if isinstance(report, dict):
            address = report.get('address')
            device_id = report.get('device_id')
            command_code = report.get('command_code')
            params = report.get('params')
            controller = ControllerRegistry.get_by_id(device_id)

            if controller is not None:
                controller.detect_package(cmd_name, params, marker)

            if answer is True:
                if marker is not None:
                    if marker == "DialUpService":
                        self.DualUp.Process_ModBus_Packet(cmd_name, params)
                        return
                    controller = ControllerRegistry.get(marker)
                    if controller is not None:
                        controller.Process_ModBus_Packet(cmd_name, params)
                    else:
                        if self.event_bus.DEV_MODE:
                            ppprint(f"ERROR::{self.__class__.__name__}::_process_regular_packet::Не найден объект с указаным маркером {marker}")
                else:
                    if self.event_bus.DEV_MODE:
                        ppprint(f"ERROR::{self.__class__.__name__}::_process_regular_packet::Не указан маркер приёма")
        else:
            if DEVELOPER_MODE:
                print("ERROR::{self.__class__.__name__}::_process_regular_packet::", report)