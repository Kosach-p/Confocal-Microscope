"""
Базовый класс для UI настроек устройства.
Компоновщик трёх независимых виджетов: Parameters, Connection, CommandBuilder.
"""
import time

from PyQt6.QtWidgets import QVBoxLayout, QWidget

from packages.Windows.Settings.DeviceSettingsBlock.comand_builder.command_builder_manager import DeviceCommandBuilder
from packages.Windows.Settings.DeviceSettingsBlock.DeviceConnectionSettings import DeviceConnectionSettings
from packages.Windows.Settings.DeviceSettingsBlock.ParametersWidget import ParametersWidget


class DeviceSettingsUI:
    """
    Базовый класс для UI настроек устройства.

    Чтобы добавить новое устройство:
        1. Создать .ui файл с параметрами
        2. Унаследоваться от DeviceSettingsUI
        3. Переопределить name, name_ru, group, controller
        4. Задать params_map

    Пример:
        class ModulatorSettingsUI(DeviceSettingsUI):
            name = "ModulatorSettingsUI"
            name_ru = "Модулятор"
            group = DeviceGroup.MODULATORS
            controller = "ModulatorControlClass"

            def __init__(self, id, page, event_bus):
                params_map = [
                    ("frq_1", "frq_1_spinBox", IntValidator),
                    ("frq_2", "frq_2_spinBox", IntValidator),
                ]
                super().__init__(id, page, event_bus, "ModulatorSettings.ui", params_map)
    """
    name = "DeviceSettingsUI"
    name_ru = "Базовый класс"
    group = None
    controller = None

    def __init__(self, id: int, page: QWidget, event_bus, ui_name: str, params_map: list):
        self.id = id
        self.ui_name = ui_name
        self.params_map = params_map
        self.event_bus = event_bus
        self.device_config = {}
        self.page = page
        self.init_cplt = False
        self.layout = QVBoxLayout(page)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.params_widget = ParametersWidget(self.ui_name, self.params_map)
        self.layout.addWidget(self.params_widget.frame)
        self.connection_widget = DeviceConnectionSettings()
        self.layout.addWidget(self.connection_widget)
        self.command_builder = DeviceCommandBuilder()
        self.layout.addWidget(self.command_builder)
        self.layout.addStretch()
        self.page.page_activated.connect(self.setupUI)
    # ------------------------------------------------------------
    # Публичный API
    # ------------------------------------------------------------
    
    def setupUI(self):
        if self.init_cplt is False:
            self.command_builder.setUI()
            self.params_widget.setupUI()
            self.connection_widget.setUI()

            self.init_cplt = True
        self.page.page_activated.disconnect(self.setupUI)
    
    def set_settings(self, settings: dict) -> None:
        """Загружает полный словарь настроек в UI"""
        if "commands" in settings:
            self.command_builder.set_commands(settings["commands"])
            self.device_config = settings
        if "connection" in settings:
            self.connection_widget.set_settings(settings["connection"])
        if "parameters" in settings:
            self.params_widget.set_parameters(settings["parameters"])

    def get_parameters(self) -> dict:
        """Возвращает параметры устройства"""
        return self.params_widget.get_parameters()

    def set_parameters(self, data: dict) -> None:
        """Устанавливает параметры устройства"""
        self.params_widget.set_parameters(data)

    def set_connection(self, connection: dict) -> None:
        """Устанавливает настройки соединения"""
        self.connection_widget.set_settings(connection)

    def set_profile_state(self, profiles_state: dict) -> None:
        """Устанавливает настройки соединения"""
        self.connection_widget.set_profile_state(profiles_state)

    def get_connections_settings(self):
        return self.connection_widget.get_settings()

    def save_settings(self) -> dict:
        """Собирает и возвращает полный конфиг устройства"""
        self.device_config['commands'] = self.command_builder.get_commands()
        self.device_config['connection'] = self.connection_widget.get_settings()
        self.device_config['parameters'] = self.params_widget.get_parameters()
        return self.device_config

    def log_message_list(self, data: list) -> None:
        """Логирование сообщения (переопределяется в наследниках при необходимости)"""
        pass

    def simple_send(self, text: str) -> None:
        """Отправка текста устройству (переопределяется в наследниках)"""
        pass