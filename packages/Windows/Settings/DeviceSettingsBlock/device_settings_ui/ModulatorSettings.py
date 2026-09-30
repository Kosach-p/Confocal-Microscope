from packages.Windows.Settings.DeviceSettingsBlock.DeviceSettingsFactory import DeviceSettingsUI
from packages.core.validators.numeric_validator import IntValidator, FloatValidator


class ModulatorSettingsUI(DeviceSettingsUI):
    name = "ModulatorSettingsUI"
    name_ru = "Модулятор"
    group = 'modulators'
    controller = "ModulatorControlClass"

    def __init__(self, id, page, event_bus):
        params_map = [
            ("frq_1", "frq_1_spinBox", IntValidator),
            ("frq_2", "frq_2_spinBox", IntValidator),
        ]
        super().__init__(id, page, event_bus, "ModulatorSettings.ui", params_map)
        self.event_bus.ModulatorControl.connect(self._on_event)

    def _on_event(self, transmitter, receiver, command, data):
        if transmitter == self.name:
            return
        if receiver in (self.name, "All"):
            if transmitter == self.controller:
                if command == "set_settings":
                    self.set_settings(data[0])