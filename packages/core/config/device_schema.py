"""
Константы, фабрики и лёгкая валидация для конфигурации устройств.
Все константы — str Enum (ведут себя как str, итерируются, JSON-сериализуются).
"""
from enum import Enum
from typing import Optional
import copy


# ======================================================================
# Константы
# ======================================================================

class CoderType(str, Enum):
    BIN = "bin"
    ASCII = "ascii"

    def __str__(self):
        return self.value


class Block(str, Enum):
    START_BYTE = "start_byte"
    ADDRESS = "address"
    COMMAND_CODE = "command_code"
    LENGTH_FIELD = "length_field"
    DATA = "data"
    CHECKSUM = "checksum"
    END_BYTE = "end_byte"

    def __str__(self):
        return self.value


class ChecksumAlgorithm(str, Enum):
    XOR = "XOR"
    SUM = "SUM"
    LRC = "LRC"
    CRC8 = "CRC8"
    CRC16_MODBUS = "CRC16_MODBUS"
    CRC16_CCITT = "CRC16_CCITT"
    CRC16_X25 = "CRC16_X25"
    CRC32 = "CRC32"
    CRC32_MPEG2 = "CRC32_MPEG2"

    def __str__(self):
        return self.value


class Source(str, Enum):
    DATA_ONLY = "data_only"
    COMMAND_AND_DATA = "command_and_data"
    ADDRESS_COMMAND_DATA = "address_command_data"
    FROM_COMMAND = "from_command"
    FROM_ADDRESS = "from_address"
    FROM_LENGTH = "from_length"
    ALL = "all"

    def __str__(self):
        return self.value


class ByteOrder(str, Enum):
    LITTLE = "little"
    BIG = "big"

    def __str__(self):
        return self.value


class DeviceGroup(str, Enum):
    BEAM_STEERERS = "beam_steerers"
    DETECTORS = "detectors"
    POSITIONERS = "positioners"
    SPECTRAL_TUNERS = "spectral_tuners"
    MODULATORS = "modulators"

    def __str__(self):
        return self.value


class ASCIIEncoding(str, Enum):
    ASCII = "ascii"
    UTF8 = "utf-8"
    CP1251 = "cp1251"
    CP866 = "cp866"

    def __str__(self):
        return self.value


class ASCIIAlignment(str, Enum):
    LEFT = "left"
    RIGHT = "right"

    def __str__(self):
        return self.value


class ASCIIFormatType(str, Enum):
    STRING = "s"
    DECIMAL = "d"
    HEX_UPPER = "X"
    HEX_LOWER = "x"
    BINARY = "b"
    OCTAL = "o"
    FLOAT = "f"

    def __str__(self):
        return self.value


class ASCIIDelimiter(str, Enum):
    CRLF = "\r\n"
    LF = "\n"
    CR = "\r"
    NONE = ""
    SPACE = " "
    COMMA = ","
    SEMICOLON = ";"
    TAB = "\t"

    def __str__(self):
        return self.value


# ======================================================================
# Русские названия
# ======================================================================

BLOCK_NAMES_RU = {
    Block.START_BYTE: "Стартовый байт",
    Block.ADDRESS: "Адрес",
    Block.COMMAND_CODE: "Код команды",
    Block.LENGTH_FIELD: "Длина",
    Block.DATA: "Данные",
    Block.CHECKSUM: "Контр. сумма",
    Block.END_BYTE: "Конечный байт",
}

LENGTH_SOURCES = {
    Source.DATA_ONLY: "Только данные",
    Source.COMMAND_AND_DATA: "Команда и данные",
    Source.ADDRESS_COMMAND_DATA: "Адрес, команда и данные",
    Source.FROM_COMMAND: "От команды",
    Source.FROM_ADDRESS: "От адреса",
    Source.FROM_LENGTH: "От длины",
    Source.ALL: "Всё сообщение",
}

