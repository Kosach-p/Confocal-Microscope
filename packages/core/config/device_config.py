"""
Доменные объекты для конфигурации устройств.
Тонкая обёртка над словарями — типизированный доступ без копипасты ключей.
"""
from dataclasses import dataclass, field
from typing import Any, Optional
from copy import deepcopy

from packages.core.config.device_schema import *


# ======================================================================
# Параметр команды
# ======================================================================

@dataclass
class Parameter:
    name: str
    value: int = 0
    length: int = 2
    sign: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> 'Parameter':
        return cls(
            name=data.get('name', ''),
            value=data.get('value', 0),
            length=data.get('length', 2),
            sign=data.get('sign', False),
        )

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'value': self.value,
            'length': self.length,
            'sign': self.sign,
        }


# ======================================================================
# Конфигурация кодера (bin/ascii)
# ======================================================================

@dataclass
class CoderConfig:
    coder_type: str = CoderType.BIN
    byteorder: str = ByteOrder.LITTLE
    order: list[str] = field(default_factory=list)
    bin_params: list[Parameter] = field(default_factory=list)
    blocks: dict[str, dict] = field(default_factory=dict)
    cmd_prefix: str = ''
    cmd_suffix: str = ''
    frame_terminator: str = ''
    cmd_separator: str = ''
    enc: str = ASCIIEncoding.ASCII
    sp_symbols: bool = False
    ascii_params: list[dict] = field(default_factory=list)
    address_value: str = ''
    address_fmt: str = 's'
    address_prefix: str = ''
    address_suffix: str = ''
    command_value: str = ''
    command_fmt: str = 's'
    command_prefix: str = ''
    command_suffix: str = ''

    @classmethod
    def from_dict(cls, data: dict, active_type: str) -> 'CoderConfig':
        bin_data = data.get(CoderType.BIN, {})
        ascii_data = data.get(CoderType.ASCII, {})
        blocks = {}
        for key, value in bin_data.items():
            if key in list(Block):
                blocks[key] = deepcopy(value)

        # Извлекаем address и command из ASCII данных
        address_data = ascii_data.get('address', {})
        command_data = ascii_data.get('command', {})

        return cls(
            coder_type=active_type,
            byteorder=bin_data.get('byteorder', ByteOrder.LITTLE),
            order=bin_data.get('order', []),
            bin_params=[Parameter.from_dict(p) for p in bin_data.get('params', [])],
            blocks=blocks,
            cmd_prefix=ascii_data.get('cmd_prefix', ''),
            cmd_suffix=ascii_data.get('cmd_suffix', ''),
            frame_terminator=ascii_data.get('frame_terminator', ''),
            cmd_separator=ascii_data.get('cmd_separator', ''),
            enc=ascii_data.get('enc', ASCIIEncoding.ASCII),
            ascii_params=deepcopy(ascii_data.get('params', [])),
            address_value=address_data.get('value', ''),
            address_fmt=address_data.get('fmt', 's'),
            address_prefix=address_data.get('prefix', ''),
            address_suffix=address_data.get('suffix', ''),
            command_value=command_data.get('value', ''),
            command_fmt=command_data.get('fmt', 's'),
            command_prefix=command_data.get('prefix', ''),
            command_suffix=command_data.get('suffix', ''),
        )

    def to_dict(self) -> dict:
        # Готовим BIN параметры
        bin_dict = {
            'byteorder': self.byteorder,
            'order': list(self.order),
            'params': [p.to_dict() for p in self.bin_params],
            **{k: deepcopy(v) for k, v in self.blocks.items()},
        }
        # Готовим ASCII параметры
        ascii_dict = {
            'cmd_prefix': self.cmd_prefix,
            'cmd_suffix': self.cmd_suffix,
            'frame_terminator': self.frame_terminator,
            'cmd_separator': self.cmd_separator,
            'enc': self.enc,
            'address': {
                'value': self.address_value,
                'fmt': self.address_fmt,
                'prefix': self.address_prefix,
                'suffix': self.address_suffix
            },
            'command': {
                'value': self.command_value,
                'fmt': self.command_fmt,
                'prefix': self.command_prefix,
                'suffix': self.command_suffix
            },
            'params': deepcopy(self.ascii_params),
        }

        return {
            CoderType.BIN: bin_dict,
            CoderType.ASCII: ascii_dict,
        }


