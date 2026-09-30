from PyQt6.QtWidgets import QMainWindow, QSplitter, QTabWidget, QFileDialog
from packages.Controllers.ParentController import ControllerSettings
from PyQt6.QtCore import QSettings, QByteArray
from packages.core.config.path import UI_SETTINGS_PATH
from PyQt6 import uic
from PyQt6.QtWidgets import (QDialog, QComboBox, QCheckBox, QLineEdit, QPushButton,
                             QLabel, QScrollArea, QWidget, QVBoxLayout)
import os
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices
from packages.core.math.timeGen import get_date


class SaveDialog(QDialog):
    """Диалог сохранения данных"""

    def __init__(self, dataset: dict, file_types: set, default_settings: dict = None):
        super().__init__()
        uic.loadUi('ui/Dialog/save_settings.ui', self)

        # Инициализация UI элементов
        self._init_ui_elements()

        # Настройка данных
        self.dataset = dataset
        self.file_types = file_types
        self._checkboxes = []

        # Заполнение комбобоксов
        self._populate_data_sources()
        self._populate_file_types()

        # Подключение сигналов
        self._connect_signals()

        # Инициализация UI
        self.update_leaf_list(self._data_comboBox.currentText())

        # Применение настроек по умолчанию
        if default_settings:
            self.apply_default_settings(default_settings)
        else:
            self._name_lineEdit.setText(self._data_comboBox.currentText())
            self.update_file_path()

    def _init_ui_elements(self):
        """Инициализация всех UI элементов"""
        self._data_comboBox = self.findChild(QComboBox, "data_comboBox")
        self._scroll_area = self.findChild(QScrollArea, "scrollArea")

        # Контейнер для чекбоксов
        self._checkboxes_container = QWidget()
        self._checkboxes_layout = QVBoxLayout(self._checkboxes_container)
        self._checkboxes_layout.setSpacing(5)
        self._checkboxes_layout.setContentsMargins(5, 5, 5, 5)
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setWidget(self._checkboxes_container)

        # Кнопки управления
        self._select_all_pushButton = self.findChild(QPushButton, "select_all_pushButton")
        self._clear_selection_pushButton = self.findChild(QPushButton, "clear_selection_pushButton")

        # Настройки файла
        self._file_type_comboBox = self.findChild(QComboBox, "file_type_comboBox")
        self._data_time_checkBox = self.findChild(QCheckBox, "data_time_checkBox")
        self._group_to_file_checkBox = self.findChild(QCheckBox, "group_to_file_checkBox")
        self._header_checkBox = self.findChild(QCheckBox, "header_checkBox")

        # Путь и имя файла
        self._name_lineEdit = self.findChild(QLineEdit, "name_lineEdit")
        self._browser_lineEdit = self.findChild(QLineEdit, "browser_lineEdit")
        self._file_path_label = self.findChild(QLabel, "file_path_label")
        self._browser_pushButton = self.findChild(QPushButton, "browser_pushButton")
        self._filePath_comment_label = self.findChild(QLabel, "filePath_comment_label")

        # Дополнительные опции
        self._open_dir_checkBox = self.findChild(QCheckBox, "open_dir_checkBox")

        # Кнопки диалога
        self._save_pushButton = self.findChild(QPushButton, "save_pushButton")
        self._exit_pushButton = self.findChild(QPushButton, "exit_pushButton")

    def _populate_data_sources(self):
        """Заполнение комбобокса источников данных"""
        for key in self.dataset.keys():
            self._data_comboBox.addItem(key)

    def _populate_file_types(self):
        """Заполнение комбобокса типов файлов"""
        self._update_file_types()

    def _update_file_types(self):
        """Обновление списка типов файлов в зависимости от режима"""
        index = self._file_type_comboBox.currentIndex()
        if index == -1:
            index = 1
        self._file_type_comboBox.clear()

        for value in sorted(self.file_types):
            if self._group_to_file_checkBox.isChecked():
                self._file_type_comboBox.addItem('.' + value, value)
            else:
                self._file_type_comboBox.addItem(value, value)

        self._file_type_comboBox.setCurrentIndex(index)

    def _connect_signals(self):
        """Подключение всех сигналов"""
        self._browser_pushButton.clicked.connect(self.browse_folder)
        self._save_pushButton.clicked.connect(self.accept)
        self._exit_pushButton.clicked.connect(self.reject)
        self._data_comboBox.currentTextChanged.connect(self._on_data_source_changed)
        self._file_type_comboBox.currentTextChanged.connect(self.update_file_path)
        self._name_lineEdit.textChanged.connect(self.update_file_path)
        self._browser_lineEdit.textChanged.connect(self.update_file_path)
        self._data_time_checkBox.toggled.connect(self.update_file_path)
        self._select_all_pushButton.clicked.connect(self.select_all)
        self._clear_selection_pushButton.clicked.connect(self.clear_selection)
        self._group_to_file_checkBox.toggled.connect(self._on_group_mode_changed)

    def _on_group_mode_changed(self, checked: bool):
        """Обработчик изменения режима группировки"""
        self._filePath_comment_label.setText("Путь к файлу" if checked else "Путь к директории")
        self._update_file_types()
        self.update_file_path()

    def _on_data_source_changed(self, branch_name: str):
        """Обработчик изменения источника данных"""
        self.update_leaf_list(branch_name)
        self._name_lineEdit.setText(branch_name)
        self.update_file_path()

    def update_leaf_list(self, branch_name: str):
        """Обновление списка листьев для выбранной ветки"""
        # Очистка layout
        while self._checkboxes_layout.count():
            item = self._checkboxes_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._checkboxes.clear()

        # Добавление новых чекбоксов
        branch_data = self.dataset.get(branch_name, {})
        if not branch_data:
            return

        for leaf_name, leaf_data in zip(branch_data['leaf_names'], branch_data['leaf_data']):
            checkbox = QCheckBox(str(leaf_name))
            checkbox.setProperty("data", {
                'leaf_name': leaf_name,
                'leaf_data': leaf_data,
                'params': branch_data['params']
            })
            checkbox.setChecked(True)
            self._checkboxes_layout.addWidget(checkbox)
            self._checkboxes.append(checkbox)

        self._checkboxes_layout.addStretch()

    def select_all(self):
        """Выбрать все листья"""
        for checkbox in self._checkboxes:
            checkbox.setChecked(True)

    def clear_selection(self):
        """Снять все выборы"""
        for checkbox in self._checkboxes:
            checkbox.setChecked(False)

    def browse_folder(self):
        """Выбор папки для сохранения"""
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку для сохранения")
        if folder:
            self._browser_lineEdit.setText(folder)

    def update_file_path(self):
        """Обновление отображаемого пути к файлу"""
        folder = self._browser_lineEdit.text()
        name = self._name_lineEdit.text()
        file_type = self._file_type_comboBox.currentText()

        name_full = name + file_type if self._group_to_file_checkBox.isChecked() else name
        if self._data_time_checkBox.isChecked():
            full_path = os.path.join(folder, get_date() + '_' + name_full)
        else:
            full_path = os.path.join(folder, name_full)

        self._file_path_label.setText(full_path)

    def apply_default_settings(self, settings: dict):
        """Применение настроек по умолчанию"""
        if 'file_type' in settings:
            index = self._file_type_comboBox.findText(settings['file_type'])
            if index >= 0:
                self._file_type_comboBox.setCurrentIndex(index)

        self._data_time_checkBox.setChecked(settings.get('add_timestamp', False))
        self._group_to_file_checkBox.setChecked(settings.get('group_to_file', False))

        if 'folder' in settings:
            self._browser_lineEdit.setText(settings['folder'])
        if 'file_name' in settings:
            self._name_lineEdit.setText(settings['file_name'])

        self._open_dir_checkBox.setChecked(settings.get('open_folder_after', False))
        self._header_checkBox.setChecked(settings.get('include_header', False))
        self.update_file_path()

    def get_settings(self) -> dict:
        """Получение настроек сохранения"""
        selected_leaves = self._get_selected_leaves()

        return {
            'save': True,
            'params': {
                'data_source': self._data_comboBox.currentText(),
                'selected_leaves': selected_leaves,
                'file_type': self._file_type_comboBox.currentData(),
                'add_timestamp': self._data_time_checkBox.isChecked(),
                'group_to_file': self._group_to_file_checkBox.isChecked(),
                'folder': self._browser_lineEdit.text(),
                'file_name': self._name_lineEdit.text(),
                'full_path': self._file_path_label.text(),
                'open_folder_after': self._open_dir_checkBox.isChecked(),
                'include_header': self._header_checkBox.isChecked()
            }
        }

    def _get_selected_leaves(self) -> dict:
        """Получение выбранных листьев"""
        leaf_names = []
        leaf_data = []
        params = {}

        for checkbox in self._checkboxes:
            if checkbox.isChecked():
                data = checkbox.property("data")
                leaf_names.append(data['leaf_name'])
                leaf_data.append(data['leaf_data'])
                if not params:  # Берем params только один раз
                    params = data['params']

        return {
            'leaf_names': leaf_names,
            'leaf_data': leaf_data,
            'params': params
        }

    def get_default_settings(self) -> dict:
        """Получение текущих настроек как дефолтных"""
        return {
            'file_type': self._file_type_comboBox.currentText(),
            'add_timestamp': self._data_time_checkBox.isChecked(),
            'group_to_file': self._group_to_file_checkBox.isChecked(),
            'folder': self._browser_lineEdit.text(),
            'file_name': self._name_lineEdit.text(),
            'full_path': self._file_path_label.text(),
            'open_folder_after': self._open_dir_checkBox.isChecked(),
            'include_header': self._header_checkBox.isChecked()
        }