CRC_ALGORITHMS = {
    ChecksumAlgorithm.XOR: 1,
    ChecksumAlgorithm.SUM: 1,
    ChecksumAlgorithm.LRC: 1,
    ChecksumAlgorithm.CRC8: 1,
    ChecksumAlgorithm.CRC16_MODBUS: 2,
    ChecksumAlgorithm.CRC16_CCITT: 2,
    ChecksumAlgorithm.CRC16_X25: 2,
    ChecksumAlgorithm.CRC32: 4,
    ChecksumAlgorithm.CRC32_MPEG2: 4,
}

CRC_SOURCES = {
    Source.DATA_ONLY: "Только данные",
    Source.COMMAND_AND_DATA: "Команда и данные",
    Source.ADDRESS_COMMAND_DATA: "Адрес, команда и данные",
    Source.FROM_COMMAND: "От команды",
    Source.FROM_ADDRESS: "От адреса",
    Source.FROM_LENGTH: "От длины",
    Source.ALL: "Всё сообщение",
}

CRC_ALGORITHMS_RU = {
    ChecksumAlgorithm.XOR: "XOR",
    ChecksumAlgorithm.SUM: "Сумма",
    ChecksumAlgorithm.LRC: "LRC",
    ChecksumAlgorithm.CRC8: "CRC-8",
    ChecksumAlgorithm.CRC16_MODBUS: "CRC-16 Modbus",
    ChecksumAlgorithm.CRC16_CCITT: "CRC-16 CCITT",
    ChecksumAlgorithm.CRC16_X25: "CRC-16 X25",
    ChecksumAlgorithm.CRC32: "CRC-32",
    ChecksumAlgorithm.CRC32_MPEG2: "CRC-32 MPEG2",
}

BYTEORDER_NAMES_RU = {
    ByteOrder.LITTLE: "Little-endian",
    ByteOrder.BIG: "Big-endian",
}

CODER_TYPE_NAMES_RU = {
    CoderType.BIN: "Бинарный формат",
    CoderType.ASCII: "ASCII формат",
}

DEVICE_GROUP_NAMES_RU = {
    DeviceGroup.BEAM_STEERERS: "Управление лучом",
    DeviceGroup.DETECTORS: "Детекторы",
    DeviceGroup.POSITIONERS: "Позиционеры",
    DeviceGroup.SPECTRAL_TUNERS: "Спектральные тюнеры",
    DeviceGroup.MODULATORS: "Модуляторы",
}

ASCII_ENCODING_NAMES_RU = {
    ASCIIEncoding.ASCII: "ASCII",
    ASCIIEncoding.UTF8: "UTF-8",
    ASCIIEncoding.CP1251: "Windows-1251",
    ASCIIEncoding.CP866: "DOS (CP866)",
}

ASCII_ALIGNMENT_NAMES_RU = {
    ASCIIAlignment.LEFT: "По левому краю",
    ASCIIAlignment.RIGHT: "По правому краю",
}

ASCII_FORMAT_NAMES_RU = {
    ASCIIFormatType.STRING: "Строка",
    ASCIIFormatType.DECIMAL: "Десятичное",
    ASCIIFormatType.HEX_UPPER: "Шестнадцатеричное (заглавные)",
    ASCIIFormatType.HEX_LOWER: "Шестнадцатеричное (строчные)",
    ASCIIFormatType.BINARY: "Двоичное",
    ASCIIFormatType.OCTAL: "Восьмеричное",
    ASCIIFormatType.FLOAT: "С плавающей точкой",
}

ASCII_DELIMITER_NAMES_RU = {
    ASCIIDelimiter.CRLF: "\\r\\n (CRLF)",
    ASCIIDelimiter.LF: "\\n (LF)",
    ASCIIDelimiter.CR: "\\r (CR)",
    ASCIIDelimiter.NONE: "Нет",
    ASCIIDelimiter.SPACE: "Пробел",
    ASCIIDelimiter.COMMA: "Запятая",
    ASCIIDelimiter.SEMICOLON: "Точка с запятой",
    ASCIIDelimiter.TAB: "Табуляция",
}


