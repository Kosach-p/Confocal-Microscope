from packages.Сommunication.protocol_controller.BaseModbusDevice import BaseModbusDevice, send_receive
from packages.Controllers.command_structure import device_command_struct
import inspect


class DynamicModbusDevice(BaseModbusDevice):
    def __init__(self, cmd_queue, group: str):
        self.config = {}
        super().__init__(cmd_queue)
        self.device_id = -1
        self.name = ''
        self.name_ru = ''
        self.group = group
        self.echo_enable = False
        self.state = False
        self.interface_id = None
        self._build_methods(device_command_struct.get(group, {}).get('commands', {}))

    def update_config(self, config):
        """Обновляет конфиг без перестроения методов"""
        self.config = config
        self.name = self.config["name"]
        self.name_ru = self.config["name_ru"]
        self.client_attr = self.config["client_attr"]
        self.device_id = self.config["id"]
        self.interface_id = self.config["connection"]["profile"]["id"]

    def _build_methods(self, commands: dict):
        for cmd_name, cmd in commands.items():
            def make_method(cmd_name, cmd):
                send_param_names = [name for name in cmd.get("send", [])]

                def method(**kwargs):
                    if "commands" in self.config:
                        current_cmd = self.config["commands"][cmd_name]
                        if self.state or not self.echo_enable or cmd_name == "ECHO":
                            coder_params = current_cmd.get("coder_params", {})
                            coder_type = current_cmd.get("coder_type")
                            params_list = coder_params.get(coder_type, {}).get('params', []) if coder_type else []
                            for field in params_list:
                                if field["name"] not in kwargs:
                                    if field["name"] != 'echo':
                                        print(f'Не найден параметр {field["name"]} в списке {kwargs}. Функция {cmd_name}')
                                else:
                                    field["value"] = kwargs.get(field["name"], 0)

                            send_receive(
                                cmd_name=cmd_name,
                                device_id=self.device_id,
                                cmd_queue=self.cmd_queue,
                                interface_id=self.interface_id,
                                coder_type=current_cmd.get("coder_type"),
                                coder_params=current_cmd.get("coder_params"),
                                decoder_type=current_cmd.get("decoder_type"),
                                decoder_params=current_cmd.get("decoder_params"),
                                receive_marker=kwargs.get('receive_marker')
                            )

                method.__signature__ = inspect.Signature([
                    inspect.Parameter(name, inspect.Parameter.KEYWORD_ONLY)
                    for name in send_param_names
                ])
                return method

            setattr(self, cmd_name, make_method(cmd_name, cmd))


class DeviceFactory:
    @classmethod
    def create(cls, cmd_queue, group: str):
        client = DynamicModbusDevice(cmd_queue, group)
        return client
