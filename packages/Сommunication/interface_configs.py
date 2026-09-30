interfaces = {
    'ser': 'serial',
    'eth': 'ethernet'
}

interfaces_name = {
    'ser': {'ru': 'COM порт', 'en': 'serial', 'icon': '🖱'},
    'eth': {'ru': 'Ethernet', 'en': 'ethernet', 'icon': '🖧'}
}

interfaces_config = {
    # ============================================================
    # SERIAL (COM порт)
    # ============================================================
    'ser': {
        'type': 'serial',
        'common': {
            'Write_timeout': 0.01,  # Таймаут записи (сек)
            'Read_timeout': 0.01,  # Таймаут чтения (сек)
            'CRC_en': True  # Включить проверку CRC
        },
        'specific': {
            'COM': "COM3",  # Имя COM-порта
            'BaudRate': 115200,  # Скорость передачи (бод)
            'Word_Length': 8,  # Длина слова (бит)
            'Parity': None,  # Четность: None, 'Even', 'Odd', 'Mark', 'Space'
            'Stop_Bits': 0,  # Стоп-биты: 0, 1, 2
            'XonXoff_en': False  # Включить XON/XOFF управление потоком
        }
    },

    # ============================================================
    # ETHERNET (сетевое подключение)
    # ============================================================
    'eth': {
        'type': 'ethernet',
        'common': {
            'Write_timeout': 0.1,  # Таймаут записи (сек)
            'Read_timeout': 0.001,  # Таймаут чтения (сек)
            'CRC_en': True  # Включить проверку CRC
        },
        'specific': {
            'IP': "192.168.1.100",  # IP-адрес устройства
            'Port': 502,  # Порт подключения
            'Timeout': 5.0  # Таймаут соединения (сек)
        }
    },
}

interfaces_class = {
    'ser': None,

    'eth': None
}

# ============================================================
# Шаблоны команд
# ============================================================

COMMAND_TEMPLATES = {
    # Команда подключения
    'connect': {
        'command': 'connect',
        'interface': None,  # 'serial', 'ethernet', 'ftdi'
        'params': {}  # Параметры для конкретного интерфейса
    },

    # Команда отправки/получения
    'send_receive': {
        'command': 'send_receive',
        'interface_id': None,  # ID интерфейса
        'params': {  # Параметры send_receive
            'slave_id': None,
            'command': None,
            'data': [],
            'format': 'binary',
            'expected_send_size': [],
            'expected_receive_size': [],
            'send_alignment': [],
            'send_sign': [],
            'receive_alignment': [],
            'receive_sign': [],
            'receive_marker': ''
        }
    },

    # Команда отключения
    'disconnect': {
        'command': 'disconnect',
        'interface_id': None
    },

    # Команда остановки
    'stop': {
        'command': 'stop'
    },

    # Команда открытия интерфейса
    'open': {
        'command': 'open',
        'id': None
    },

    # Команда закрытия интерфейса
    'close': {
        'command': 'close',
        'id': None
    }
}

# ============================================================
# коды ошибок
# ============================================================

PORT_NOT_EXISTS = 1
PORT_EXISTS_NOT_OPEN = 2
PORT_EXISTS_AND_OPEN = 3

SENDING_ERROR = 10
PACK_ERROR = 11

RECEPTION_ERROR = 20
NO_DATA = 21
LITTLE_DATA = 22
CRC_ERROR = 23
UNKNOWN_FORMAT = 24
UNPACK_ERROR = 25
