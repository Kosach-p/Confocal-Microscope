import time

start = time.time()
import_times = {}

# PyQt6
from PyQt6.uic import loadUi
from PyQt6.QtGui import QIcon

print("Импортировано: PyQt6")

# Modbus и периферия
from packages.Сommunication.DeviceManager import DeviceManager
print("Импортировано: Modbus и периферия")

# Загрузка конфигурации
from packages.core.config.app_config import *
from Icon.IconName import *
from packages.core.config.path import ui
from packages.Floating_window.user_guide.user_guide import DocumentationDialog
print("Импортировано: Визуализация")

# Стандартные библиотеки
from packages.Controllers.ParentController import ControllerSettings
print("Импортировано: Стандартные библиотеки")

# Ядро
from packages.core.services.EventBus import EventBus
from packages.core.widgets.WindowStacker import WindowStacker
from packages.core.services.HotKey import HotKeyManager
from packages.Windows.Settings.SettingsWindow import SettingsWindowClass

# Реестры и Статус
from packages.Windows.ParentWindow import WindowRegistry
from packages.Windows.StatusBar import StatusBarClass
print("Импортировано: Реестры и Статус")
print("Рендер UI")

from PyQt6.QtWidgets import QMainWindow
from packages.core.widgets.FloatingWindowManager import FloatingWindowManager

DEVELOPER_MODE = False


class MainWindowSettings(ControllerSettings):
    # Класс для хранения и управления настройками главного окна

    def _post_init(self):
        self._parameters = {'last_window': "View2DClass"}
        self.JSON_object.set_settings_file_name("window_settings.json")
        self._load_settings()


class MainWindow(QMainWindow):
    name = "MainWindow"

    def __init__(self):
        super().__init__()

        # Загружаем главное окно с MenuBar
        loadUi(ui('Main_window.ui'), self)
        self.setWindowIcon(QIcon(logo_Icon))

        self.event_bus = EventBus()
        self.statusBar = StatusBarClass(self.statusBar, self.event_bus)
        # **************************************** Инициализация RS485 *************************************************
        self.device_manager = DeviceManager(self.event_bus, self.statusBar)
        # ***************************************** Переферия **********************************************************
        self.__ControllerClass_list = CONTROLLERS
        self.__ControllerObject_list = list()
        for ControllerClass in self.__ControllerClass_list:
            self.__ControllerObject_list.append(ControllerClass(parent=self))
        # **************************************** Сбор стака экранов **************************************************
        self.current_window = None
        self.__WindowClass_list = WINDOWS
        self.__WindowObject_list = list()
        for WindowClass in self.__WindowClass_list:
            self.__WindowObject_list.append(WindowClass(parent=self))
        self.stack = WindowStacker()
        self.setCentralWidget(self.stack)
        self.stack.set_window_list(WindowRegistry.get_all()[1])

        # **************************************** Сбор плавающих окно *************************************************
        self.NodeEditorWindow = NodeEditorClass()

        self.FloatingWindow = FloatingWindowManager()
        self.FloatingWindow.set_window_list([self.NodeEditorWindow])
        # ************************************** Настройка окон настроек ***********************************************
        self.hot_key = HotKeyManager(self, self.event_bus)

        self.__settingsObject = MainWindowSettings(self.name)

        self.change_window(self.__settingsObject.last_window)

        self.Settings_window_object = SettingsWindowClass(self.event_bus)

        self._setup_menu()

    def center_on_screen(self):
        self.resize(1600, 900)
        screen = self.screen().availableGeometry()
        center_point = screen.center()
        self.move(center_point - self.rect().center())

    def FastOpenFile(self):
        WindowRegistry.get(self.current_window).openFile()

    def FastSaveFile(self, save_type="save"):
        WindowRegistry.get(self.current_window).saveFile()

    def ToggleFullScreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def change_window(self, name):
        if self.stack.show_window(name):
            self.current_window = name
        else:
            print(f"ERROR::{self.__class__.__name__}::change_window::Не удалось открыть окно {name}, не найдено в списке")

    def change_float_window(self, name):
        if self.FloatingWindow.show_window(name):
            pass
        else:
            print(f"ERROR::{self.__class__.__name__}::change_window::Не удалось открыть окно {name}, не найдено в списке")

    def show_help(self):
        """Показать руководство пользователя"""
        guide = DocumentationDialog(parent=self)
        guide.exec()

    def _setup_menu(self):
        self.MenuBar_Settings.triggered.connect(self.Settings_window_object.show)
        self.MenuBar_user_guide.triggered.connect(self.show_help)

        self.MenuBar_2D_view.triggered.connect(lambda: self.change_window(View2DClass.name))
        self.MenuBar_Spectrometer_Window.triggered.connect(lambda: self.change_window(SpectrometerWindowClass.name))
        self.MenuBar_Gcode_Window.triggered.connect(lambda: self.change_window(GcodeWindowClass.name))
        self.MenuBar_ODMR_Spectrometer_Window.triggered.connect(lambda: self.change_window(ODMRSpectrometerWindowClass.name))

        self.MenuBar_open.triggered.connect(self.FastOpenFile)
        self.MenuBar_save.triggered.connect(lambda: self.FastSaveFile("save"))
        self.MenuBar_save_as.triggered.connect(lambda: self.FastSaveFile("save_as"))
        self.MenuBar_save_all.triggered.connect(lambda: self.FastSaveFile("save_all"))

        self.MenuBar_user_guide.triggered.connect(self.hot_key.clear_current_keys)
        self.MenuBar_2D_view.triggered.connect(self.hot_key.clear_current_keys)
        self.MenuBar_Spectrometer_Window.triggered.connect(self.hot_key.clear_current_keys)
        self.MenuBar_Gcode_Window.triggered.connect(self.hot_key.clear_current_keys)
        self.MenuBar_ODMR_Spectrometer_Window.triggered.connect(self.hot_key.clear_current_keys)

        self.MenuBar_open.triggered.connect(self.hot_key.clear_current_keys)
        self.MenuBar_save.triggered.connect(self.hot_key.clear_current_keys)
        self.MenuBar_save_as.triggered.connect(self.hot_key.clear_current_keys)
        self.MenuBar_save_all.triggered.connect(self.hot_key.clear_current_keys)

    def save_all_settings(self):
        if not self.event_bus.ProgramBusy:
            for ControllerObject in self.__ControllerObject_list:
                try:
                    ControllerObject.save_settings()
                except Exception as e:
                    print(f"MainWindow::save_all_settings::{ControllerObject.name} не обладает функцией сохранения или она неисправна\nОшибка {e}")
            try:
                self.__settingsObject.save_settings([self.current_window])
            except Exception as e:
                print(f"MainWindow::save_all_settings::{self.name} не обладает функцией сохранения или она неисправна\nОшибка {e}")

            for WindowObject in self.__WindowObject_list:
                try:
                    WindowObject.save_settings()
                except Exception as e:
                    print(f"MainWindow::save_all_settings::{WindowObject.name} не обладает функцией сохранения или она неисправна\nОшибка {e}")
            try:
                self.__settingsObject.save_settings([self.current_window])
            except Exception as e:
                print(f"MainWindow::save_all_settings::{self.name} не обладает функцией сохранения или она неисправна\nОшибка {e}")

