# Встроенные библиотеки
import time

Time = time.time()
import os
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = ""  # Отключает ненужные Qt-плагины

# Визуализация
from PyQt6.QtWidgets import QMainWindow

from PyQt6.uic import loadUi
from PyQt6.QtWidgets import QPushButton

from packages.Windows.Settings.ConnectionSettingBlock.ConnectionSettingsWindow import ConnectionSettings
from packages.Windows.Settings.DeviceSettingsBlock.DeviceSettingsWindow import DeviceSettings

from packages.Windows.Settings.InterfaceSettingsBlock.InterfaceSettings import InterfaceSettings
from packages.core.config.path import ui


class SettingsWindowClass(QMainWindow):
    name = "SettingsWindowClass"
    filename = "AppSettings"

    def __init__(self, event_bus):
        super().__init__()
        loadUi(ui("Settings_window.ui"), self)
        self.event_bus = event_bus
        self.interface_set = InterfaceSettings(self.interface_widget, self.event_bus)
        self.device_settings = DeviceSettings(self.device_widget, self.event_bus)
        self.connection_settings = ConnectionSettings(self.connection_widget, self.event_bus)
        self.save_button = self.findChild(QPushButton, "save_button")
        self.apply_button = self.findChild(QPushButton, "apply_button")
        self.cancel_button = self.findChild(QPushButton, "cancel_button")
        self.ui_Init()


    def ui_Init(self):
        """ Заполняем UI данными из настроек """
        self.save_button.clicked.connect(self.save_btn_clicked)
        self.apply_button.clicked.connect(self.apply_button_clicked)
        self.cancel_button.clicked.connect(self.cancel_button_clicked)

        self.connection_settings.send_update_connect()
        self.device_settings.emit_settings()
        self.interface_set.emit_settings()

    def save_btn_clicked(self):
        """ Нажата кнопка сохранения """
        self.apply_button_clicked()
        self.close()

    def apply_button_clicked(self):
        """ Нажата кнопка применения настроек """
        self.connection_settings.apply()
        self.device_settings.apply()
        self.interface_set.apply()

    def cancel_button_clicked(self):
        """ Нажата кнопка отмены изменений """
        self.close()

    def keyPressEvent(self, event):
        #self.interface_set.HotKey.keyPressEvent(event)
        super().keyPressEvent(event)