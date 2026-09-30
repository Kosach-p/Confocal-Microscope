from packages.Controllers.controllers_config import device_groups
from packages.Controllers.command_structure import device_command_struct
from packages.Windows.Settings.Stacker import SettingsSwitcher
from packages.Windows.Settings.DeviceSettingsBlock.device_settings_ui.GalvoSettings import GalvoSettingsUI
from packages.Windows.Settings.DeviceSettingsBlock.device_settings_ui.PiezoSettings import PiezoSettingsUI
from packages.Windows.Settings.DeviceSettingsBlock.device_settings_ui.PhotonCounterSettings import PhotonCounterSettingsUI
from packages.Windows.Settings.DeviceSettingsBlock.device_settings_ui.StepperMotorSettings import StepperMotorSettingsUI

from packages.core.services.device_config_service import (
    load_or_create_config,
    load_config,
    save_full_state,
)
from packages.core.services.app_state_config import (
    get_current_device_id,
    get_all_active_ids,
)

from packages.core.config.device_schema import (
    DeviceGroup,
    CoderType,
    make_device_config,
    make_command_config,
    make_parameter,
    make_ascii_parameter,
    make_group_config,
    make_ascii_coder_config
)

from packages.core.config.device_config import (
    FullConfig,
    DeviceConfig,
)

from PyQt6.QtWidgets import QMenu
from PyQt6.QtGui import QAction


