"""
Сервис для хранения состояния приложения.
Отдельно от конфигурации устройств.
"""
import json
import os
from copy import deepcopy

APP_STATE_PATH = 'service_files/settings/app_state.json'

DEFAULT_APP_STATE = {
    "current_device_ids": {}
}


def load_app_state() -> dict:
    """Загружает состояние приложения"""
    if not os.path.exists(APP_STATE_PATH):
        return deepcopy(DEFAULT_APP_STATE)

    try:
        with open(APP_STATE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return deepcopy(DEFAULT_APP_STATE)


def save_app_state(state: dict) -> None:
    """Сохраняет состояние приложения атомарно"""
    os.makedirs(os.path.dirname(APP_STATE_PATH), exist_ok=True)

    temp_path = APP_STATE_PATH + '.tmp'

    try:
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_path, APP_STATE_PATH)
    except Exception:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise


def get_current_device_id(group: str) -> int | None:
    """Возвращает ID текущего устройства для группы или None"""
    state = load_app_state()
    return state.get("current_device_ids", {}).get(group)


def set_current_device_id(group: str, device_id: int) -> None:
    """Устанавливает ID текущего устройства для группы"""
    state = load_app_state()
    if "current_device_ids" not in state:
        state["current_device_ids"] = {}
    state["current_device_ids"][group] = device_id
    save_app_state(state)


def get_all_active_ids() -> dict[str, int]:
    """Возвращает {group_key: device_id} для всех групп"""
    state = load_app_state()
    return state.get("current_device_ids", {})