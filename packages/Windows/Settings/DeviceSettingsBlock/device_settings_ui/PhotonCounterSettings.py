# packages/Windows/Settings/DeviceSettingsBlock/PhotonCounterSettings.py
from packages.Windows.Settings.DeviceSettingsBlock.DeviceSettingsFactory import DeviceSettingsUI
from packages.core.validators.numeric_validator import IntValidator
from packages.core.config.device_schema import DeviceGroup


class PhotonCounterSettingsUI(DeviceSettingsUI):
    """Настройки счётчика фотонов"""
    name = "PhotonCounterSettingsUI"
    name_ru = "Счётчик фотонов"
    group = DeviceGroup.DETECTORS
    controller = "PhotonCounterControlClass"

    def __init__(self, id, page, event_bus):
        params_map = [
            ("accum_time_ms", "accum_time", IntValidator),
            ("period_of_polling", "period_of_polling", IntValidator),
            ("comp_level", "comp_level", IntValidator),
        ]
        super().__init__(id, page, event_bus, "PhotonCounterSettings.ui", params_map)

        self.event_bus = self.event_bus.PhotonCounterControl
        self.event_bus.connect(self._on_event)

    def _on_event(self, transmitter, receiver, command, data):
        if transmitter == self.name:
            return
        if receiver in (self.name, "All"):
            if transmitter == self.controller:
                if command == "set_settings":
                    self.set_settings(data[0])
                if command == "Log":
                    self.log_message_list(data)

    def simple_send(self, text):
        self.event_bus.emit(self.name, self.controller, "simple_send", [text])