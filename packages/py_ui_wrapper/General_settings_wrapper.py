from PyQt6.QtWidgets import QMainWindow
from PyQt6.uic import loadUi
from Icon.IconName import *
from packages.core.config.path import ui


class GeneralSettingsWindow(QMainWindow):
    def __init__(self, path=None):
        super(GeneralSettingsWindow, self).__init__()
        loadUi(ui("General_settings.ui"), self)
        self.__init_widget_settings()

    def __init_widget_settings(self):
        """ Инициализирует текст в ComboBox """
        self.SpectrometerMU_ComboBox.setStyleSheet(f"QComboBox::down-arrow {{ image: url({arrow_down_Icon}); }}")
        self.ScanerMU_ComboBox.setStyleSheet(f"QComboBox::down-arrow {{ image: url({arrow_down_Icon}); }}")