class ControllerWindowSettings(ControllerSettings):
    """Класс для хранения и управления настройками окон"""

    def _post_init(self):
        self._parameters = {'default_settings': ""}
        self.JSON_object.set_settings_file_name("window_settings.json")
        self._load_settings()


class WindowRegistry:
    """Реестр всех окон"""
    __registry = {}

    @classmethod
    def register(cls, window):
        """Регистрация окна"""
        cls.__registry[window.name] = window

    @classmethod
    def get(cls, name):
        """Получение окна по имени"""
        return cls.__registry.get(name)

    @classmethod
    def get_all(cls):
        """Получение всех зарегистрированных окон"""
        return list(cls.__registry.keys()), list(cls.__registry.values())


class ParentWindow(QMainWindow):
    """Родительский класс для всех окон приложения"""
    name = "ParentWindow"

    def __init__(self, parent=None):
        super().__init__(parent)
        WindowRegistry.register(self)

        self.parent = parent
        self.default_settings = {}
        self.default_open_dir = ''
        self._settings = ControllerWindowSettings(name=self.name)
        self.initialized = False
        self.Tree = None
        self.FileManager = None
        self.event_bus = None

    def post_init(self):
        """Инициализация окна (если еще не была выполнена)"""
        if not self.initialized:
            self._post_init()
            self.initialized = True
            self.restore_ui_state()

    def _post_init(self):
        """
        Базовая инициализация окна.
        Должна быть переопределена в дочерних классах.
        """
        pass

    def Window_Selected(self):
        """Действия при выборе окна"""
        print(f"Window_Selected не реализован для {self.name}")

    def Set_Widget_Settings(self):
        """Установка настроек виджетов"""
        pass

    # ===== Методы для работы с UI =====

    def get_all_splitters(self):
        """Получение всех сплиттеров в UI"""
        return self.findChildren(QSplitter)

    # ===== Методы для работы с файлами =====

    def openFile(self):
        """Открытие файлов через диалог"""
        if not self.FileManager:
            self._show_error("FileManager не инициализирован")
            return

        file_paths = self._get_openFile_paths()
        if not file_paths:
            return

        self._load_files(file_paths)

    def _get_openFile_paths(self) -> list:
        """Диалог выбора файлов для открытия"""
        supported_formats = self.FileManager.SUPPORTED_FORMATS

        # Формирование фильтров
        all_filter = "Все поддерживаемые форматы (*"
        for fmt in sorted(supported_formats):
            all_filter += f" *.{fmt}"
        all_filter += ")"

        single_filters = [f"{fmt.upper()} файлы (*.{fmt})" for fmt in sorted(supported_formats)]
        filter_string = ";;".join([all_filter] + single_filters)

        # Настройка диалога
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        dialog.setNameFilter(filter_string)
        dialog.setWindowTitle("Открыть файлы")
        dialog.setDirectory(self.default_open_dir)

        if dialog.exec():
            return dialog.selectedFiles()
        return []

    def _load_files(self, file_paths: list):
        """Загрузка выбранных файлов"""
        for file_path in file_paths:
            self._load_single_file(file_path)

        if self.Tree:
            self.Tree.show_data()

    def _load_single_file(self, file_path: str):
        """Загрузка одного файла"""
        try:
            data, info = self.FileManager.load(file_path, with_inf=True)
            name = os.path.splitext(os.path.basename(file_path))[0]
            if data is None:
                self._show_status(f"Файл поврежден или не существует ❌", 3, "error")
                return
            if info is None:
                info = self.ScanFSM.inf_file_from_dat(dat=data, name=name)
                self._show_status(f"INF файл не найден, параметры восстановлены ❗️", 3, "warning")
            if self.Tree:
                self.Tree.Add_branch(params=info, data=data)

        except Exception as e:
            self._show_status(f"Ошибка загрузки файла {file_path}: {str(e)}", 3, "error")

    def saveFile(self):
        """Сохранение данных через диалог"""
        if not self.Tree or not self.Tree.all_data:
            self._show_status("Нет данных для сохранения ❗️", 3, "warning")
            return

        dataset = self._prepare_dataset_for_save()
        if not dataset:
            self._show_status("Ошибка подготовки данных для сохранения", 3, "error")
            return

        dialog = SaveDialog(
            dataset=dataset,
            file_types=self.FileManager.SUPPORTED_FORMATS,
            default_settings=self.default_settings
        )
        dialog.setWindowTitle("Сохранение данных")

        if dialog.exec():
            self._process_save(dialog)

    def _prepare_dataset_for_save(self) -> dict:
        """Подготовка данных для диалога сохранения"""
        dataset = {}
        try:
            for branch in self.Tree.all_data:
                name = branch[0]['params']['name']
                leaf_names = branch[0]['leaf_names']
                dataset[name] = {
                    'leaf_names': leaf_names,
                    'params': branch[0]['params'],
                    'leaf_data': branch[1]
                }
        except Exception as e:
            print(f"Ошибка подготовки данных: {e}")
            return {}

        return dataset

    def _process_save(self, dialog: SaveDialog):
        """Обработка сохранения данных"""
        try:
            # Сохраняем настройки
            self.default_settings = dialog.get_default_settings()

            # Получаем параметры сохранения
            settings = dialog.get_settings()
            params = settings['params']

            # Выполняем сохранение
            if params['group_to_file']:
                self._save_to_single_file(params)
            else:
                self._save_to_multiple_files(params)

            self._show_status(f"Данные успешно сохранены ✅\n{params['full_path']}", 5, "success")

            if params['open_folder_after']:
                QDesktopServices.openUrl(QUrl.fromLocalFile(params['folder']))

        except Exception as e:
            self._show_status(f"Ошибка сохранения: {str(e)}", 3, "error")

    def _save_to_single_file(self, params: dict):
        """Сохранение в один файл"""
        leaf_data = params['selected_leaves']['leaf_data']
        file_params = params['selected_leaves']['params']

        self.FileManager.set_data(leaf_data, file_params)
        self.FileManager.save(filepath=params['full_path'], format=params['file_type'],
                                include_header=params['include_header'], delimiter='\t')

    def _save_to_multiple_files(self, params: dict):
        """Сохранение в несколько файлов"""
        dir_path = params['full_path']
        os.makedirs(dir_path, exist_ok=True)

        leaf_data = params['selected_leaves']['leaf_data']
        leaf_names = params['selected_leaves']['leaf_names']
        file_params = params['selected_leaves']['params']

        for name, data in zip(leaf_names, leaf_data):
            file_path = os.path.join(dir_path, f"{name}.{params['file_type']}")
            self.FileManager.set_data(data, file_params)
            self.FileManager.save(filepath=file_path, format=params['file_type'],
                                  include_header=params['include_header'], delimiter='\t')

    # ===== Вспомогательные методы =====

    def _show_status(self, message: str, timeout: int = 3, level: str = "info"):
        """Отображение сообщения в статус-баре"""
        if self.event_bus:
            self.event_bus.StatusBar.emit(message, timeout, level)

    def _show_error(self, message: str):
        """Отображение ошибки"""
        print(f"ERROR: {message}")
        self._show_status(message, 5, "error")

    # ===== Методы сохранения/восстановления состояния UI =====

    def save_ui_state(self):
        """Сохранение геометрии окна и состояний сплиттеров"""
        try:
            UI_SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
            settings = QSettings(str(UI_SETTINGS_PATH), QSettings.Format.IniFormat)

            settings.setValue(f"{self.name}/geometry", QByteArray(self.saveGeometry()))
            settings.setValue(f"{self.name}/state", QByteArray(self.saveState()))

            for i, splitter in enumerate(self.get_all_splitters()):
                settings.setValue(f"{self.name}/splitter_{i}", QByteArray(splitter.saveState()))

            for j, tab in enumerate(self.findChildren(QTabWidget)):
                settings.setValue(f"{self.name}/tab_{j}", tab.currentIndex())

            settings.sync()

        except Exception as e:
            print(f"ERROR::ParentWindow::save_ui_state:: {e}")

    def save_settings(self):
        """Сохранение всех настроек окна"""
        self.save_ui_state()
        self.save_window_settings()

    def save_window_settings(self):
        """Сохранение базовых настроек окна"""
        settings_list = [self.default_settings, self.default_open_dir]
        self._settings.save_settings(settings=settings_list)

    def restore_ui_state(self):
        """Восстановление геометрии окна и состояний сплиттеров"""
        try:
            if not UI_SETTINGS_PATH.exists():
                return

            settings = QSettings(str(UI_SETTINGS_PATH), QSettings.Format.IniFormat)

            if settings.contains(f"{self.name}/geometry"):
                self.restoreGeometry(settings.value(f"{self.name}/geometry"))

            if settings.contains(f"{self.name}/state"):
                self.restoreState(settings.value(f"{self.name}/state"))

            for i, splitter in enumerate(self.get_all_splitters()):
                if settings.contains(f"{self.name}/splitter_{i}"):
                    splitter.restoreState(settings.value(f"{self.name}/splitter_{i}"))

            for j, tab in enumerate(self.findChildren(QTabWidget)):
                if settings.contains(f"{self.name}/tab_{j}"):
                    idx = int(settings.value(f"{self.name}/tab_{j}"))
                    if 0 <= idx < tab.count():
                        tab.setCurrentIndex(idx)

        except Exception as e:
            print(f"ERROR::ParentWindow::restore_ui_state:: {e}")
