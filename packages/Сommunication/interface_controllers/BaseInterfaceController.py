import time
from abc import ABC, abstractmethod
from packages.Сommunication.interface_controllers.CommandCalc import *
import numpy as np
from packages.Сommunication.interface_configs import *

import logging

logger = logging.getLogger(__name__)


class CommunicationInterface():
    """Интерфейс для любого типа связи с устройствами"""

    def __init__(self):
        self.client = None
        self.connection_params = {}
        self.CRC_enable = True
        self.recovery_attempts_num = 3

        self.crc_table = np.zeros((256), dtype=np.uint16)
        self._generate_crc_table()
        
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.a = 0

    # ======================== Абстрактные методы ========================

    @abstractmethod
    def connect(self, connection_params: dict) -> bool:
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        pass

    @abstractmethod
    def _write(self, data: bytes):
        """Низкоуровневая запись байт"""
        pass

    @abstractmethod
    def _read(self, size: int) -> bytes:
        """Низкоуровневое чтение байт"""
        pass

    @abstractmethod
    def _readline(self) -> bytes:
        """Низкоуровневое чтение байт"""
        pass

    @abstractmethod
    def _read_all(self) -> bytes:
        """Низкоуровневое чтение всех данных, что придут"""
        pass

    @abstractmethod
    def _read_until(self, suffix: str) -> bytes:
        """Низкоуровневое чтение всех данных, что придут"""
        pass

    @abstractmethod
    def get_available_devices_inf(self) -> list:
        pass

    @abstractmethod
    def get_available_devices(self) -> list:
        pass

    @abstractmethod
    def get_current_connection_info(self) -> dict:
        pass

    @abstractmethod
    def get_current_device(self):
        pass

    @abstractmethod
    def get_info(self):
        pass

    @abstractmethod
    def check_port(self):
        pass

    @abstractmethod
    def reconnect(self):
        pass

    # ======================== Общие методы ========================

    def send_receive(self, **params):
        """ Метод, который реализует передачу и приём всего """
        self.client.reset_input_buffer()
        self.client.reset_output_buffer()
        receive_marker = params['receive_marker']

        if params.get('coder_type') is not None:
            # ======================================== КОДИРОВКА ========================================
            if params.get('coder_type') == 'bin':
                request = bin_coder(**params.get('coder_params').get('bin'))
            elif params.get('coder_type') == 'ascii':
                request = ascii_coder(**params.get('coder_params').get('ascii'))
            else:
                return {
                    'receive_marker': receive_marker,
                    'answer': False,
                    'report': f"Не удалось закодировать, несуществующий кодер {params.get('coder_type')}. Выберите из bin и ascii"
                }
                # ======================================== ОТПРАВКА ========================================
            if request['error'] is False:
                try:
                    self._write(request['result'])
                except Exception as e:
                    return {'answer': False, 'report': f"Ошибка отправки::{e}"}
            else:
                return {'answer': False, 'report': f"Ошибка при кодировке {request}"}

            if params.get('decoder_type') is not None:
                # ================================== РАЗМЕР ПРИНИМАЕМОГО ПАКЕТА ========================================
                if params.get('decoder_type') == 'bin':
                    request = bin_decoder_expected_length(**params.get('decoder_params').get('bin'))
                    cmd = self._read(request["result"])
                elif params.get('decoder_type') == 'ascii':
                    cmd = self._read_all()
                else:
                    return {
                    'receive_marker': receive_marker,
                    'answer': False,
                    'report': f"Не удалось декодировать, несуществующий кодер {params.get('coder_type')}. Выберите из bin и ascii"
                    }
                # ======================================== ДЕКОДИРОВКА ========================================
                if params.get('decoder_type') == 'bin':
                    decoded = bin_decoder(cmd=cmd, **params.get('decoder_params').get('bin'))
                elif params.get('decoder_type') == 'ascii':
                    decoded = ascii_decoder(cmd=cmd, **params.get('decoder_params').get('ascii'))
                else:
                    return {
                    'receive_marker': receive_marker,
                    'answer': False,
                    'report': f"Не удалось декодировать, несуществующий кодер {params.get('coder_type')}. Выберите из bin и ascii"
                    }
                if decoded['error']:
                    address = params.get('decoder_params').get('bin').get('address').get('value')
                    command_code = params.get('decoder_params').get('bin').get('command_code').get('value')
                    device_id = params.get('device_id')
                    return {
                        'receive_marker': receive_marker,
                        'answer': not decoded['error'],
                        'report': {'device_id': device_id, 'address': address, 'command_code': command_code, 'params': None, 'info': decoded['result']}
                    }
                else:
                    device_id = params.get('device_id')
                    decoded['result']['device_id'] = device_id
                    return {
                        'receive_marker': receive_marker,
                        'answer': not decoded['error'],
                        'report': decoded['result']
                    }
        else:
            return {
                'receive_marker': receive_marker,
                'answer': False,
                'report': f"Кодер не указан!"
            }
    def _pack_data_bin(self, data: list[int], expected_size: list[int], alignment: list[str],
                       sign: list[bool]) -> bytearray:
        """Упаковка данных в бинарный формат"""
        data_bytes = bytearray()
        for i, (value, size) in enumerate(zip(data, expected_size)):
            if size == 0:
                continue
            try:
                data_bytes += value.to_bytes(size, byteorder=alignment[i], signed=sign[i])
            except OverflowError:
                print(f"{self.__class__.__name__}::Значение {value} не помещается в {size} байт")
                raise
        return data_bytes

    def _pack_data_ascii(self, data: list[int], expected_size: list[int], alignment: list[str],
                         sign: list[bool]) -> bytearray:
        """Упаковка данных в ASCII формат"""
        data_bytes = bytearray()
        for i, (value, size) in enumerate(zip(data, expected_size)):
            if size == 0:
                continue

            str_value = str(value)

            # Выравнивание
            if alignment[i] == "left":
                str_value = str_value.ljust(size)
            elif alignment[i] == "right":
                str_value = str_value.rjust(size)
            elif alignment[i] == "center":
                str_value = str_value.center(size)
            else:
                str_value = str_value.rjust(size)

            # Обрезаем, если длиннее size
            if len(str_value) > size:
                str_value = str_value[:size]
                print(f"{self.__class__.__name__}::Предупреждение: значение {value} обрезано до {size} символов")

            data_bytes += str_value.encode('ascii')

        return data_bytes

    def _unpack_data_bin(self, payload: bytes, expected_size: list[int], alignment: list[str], sign: list[bool]) -> \
    list[int]:
        """Распаковка данных из бинарного формата"""
        data = []
        pos = 0
        for i, size in enumerate(expected_size):
            if pos + size > len(payload):
                raise ValueError("Недостаточно данных")
            value_bytes = payload[pos:pos + size]
            al = alignment[i] if isinstance(alignment[i], str) else alignment[i][0]
            sg = sign[i] if isinstance(sign[i], bool) else sign[i][0]
            data.append(int.from_bytes(value_bytes, byteorder=al, signed=sg))
            pos += size
        return data

    def _unpack_data_ascii(self, payload: bytes, expected_size: list[int], alignment: list[str], sign: list[bool]) -> \
    list[int]:
        """Распаковка данных из ASCII формата"""
        data = []
        pos = 0
        for i, size in enumerate(expected_size):
            if pos + size > len(payload):
                raise ValueError("Недостаточно данных")

            str_bytes = payload[pos:pos + size]
            str_value = str_bytes.decode('ascii', errors='replace').strip()

            try:
                value = int(str_value)
            except ValueError:
                print(f"{self.__class__.__name__}::Не удалось преобразовать '{str_value}' в число")
                value = 0

            data.append(value)
            pos += size
        return data

    def send(self, slave_id: int, command: int, data: list[int], expected_size: list[int], alignment: list[str],
             sign: list[bool], fmt: str):
        if not self.is_connected:
            return {'answer': False, 'report': PORT_EXISTS_NOT_OPEN}

        try:
            if 'bin' in fmt:
                data_bytes = self._pack_data_bin(data, expected_size, alignment, sign)
            elif fmt == "ascii":
                data_bytes = self._pack_data_ascii(data, expected_size, alignment, sign)
            else:
                return {'answer': False, 'report': UNKNOWN_FORMAT}
        except Exception as e:
            return {'answer': False, 'report': PACK_ERROR}

        request = bytes([slave_id, command]) + data_bytes

        if self.CRC_enable:
            crc = self._calculate_crc(request)
            request += bytes([crc & 0xFF, (crc >> 8) & 0xFF])

        try:
            self._write(request)
            return {'answer': True, 'report': True}
        except Exception as e:
            return {'answer': False, 'report': CRC_ERROR}

    def receive(self, expected_size: list[int], alignment: list[str], sign: list[bool], fmt: str):
        if not self.is_connected:
            return {'answer': False, 'report': PORT_EXISTS_NOT_OPEN}

        read_size = 4 + sum(expected_size) if self.CRC_enable else 2 + sum(expected_size)

        try:
            raw_data = self._read(read_size)
        except Exception as e:
            return {'answer': False, 'report': RECEPTION_ERROR}

        if not raw_data or len(raw_data) == 0:
            return {'answer': False, 'report': NO_DATA}

        raw_bytes = bytes(raw_data)

        if self.CRC_enable:
            if len(raw_bytes) < 4:
                return {'answer': False, 'report': LITTLE_DATA}
            received_crc = int.from_bytes(raw_bytes[-2:], 'little')
            calculated_crc = self._calculate_crc(raw_bytes[:-2])
            if received_crc != calculated_crc:
                return {'answer': False, 'report': CRC_ERROR}
            slave_id = raw_bytes[0]
            command_echo = raw_bytes[1]
            payload = raw_bytes[2:-2]
        else:
            slave_id = raw_bytes[0]
            command_echo = raw_bytes[1]
            payload = raw_bytes[2:]

        try:
            if 'bin' in fmt:
                data = self._unpack_data_bin(payload, expected_size, alignment, sign)
            elif fmt == "ascii":
                data = self._unpack_data_ascii(payload, expected_size, alignment, sign)
            else:
                print(f"{self.__class__.__name__}::receive::Неизвестный формат: {fmt}")
                return {'answer': False, 'report': UNKNOWN_FORMAT}
        except Exception as e:
            return {'answer': False, 'report': UNPACK_ERROR}

        return {'answer': True, 'report': {'slave_id': slave_id, 'command_echo': command_echo, 'data': data}}

    def simple_send(self, slave_id, data, expected_size):
        """ Простая отправка, без разбиения на байты """
        message = ""
        if expected_size[0] is True:
            message += f"{slave_id}"

        if expected_size[1] is True:
            message += f"{data}"

        if expected_size[2] is True:
            message += f"{self._calculate_crc(message.encode())}"

        #self._write(message.encode('ascii'))

    def simple_receive(self, slave_id):
        """ Простой приём, без разбиения на байты и без команды """
        command_echo = None
        data = self._read_all()
        return [slave_id, command_echo, data]

    def _calculate_crc(self, data: bytes) -> int:
        crc = np.uint16(0xFFFF)
        for byte in data:
            crc = (crc >> 8) ^ self.crc_table[(crc ^ byte) & 0xFF]
        return crc

    def _generate_crc_table(self):
        for bit_nun in range(0, 256):
            crc = bit_nun
            for _ in range(0, 8):
                if crc & 0x0001:
                    crc >>= 1
                    crc ^= 0xA001
                else:
                    crc >>= 1
            self.crc_table[bit_nun] = crc