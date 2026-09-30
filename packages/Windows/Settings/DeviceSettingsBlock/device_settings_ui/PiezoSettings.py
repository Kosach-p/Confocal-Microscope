# packages/Windows/Settings/DeviceSettingsBlock/PiezoSettings.py
from packages.Windows.Settings.DeviceSettingsBlock.DeviceSettingsFactory import DeviceSettingsUI
from packages.core.validators.numeric_validator import IntValidator, FloatValidator
from packages.core.config.device_schema import DeviceGroup


class PiezoSettingsUI(DeviceSettingsUI):
    """Настройки Пьезосканера"""
    name = "PiezoSettingsUI"
    name_ru = "Пьезосканер"
    group = DeviceGroup.POSITIONERS
    controller = "PiezoControlClass"

    def __init__(self, id, page, event_bus):
        params_map = [
            ("x_min", "X_min", IntValidator),
            ("y_min", "Y_min", IntValidator),
            ("z_min", "Z_min", IntValidator),
            ("x_max", "X_max", IntValidator),
            ("y_max", "Y_max", IntValidator),
            ("z_max", "Z_max", IntValidator),
            ("x_um_to_pixel", "X_um_to_pixel", FloatValidator),
            ("y_um_to_pixel", "Y_um_to_pixel", FloatValidator),
            ("z_um_to_pixel", "Z_um_to_pixel", FloatValidator),
            ("rise_speed", "rise_speed", FloatValidator),
        ]
        super().__init__(id, page, event_bus, "PiezoSettings.ui", params_map)

        self.event_bus = self.event_bus.PiezoControl
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