# ======================================================================
# Значения по умолчанию
# ======================================================================

BIN_BLOCK_DEFAULTS = {
    Block.START_BYTE: {"use": False, "length": 1, "value": 255},
    Block.ADDRESS: {"use": True, "length": 1},
    Block.COMMAND_CODE: {"use": True, "length": 1},
    Block.LENGTH_FIELD: {"use": False, "length": 1, "include": Source.DATA_ONLY},
    Block.CHECKSUM: {
        "use": True,
        "length": 2,
        "algorithm": ChecksumAlgorithm.CRC16_MODBUS,
        "source": Source.FROM_ADDRESS,
    },
    Block.END_BYTE: {"use": False, "length": 1, "value": 255},
}

ASCII_DEFAULTS = {
    "cmd_prefix": "",
    "cmd_suffix": "",
    "frame_terminator": "",
    "cmd_separator": "",
    "enc": ASCIIEncoding.ASCII,
    "sp_symbols": False,
    "address": {"value": "", "fmt": ASCIIFormatType.STRING, "prefix": "", "suffix": ""},
    "command": {"value": "", "fmt": ASCIIFormatType.STRING, "prefix": "", "suffix": ""},
}

ASCII_PARAM_DEFAULTS = {
    "param_prefix": "",
    "param_suffix": "",
    "param_fmt": ".1f",
    "param_space": 10,
    "param_alignment": ASCIIAlignment.RIGHT,
    "fill_symbol": "0",
}

DEFAULT_ORDER = {
    CoderType.BIN: [
        Block.START_BYTE, Block.ADDRESS, Block.COMMAND_CODE,
        Block.LENGTH_FIELD, Block.DATA, Block.CHECKSUM, Block.END_BYTE,
    ],
    CoderType.ASCII: [
        Block.START_BYTE, Block.ADDRESS, Block.COMMAND_CODE,
        Block.DATA, Block.CHECKSUM, Block.END_BYTE,
    ],
}

CODER_ORDER = {
    CoderType.BIN: [Block.DATA, Block.ADDRESS, Block.COMMAND_CODE, Block.CHECKSUM],
}


# ======================================================================
# Фабрики
# ======================================================================

def make_bin_coder_config(
    command_code: int = 0,
    params: Optional[list[dict]] = None,
    order: Optional[list[str]] = None,
    block_overrides: Optional[dict[str, dict]] = None,
) -> dict:
    """Создаёт конфигурацию BIN кодера."""
    if params is None:
        params = []
    if order is None:
        order = CODER_ORDER.get(CoderType.BIN, [])
    block_overrides = block_overrides or {}

    config = {
        "byteorder": ByteOrder.LITTLE,
        "order": list(order),
        "params": copy.deepcopy(params),
    }

    for block in Block:
        if block == Block.DATA:
            continue
        block_config = copy.deepcopy(BIN_BLOCK_DEFAULTS.get(block, {}))
        if block == Block.COMMAND_CODE:
            block_config["value"] = command_code
        if block in block_overrides:
            block_config.update(block_overrides[block])
        config[block] = block_config

    return config


def make_ascii_coder_config(
    params: Optional[list[dict]] = None,
    ascii_overrides: Optional[dict] = None,
) -> dict:
    """Создаёт конфигурацию ASCII кодера."""
    if params is None:
        params = []

    config = copy.deepcopy(ASCII_DEFAULTS)
    if ascii_overrides:
        config.update(ascii_overrides)

    # Добавляем параметры с ASCII-специфичными полями
    config["params"] = []
    for p in params:
        param_config = copy.deepcopy(ASCII_PARAM_DEFAULTS)
        param_config["name"] = p.get("name", "")
        param_config["value"] = p.get("value", 0)
        config["params"].append(param_config)

    return config


