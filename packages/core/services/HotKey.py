# packages/core/services/ShortcutManager.py
from PyQt6.QtGui import QShortcut, QKeySequence
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication
from packages.Floating_window.node_editor.NodeEditor import NodeEditorClass


class HotKeyConverter:
    def get_key_by_physical_code(self, native_code):
        """
        Возвращает название клавиши на основе физической позиции,
        игнорируя раскладку клавиатуры.
        """
        # Маппинг физических позиций QWERTY клавиатуры

        physical_map_soft = {
            0x10: 'Q', 0x11: 'W', 0x12: 'E', 0x13: 'R', 0x14: 'T',
            0x15: 'Y', 0x16: 'U', 0x17: 'I', 0x18: 'O', 0x19: 'P',
            0x1E: 'A', 0x1F: 'S', 0x20: 'D', 0x21: 'F', 0x22: 'G',
            0x23: 'H', 0x24: 'J', 0x25: 'K', 0x26: 'L',
            0x2C: 'Z', 0x2D: 'X', 0x2E: 'C', 0x2F: 'V', 0x30: 'B',
            0x31: 'N', 0x32: 'M',

            # Цифры (верхний ряд)
            0x02: '1', 0x03: '2', 0x04: '3', 0x05: '4', 0x06: '5',
            0x07: '6', 0x08: '7', 0x09: '8', 0x0A: '9', 0x0B: '0',

            # NumPad
            0x52: 'Num 0', 0x4F: 'Num 1', 0x50: 'Num 2',
            0x51: 'Num 3', 0x4B: 'Num 4', 0x4C: 'Num 5',
            0x4D: 'Num 6', 0x47: 'Num 7', 0x48: 'Num 8',
            0x49: 'Num 9',
            0x53: 'Num .', 0x37: 'Num *', 0x4A: 'Num -',
            0x4E: 'Num +', 0xE01C: 'Num Enter', 0xE035: 'Num /',
            0xE045: 'Num Lock',

            # Специальные клавиши
            0x01: 'Esc', 0x0F: 'Tab', 0x3A: 'CapsLock',
            0x2A: 'Shift', 0x36: 'Shift',
            0x1D: 'Ctrl', 0xE01D: 'Ctrl',
            0x38: 'Alt', 0xE038: 'Alt',
            0x39: 'Space', 0x1C: 'Enter',
            0x0E: 'Backspace', 0xE037: 'Print Screen',
            0x46: 'Scroll Lock', 0x45: 'Pause/Break',

            # Стрелки
            0xE048: 'Up', 0xE050: 'Down',
            0xE04B: 'Left', 0xE04D: 'Right',

            # Функциональные клавиши
            0x3B: 'F1', 0x3C: 'F2', 0x3D: 'F3', 0x3E: 'F4',
            0x3F: 'F5', 0x40: 'F6', 0x41: 'F7', 0x42: 'F8',
            0x43: 'F9', 0x44: 'F10', 0x57: 'F11', 0x58: 'F12',

            # Клавиши редактирования
            0xE052: 'Insert', 0xE053: 'Delete',
            0xE047: 'Home', 0xE04F: 'End',
            0xE049: 'Page Up', 0xE051: 'Page Down',

            # Скобки и символы (физические позиции QWERTY)
            0x1A: '[', 0x1B: ']',
            0x27: ';', 0x28: '\'',
            0x33: ',', 0x34: '.', 0x35: '/',
            0x29: '`',
            0x2B: '\\',
        }

        return physical_map_soft.get(native_code, f"Unknown (0x{native_code:02X})")

    def nativeCodeCombination2str(self, combination):
        if "Shift" in combination:
            combination.remove("Shift")
            combination.insert(0, "Shift")
        if "Alt" in combination:
            combination.remove("Alt")
            combination.insert(0, "Alt")
        if "Ctrl" in combination:
            combination.remove("Ctrl")
            combination.insert(0, "Ctrl")
        if combination:
            display_text = "+".join(combination)
        else:
            display_text = "Нажмите клавиши"

        return display_text


