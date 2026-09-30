from PyQt6.uic import loadUi
from packages.Windows.Settings.InterfaceSettingsBlock.HotKey.HotKey import HotKey
from packages.core.widgets.ListStacker import ListStacker
from packages.Windows.Settings.InterfaceSettingsBlock.SaveSettings import SaveSettings
from packages.Windows.Settings.InterfaceSettingsBlock.GeneralSettings import GeneralSettings
from packages.core.services.device_config_service import _read_json, _write_json_atomic
from packages.core.services.ThemeManager import ThemeManager

SETTINGS_PATH = "service_files/settings/UI_settings/interface.json"

class InterfaceSettings:
    name = "InterfaceSettings"

    def __init__(self, widget, event_bus):
        HotKeySettings_frame = loadUi("ui/InterfaceSettings/HotKeySettings.ui")
        SaveSettings_frame = loadUi("ui/InterfaceSettings/SaveSettings.ui")
        GeneralSettings_frame = loadUi("ui/InterfaceSettings/GeneralSettings.ui")
        self.event_bus = event_bus

        self.switcher = ListStacker(widget)

        self.switcher.append_page("Общие настройки", GeneralSettings_frame)
        self.switcher.append_page("Настройки сохранения", SaveSettings_frame)
        self.switcher.append_page("Горячие клавиши", HotKeySettings_frame)

        self.save_set = SaveSettings(SaveSettings_frame, self.event_bus)
        self.General = GeneralSettings(GeneralSettings_frame, self.event_bus)
        self.HotKey = HotKey(HotKeySettings_frame.frame, self.event_bus)

        self.settings = _read_json(SETTINGS_PATH)
        self.set_settings(self.settings)

        self.apply()

    def set_settings(self, settings):
        """Загружает полный словарь настроек в UI"""
        self.settings = settings
        if "save_set" in settings:
            self.save_set.set_settings(settings["save_set"])
        if "HotKey" in settings:
            self.HotKey.set_settings(settings["HotKey"])
        if "General" in settings:
            self.General.set_settings(settings["General"])

    def get_settings(self):
        settings = {}

        settings["save_set"] = self.save_set.get_settings()
        settings["HotKey"] = self.HotKey.get_settings()
        settings["General"] = self.General.get_settings()

        return settings

    def apply(self):
        self.settings = self.get_settings()
        ThemeManager.apply(self.settings["General"]["theme"])

        _write_json_atomic(filepath=SETTINGS_PATH, data=self.settings)
        self.emit_settings()

    def emit_settings(self):
        self.event_bus.Settings.emit(self.name, "All", "qss_update", [self.settings])
        self.event_bus.Settings.emit(self.name, "All", "HotKeys", [self.settings["HotKey"]])
        pass
