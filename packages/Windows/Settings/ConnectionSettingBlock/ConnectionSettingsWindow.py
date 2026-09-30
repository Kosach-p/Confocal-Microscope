import os
import json
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = ""

from packages.core.services.save_service.SettingsSave_service import SettingsSaver
from packages.core.config.path import CONN_SETTINGS_DIR
from packages.Windows.Settings.Stacker import SettingsSwitcher
from packages.Windows.Settings.ConnectionSettingBlock.serSettingsUI import COMSettingsUI, serSettings
from packages.Windows.Settings.ConnectionSettingBlock.ethSettingsUI import EthSettingsUI, ethSettings
from packages.Сommunication.interface_configs import interfaces_name
from PyQt6.QtWidgets import QMenu
from PyQt6.QtGui import QAction


class ConnectionSettingsStorage(SettingsSaver):
    def _post_init(self):
        self._settings = {}

        self.JSON_object.set_settings_file_name("settings.json")
        self.JSON_object.set_settings_dir(CONN_SETTINGS_DIR)
        self._load_settings()


class ConnectionSettings:
    name = "ConnectionSettings"

    def __init__(self, widget, event_bus):
        self.widget = widget
        self.event_bus = event_bus
        self.switcher = SettingsSwitcher(widget, widget_name='profile_listWidget')
        self.create_btn = self.switcher.list_widget.create_btn
        self.switcher.list_widget.delete_item_ext = self.delete_current_profile

        self.create_menu = QMenu(self.create_btn)

        for type_key, type_info in interfaces_name.items():
            action = QAction(f"{type_info['icon']} {type_info['ru']}", self.create_menu)
            action.setData(type_key)
            action.triggered.connect(
                lambda checked, t=type_info, key=type_key: self.add_settingsUI(f"{t['icon']} {t['ru']}", key)
            )
            self.create_menu.addAction(action)

        self.create_btn.setMenu(self.create_menu)

        self.settings_obj = ConnectionSettingsStorage(name='profiles')

        self.SettingsUI = {}
        self.id = 0

        data = self.settings_obj.load_settings_dict()
        for key, value in data.items():
            UI = self.add_settingsUI(value.get('name', key), value.get('type', None))
            UI.set_settings(value)

        self.create_btn.clicked.connect(self.add_settingsUI)

        self.event_bus.ModbusService.connect(self.__event_process)

    def add_settingsUI(self, name='Name', type='ser', pref_id=None):
        if pref_id is None:
            while self.id in self.SettingsUI.keys() or str(self.id) in self.SettingsUI.keys():
                self.id += 1
            id_real = self.id
        else:
            id_real = pref_id
        self.switcher.append_page(name, id_real, interfaces_name[type]['ru'])
        UI_class = None
        if type == 'ser':
            UI_class = COMSettingsUI
        elif type == 'eth':
            UI_class = EthSettingsUI

        if UI_class is not None:
            self.SettingsUI[id_real] = UI_class(page=self.switcher.get_page(id_real), parent=self, id=int(id_real))
        else:
            print(f"ERROR::ConnectionSettings::add_settingsUI::Не существует такого интерфейса как {type}")

        return self.SettingsUI[id_real]

    def delete_current_profile(self, item_id):
        """Удаляет текущий выбранный профиль"""
        self.SettingsUI.pop(item_id)
        self.event_bus.ModbusService.emit(self.name, "DeviceManager", "disconnect", [{'id': item_id}])
        self.collect_data()

    def __event_process(self, transmitter, receiver, command, data):
        """ Обработчик emit в выбранном канале """
        if transmitter == self.name:
            return

        if receiver == "All" or receiver == self.name:
            if command == "get_info":
                response = data[0]
                if self.SettingsUI.get(response['id']) is not None:
                    self.SettingsUI[response['id']].set_params(response['params'])

            elif command == "get_connection_params":
                self.send_update_connect()

    def send_update_connect(self):
        self.event_bus.ModbusService.emit(self.name, "All", "connect", [self.settings_obj.load_settings_dict()])

    def collect_data(self):
        params_dict = {}

        profiles_data = self.switcher.list_widget.get_all_items_data()
        for profile in profiles_data:

            if self.SettingsUI.get(profile.get('id')) is not None:
                params = self.SettingsUI.get(profile.get('id')).params
                params['name'] = profile['name']
                params_dict[str(profile.get('id'))] = params

        self.settings_obj.save_settings_dict(params_dict)

    def apply(self):
        """ Применяет текущие настройки """
        self.collect_data()
        self.send_update_connect()

