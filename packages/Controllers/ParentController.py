from packages.core.services.save_service.Json import JsonSettingsClass
from PyQt6.QtCore import QTimer
from packages.core.services.save_service.SettingsSave_service import SettingsSaver
from packages.Сommunication.ClientRegistry import ClientRegistry


class ControllerSettings:
    def __init__(self, name):
        self.JSON_object = JsonSettingsClass(name)
        self.JSON_object.set_settings_file_name("controller_settings.json")
        self.JSON_object.set_settings_dir("service_files/settings/controllers")
        self._parameters = {}
        self._connection = {
            "echo_enable": True,
            "poll_interval": 5.0,
            "profile": '0',
        }
        self._post_init()


    def __getattr__(self, name):
        if '_parameters' in self.__dict__ and name in self.__dict__['_parameters']:
            return self.__dict__['_parameters'][name]
        if '_connection' in self.__dict__ and name in self.__dict__['_connection']:
            return self.__dict__['_connection'][name]
        raise AttributeError(f"'{name}' not found")

    def __setattr__(self, name, value):
        if name in ('_parameters', '_connection'):
            super().__setattr__(name, value)
            return
        if hasattr(self, '_parameters') and name in self._parameters:
            self._parameters[name] = type(self._parameters[name])(value)
        elif hasattr(self, '_connection') and name in self._connection:
            self._connection[name] = type(self._connection[name])(value)
        else:
            super().__setattr__(name, value)

    def _post_init(self):
        pass

    def _save_settings(self):
        data = {
            "parameters": self._parameters
        }
        self.JSON_object.Json_save_settings(data)

    def _load_settings(self):
        loaded = self.JSON_object.Json_load_settings()
        if loaded:
            if "parameters" in loaded:
                self._parameters.update(loaded["parameters"])

    def save_settings(self, settings: list):
        keys = list(self._parameters.keys())
        for i, key in enumerate(keys):
            if i < len(settings):
                self._parameters[key] = type(self._parameters[key])(settings[i])
        self._save_settings()

    def set_settings_dict(self, settings: dict):
        self._connection.update(settings.get("connection"))
        self._parameters.update(settings.get("parameters"))

    def save_settings_dict(self, settings: dict):
        self._connection.update(settings.get("connection"))
        self._parameters.update(settings.get("parameters"))
        self._save_settings()

    def save_current_settings(self):
        self._save_settings()

    def load_settings(self):
        self._load_settings()
        return list(self._parameters.values())

    def load_settings_dict(self):
        self._load_settings()
        data = {
            "connection": self._connection,
            "parameters": self._parameters
        }
        return data

    def save_connection(self, data: dict):
        self._connection.update(data)
        self._save_settings()

    def save_parameters(self, data: dict):
        self._parameters.update(data)
        self._save_settings()

    def load_connection(self) -> dict:
        self._load_settings()
        return self._connection.copy()

    def load_parameters(self) -> dict:
        self._load_settings()
        return self._parameters.copy()


class DeviceSettings(SettingsSaver):
    def _post_init(self):
        self._settings = {}
        self.JSON_object.set_settings_file_name("settings.json")
        self.JSON_object.set_settings_dir('service_files/settings/devices')
        self._load_settings()


class ControllerRegistry:
    """ Словарь всех добавленных контроллеров """
    __registry = {}

    @classmethod
    def register(cls, controller):
        """ Добавляем ссылку на контроллер в общий словарь """
        cls.__registry[controller.name] = controller

    @classmethod
    def get(cls, name):
        """ Возвращаем ссылку на контроллер с name """
        controller = cls.__registry.get(name)
        return controller

    @classmethod
    def get_by_id(cls, id):
        """ Возвращаем ссылку на контроллер с name """
        _, controller_list = cls.get_all()
        for controller in controller_list:
            if controller.client.device_id == id:
                return controller

    @classmethod
    def get_all(cls):
        """ Возвращаем список всех name, которые были добавлены """
        name_list = list()
        controller_list = list()
        for name, controller in cls.__registry.items():
            name_list.append(name)
            controller_list.append(controller)

        return name_list, controller_list


