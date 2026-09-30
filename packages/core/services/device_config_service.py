"""
Сервис для загрузки/сохранения конфигурации устройств.
Единственная точка входа для работы с файлом конфигурации.
"""
import json
import os
import portalocker
from copy import deepcopy
from typing import Callable

from packages.core.config.device_schema import validate_full_config, ValidationError

CONFIG_PATH = 'service_files/settings/devices/devices_settings.json'


class ConfigError(Exception):
    """Базовая ошибка конфигурации"""
    pass


class ConfigLoadError(ConfigError):
    """Ошибка загрузки"""
    pass


class ConfigSaveError(ConfigError):
    """Ошибка сохранения"""
    pass


class ConfigValidationError(ConfigError):
    """Ошибка валидации"""
    pass


# ======================================================================
# Низкоуровневые операции с файлом
# ======================================================================

def _read_json(filepath: str) -> dict:
    """Читает JSON из файла."""
    if not os.path.exists(filepath):
        raise ConfigLoadError(f"Файл конфига устройств не найден")

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            portalocker.lock(f, portalocker.LOCK_SH)
            data = json.load(f)
            portalocker.unlock(f)
        return data
    except json.JSONDecodeError as e:
        raise ConfigLoadError(f"Повреждённый JSON: {e}")
    except Exception as e:
        raise ConfigLoadError(f"Ошибка чтения: {e}")

def _write_json_atomic(filepath: str, data: dict) -> None:
    """Атомарная запись JSON через временный файл."""
    temp_path = filepath + '.tmp'

    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    try:
        with open(temp_path, 'w', encoding='utf-8') as f:
            portalocker.lock(f, portalocker.LOCK_EX)
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
            portalocker.unlock(f)

        os.replace(temp_path, filepath)

    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise ConfigSaveError(f"Ошибка записи: {e}")


# ======================================================================
# Публичный API
# ======================================================================

def load_config(validate: bool = True) -> dict:
    """
    Загружает конфигурацию из файла.
    Возвращает ГЛУБОКУЮ КОПИЮ.
    """
    data = _read_json(CONFIG_PATH)
    if validate:
        try:
            validate_full_config(data)
        except ValidationError as e:
            raise ConfigValidationError(f"Конфигурация не прошла валидацию: {e}")

    return deepcopy(data)


def save_config(config: dict, validate: bool = True) -> None:
    """Сохраняет конфигурацию в файл атомарно."""
    if validate:
        try:
            validate_full_config(config)
        except ValidationError as e:
            import pprint
            pprint.pprint(config, indent=4)
            raise ConfigValidationError(f"Попытка сохранить невалидный конфиг: {e}")

    _write_json_atomic(CONFIG_PATH, config)


def load_or_create_config(default_factory: Callable[[], dict]) -> dict:
    """Загружает конфиг. Если файла нет — создаёт из default_factory и сохраняет."""
    try:
        return load_config()
    except ConfigLoadError:
        config = default_factory()
        try:
            validate_full_config(config)
        except ValidationError as e:
            raise ConfigValidationError(f"Дефолтная конфигурация невалидна: {e}")
        save_config(config, validate=False)
        return deepcopy(config)


def save_full_state(config: dict, active_device_ids: dict[str, int]) -> None:
    """
    Сохраняет конфиг + active_device_ids атомарно.

    Args:
        config: полная конфигурация устройств
        active_device_ids: {group_key: device_id}
    """
    from packages.core.services.app_state_config import save_app_state

    save_config(config)

    state = {'current_device_ids': active_device_ids}
    save_app_state(state)