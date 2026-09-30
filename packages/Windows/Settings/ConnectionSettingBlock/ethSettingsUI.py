from PyQt6.QtWidgets import QVBoxLayout, QLineEdit, QSpinBox
from PyQt6.uic import loadUi
from packages.core.config.path import CONN_SETTINGS_DIR
from packages.core.services.save_service.SettingsSave_service import SettingsSaver
from PyQt6.QtWidgets import QDoubleSpinBox, QComboBox
from packages.core.config.path import ui
from packages.core.widgets.SpinBox import upgradeDoubleSpinBox
from packages.core.widgets.SpinBox import upgradeSpinBox


class ethSettings(SettingsSaver):
    def _post_init(self):
        self._settings = {
            'type': 'ethernet',
            'ip_address': '127.0.0.1',
            'port': 502,
            'connection_timeout': 5.0,
            'read_timeout': 1.0,
            'write_timeout': 1.0,
            'auto_reconnect': False,
            'reconnect_attempts': 3,
            'reconnect_delay': 2.0,
        }

        self.JSON_object.set_settings_file_name("settings.json")
        self.JSON_object.set_settings_dir(CONN_SETTINGS_DIR)

        self._load_settings()


class EthSettingsUI:
    name = "EthSettings"

    def __init__(self, page, parent, id):
        self.parent = parent
        self.id = id
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        frame = loadUi(ui("EthSettings.ui"))
        layout.addWidget(frame)
        layout.addStretch()
        page.connection = frame

        # Виджеты
        self.Device_comboBox = frame.findChild(QComboBox, "Device_comboBox")
        self.IP_lineEdit = frame.findChild(QLineEdit, "IP_lineEdit")
        self.Port_spinBox = upgradeSpinBox(frame.findChild(QSpinBox, "Port_spinBox"))
        self.Timeout_doubleSpinBox = upgradeDoubleSpinBox(frame.findChild(QDoubleSpinBox, "Timeout_doubleSpinBox"))
        self.WriteTimeout_doubleSpinBox = upgradeDoubleSpinBox(frame.findChild(QDoubleSpinBox, "WriteTimeout_doubleSpinBox"))
        self.ReadTimeout_doubleSpinBox = upgradeDoubleSpinBox(frame.findChild(QDoubleSpinBox, "ReadTimeout_doubleSpinBox"))

        self.__setting_dict = {}
        self.__params = None
        self.Device_comboBox_currentText = ''

        self.ui_init_cplt = True

    def ui_Init(self):
        """Заполняем UI данными из настроек"""
        self.IP_lineEdit.setText(self.__setting_dict['host'])
        self.Port_spinBox.setRange(1, 65535)
        self.Port_spinBox.setValue(self.__setting_dict['port'])
        self.Timeout_doubleSpinBox.setValue(self.__setting_dict['timeout'])
        self.WriteTimeout_doubleSpinBox.setValue(self.__setting_dict['write_timeout'])
        self.ReadTimeout_doubleSpinBox.setValue(self.__setting_dict['read_timeout'])

    @property
    def params(self):
        """Возвращает dict со всеми параметрами подключения"""
        if not self.ui_init_cplt:
            self.ui_Init()

        # Берём host из Device_comboBox или из IP_lineEdit
        if not (self.Device_comboBox.currentText() == ""):
            self.__setting_dict['host'] = self.Device_comboBox.currentData()
        else:
            self.__setting_dict['host'] = self.IP_lineEdit.text()

        self.__setting_dict['id'] = self.id
        self.__setting_dict['port'] = self.Port_spinBox.value()
        self.__setting_dict['timeout'] = self.Timeout_doubleSpinBox.value()
        self.__setting_dict['write_timeout'] = self.WriteTimeout_doubleSpinBox.value()
        self.__setting_dict['read_timeout'] = self.ReadTimeout_doubleSpinBox.value()
        self.__setting_dict['type'] = 'eth'

        return self.__setting_dict

    def set_settings(self, settings):
        """Получает параметры из настроек"""
        self.__setting_dict = settings
        self.Device_comboBox_currentText = f"{self.__setting_dict['host']}:{self.__setting_dict['port']}"
        self.ui_Init()

    def set_params(self, params):
        """Получает параметры от интерфейса (список доступных устройств)"""
        if params is not None:
            if self.Device_comboBox.currentText() != "":
                self.Device_comboBox_currentText = self.Device_comboBox.currentText()

            self.Device_comboBox.clear()

            for device in params.get('discovered_devices', []):
                # host:port — это и есть устройство
                display_text = f"{device['host']}:{device['port']}"
                if device.get('status') == 'online':
                    display_text += " ✓"
                elif device.get('status') == 'timeout':
                    display_text += " ⚠"

                self.Device_comboBox.addItem(display_text, device['host'])

            if self.Device_comboBox_currentText:
                self.Device_comboBox.setCurrentText(self.Device_comboBox_currentText)