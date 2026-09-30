from PyQt6.QtWidgets import QLabel
from packages.core.widgets.QLineEdit_BlenderStyle import QLineEditBlenderStyle
from packages.core.validators.numeric_validator import *
from packages.Controllers.ParentController import ControllerSettings
from packages.py_ui_wrapper.General_settings_wrapper import GeneralSettingsWindow


class UnitManager:
    _systems = {'galvo': {
        'м': {'coef': {'x': 0.0000000278, 'y': 0.0000000278}, 'validator': FloatCalcValidator, 'data type': float,
              'step': 0.001, 'decimal': 3, 'name': 'м'},
        'мм': {'coef': {'x': 0.0000278, 'y': 0.0000278}, 'validator': FloatCalcValidator, 'data type': float,
               'step': 0.001, 'decimal': 3, 'name': 'мм'},
        'мкм': {'coef': {'x': 0.0278, 'y': 0.0278}, 'validator': FloatCalcValidator, 'data type': float,
                'step': 0.001, 'decimal': 3, 'name': 'мкм'},
        'нм': {'coef': {'x': 27.8, 'y': 27.8}, 'validator': FloatCalcValidator, 'data type': float,
               'step': 0.1, 'decimal': 1, 'name': 'нм'},
        'LSB': {'coef': {'x': 1.0, 'y': 1.0}, 'validator': IntCalcValidator, 'data type': int,
                'step': 1, 'decimal': 0, 'name': 'LSB'}},
        'piezo': {
            'м': {'coef': {'x': 27.8e-9, 'y': 27.8e-9, 'z': 27.8e-9}, 'validator': FloatCalcValidator,
                  'data type': float, 'step': 1e-3, 'decimal': 3, 'name': 'м'},
            'мм': {'coef': {'x': 27.8e-6, 'y': 27.8e-6, 'z': 7.8e-6}, 'validator': FloatCalcValidator,
                   'data type': float, 'step': 1e-3, 'decimal': 3, 'name': 'мм'},
            'мкм': {'coef': {'x': 27.8e-3, 'y': 27.8e-3, 'z': 27.8e-3}, 'validator': FloatCalcValidator, 'data type': float,
                   'step': 1e-3, 'decimal': 3, 'name': 'мкм'},
            'нм': {'coef': {'x': 27.8, 'y': 27.8, 'z': 27.8}, 'validator': FloatCalcValidator, 'data type': float,
                   'step': 1e-1, 'decimal': 1, 'name': 'нм'},
            'LSB': {'coef': {'x': 1.0, 'y': 1.0, 'z': 1.0}, 'validator': IntCalcValidator, 'data type': int,
                    'step': 1, 'decimal': 0, 'name': 'LSB'}},
        'Spectrometer': {
            'эВ': {'coef': -1.239841336215e3, 'validator': FloatCalcValidator, 'data type': float, 'step': 1e-3, 'decimal': 3, 'name': 'м'},
            'Гц': {'coef': -2.99792458e17, 'validator': FloatCalcValidator,
                   'data type': float, 'step': 1e-3, 'decimal': 3, 'name': 'мм'},
            'см⁻¹': {'coef': -10e7, 'validator': FloatCalcValidator, 'data type': float, 'step': 1e-3, 'decimal': 3, 'name': 'мкм'},
            'мкм': {'coef': 0.001, 'validator': FloatCalcValidator, 'data type': float, 'step': 1e-3, 'decimal': 3, 'name': 'мкм'},
            'нм': {'coef': 1.0, 'validator': FloatCalcValidator, 'data type': float, 'step': 1e-2, 'decimal': 2, 'name': 'нм'}}
    }

    _current = {"galvo": 'LSB', "piezo": 'LSB', "Spectrometer": 'нм'}

    @classmethod
    def set_coef(cls, coef, device='galvo'):
        cls._systems[device]['м']["coef"] = {key: value * 1e-6 for key, value in coef.items()}
        cls._systems[device]['мм']["coef"] = {key: value * 1e-3 for key, value in coef.items()}
        cls._systems[device]['мкм']["coef"] = coef
        cls._systems[device]['нм']["coef"] = {key: value * 1e3 for key, value in coef.items()}

    @classmethod
    def coef(cls, device='galvo'):
        if device == "galvo":
            return cls._systems[device][cls._current[device]]['coef']['x']
        if device == "piezo":
            return cls._systems[device][cls._current[device]]['coef']['x']
        if device == "Spectrometer":
            return cls._systems[device][cls._current[device]]['coef']

    @classmethod
    def get_validator(cls, device='galvo'):
        return cls._systems[device][cls._current[device]]['validator']

    @classmethod
    def get_decimal(cls, device='galvo'):
        return cls._systems[device][cls._current[device]]['decimal']

    @classmethod
    def get_step(cls, device='galvo'):
        return cls._systems[device][cls._current[device]]['step']

    @classmethod
    def get_data_type(cls, device='galvo'):
        return cls._systems[device][cls._current[device]]['data type']

    @classmethod
    def get_name(cls, device='galvo'):
        return cls._systems[device][cls._current[device]]['name']

    @classmethod
    def set_system(cls, system, device='galvo'):
        cls._current[device] = system


