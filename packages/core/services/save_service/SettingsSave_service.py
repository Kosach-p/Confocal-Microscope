from packages.core.services.save_service.Json import JsonSettingsClass


class SettingsSaver:
    # Универсальный класс-контроллер для хранения и управления настройками

    def __init__(self, name):
        # Инициализация настроек с заданными параметрами
        self.JSON_object = JsonSettingsClass(name)
        self.JSON_object.set_settings_file_name("settings.json")
        self._settings = {}  # Пустой словарь, будет заполняться в дочерних классах
        self._post_init()

    def __getattr__(self, name):
        """Позволяет обращаться к настройкам как к атрибутам"""
        # Важно: проверяем, что _settings уже существует
        if '_settings' in self.__dict__ and name in self.__dict__['_settings']:
            return self.__dict__['_settings'][name]
        raise AttributeError(f"'{name}' not found")

    def __setattr__(self, name, value):
        """Позволяет устанавливать настройки как атрибуты"""
        if name != '_settings' and hasattr(self, '_settings') and name in self._settings:
            current_type = type(self._settings[name])
            self._settings[name] = current_type(value)
        else:
            super().__setattr__(name, value)

    def _post_init(self):
        """Дочерние классы должны переопределить этот метод и заполнить self._settings"""
        pass

    def _save_settings(self):
        """Сохранение настроек в JSON файл"""
        self.JSON_object.Json_save_settings(self._settings)

    def _load_settings(self):
        """Загрузка настроек из JSON файла"""
        try:
            loaded = self.JSON_object.Json_load_settings()
            if loaded:
                self._settings.update(loaded)
        except:
            self._save_settings()

    def save_settings(self, settings: list):
        """
        Обновление настроек из списка
        :param settings: список значений в правильном порядке
        """
        keys = list(self._settings.keys())
        for i, key in enumerate(keys):
            if i < len(settings):
                current_type = type(self._settings[key])
                try:
                    self._settings[key] = current_type(settings[i])
                except (ValueError, TypeError):
                    print(f"Ошибка конвертации {key} = {settings[i]}")
        self._save_settings()

    def save_current_settings(self):
        """
        Сохранение уже записанных настроек
        :param settings: список значений в правильном порядке
        """
        self._save_settings()

    def load_settings(self):
        """
        Получение настроек в виде списка
        :return: список всех сохранённых настроек
        """
        self._load_settings()
        return list(self._settings.values())

    def update_settings_dict(self, new_settings: dict):
        """Получить все настройки в виде словаря"""
        if new_settings:
            self._settings.update(new_settings)
        self._save_settings()

    def save_settings_dict(self, new_settings: dict):
        """Получить все настройки в виде словаря"""
        if new_settings:
            self._settings = new_settings
        self._save_settings()

    def load_settings_dict(self):
        """Получить все настройки в виде словаря"""
        self._load_settings()
        return self._settings.copy()
