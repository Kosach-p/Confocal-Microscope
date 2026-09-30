from PyQt6.QtWidgets import QVBoxLayout
from PyQt6.uic import loadUi
from packages.core.services.save_service.SettingsSave_service import SettingsSaver
from PyQt6.QtWidgets import QCheckBox, QDoubleSpinBox, QComboBox, QLabel, QPushButton
import serial
from packages.core.config.path import ui
from packages.core.config.path import CONN_SETTINGS_DIR
from packages.core.widgets.ComboBox import upgradeComboBox
from packages.core.widgets.SpinBox import upgradeDoubleSpinBox
from packages.core.widgets.Animated_button import add_simple_click_feedback
from PyQt6.QtGui import QIcon
from Icon.IconName import *


class serSettings(SettingsSaver):
    # Класс для хранения и управления настройками COM порта
    BAUDRATES = [4800, 9600, 14400, 19200, 38400, 57600, 115200, 230400, 460800, 921600, 1000000]
    WORD_LENGTHS = [8, 9]
    DATA_BITS = [5, 6, 7, 8]
    STOP_BITS = {
        1: serial.STOPBITS_ONE,
        1.5: serial.STOPBITS_ONE_POINT_FIVE,
        2: serial.STOPBITS_TWO,
    }
    PARITIES = {
        "None": serial.PARITY_NONE,
        "Even": serial.PARITY_EVEN,
        "Odd": serial.PARITY_ODD,
        "Mark": serial.PARITY_MARK,
        "Space": serial.PARITY_SPACE}

    def _post_init(self):
        self._settings = {'type': 'ser', 'port': {}, 'baudrate': 115200, 'word_length': 8, 'parity': None, 'stop_bits': 0,
                          'write_timeout': 0.1, 'read_timeout': 0.001,
                          'xonxoff': False, 'crc_en': True}

        self.JSON_object.set_settings_file_name("settings.json")
        self.JSON_object.set_settings_dir(CONN_SETTINGS_DIR)

        self._load_settings()


class COMSettingsUI:
    name = "COMSettings"

    def __init__(self, page, parent, id):
        self.parent = parent
        self.id = id
        layout = QVBoxLayout(page)
        frame = loadUi(ui("SerSettings.ui"))
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(frame)
        layout.addStretch()
        page.connection = frame

        self.ComPort_comboBox = upgradeComboBox(frame.findChild(QComboBox, "ComPort_comboBox"))
        self.BaudRate_comboBox = upgradeComboBox(frame.findChild(QComboBox, "BaudRate_comboBox"))
        self.WordLength_comboBox = upgradeComboBox(frame.findChild(QComboBox, "WordLength_comboBox"))
        self.Parity_comboBox = upgradeComboBox(frame.findChild(QComboBox, "Parity_comboBox"))
        self.StopBits_comboBox = upgradeComboBox(frame.findChild(QComboBox, "StopBits_comboBox"))
        self.WriteTimeout_doubleSpinBox = upgradeDoubleSpinBox(frame.findChild(QDoubleSpinBox, "WriteTimeout_doubleSpinBox"))
        self.ReadTimeout_doubleSpinBox = upgradeDoubleSpinBox(frame.findChild(QDoubleSpinBox, "ReadTimeout_doubleSpinBox"))
        self.ComPort_Label = frame.findChild(QLabel, "ComPort_Label")
        self.select_pushButton = frame.findChild(QPushButton, "select_pushButton")

        add_simple_click_feedback(self.select_pushButton, QIcon(arrow_right_Icon), QIcon(check_mark_Icon))
        self.select_pushButton.clicked.connect(self._on_select_pushButton_clicked)

        self.__params = None
        self.__setting_dict = {}
        self.ui_Init()
        self.fill_ui()

    def ui_Init(self):
        """ Заполняем UI данными из настроек """
        for BaudRate in serSettings.BAUDRATES:
            self.BaudRate_comboBox.addItem(f"{BaudRate} бит/с", BaudRate)
        for Word_Length in serSettings.WORD_LENGTHS:
            self.WordLength_comboBox.addItem(f"{Word_Length} бит", Word_Length)
        for Parity in serSettings.PARITIES.keys():
            self.Parity_comboBox.addItem(f"{Parity}", serSettings.PARITIES[Parity])
        for Stop_Bits in serSettings.STOP_BITS.keys():
            self.StopBits_comboBox.addItem(f"{Stop_Bits}", serSettings.STOP_BITS[Stop_Bits])
        self.ui_init_cplt = True

    def fill_ui(self):
        self.BaudRate_comboBox.setCurrentText(f"{self.__setting_dict.get('baudrate', 9600)} бит/с")
        self.WordLength_comboBox.setCurrentText(f"{self.__setting_dict.get('word_length', 8)} бит")
        self.Parity_comboBox.setCurrentText(f"{self.__setting_dict.get('parity', 1)}")
        self.StopBits_comboBox.setCurrentText(f"{self.__setting_dict.get('stop_bits', 'none')}")
        self.WriteTimeout_doubleSpinBox.setValue(self.__setting_dict.get('write_timeout', 0.01))
        self.ReadTimeout_doubleSpinBox.setValue(self.__setting_dict.get('read_timeout', 0.01))

    def _on_select_pushButton_clicked(self):
        self.ComPort_Label.setText(self.ComPort_comboBox.currentText())
        self.ComPort_Label.setProperty("port", self.ComPort_comboBox.currentData())

    @property
    def params(self):
        """ Возвращает dict со всеми параметрами подключения """
        if not self.ui_init_cplt:
            self.ui_Init()
            self.fill_ui()

        self.__setting_dict['port'] = self.ComPort_Label.property("port")
        self.__setting_dict['id'] = self.id
        self.__setting_dict['baudrate'] = self.BaudRate_comboBox.currentData()
        self.__setting_dict['word_length'] = self.WordLength_comboBox.currentData()
        self.__setting_dict['parity'] = self.Parity_comboBox.currentData()
        self.__setting_dict['stop_bits'] = self.StopBits_comboBox.currentData()
        self.__setting_dict['write_timeout'] = self.WriteTimeout_doubleSpinBox.value()
        self.__setting_dict['read_timeout'] = self.ReadTimeout_doubleSpinBox.value()
        self.__setting_dict['type'] = 'ser'
        return self.__setting_dict

    def set_settings(self, settings):
        """ Получает параметры из настроек """
        self.__setting_dict = settings
        self.__setting_dict['port'].get('device', '')

        self.ComPort_Label.setText(self.__setting_dict['port'].get('device', ''))
        self.ComPort_Label.setProperty("port", self.__setting_dict['port'])

        self.fill_ui()

    def _are_params_equal(self, params: dict) -> bool:
        """Проверяет, совпадает ли новый список профилей с текущим"""
        if self.ComPort_comboBox.count() != len(params):
            return False

        key_list = []

        for i in range(self.ComPort_comboBox.count()):
            key_list.append(self.ComPort_comboBox.itemText(i))

        for profile in params:
            if profile.get('device') not in key_list:
                return False

        return True

    def set_params(self, params):
        """ Получает параметры от интерфейса """
        if params is not None and not self._are_params_equal(params['available_ports']):
            self.ComPort_comboBox.clear()
            for port in params['available_ports']:
                self.ComPort_comboBox.addItem(port['device'], port)
