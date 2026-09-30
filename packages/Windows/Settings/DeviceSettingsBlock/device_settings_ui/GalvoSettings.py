from packages.Windows.Settings.DeviceSettingsBlock.DeviceSettingsFactory import DeviceSettingsUI
from packages.core.validators.numeric_validator import IntValidator, FloatValidator


class GalvoSettingsUI(DeviceSettingsUI):
    name = "GalvoSettingsUI"
    name_ru = "Гальвосканер"
    group = 'beam_steerers'
    controller = "GalvoControlClass"

    def __init__(self, id, page, event_bus):
        params_map = [
            ("x_min", "X_min", IntValidator),
            ("y_min", "Y_min", IntValidator),
            ("x_max", "X_max", IntValidator),
            ("y_max", "Y_max", IntValidator),
            ("x_um_to_pixel", "X_um_to_pixel", FloatValidator),
            ("y_um_to_pixel", "Y_um_to_pixel", FloatValidator),
            ("x_backlash", "X_backlash", FloatValidator),
            ("y_backlash", "Y_backlash", FloatValidator),
            ("x_hysteresis", "X_hysteresis", FloatValidator),
            ("y_hysteresis", "Y_hysteresis", FloatValidator),
            ("xsqr_hysteresis", "Xsqr_hysteresis", FloatValidator),
            ("ysqr_hysteresis", "Ysqr_hysteresis", FloatValidator),
        ]
        super().__init__(id, page, event_bus, "GalvoSettings.ui", params_map)

        self.event_bus.GalvoControl.connect(self._on_event)

    def _on_event(self, transmitter, receiver, command, data):
        if transmitter == self.name:
            return
        if receiver in (self.name, "All"):
            if transmitter == self.controller:
                if command == "set_settings":
                    self.set_settings(data[0])

    def simple_send(self, text):
        self.event_bus.GalvoControl.emit(self.name, self.controller, "simple_send", [text])