# ======================================================================
# Команда
# ======================================================================

@dataclass
class Command:
    name: str
    coder_type: str
    decoder_type: str
    coder: CoderConfig
    decoder: CoderConfig

    @classmethod
    def from_dict(cls, name: str, data: dict) -> 'Command':
        coder_type = data.get('coder_type', CoderType.BIN)
        decoder_type = data.get('decoder_type', CoderType.BIN)

        return cls(
            name=name,
            coder_type=coder_type,
            decoder_type=decoder_type,
            coder=CoderConfig.from_dict(data.get('coder_params', {}), coder_type),
            decoder=CoderConfig.from_dict(data.get('decoder_params', {}), decoder_type),
        )

    def to_dict(self) -> dict:
        return {
            'coder_type': self.coder_type,
            'decoder_type': self.decoder_type,
            'coder_params': self.coder.to_dict(),
            'decoder_params': self.decoder.to_dict(),
        }


# ======================================================================
# Устройство
# ======================================================================

@dataclass
class DeviceConfig:
    id: int
    name: str
    name_ru: str
    group: str
    client_attr: str
    commands: dict[str, Command] = field(default_factory=dict)
    connection: dict = field(default_factory=dict)
    parameters: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict, group: str) -> 'DeviceConfig':
        commands = {}
        for cmd_name, cmd_data in data.get('commands', {}).items():
            commands[cmd_name] = Command.from_dict(cmd_name, cmd_data)

        return cls(
            id=data.get('id', 0),
            name=data.get('name', ''),
            name_ru=data.get('name_ru', ''),
            group=group,
            client_attr=data.get('client_attr', ''),
            commands=commands,
            connection=deepcopy(data.get('connection', {})),
            parameters=deepcopy(data.get('parameters', {})),
        )

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'name_ru': self.name_ru,
            'client_attr': self.client_attr,
            'commands': {name: cmd.to_dict() for name, cmd in self.commands.items()},
            'connection': deepcopy(self.connection),
            'parameters': deepcopy(self.parameters),
        }

    def get_command(self, name: str) -> Optional[Command]:
        return self.commands.get(name)

    def set_parameter(self, key: str, value: Any) -> None:
        self.parameters[key] = value

    def get_parameter(self, key: str, default=None) -> Any:
        return self.parameters.get(key, default)


# ======================================================================
# Группа
# ======================================================================

@dataclass
class GroupConfig:
    name: str
    ru_name: str
    devices: list[DeviceConfig] = field(default_factory=list)
    current_device_id: int = 0

    @classmethod
    def from_dict(cls, name: str, data: dict) -> 'GroupConfig':
        devices = [
            DeviceConfig.from_dict(d, name) for d in data.get('devices', [])
        ]
        return cls(
            name=name,
            ru_name=data.get('ru', name),
            devices=devices,
            current_device_id=data.get('current_device_id', 0),
        )

    def to_dict(self) -> dict:
        return {
            'ru': self.ru_name,
            'devices': [d.to_dict() for d in self.devices],
            'current_device_id': self.current_device_id,
        }

    def get_device_by_id(self, device_id: int) -> Optional[DeviceConfig]:
        for device in self.devices:
            if device.id == device_id:
                return device
        return None


# ======================================================================
# Вся конфигурация
# ======================================================================

@dataclass
class FullConfig:
    groups: dict[str, GroupConfig] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> 'FullConfig':
        groups = {
            name: GroupConfig.from_dict(name, group_data)
            for name, group_data in data.items()
        }
        return cls(groups=groups)

    def to_dict(self) -> dict:
        return {name: group.to_dict() for name, group in self.groups.items()}

    def get_group(self, name: str) -> Optional[GroupConfig]:
        return self.groups.get(name)

    def get_device_by_id(self, device_id: int) -> Optional[DeviceConfig]:
        for group in self.groupss():
            device = group.get_device_by_id(device_id)
            if device:
                return device
        return None

    def get_command(self, device_id: int, command_name: str) -> Optional[Command]:
        device = self.get_device_by_id(device_id)
        if device:
            return device.get_command(command_name)
        return None