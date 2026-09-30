from PyQt6.QtWidgets import QComboBox, QLineEdit, QCheckBox, QRadioButton, QButtonGroup, QFileDialog, QPushButton
from packages.core.widgets.ComboBox import upgradeComboBox


class SaveSettings:
    def __init__(self, frame, event_bus):
        self.event_bus = event_bus

        self.row_separator_tab_radioButton = frame.findChild(QRadioButton, "row_separator_tab_radioButton")
        self.row_separator_comma_radioButton = frame.findChild(QRadioButton, "row_separator_comma_radioButton")
        self.row_separator_semicolon_radioButton = frame.findChild(QRadioButton, "row_separator_semicolon_radioButton")

        self.decimal_separator_dot_radioButton = frame.findChild(QRadioButton, "decimal_separator_dot_radioButton")
        self.decimal_separator_comma_radioButton = frame.findChild(QRadioButton, "decimal_separator_comma_radioButton")

        self.thousands_separator_dot_radioButton = frame.findChild(QRadioButton, "thousands_separator_dot_radioButton")
        self.thousands_separator_space_radioButton = frame.findChild(QRadioButton,
                                                                     "thousands_separator_space_radioButton")
        self.thousands_separator_none_radioButton = frame.findChild(QRadioButton,
                                                                    "thousands_separator_none_radioButton")

        self.string_quotes_double_radioButton = frame.findChild(QRadioButton, "string_quotes_double_radioButton")
        self.string_quotes_single_radioButton = frame.findChild(QRadioButton, "string_quotes_single_radioButton")
        self.string_quotes_none_radioButton = frame.findChild(QRadioButton, "string_quotes_none_radioButton")

        self.encoding_comboBox = upgradeComboBox(frame.findChild(QComboBox, "encoding_comboBox"))
        self.empty_value_comboBox = upgradeComboBox(frame.findChild(QComboBox, "empty_value_comboBox"))

        self.date_separator_dash_radioButton = frame.findChild(QRadioButton, "date_separator_dash_radioButton")
        self.date_separator_slash_radioButton = frame.findChild(QRadioButton, "date_separator_slash_radioButton")
        self.date_separator_underscore_radioButton = frame.findChild(QRadioButton,
                                                                     "date_separator_underscore_radioButton")

        self.date_format_ymd_radioButton = frame.findChild(QRadioButton, "date_format_ymd_radioButton")
        self.date_format_dmy_radioButton = frame.findChild(QRadioButton, "date_format_dmy_radioButton")
        self.date_format_mdy_radioButton = frame.findChild(QRadioButton, "date_format_mdy_radioButton")

        self.time_separator_colon_radioButton = frame.findChild(QRadioButton, "time_separator_colon_radioButton")
        self.time_separator_underscore_radioButton = frame.findChild(QRadioButton,
                                                                     "time_separator_underscore_radioButton")

        self.time_format_24h_radioButton = frame.findChild(QRadioButton, "time_format_24h_radioButton")
        self.time_format_12h_radioButton = frame.findChild(QRadioButton, "time_format_12h_radioButton")

        self.temp_directory_lineEdit = frame.findChild(QLineEdit, "temp_directory_lineEdit")
        self.temp_directory_browse_pushButton = frame.findChild(QPushButton, "temp_directory_browse_pushButton")

        self.temp_format_custom_comboBox = upgradeComboBox(frame.findChild(QComboBox, "temp_format_custom_comboBox"))

        self.radio_button_groups = {}
        self.button_groups = {}

        self._set_widgets_data()
        self._create_button_groups()
        self._populate_comboboxes()
        self._connect_signals()

    def _set_widgets_data(self):
        """Установка данных для виджетов"""
        radio_data = {
            self.row_separator_tab_radioButton: "\t",
            self.row_separator_comma_radioButton: ",",
            self.row_separator_semicolon_radioButton: ";",

            self.decimal_separator_dot_radioButton: ".",
            self.decimal_separator_comma_radioButton: ",",

            self.thousands_separator_dot_radioButton: ".",
            self.thousands_separator_space_radioButton: " ",
            self.thousands_separator_none_radioButton: "",

            self.string_quotes_double_radioButton: '"',
            self.string_quotes_single_radioButton: "'",
            self.string_quotes_none_radioButton: "",

            self.date_separator_dash_radioButton: "-",
            self.date_separator_slash_radioButton: "/",
            self.date_separator_underscore_radioButton: "_",

            self.date_format_ymd_radioButton: "%Y-%m-%d",
            self.date_format_dmy_radioButton: "%d-%m-%Y",
            self.date_format_mdy_radioButton: "%m-%d-%Y",

            self.time_separator_colon_radioButton: ":",
            self.time_separator_underscore_radioButton: "_",

            self.time_format_24h_radioButton: "%H:%M:%S",
            self.time_format_12h_radioButton: "%I:%M:%S %p",
        }

        for widget, value in radio_data.items():
            if widget:
                widget.setProperty("value", value)

    def _create_button_groups(self):
        groups = {
            "row_separator": [
                self.row_separator_tab_radioButton,
                self.row_separator_comma_radioButton,
                self.row_separator_semicolon_radioButton
            ],
            "decimal_separator": [
                self.decimal_separator_dot_radioButton,
                self.decimal_separator_comma_radioButton
            ],
            "thousands_separator": [
                self.thousands_separator_dot_radioButton,
                self.thousands_separator_space_radioButton,
                self.thousands_separator_none_radioButton
            ],
            "string_quotes": [
                self.string_quotes_double_radioButton,
                self.string_quotes_single_radioButton,
                self.string_quotes_none_radioButton
            ],
            "date_separator": [
                self.date_separator_dash_radioButton,
                self.date_separator_slash_radioButton,
                self.date_separator_underscore_radioButton
            ],
            "date_format": [
                self.date_format_ymd_radioButton,
                self.date_format_dmy_radioButton,
                self.date_format_mdy_radioButton
            ],
            "time_separator": [
                self.time_separator_colon_radioButton,
                self.time_separator_underscore_radioButton
            ],
            "time_format": [
                self.time_format_24h_radioButton,
                self.time_format_12h_radioButton
            ]
        }

        for group_name, radios in groups.items():
            button_group = QButtonGroup()
            button_group.setExclusive(True)

            for radio in radios:
                if radio:
                    button_group.addButton(radio)

            self.button_groups[group_name] = button_group
            self.radio_button_groups[group_name] = radios

    def _populate_comboboxes(self):
        self.encoding_comboBox.addItems(["UTF-8", "UTF-8 BOM", "CP1251", "CP1252", "ISO-8859-1", "ASCII"])
        self.empty_value_comboBox.addItems(["NaN", "NULL", "None", "пустая строка", "0"])
        self.temp_format_custom_comboBox.addItems(["CSV", "HDF5", "JSON", "Parquet"])

    def _connect_signals(self):
        self.temp_directory_browse_pushButton.clicked.connect(self._browse_temp_directory)

    def _browse_temp_directory(self):
        directory = QFileDialog.getExistingDirectory(
            None,
            "Выберите директорию для временных файлов",
            self.temp_directory_lineEdit.text() or ""
        )
        if directory:
            self.temp_directory_lineEdit.setText(directory)

    def _get_radio_value(self, radio_group):
        for radio in radio_group:
            if radio and radio.isChecked():
                return radio.property("value")
        return None

    def _set_radio_by_value(self, radio_group, value):
        for radio in radio_group:
            if radio and radio.property("value") == value:
                radio.setChecked(True)
                return True
        return False

    def get_settings(self) -> dict:
        return {
            "row_separator": self._get_radio_value(self.radio_button_groups["row_separator"]),
            "decimal_separator": self._get_radio_value(self.radio_button_groups["decimal_separator"]),
            "thousands_separator": self._get_radio_value(self.radio_button_groups["thousands_separator"]),
            "string_quotes": self._get_radio_value(self.radio_button_groups["string_quotes"]),
            "encoding": self.encoding_comboBox.currentText(),
            "empty_value": self.empty_value_comboBox.currentText(),
            "date_separator": self._get_radio_value(self.radio_button_groups["date_separator"]),
            "date_format": self._get_radio_value(self.radio_button_groups["date_format"]),
            "time_separator": self._get_radio_value(self.radio_button_groups["time_separator"]),
            "time_format": self._get_radio_value(self.radio_button_groups["time_format"]),
            "temp_directory": self.temp_directory_lineEdit.text(),
            "temp_format": self.temp_format_custom_comboBox.currentText()
        }

    def set_settings(self, settings: dict):
        for group_name, radios in self.radio_button_groups.items():
            value = settings.get(group_name)
            if value is not None:
                self._set_radio_by_value(radios, value)

        index = self.encoding_comboBox.findText(settings.get("encoding", "UTF-8"))
        if index >= 0:
            self.encoding_comboBox.setCurrentIndex(index)

        index = self.empty_value_comboBox.findText(settings.get("empty_value", "NaN"))
        if index >= 0:
            self.empty_value_comboBox.setCurrentIndex(index)

        self.temp_directory_lineEdit.setText(settings.get("temp_directory", ""))

        index = self.temp_format_custom_comboBox.findText(settings.get("temp_format", "CSV"))
        if index >= 0:
            self.temp_format_custom_comboBox.setCurrentIndex(index)

    def apply(self):
        pass