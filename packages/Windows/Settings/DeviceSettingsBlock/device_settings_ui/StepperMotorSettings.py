# packages/Windows/Settings/DeviceSettingsBlock/StepperMotorSettings.py
from packages.Windows.Settings.DeviceSettingsBlock.DeviceSettingsFactory import DeviceSettingsUI
from packages.core.validators.numeric_validator import IntValidator, FloatValidator
from packages.core.config.device_schema import DeviceGroup


class StepperMotorSettingsUI(DeviceSettingsUI):
    """Настройки Шагового мотора"""
    name = "StepperMotorSettingsUI"
    name_ru = "Шаговый мотор"
    group = DeviceGroup.SPECTRAL_TUNERS
    controller = "StepperMotorControlClass"

    def __init__(self, id, page, event_bus):
        params_map = [
            ("MAX_speed", "MAX_speed", FloatValidator),
            ("MIN_speed", "MIN_speed", FloatValidator),
            ("accel_per_sec", "accel_per_sec", FloatValidator),
            ("I_HOLD", "I_HOLD", IntValidator),
            ("I_RUN", "I_RUN", IntValidator),
            ("I_HOLD_DELAY", "I_HOLD_DELAY", IntValidator),
            ("threshold", "threshold", IntValidator),
            ("steps_in_nm", "steps_in_nm", IntValidator),
        ]
        super().__init__(id, page, event_bus, "StepperMotorSettings.ui", params_map)

        self.event_bus = self.event_bus.StepperMotorControl
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