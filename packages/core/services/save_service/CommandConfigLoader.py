# packages/communication/protocol_controller/CommandConfigLoader.py
from typing import Dict, List, Optional
import json
import os
from packages.core.config.path import CONFIG_DIR, filepath_in_dir


class DeviceConfigController:
    def __init__(self, device_name: str = ""):
        self.device_name = device_name
        self.filepath = filepath_in_dir(CONFIG_DIR, f"devices_settings.json")

    def load(self) -> Optional[dict]:
        with open(self.filepath, 'r', encoding='utf-8') as f:
            configs = json.load(f)

        config = configs.get(self.device_name)
        current_device = config.get('current_device', 0)
        return config.get('devices')[current_device]