class ParentController:
    name = "ParentController"
    group = "None"

    def __init__(self, event_bus, event_bus_controller, settings, device_name):
        self.client = ClientRegistry.get(self.group)
        self.event_bus = event_bus
        self.event_bus_controller = event_bus_controller
        self.event_bus_settings = event_bus.DeviceSettings
        self.settings = settings

        self.TIM = QTimer()
        self.TIM.timeout.connect(self.__send_ECHO)
        self.TIM.start(1000)

        self.log_commands = False
        self.poll_interval = 5.0
        self.use_device = False

        ControllerRegistry.register(self)

        self.connection_init()

    def connection_init(self):
        """ Подключаем триггеры к действиям с виджетами в окне настроек """
        self.event_bus_controller.connect(self.event_preprocess)
        self.event_bus.DialUp.connect(self.event_preprocess)
        self.event_bus_settings.connect(self.event_preprocess)

    def event_preprocess(self, transmitter, receiver, command, data):
        """ Обработка emit на линии event_bus """
        if transmitter == self.name:
            return
        if receiver == self.name or receiver == self.group:
            if command == "update_settings":
                settings = data[0]
                self.settings.set_settings_dict(settings)
                self.connection_settings_update(settings.get("connection"))
                self.update_settings(settings)
                if self.client is not None:
                    self.client.update_config(settings)

            elif command == "get_settings":
                self.event_bus_controller.emit(self.name, transmitter, "set_settings", [self.settings.load_settings_dict()])
            else:
                self.event_process(transmitter, receiver, command, data)
        else:
            self.event_process(transmitter, receiver, command, data)

    def event_process(self, transmitter, receiver, command, data):
        """ Для переопределения в дочерних классах """
        pass

    def save_settings(self):
        """ Сохранение всех настроек """

    def load_settings(self):
        """ Сохранение всех настроек """

    def update_settings(self, settings):
        """ Для переопределения в дочерних классах """
        pass

    def __send_ECHO(self):
        """ Оптравляет ЭХО """
        if self.client is None:
            return
        elif not self.client.echo_enable:
            return
        elif self.event_bus is None:
            return
        elif self.event_bus.ProgramBusy:
            return
        self.client.ECHO(receive_marker=self.name)

    def set_client(self, client):
        """ Устанавливает клиента """
        self.client = client
        self.client.state = False

    def connection_settings_update(self, conn_settings):
        """ Обновляем настройки подключения """
        self.client.echo_enable = conn_settings.get("echo_enable", False)
        self.log_commands = conn_settings.get("log_commands", False)
        self.poll_interval = conn_settings.get("poll_interval", 5.0)
        self.use_device = conn_settings.get("use_device", True)
        self.TIM.stop()
        self.TIM.start(int(self.poll_interval * 1000))
        self.__send_ECHO()

    @property
    def id(self):
        """ Возвращает id своего клиента """
        if self.client is None:
            return None
        return self.client.device_id

    @property
    def dev_name(self):
        """ Возвращает id своего клиента """
        if self.client is None:
            return None
        return self.client.name_ru

    @property
    def dev_state(self):
        """ Возвращает id своего клиента """
        if self.client is None:
            return False
        return self.client.state

    def detect_package(self, cmd_name, params, marker):
        """ Получает команду и данные и по ним определяет, существует ли устройство """
        if self.log_commands:
            self.event_bus_controller.emit(self.name, "All", "Log", [self.client.device_id, cmd_name, params])

        if marker is not None:
            self.event_bus_controller.emit(self.name, marker, cmd_name, [params])

        if self.event_bus.ProgramBusy:
            return
        if self.client.echo_enable:
            if cmd_name == 'ECHO':
                if params is not None and params is not False:
                    self.client.state = True
                else:
                    self.client.state = False
        else:
            if params is not None and params is not False:
                self.client.state = True
            else:
                self.client.state = False

    def Process_ModBus_Packet(self, cmd_name, params):
        """ Обработчик ModBus пакетов """
        print("Process_ModBus_Packet не реализован")
        pass
