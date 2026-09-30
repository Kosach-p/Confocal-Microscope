# ScriptAPI.py

class DeviceScriptAPI:
    """Базовый класс — прямой доступ к клиенту + безопасные методы контроллера"""

    def __init__(self, controller, client):
        self._c = controller
        self.client = client  # DynamicModbusDevice — все команды из конфига


class GalvoScriptAPI(DeviceScriptAPI):
    def move(self, x: int, y: int):
        self._c.set_cord(x, y)

    def home(self):
        self._c.set_cord_middle()

    def laser_on(self):
        self._c.M03()

    def laser_off(self):
        self._c.M05()

    def print(self, text):
        print(text)


class PiezoScriptAPI(DeviceScriptAPI):
    def move(self, x: int, y: int, z: int):
        self._c.set_cord(x, y, z)

    def home(self):
        self._c.set_cord_middle()


class CounterScriptAPI(DeviceScriptAPI):
    def measure(self) -> int:
        return self._c.get_count()

    def start(self):
        self._c.start_counting()


class SpectrometerScriptAPI(DeviceScriptAPI):
    def set_wavelength(self, nm: float):
        self._c.set_wavelength(nm)

    def scan(self, start: float, end: float, step: float):
        self._c.scan(start, end, step)


def build_script_context(controllers: dict, clients: dict) -> dict:
    print([m for m in dir(clients.get("galvo")) if not m.startswith('_')])
    return {
        "galvo": GalvoScriptAPI(controllers.get("galvo"), clients.get("galvo")),
        "piezo": PiezoScriptAPI(controllers.get("piezo"), clients.get("piezo")),
        "counter": CounterScriptAPI(controllers.get("counter"), clients.get("counter")),
        "spectrometer": SpectrometerScriptAPI(controllers.get("spectrometer"), clients.get("spectrometer")),
        "galvoClient": clients.get("galvo"),
        "piezoClient": clients.get("piezo"),
        "counterClient": clients.get("counter"),
        "spectrometerClient": clients.get("spectrometer"),
        "range": range, "print": print, "len": len, "int": int,
        "float": float, "str": str, "list": list, "dict": dict,
        "min": min, "max": max, "sum": sum, "round": round,
        "sorted": sorted, "reversed": reversed, "enumerate": enumerate,
        "zip": zip, "map": map, "filter": filter,
        "True": True, "False": False, "None": None,
    }