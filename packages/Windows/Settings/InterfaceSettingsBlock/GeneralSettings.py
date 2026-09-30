from PyQt6.QtWidgets import QCheckBox, QRadioButton, QComboBox, QLineEdit, QButtonGroup, QPushButton, QColorDialog
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QIntValidator
from packages.core.widgets.ComboBox import upgradeComboBox


class GeneralSettings:
    def __init__(self, frame, event_bus):
        self.event_bus = event_bus

        self.theme_dark_radioButton = frame.findChild(QRadioButton, "theme_dark_radioButton")
        self.theme_light_radioButton = frame.findChild(QRadioButton, "theme_light_radioButton")
        self.theme_system_radioButton = frame.findChild(QRadioButton, "theme_system_radioButton")

        self.length_comboBox = upgradeComboBox(frame.findChild(QComboBox, "length_comboBox"))
        self.wavelength_comboBox = upgradeComboBox(frame.findChild(QComboBox, "wavelength_comboBox"))
        self.frequency_comboBox = upgradeComboBox(frame.findChild(QComboBox, "frequency_comboBox"))
        self.time_comboBox = upgradeComboBox(frame.findChild(QComboBox, "time_comboBox"))

        self.window_remember_position_checkBox = frame.findChild(QCheckBox, "window_remember_position_checkBox")
        self.window_remember_size_checkBox = frame.findChild(QCheckBox, "window_remember_size_checkBox")
        self.window_restore_interface_checkBox = frame.findChild(QCheckBox, "window_restore_interface_checkBox")
        self.window_tray_checkBox = frame.findChild(QCheckBox, "window_tray_checkBox")
        self.window_always_on_top_checkBox = frame.findChild(QCheckBox, "window_always_on_top_checkBox")

        self.plot_antialiasing_checkBox = frame.findChild(QCheckBox, "plot_antialiasing_checkBox")
        self.plot_cache_background_checkBox = frame.findChild(QCheckBox, "plot_cache_background_checkBox")
        self.plot_fill_under_curve_checkBox = frame.findChild(QCheckBox, "plot_fill_under_curve_checkBox")
        self.plot_fill_color_pushButton = frame.findChild(QPushButton, "plot_fill_color_pushButton")
        self.plot_fill_color_lineEdit = frame.findChild(QLineEdit, "plot_fill_color_lineEdit")
        self.plot_fill_color_lineEdit.setValidator(QIntValidator(0, 16777215))
        self.plot_fill_color_lineEdit.setText("4CAF50")
        self.plot_rand_line_color_checkBox = frame.findChild(QCheckBox, "plot_rand_line_color_checkBox")

        self.confirm_exit_checkBox = frame.findChild(QCheckBox, "confirm_exit_checkBox")
        self.confirm_stop_experiment_checkBox = frame.findChild(QCheckBox, "confirm_stop_experiment_checkBox")
        self.confirm_delete_from_tree_checkBox = frame.findChild(QCheckBox, "confirm_delete_from_tree_checkBox")

        self._setup_radio_groups()
        self._populate_comboboxes()
        self._connect_signals()

    def _setup_radio_groups(self):
        group = QButtonGroup()
        group.setExclusive(True)
        group.addButton(self.theme_dark_radioButton)
        group.addButton(self.theme_light_radioButton)
        group.addButton(self.theme_system_radioButton)

        self.theme_dark_radioButton.setProperty("theme", "dark")
        self.theme_light_radioButton.setProperty("theme", "light")
        self.theme_system_radioButton.setProperty("theme", "system")

        self.theme_group = group

    def _populate_comboboxes(self):
        self.length_comboBox.addItems(["м", "см", "мм", "км", "дюйм", "фут"])
        self.wavelength_comboBox.addItems(["нм", "мкм", "мм", "см", "м"])
        self.frequency_comboBox.addItems(["Гц", "кГц", "МГц", "ГГц"])
        self.time_comboBox.addItems(["с", "мс", "мкс", "нс", "мин", "ч"])

    def _connect_signals(self):
        self.plot_fill_color_pushButton.clicked.connect(self._choose_fill_color)
        self.plot_fill_color_lineEdit.textChanged.connect(self._update_fill_color_from_lineedit)

    def _update_fill_color_from_lineedit(self, text):
        if text:
            hex_color = f"#{text}"
            self.plot_fill_color_pushButton.setStyleSheet(f"background-color: {hex_color}; border: 1px solid #666;")

    def _choose_fill_color(self):
        current_color = self.plot_fill_color_lineEdit.text()
        color = QColorDialog.getColor(
            QColor(f"#{current_color}") if current_color else Qt.GlobalColor.blue,
            None,
            "Выберите цвет заливки"
        )
        if color.isValid():
            hex_color = color.name()[1:]
            self.plot_fill_color_lineEdit.setText(hex_color)
            self.plot_fill_color_pushButton.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #666;")

    def _get_theme(self):
        for btn in self.theme_group.buttons():
            if btn.isChecked():
                return btn.property("theme") if btn.property("theme") else btn.text().lower()
        return "system"

    def _set_theme(self, value):
        for btn in self.theme_group.buttons():
            if btn.property("theme") == value or btn.text().lower() == value:
                btn.setChecked(True)
                return

    def _apply_color_to_button(self, pushButton, hex_value):
        if hex_value:
            pushButton.setStyleSheet(f"background-color: #{hex_value}; border: 1px solid #666;")
        else:
            pushButton.setStyleSheet("")

    def get_settings(self) -> dict:
        return {
            "theme": self._get_theme(),
            "length_unit": self.length_comboBox.currentText(),
            "wavelength_unit": self.wavelength_comboBox.currentText(),
            "frequency_unit": self.frequency_comboBox.currentText(),
            "time_unit": self.time_comboBox.currentText(),
            "window_remember_position": self.window_remember_position_checkBox.isChecked(),
            "window_remember_size": self.window_remember_size_checkBox.isChecked(),
            "window_restore_interface": self.window_restore_interface_checkBox.isChecked(),
            "window_tray": self.window_tray_checkBox.isChecked(),
            "window_always_on_top": self.window_always_on_top_checkBox.isChecked(),
            "plot_antialiasing": self.plot_antialiasing_checkBox.isChecked(),
            "plot_cache_background": self.plot_cache_background_checkBox.isChecked(),
            "plot_fill_under_curve": self.plot_fill_under_curve_checkBox.isChecked(),
            "plot_fill_color": self.plot_fill_color_lineEdit.text(),
            "plot_rand_line_color": self.plot_rand_line_color_checkBox.isChecked(),
            "confirm_exit": self.confirm_exit_checkBox.isChecked(),
            "confirm_stop_experiment": self.confirm_stop_experiment_checkBox.isChecked(),
            "confirm_delete_from_tree": self.confirm_delete_from_tree_checkBox.isChecked(),
        }

    def set_settings(self, settings: dict):
        self._set_theme(settings.get("theme", "system"))

        for combo, key in [(self.length_comboBox, "length_unit"),
                           (self.wavelength_comboBox, "wavelength_unit"),
                           (self.frequency_comboBox, "frequency_unit"),
                           (self.time_comboBox, "time_unit")]:
            idx = combo.findText(settings.get(key, ""))
            if idx >= 0:
                combo.setCurrentIndex(idx)

        self.window_remember_position_checkBox.setChecked(settings.get("window_remember_position", False))
        self.window_remember_size_checkBox.setChecked(settings.get("window_remember_size", False))
        self.window_restore_interface_checkBox.setChecked(settings.get("window_restore_interface", False))
        self.window_tray_checkBox.setChecked(settings.get("window_tray", False))
        self.window_always_on_top_checkBox.setChecked(settings.get("window_always_on_top", False))

        self.plot_antialiasing_checkBox.setChecked(settings.get("plot_antialiasing", False))
        self.plot_cache_background_checkBox.setChecked(settings.get("plot_cache_background", False))
        self.plot_fill_under_curve_checkBox.setChecked(settings.get("plot_fill_under_curve", False))

        fill_color = settings.get("plot_fill_color", "4CAF50")
        self.plot_fill_color_lineEdit.setText(fill_color)
        self._apply_color_to_button(self.plot_fill_color_pushButton, fill_color)

        self.plot_rand_line_color_checkBox.setChecked(settings.get("plot_rand_line_color", False))

        self.confirm_exit_checkBox.setChecked(settings.get("confirm_exit", False))
        self.confirm_stop_experiment_checkBox.setChecked(settings.get("confirm_stop_experiment", False))
        self.confirm_delete_from_tree_checkBox.setChecked(settings.get("confirm_delete_from_tree", False))
