# packages/core/services/EventBus.py
from PyQt6.QtCore import QObject, pyqtSignal


class EventBus(QObject):
    """ Общая шина всех сообщений между контроллерами и окнами """

    # Сигналы для устройств
    GalvoControl = pyqtSignal(str, str, str, list)
    PiezoControl = pyqtSignal(str, str, str, list)
    PhotonCounterControl = pyqtSignal(str, str, str, list)
    StepperMotorControl = pyqtSignal(str, str, str, list)
    LMX2820Control = pyqtSignal(str, str, str, list)

    # Сигналы для UI
    View2DUI = pyqtSignal(str, str, str, list)
    View3DUI = pyqtSignal(str, str, str, list)
    SpectrometerUI = pyqtSignal(str, str, str, list)
    ODMRSpectrometerUI = pyqtSignal(str, str, str, list)
    GcodeUI = pyqtSignal(str, str, str, list)

    # Служебные сигналы
    StatusBar = pyqtSignal(str, float, str)
    DialUp = pyqtSignal(str, str, str, list)
    ModbusService = pyqtSignal(str, str, str, list)
    ScriptExecutorClass = pyqtSignal(str, str, str, list)
    Settings = pyqtSignal(str, str, str, list)

    DeviceSettings = pyqtSignal(str, str, str, list)

    def __init__(self):
        super().__init__()
        self.ProgramBusy = False
        self.TXRX_connected = False
        self.DEV_MODE = False