def make_coder_config(
    coder_type: str,
    command_code: int = 0,
    params: Optional[list[dict]] = None,
    order: Optional[list[str]] = None,
    block_overrides: Optional[dict[str, dict]] = None,
    ascii_overrides: Optional[dict] = None,
) -> dict:
    """Универсальная фабрика: создаёт конфигурацию для BIN или ASCII."""
    if coder_type == CoderType.ASCII:
        return make_ascii_coder_config(params=params, ascii_overrides=ascii_overrides)
    else:
        return make_bin_coder_config(
            command_code=command_code,
            params=params,
            order=order,
            block_overrides=block_overrides,
        )


def make_command_config(
    coder_type: str = CoderType.BIN,
    decoder_type: str = CoderType.BIN,
    command_code: int = 0,
    coder_params: Optional[list[dict]] = None,
    decoder_params: Optional[list[dict]] = None,
) -> dict:
    return {
        "coder_type": coder_type,
        "decoder_type": decoder_type,
        "coder_params": {
            coder_type: make_coder_config(
                coder_type=coder_type,
                command_code=command_code,
                params=coder_params or [],
                order=CODER_ORDER.get(coder_type),
            )
        },
        "decoder_params": {
            decoder_type: make_coder_config(
                coder_type=decoder_type,
                command_code=command_code,
                params=decoder_params or [],
            )
        },
    }


def make_parameter(name: str, value: int = 0, length: int = 2, sign: bool = False) -> dict:
    return {"name": name, "value": value, "length": length, "sign": sign}


def make_ascii_parameter(
    name: str,
    value: float = 0,
    param_prefix: str = "",
    param_suffix: str = "",
    param_fmt: str = ".1f",
    param_space: int = 10,
    param_alignment: str = ASCIIAlignment.RIGHT,
    fill_symbol: str = "0",
) -> dict:
    return {
        "name": name,
        "value": value,
        "param_prefix": param_prefix,
        "param_suffix": param_suffix,
        "param_fmt": param_fmt,
        "param_space": param_space,
        "param_alignment": param_alignment,
        "fill_symbol": fill_symbol,
    }


def make_device_config(
    device_id: int,
    name: str,
    name_ru: str,
    group: str,
    client_attr: str,
    commands: dict,
    connection: Optional[dict] = None,
    parameters: Optional[dict] = None,
) -> dict:
    return {
        "id": device_id,
        "name": name,
        "name_ru": name_ru,
        "client_attr": client_attr,
        "commands": commands,
        "connection": {
            "profile": {'id': None},
            "echo_enable": True,
            "poll_interval": 1.0,
        },
        "parameters": parameters or {},
    }


def make_group_config(ru_name: str, devices: list, current_device_id: int = 0) -> dict:
    return {
        "ru": ru_name,
        "devices": devices,
        "current_device_id": current_device_id,
    }


# ======================================================================
# Валидация
# ======================================================================

class ValidationError(Exception):
    pass


def _check_keys_exist(data: dict, required_keys: list, context: str) -> None:
    for key in required_keys:
        if key not in data:
            raise ValidationError(f"{context}: отсутствует ключ '{key}'")


def validate_device_config(device: dict, index: int, group_name: str) -> None:
    ctx = f"Группа '{group_name}', устройство[{index}]"
    _check_keys_exist(device, ["id", "name", "name_ru", "client_attr", "commands", "connection", "parameters"], ctx)
    for cmd_name, cmd in device.get("commands", {}).items():
        _check_keys_exist(cmd, ["coder_type", "decoder_type", "coder_params", "decoder_params"], f"{ctx}, команда '{cmd_name}'")


def validate_group_config(group: dict, group_name: str) -> None:
    ctx = f"Группа '{group_name}'"
    _check_keys_exist(group, ["ru", "devices", "current_device_id"], ctx)
    for i, device in enumerate(group.get("devices", [])):
        validate_device_config(device, i, group_name)


def validate_full_config(config: dict) -> None:
    for group_name, group_data in config.items():
        validate_group_config(group_data, group_name)