class HotKeyManager:
    """Обработчик горячих клавиш приложения"""
    name = "HotKeyManager"
    HotKeyBlock = "Main Window"

    def __init__(self, main_window, event_bus):
        self.main_window = main_window
        self.event_bus = event_bus
        self._original_key_press = main_window.keyPressEvent
        main_window.keyPressEvent = self.keyPressEvent
        main_window.keyReleaseEvent = self.keyReleaseEvent

        self.current_keys = list()
        self.HotKeys = dict()
        self.actions = dict()
        self.codeConverter = HotKeyConverter()

        self.__connection_init()
        #print("HotKeyManager::__init__:: УБРАТЬ, если не нужно запускать NODE editor по умолчанию")
        #self.main_window.change_float_window(NodeEditorClass.name)

    def __connection_init(self):
        self.event_bus.Settings.connect(self.__event_process)

    def __event_process(self, transmitter, receiver, command, data):
        """ Обработчик emit в выбранном канале """
        if transmitter == self.name:
            return
        if receiver == self.name or receiver == "All":
            if command == "HotKeys":
                self.HotKeys = data[0].get(self.HotKeyBlock, None)

                self.actions = self.HotKeys.get("actions")
                self.main_window.MenuBar_2D_view.setShortcut(QKeySequence(self.actions.get("view.2d").get("keys")))
                self.main_window.MenuBar_Spectrometer_Window.setShortcut(QKeySequence(self.actions.get("view.spectrometer").get("keys")))
                self.main_window.MenuBar_Gcode_Window.setShortcut(QKeySequence(self.actions.get("view.gcode").get("keys")))
                self.main_window.MenuBar_ODMR_Spectrometer_Window.setShortcut(QKeySequence(self.actions.get("view.odmr").get("keys")))

                self.main_window.MenuBar_open.setShortcut(QKeySequence(self.actions.get("file.open").get("keys")))
                self.main_window.MenuBar_save.setShortcut(QKeySequence(self.actions.get("file.save").get("keys")))
                self.main_window.MenuBar_save_as.setShortcut(QKeySequence(self.actions.get("file.save_as").get("keys")))
                self.main_window.MenuBar_save_all.setShortcut(QKeySequence(self.actions.get("file.save_all").get("keys")))

                self.main_window.MenuBar_user_guide.setShortcut(QKeySequence(self.actions.get("settings.help").get("keys")))

    def keyPressEvent(self, event):
        native_code = event.nativeScanCode()
        key_name = self.codeConverter.get_key_by_physical_code(native_code)
        if key_name:
            if key_name not in self.current_keys:
                self.current_keys.append(key_name)
            self._keyPressEvent()

    def keyReleaseEvent(self, event):
        native_code = event.nativeScanCode()
        key_name = self.codeConverter.get_key_by_physical_code(native_code)

        if key_name and key_name in self.current_keys:
            self.current_keys.remove(key_name)

        event.accept()

    def clear_current_keys(self):
        self.current_keys = []

    def _keyPressEvent(self):
        """Обработчик нажатий клавиш с использованием скан-кодов"""
        if self.HotKeys is None:
            return
        KeyCombo = self.codeConverter.nativeCodeCombination2str(self.current_keys)

        action_name = None

        for a in self.HotKeys.get("actions"):
            action = self.actions.get(a)
            keys = action.get("keys", "")
            if KeyCombo == keys:
                action_name = a
                self.current_keys = []

        if action_name is None:
            return
        elif action_name == "view.fullscreen":
            self.main_window.ToggleFullScreen()
        elif action_name == "floatwindow.node":
            self.main_window.change_float_window(NodeEditorClass.name)
        elif action_name == "floatwindow.script":
            print("Открыть скриптовое окно")
