import serial
import serial.tools.list_ports
from packages.Сommunication.interface_controllers.BaseInterfaceController import *
import pprint

DEVELOPER_MODE = False
GOOD_PRINT_MODE = True


def ppprint(values):
    if DEVELOPER_MODE:
        if GOOD_PRINT_MODE:
            pprint.pprint(values, indent=2)
        else:
            print(values)


class SerialInterfaceController(CommunicationInterface):

    def __init__(self):
        super().__init__()
        self.serial_port = ''

    def connect(self, connection_params: dict) -> bool:
        if self.client is not None:
            try:
                self.client.close()
            except:
                pass
            self.client = None

        try:
            if type(connection_params['port']) is dict:
                port = connection_params['port'].get('device', None)
            else:
                port = connection_params['port']

            if port is not None:
                self.connection_params = connection_params
                self.serial_port = port

                self.client = serial.Serial(
                    port=port,
                    baudrate=connection_params["baudrate"],
                    parity=connection_params["parity"],
                    stopbits=connection_params["stop_bits"],
                    write_timeout=connection_params["write_timeout"],
                    timeout=connection_params["read_timeout"],
                    xonxoff=connection_params.get("xonxoff", False)
                )
                if self.client.is_open:
                    self.crc_enable = connection_params.get("crc_en", True)
                    ppprint(f"SerialInterfaceController::connect::Успешно подключились {self.serial_port}")
                    return True
                return False
        except Exception as e:
            ppprint(f"SerialInterfaceController::connect::ERROR:: {port} {e}")
            return False

    def disconnect(self):
        if self.client and self.client.is_open:
            self.client.close()
        self.client = None

    def reconnect(self):
        if self.connection_params:
            self.connect(self.connection_params)

    def is_connected(self) -> bool:
        return self.client is not None and self.client.is_open

    def _write(self, data: bytes):
        #print()
        #print(data.hex("|"))
        #print(self.serial_port)
        #print()
        return self.client.write(data)

    def _read(self, size: int) -> bytes:
        a = ''
        try:
            a = self.client.read(size)
        except Exception as e:
            print(e)
        return a

    def _read_all(self) -> bytes:
        return self.client.readline()

    def _read_until(self, suffix) -> bytes:
        return self.client.read_until(suffix)

    def get_available_devices_inf(self):
        ports = serial.tools.list_ports.comports()
        return [{'port': port, "inf": desc, "VID:PID": hwid} for port, desc, hwid in ports]

    def get_available_devices(self):
        return [port for port, _, _ in serial.tools.list_ports.comports()]

    def get_current_connection_info(self):
        return {
            "port": self.serial_port,
            "baudrate": self.connection_params.get("baudrate") if self.connection_params else None
        }

    def get_current_device(self):
        return self.serial_port

    def check_port(self):
        port_list = self.get_available_devices()

        if self.serial_port is not None:
            if self.serial_port in port_list:
                try:
                    if self.client and self.client.is_open:
                        return PORT_EXISTS_AND_OPEN
                    else:
                        self.reconnect()
                        if self.client and self.client.is_open:
                            return PORT_EXISTS_AND_OPEN
                        return PORT_EXISTS_NOT_OPEN
                except:
                    return PORT_EXISTS_NOT_OPEN
            else:
                try:
                    if self.client and self.client.is_open:
                        self.disconnect()
                except:
                    pass
                return PORT_NOT_EXISTS
        return PORT_NOT_EXISTS

    def get_info(self) -> dict:
        """Возвращает информацию о COM-портах и текущем подключении"""
        available_ports = []
        for port in serial.tools.list_ports.comports():
            available_ports.append({
                'device': port.device,
                'description': port.description,
                'hwid': port.hwid,
                'vid': port.vid,
                'pid': port.pid,
                'serial_number': port.serial_number,
                'manufacturer': port.manufacturer,
                'product': port.product,
                'interface': port.interface,
                'location': port.location,
            })

        return {
            'current_port': self.serial_port,  # К какому порту подключены (или None)

            # === Статистика текущего подключения ===
            'is_open': self.is_connected(),
            'port_state': self.check_port(),
            'baudrate': self.connection_params.get('baudrate'),
            'parity': self.connection_params.get('parity'),
            'stop_bits': self.connection_params.get('stop_bits'),
            'write_timeout': self.connection_params.get('write_timeout'),
            'read_timeout': self.connection_params.get('read_timeout'),
            'xonxoff':  self.connection_params.get('xonxoff'),

            # === Список доступных устройств ===
            'available_ports': available_ports,
            'ports_count': len(available_ports),

            # === Выделенные списки для UI ===
            'ports_list': [p['device'] for p in available_ports],  # ["COM1", "COM3", "COM5"]
            'ports_descriptions': {p['device']: p['description'] for p in available_ports},
        }