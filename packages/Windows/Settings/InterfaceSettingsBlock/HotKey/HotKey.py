from packages.Windows.Settings.InterfaceSettingsBlock.HotKey.HotKey_Table import HotkeyTable
from PyQt6.QtWidgets import QPushButton, QHBoxLayout, QSpacerItem, QSizePolicy
from packages.core.services.save_service.SettingsSave_service import SettingsSaver
from packages.core.config.path import UI_SETTINGS_DIR


DEFAULT_SHORTCUTS = {
    "Main Window": {
        "name_ru": "Главное окно",
        "actions": {
            "file.open": {"name_ru": "Открыть файл", "keys": "Ctrl+O"},
            "file.save": {"name_ru": "Сохранить", "keys": "Ctrl+S"},
            "file.save_as": {"name_ru": "Сохранить как", "keys": "Ctrl+Shift+S"},
            "file.save_all": {"name_ru": "Сохранить всё", "keys": "Ctrl+Alt+S"},
            "view.fullscreen": {"name_ru": "Полный экран", "keys": "F11"},
            "view.2d": {"name_ru": "2D вид", "keys": "Ctrl+1"},
            "view.spectrometer": {"name_ru": "Спектрометр", "keys": "Ctrl+3"},
            "view.odmr": {"name_ru": "ODMR спектрометр", "keys": "Ctrl+4"},
            "view.gcode": {"name_ru": "Gcode", "keys": "Ctrl+5"},
            "floatwindow.node": {"name_ru": "Открыть редактор нод", "keys": "Ctrl+Shift+Alt+N"},
            "floatwindow.script": {"name_ru": "Открыть редактор скриптов", "keys": "Ctrl+Shift+Alt+S"},
            "settings.help": {"name_ru": "Руководство пользователя", "keys": "Ctrl+H"}
        }
    },
    "settings": {
        "name_ru": "Настройки",
        "actions": {
            "settings.interface": {"name_ru": "Настройки интерфейса", "keys": "Ctrl+1"},
            "settings.connection": {"name_ru": "Настройки подключения", "keys": "Ctrl+2"},
            "settings.device": {"name_ru": "Настройки устройств", "keys": "Ctrl+3"},
            "settings.save": {"name_ru": "Настройки сохранения", "keys": "Ctrl+4"}
        }
    },
    "editors": {
        "name_ru": "Редакторы",
        "actions": {
            "node_editor.show": {"name_ru": "Нодовый редактор", "keys": "Ctrl+Shift+N"},
        }
    },
}


class HotKey:
    name = "HotKey"

    def __init__(self, frame, event_bus):
        self.table = HotkeyTable(frame)
        self.event_bus = event_bus

        btn_layout = QHBoxLayout()
        spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        btn_layout.addSpacerItem(spacer)

        reset_btn = QPushButton("Сбросить")
        reset_btn.setMinimumHeight(22)
        reset_btn.setMaximumHeight(22)
        reset_btn.clicked.connect(self.reset_defaults)
        btn_layout.addWidget(reset_btn)

        frame.layout().insertLayout(0, btn_layout)

    def get_settings(self) -> dict:
        """Собирает все горячие клавиши с UI и возвращает в формате DEFAULT_SHORTCUTS"""
        table = {}
        for row in range(self.table.rowCount()):
            action_item = self.table.item(row, 0)
            shortcut_item = self.table.item(row, 1)
            if action_item is None or shortcut_item is None:
                continue
            action = action_item.text()
            shortcut = shortcut_item.text()
            if shortcut and action:
                table[action] = shortcut

        result = {}
        for category_id, category_data in DEFAULT_SHORTCUTS.items():
            result[category_id] = {"name_ru": category_data["name_ru"], "actions": {}}
            for action_id, action_data in category_data["actions"].items():
                name = action_data["name_ru"]
                result[category_id]["actions"][action_id] = {
                    "name_ru": name,
                    "keys": table.get(name, action_data["keys"])
                }
        return result

    def set_settings(self, shortcuts: dict):
        """Заполняет UI таблицу из словаря shortcuts"""
        self.table.reset_defaults()
        self._fill_shortcuts(shortcuts)

    def _fill_system_shortcuts(self):
        self.set_settings(DEFAULT_SHORTCUTS)

    def _fill_shortcuts(self, shortcuts):
        for category_id, category_data in shortcuts.items():
            self.table.add_category(category_data["name_ru"])
            for action_id, action_data in category_data["actions"].items():
                self.table.add_row(action_data["name_ru"], action_data["keys"])

    def reset_defaults(self):
        self.table.clear()
        self._fill_system_shortcuts()