class UnitLineEdit(QLineEditBlenderStyle):
    _instances = []  # Список всех созданных экземпляров
    device = 'galvo'

    def __init__(self, parent=None, device='galvo', label='', step=1, decimal=0):
        super().__init__(parent, label=label, step=step, decimal=decimal)
        self.Enable = False
        self.real_value = 0.0
        self.from_lineedit(parent)
        self._instances.append(self)
        self.getValue()
        self.update_settings()
        self.update_display()
        self.device = device

        self.textChanged.connect(self.on_text_changed)

    def update_settings(self):
        """ Установка параметров в QLineEditBlenderStyle """
        self.step = UnitManager.get_step(self.device)
        self.decimal = UnitManager.get_decimal(self.device)

    def from_lineedit(self, lineedit):
        """Создает UnitLineEdit, копируя настройки из существующего QLineEdit"""
        # Копируем все важные свойства
        self.setGeometry(lineedit.geometry())
        self.setObjectName(lineedit.objectName())
        self.setAlignment(lineedit.alignment())
        self.setStyleSheet(lineedit.styleSheet())
        self.setFont(lineedit.font())
        self.setPalette(lineedit.palette())
        self.setMinimumSize(lineedit.minimumSize())
        self.setMaximumSize(lineedit.maximumSize())
        self.setSizePolicy(lineedit.sizePolicy())

        # Копируем текст, если есть
        self.setText(lineedit.text())

        # Заменяем в родителе
        if lineedit.parent():
            layout = lineedit.parent().layout()
            if layout:
                layout.replaceWidget(lineedit, self)

        # Удаляем старый
        lineedit.deleteLater()

        return self

    def on_text_changed(self, text):
        """Обработка изменения текста (в том числе от BlenderLineEdit)"""
        try:
            display_value = float(text)
            self.real_value = self.to_real_value(display_value)
        except ValueError:
            pass

    def setValue(self, value):
        self.real_value = float(value)
        self.setText(f"{UnitManager.get_data_type(self.device)(self.to_display_value(self.real_value)):.{UnitManager.get_decimal(self.device)}f}")

    def getValue(self):
        display_value = float(self.text())
        self.real_value = self.to_real_value(display_value)
        return self.real_value

    def update_display(self):
        validator = UnitManager.get_validator()
        self.setValidator(validator)
        self.setText(
            f"{UnitManager.get_data_type(self.device)(self.to_display_value(self.real_value)):.{UnitManager.get_decimal(self.device)}f}")

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        try:
            display_value = float(self.text())
            self.real_value = self.to_real_value(display_value)
        except ValueError:
            pass

    def to_real_value(self, value):
        """ Преобразует value в реальное число """
        coef = UnitManager.coef(self.device)

        if coef >= 0:
            self.real_value = value / coef
            return self.real_value
        elif coef < 0:
            if value == 0:
                return False
            self.real_value = abs(coef) / value
            return self.real_value

    def to_display_value(self, value):
        """ Преобразует value в число для вывода в LineEdit """
        coef = UnitManager.coef(self.device)
        if coef >= 0:
            return coef * value
        elif coef < 0:
            return abs(coef) / value

    @classmethod
    def update_all(cls):
        """Обновить все экземпляры класса"""
        for instance in cls._instances:
            instance.update_display()
            instance.update_settings()


