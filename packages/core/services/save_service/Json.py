import json
import os
from typing import Dict, Any
from packages.core.config.path import UI_settings, filepath_in_dir, create_file_in_dir


class JsonSettingsClass:
    def __init__(self, settings_selection):
        self.__settings_file_dir = ""
        self.__settings_file_name = ""
        self.__settings_file_path = filepath_in_dir(dir=self.__settings_file_dir, name=self.__settings_file_name)

        self.__settings_selection = settings_selection

    def set_settings_file_name(self, file_name):
        """ Устанавливает название файла с настройками по умолчанию """
        self.__settings_file_name = file_name
        self.__settings_file_path = filepath_in_dir(dir=self.__settings_file_dir, name=self.__settings_file_name)
        if self.__settings_file_path is None:
            self.__settings_file_path = create_file_in_dir(dir=self.__settings_file_dir, name=self.__settings_file_name)

    def set_settings_dir(self, dir):
        """ Устанавливает директорию файла с настройками по умолчанию """
        self.__settings_file_dir = dir
        self.__settings_file_path = filepath_in_dir(dir=self.__settings_file_dir, name=self.__settings_file_name)
        if self.__settings_file_path is None:
            self.__settings_file_path = create_file_in_dir(dir=self.__settings_file_dir, name=self.__settings_file_name)

    def __load_all(self) -> Dict[str, Any]:
        """Загружает все настройки из файла"""
        if not os.path.exists(self.__settings_file_path):
            print(f"JsonSettingsMixin:: Не обнаружен файл настроек {self.__settings_file_path}")
            return {}

        try:
            with open(self.__settings_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            print(f"JsonSettingsMixin:: Не удалось открыть файл настроек {self.__settings_file_path}")
            return {}

    def Json_save_settings(self, data: Dict[str, Any]):
        """Сохраняет настройки раздела"""
        all_data = self.__load_all()
        all_data[self.__settings_selection] = None
        all_data[self.__settings_selection] = data
        with open(self.__settings_file_path, 'w', encoding="utf-8") as f:
            json.dump(all_data, f, indent=4, ensure_ascii=False)

    def Json_load_settings(self) -> Dict[str, Any]:
        """Загружает настройки раздела"""
        return self.__load_all().get(self.__settings_selection, {})