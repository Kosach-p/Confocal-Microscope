# packages/core/paths.py
import sys
from pathlib import Path
from ui.ControllerSettings.GalvoSettings import Ui_GroupBox as GalvoSettings
from ui.ControllerSettings.PiezoSettings import Ui_GroupBox as PiezoSettings
from ui.ControllerSettings.PhotonCounterSettings import Ui_GroupBox as PhotonCounterSettings
from ui.ControllerSettings.StepperMotorSettings import Ui_GroupBox as StepperMotorSettings


if getattr(sys, 'frozen', False):
    ROOT = Path(sys.executable).parent
else:
    # Если запущено как скрипт — ищем main.py
    ROOT = Path(sys.argv[0]).resolve().parent

UI_DIR = ROOT / "ui"
ICONS_DIR = ROOT / "Icon"
THEMES_DIR = ROOT / "themes"
CONFIG_DIR = ROOT / "service_files" / "settings" / "devices"
UI_SETTINGS_DIR = ROOT / "service_files" / "settings" / "UI_settings"
UI_SETTINGS_PATH = ROOT / "service_files" / "settings" / "UI_settings" / "UI_settings.ini"
CONN_SETTINGS_DIR = ROOT / "service_files" / "settings" / "connections"
CONN_SETTINGS_PATH = ROOT / "service_files" / "settings" / "connections" / "settings.json"

ParametersWidget_dict = {
    'GalvoSettings': GalvoSettings,
    'PiezoSettings': PiezoSettings,
    'PhotonCounterSettings': PhotonCounterSettings,
    'StepperMotorSettings': StepperMotorSettings,
}

def ui(name: str) -> str:
    path = UI_DIR / name
    if path.exists():
        return str(path)

    path = ROOT / name
    if path.exists():
        return str(path)

    for found in ROOT.rglob(name):
        return str(found)
    print(f"paths::ui::Не найден файл: {name}")
    return None


def icon(name: str) -> str:
    if name == "":
        return None
    return str(ICONS_DIR / name)


def UI_settings(name: str) -> str:
    if name == "":
        return None
    path = UI_SETTINGS_DIR / name
    if path.exists():
        return str(path)

    path = ROOT / name
    if path.exists():
        return str(path)

    for found in ROOT.rglob(name):
        return str(found)
    print(f"paths::UI_settings::Не найден файл: {name}")
    return None


def filepath_in_dir(dir: str, name: str) -> str:
    if dir == "" or name == "":
        return None
    path = Path(dir) / name
    if path.exists():
        return str(path)

    path = ROOT / name
    if path.exists():
        return str(path)

    for found in ROOT.rglob(name):
        return str(found)
    print(f"paths::filepath_in_dir::Не найден файл: {name}")
    return None


def create_file_in_dir(dir: str, name: str) -> str:
    if dir == "" or name == "":
        return None
    path = Path(dir) / name
    if path.exists():
        return str(path)
    else:
        filepath = Path(path)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.touch()
        return str(path)