class DeviceSettings:
    """
    Управление настройками устройств.
    Единственный вход для создания, удаления, сохранения устройств.
    """
    name = "DeviceSettings"

    UI_CLASS_MAP = {
        DeviceGroup.BEAM_STEERERS: GalvoSettingsUI,
        DeviceGroup.DETECTORS: PhotonCounterSettingsUI,
        DeviceGroup.POSITIONERS: PiezoSettingsUI,
        DeviceGroup.SPECTRAL_TUNERS: StepperMotorSettingsUI,
        DeviceGroup.MODULATORS: GalvoSettingsUI,
    }

    def __init__(self, widget, event_bus):
        self.widget = widget
        self.event_bus = event_bus
        self._next_id = 1
        self._used_ids = set()
        # Switcher управляет списком устройств в UI
        self.switcher = SettingsSwitcher(
            widget, widget_name='device_listWidget', enable_radio=True
        )
        self.switcher.list_widget.delete_item_ext = self._on_device_deleted_from_ui
        # Загружаем конфиг (или создаём из command_structure)
        self._config = load_or_create_config(self._build_default_config)
        # Живые UI-объекты: {group_key: [DeviceSettingsUI, ...]}
        self._device_uis = {}
        # Восстанавливаем UI из конфига
        self._restore_from_config()
        # Кнопка создания нового устройства
        self._setup_create_button()
        self.event_bus.DeviceSettings.connect(self._on_event)

    # ==================================================================
    # Публичный API
    # ==================================================================

    def apply(self):
        """Сохраняет ВСЕ изменения из UI в файл конфига + app_state"""
        config = self._config
        active_ids = {}

        for group_key, ui_list in self._device_uis.items():
            devices = []
            for ui in ui_list:
                device_dict = ui.save_settings()
                device_dict['name_ru'] = self.switcher.list_widget.get_item_name_by_id(ui.id)
                devices.append(device_dict)

            group = config.get(group_key)
            if group is not None:
                group['devices'] = devices
                group_ru = device_groups[group_key]["ru"]
                active_id = self.switcher.list_widget.get_active_id_in_branch(group_ru)
                if active_id != -1:
                    active_ids[group_key] = active_id
                    config[group_key]['current_device_id'] = active_id
        # Атомарно: и конфиг, и active_ids сохраняются вместе
        save_full_state(config, active_ids)
        self.emit_settings()

    def emit_settings(self):
        self._emit_current_device_settings()
        self._emit_active_ids()

    def get_device_config_by_id(self, device_id: int) -> DeviceConfig | None:
        """
        Возвращает DeviceConfig (доменный объект) по ID устройства.
        Если не найдено — None.
        """
        config = load_config()
        full_config = FullConfig.from_dict(config)
        return full_config.get_device_by_id(device_id)

    def get_device_ui_by_id(self, device_id: int):
        """
        Возвращает UI-объект устройства по ID.
        Если не найдено — None.
        """
        for ui_list in self._device_uis.values():
            for ui in ui_list:
                if ui.id == device_id:
                    return ui
        return None

    def _restore_from_config(self):
        """Создаёт UI для всех устройств из загруженного конфига"""
        full_config = FullConfig.from_dict(self._config)
        for group_name, group in full_config.groups.items():

            group_ru = device_groups[group_name]["ru"]
            for device in group.devices:
                self._used_ids.add(device.id)
                self._next_id = max(self._next_id, device.id + 1)
                ui = self._create_device_ui(
                    name=device.name_ru,
                    group=group_name,
                    group_ru=group_ru,
                    device_id=device.id,
                    use_defaults=False,
                )
                ui.set_settings(device.to_dict())
                # Восстанавливаем активное устройство из app_state
                saved_active_id = get_current_device_id(group_name)
                if saved_active_id == device.id:
                    self.switcher.set_active_page_by_id(device.id, group_ru)

    def _setup_create_button(self):
        """Настраивает кнопку '+' с выпадающим меню групп"""
        self.create_btn = self.switcher.list_widget.create_btn
        self.create_menu = QMenu(self.create_btn)

        for group_key, group_info in device_groups.items():
            action = QAction(group_info['ru'], self.create_menu)
            action.setData(group_key)
            action.triggered.connect(
                lambda checked, gk=group_key, gru=group_info['ru']:
                    self._create_device_ui(
                        name=self._get_default_name(gk),
                        group=gk,
                        group_ru=gru,
                    )
            )
            self.create_menu.addAction(action)

        self.create_btn.setMenu(self.create_menu)

    def _create_device_ui(self, name, group, group_ru, device_id=None, use_defaults=True):
        """
        Создаёт UI для одного устройства.
        Возвращает DeviceSettingsUI.
        """
        if group not in self._device_uis:
            self._device_uis[group] = []
        if device_id is None:
            device_id = self._generate_id()
        self.switcher.append_page(name, device_id, group_ru)
        page = self.switcher.get_page(device_id)
        ui_class = self.UI_CLASS_MAP.get(group)
        if ui_class is None:
            raise ValueError(f"Нет UI класса для группы '{group}'")
        ui = ui_class(id=device_id, page=page, event_bus=self.event_bus)
        self._device_uis[group].append(ui)
        return ui

    def _on_device_deleted_from_ui(self, device_id):
        """Колбэк: пользователь удалил устройство из списка"""
        for ui_list in self._device_uis.values():
            for ui in ui_list:
                if ui.id == device_id:
                    ui_list.remove(ui)
                    self._used_ids.discard(device_id)
                    return

    # ==================================================================
    # Дефолтные значения
    # ==================================================================

    def _build_default_config(self):
        """
        Собирает полную дефолтную конфигурацию из command_structure + schema.
        Для каждой команды создаёт и BIN, и ASCII параметры.
        """
        config = {}

        for device_key, device_info in device_command_struct.items():
            device_name = device_info.get('device', {}).get('name', device_key)
            device_name_ru = device_info.get('device', {}).get('name_ru', device_key)
            client_attr = device_info.get('device', {}).get('client_attr', '')

            commands = {}
            for cmd_name, cmd_data in device_info.get('commands', {}).items():
                # BIN параметры
                bin_coder_params = [
                    make_parameter(name=p, length=2)
                    for p in cmd_data.get('send', [])
                ]
                bin_decoder_params = [
                    make_parameter(name=p, length=2)
                    for p in cmd_data.get('receive', [])
                ]

                # ASCII параметры
                ascii_coder_params = [
                    make_ascii_parameter(name=p)
                    for p in cmd_data.get('send', [])
                ]
                ascii_decoder_params = [
                    make_ascii_parameter(name=p)
                    for p in cmd_data.get('receive', [])
                ]

                # Создаём команду с BIN по умолчанию
                cmd_config = make_command_config(
                    coder_type=CoderType.BIN,
                    decoder_type=CoderType.BIN,
                    command_code=0,
                    coder_params=bin_coder_params,
                    decoder_params=bin_decoder_params,
                )

                # Добавляем ASCII конфигурации в params
                cmd_config['coder_params'][CoderType.ASCII] = make_ascii_coder_config(
                    params=ascii_coder_params,
                )
                cmd_config['decoder_params'][CoderType.ASCII] = make_ascii_coder_config(
                    params=ascii_decoder_params,
                )
                commands[cmd_name] = cmd_config

            device_id = self._generate_id()
            device = make_device_config(
                device_id=device_id,
                name=device_name,
                name_ru=device_name_ru,
                group=DeviceGroup(device_key),
                client_attr=client_attr,
                commands=commands,
            )

            if device_key not in config:
                config[device_key] = make_group_config(
                    ru_name=device_groups[device_key]["ru"],
                    devices=[],
                )

            config[device_key]['devices'].append(device)

        return config

    def _get_default_name(self, group_key):
        """Возвращает имя устройства по умолчанию для группы"""
        default_device = self._get_default_device(group_key)
        return default_device.get('name_ru', 'Новое устройство')

    def _get_default_device(self, group_key):
        """Возвращает дефолтное устройство из command_structure"""
        device_info = device_command_struct.get(group_key, {})

        device = device_info.get('device', {})
        commands = {}
        for cmd_name, cmd_data in device_info.get('commands', {}).items():
            commands[cmd_name] = make_command_config(
                coder_type=CoderType.BIN.value,
                command_code=0,
                coder_params=[
                    make_parameter(name=p, length=2)
                    for p in cmd_data.get('send', [])
                ],
                decoder_params=[
                    make_parameter(name=p, length=2)
                    for p in cmd_data.get('receive', [])
                ],
            )

        return make_device_config(
            device_id=0,
            name=device.get('name', 'new_device'),
            name_ru=device.get('name_ru', 'Новое устройство'),
            group=DeviceGroup(group_key),
            client_attr=device.get('client_attr', ''),
            commands=commands,
        )

    # ==================================================================
    # Генерация ID
    # ==================================================================

    def _generate_id(self):
        """Возвращает следующий свободный ID"""
        while self._next_id in self._used_ids:
            self._next_id += 1
        self._used_ids.add(self._next_id)
        return self._next_id

    def _emit_active_ids(self):
        """ Рассылает id активных сейчас устройств """
        active_ids = get_all_active_ids()
        self.event_bus.ModbusService.emit(self.name, "All", "active_ids", [active_ids])

    def _emit_current_device_settings(self):
        """Рассылает настройки текущих (активных) устройств"""
        config = load_config()
        active_ids = get_all_active_ids()

        for group_key, group_data in config.items():
            current_id = active_ids.get(group_key)
            if current_id is None:
                current_id = -1

            for device in group_data.get('devices', []):
                if device.get('id') == current_id or current_id == -1:
                    self.event_bus.DeviceSettings.emit(
                        self.name, group_key, 'update_settings', [device]
                    )
                    break

    def _on_event(self, transmitter, receiver, command, data):
        """Обработчик событий шины"""
        if transmitter == self.name:
            return

        if receiver in ("All", self.name):
            if command == "port_state":
                for ui_list in self._device_uis.values():
                    for ui in ui_list:
                        ui.set_profile_state(data[0])
