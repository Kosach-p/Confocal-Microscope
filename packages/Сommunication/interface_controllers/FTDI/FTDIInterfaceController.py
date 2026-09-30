# FTDIInterfaceController.py

from packages.Сommunication.interface_controllers.BaseInterfaceController import CommunicationInterface


PORT_NOT_EXISTS = 0x01
PORT_EXISTS_NOT_OPEN = 0x02
PORT_EXISTS_AND_OPEN = 0x03


class FTDIInterfaceController(CommunicationInterface):

    def __init__(self):
        super().__init__()
        self.device_index = None

    def connect(self, connection_params: dict) -> bool:
        try:
            import ftd2xx
        except ImportError:
            print("FTDI::connect::библиотека ftd2xx не установлена")
            return False

        if self.client is not None:
            try:
                self.client.close()
            except:
                pass
            self.client = None

        try:
            self.device_index = connection_params.get("device_index", 0)
            baudrate = connection_params.get("BaudRate", 115200)
            write_timeout = int(connection_params.get("Write_timeout", 0.1) * 1000)
            read_timeout = int(connection_params.get("Read_timeout", 0.5) * 1000)

            self.client = ftd2xx.open(self.device_index)
            self.client.setBaudRate(baudrate)
            self.client.setDataCharacteristics(
                ftd2xx.defines.BITS_8,
                ftd2xx.defines.STOP_BITS_1,
                ftd2xx.defines.PARITY_NONE
            )
            self.client.setTimeouts(read_timeout, write_timeout)
            self.client.setLatencyTimer(1)
            self.client.setUSBParameters(4096, 4096)

            self.connection_params = connection_params
            self.CRC_enable = connection_params.get("CRC_en", True)
            return True
        except Exception as e:
            print(f"FTDI::connect::ERROR:: {e}")
            self.client = None
            return False

    def disconnect(self):
        if self.client:
            try:
                self.client.close()
            except:
                pass
            self.client = None
        self.device_index = None

    def reconnect(self):
        if self.connection_params:
            self.connect(self.connection_params)

    def is_connected(self) -> bool:
        return self.client is not None

    def _write(self, data: bytes):
        self.client.write(data)

    def _read(self, size: int) -> bytes:
        raw = self.client.read(size)
        return bytes(raw) if raw else b""

    def _readline(self):
        raw = self.client.readline()
        if raw is None:
            return "Пупупу"
        return raw

    def get_available_devices_inf(self):
        try:
            import ftd2xx
            num_devices = ftd2xx.createDeviceInfoList()
            devices = []
            for i in range(num_devices):
                info = ftd2xx.getDeviceInfoDetail(i)
                devices.append({
                    "index": i,
                    "inf": info.get("description", "Unknown").decode("utf-8", errors="ignore"),
                    "serial": info.get("serial", "N/A").decode("utf-8", errors="ignore"),
                    "VID:PID": f"{info.get('id', 0):08X}"
                })
            return devices
        except ImportError:
            return []

    def get_available_devices(self):
        return [d["index"] for d in self.get_available_devices_inf()]

    def get_current_connection_info(self):
        return {
            "device_index": self.device_index,
            "baudrate": self.connection_params.get("BaudRate") if self.connection_params else None
        }

    def get_current_device(self):
        return self.device_index

    def check_port(self):
        available = self.get_available_devices()
        if self.device_index is not None and self.device_index in available:
            return PORT_EXISTS_AND_OPEN
        return PORT_NOT_EXISTS