class UnitLabel(QLabel):
    _instances = []  # Список всех созданных экземпляров
    device = 'galvo'

    def __init__(self, parent=None, device='galvo'):
        super().__init__(parent)
        self.from_label(parent)
        self._instances.append(self)
        self.update_display()
        self.device = device

    def from_label(self, lineedit):
        """Создает UnitLabel, копируя настройки из существующего QLabel"""
        # Копируем все важные свойства
        self.setGeometry(lineedit.geometry())
        self.setObjectName(lineedit.objectName())
        self.setAlignment(lineedit.alignment())
        self.setStyleSheet(lineedit.styleSheet())
        self.setFont(lineedit.font())
        self.setPalette(lineedit.palette())
        self.setMinimumSize(lineedit.minimumSize())
        self.setMaximumSize(lineedit.maximumSize())
        self.setSizePolicy(lineedit.sizePolicy())

        # Копируем текст, если есть
        self.setText(lineedit.text())

        # Заменяем в родителе
        if lineedit.parent():
            layout = lineedit.parent().layout()
            if layout:
                layout.replaceWidget(lineedit, self)

        # Удаляем старый
        lineedit.deleteLater()

        return self

    def update_display(self):
        """ Заменяет единицы измерения в lineEdit """
        text = self.text()
        # Разделяем строку по запятой (maxsplit=1, чтобы разделить только на 2 части)
        parts = text.split(', ', 1)

        if len(parts) == 2:
            description = parts[0]
            new_text = f"{description}, {UnitManager.get_name(device=self.device)}"
        else:
            # Формат: просто "нм"
            new_text = UnitManager.get_name(device=self.device)

        self.setText(new_text)

    @classmethod
    def update_all(cls):
        """Обновить все экземпляры класса"""
        for instance in cls._instances:
            instance.update_display()


class GeneralSettings(ControllerSettings):
    # Класс для хранения и управления общими настройками

    def _post_init(self):
        self._parameters = {'SpectrometerMU_List': ["нм", "мкм", "см⁻¹", "Гц", "эВ"],
                          'ScanerMU_List': ["нм", "мкм", "м", "LSB"], 'SpectrometerMU': 'нм', 'ScanerMU': 'LSB'}

        try:
            self._load_settings()
        except:
            print("WARNING::GeneralSettings::_post_init::Настроек GeneralSettings нет в списке, загружаю стандартные")
            self._save_settings()


class GeneralSettingsClass:
    """ Основной класс для управления окном общих настроек """
    name = "GeneralSettingsClass"

    def __init__(self, parent):
        self.parent = parent
        self.__settings_window = GeneralSettingsWindow()
        self.__settingsObject = GeneralSettings(self.name)
        self.__settingsButton = self.parent.MenuBar_General_settings

        self.__SpectrometerMU_ComboBox = self.__settings_window.SpectrometerMU_ComboBox
        self.__ScanerMU_ComboBox = self.__settings_window.ScanerMU_ComboBox

        self.__connection_init()

    def __connection_init(self):
        """ Подключаем триггеры к действиям с виджетами в окне настроек """
        self.__settingsButton.triggered.connect(self.__settings_window.show)

        self.__SpectrometerMU_ComboBox.addItems(self.__settingsObject.SpectrometerMU_List)
        self.__SpectrometerMU_ComboBox.setCurrentText(self.__settingsObject.SpectrometerMU)
        self.__SpectrometerMU_ComboBox.currentTextChanged.connect(self.__SpectrometerMU_ComboBox_changed)

        self.__ScanerMU_ComboBox.addItems(self.__settingsObject.ScanerMU_List)
        self.__ScanerMU_ComboBox.setCurrentText(self.__settingsObject.ScanerMU)
        self.__ScanerMU_ComboBox.currentTextChanged.connect(self.__ScanerMU_ComboBox_changed)

        self.__update_all_MU()

    def __SpectrometerMU_ComboBox_changed(self):
        """ Изменяет единицы измерения спектрометра """
        UnitManager.set_system(self.__SpectrometerMU_ComboBox.currentText(), "Spectrometer")
        UnitLineEdit.update_all()
        UnitLabel.update_all()

    def __ScanerMU_ComboBox_changed(self):
        """ Изменяет единицы измерения сканера """
        UnitManager.set_system(self.__ScanerMU_ComboBox.currentText(), "galvo")
        UnitManager.set_system(self.__ScanerMU_ComboBox.currentText(), "piezo")
        UnitLineEdit.update_all()
        UnitLabel.update_all()

    def __update_all_MU(self):
        """ Обновляет все MU """
        UnitManager.set_system(self.__ScanerMU_ComboBox.currentText(), "galvo")
        UnitManager.set_system(self.__ScanerMU_ComboBox.currentText(), "piezo")
        UnitManager.set_system(self.__SpectrometerMU_ComboBox.currentText(), "Spectrometer")
        UnitLineEdit.update_all()
        UnitLabel.update_all()
