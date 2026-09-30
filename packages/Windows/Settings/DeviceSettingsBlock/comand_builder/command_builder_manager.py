from PyQt6.QtWidgets import QComboBox, QStackedWidget, QGroupBox
from packages.Windows.Settings.DeviceSettingsBlock.comand_builder.bin.bin_coder import binCoder
from packages.Windows.Settings.DeviceSettingsBlock.comand_builder.ascii.ascii_coder import asciiCoder
from packages.core.widgets.ComboBox import upgradeComboBox
from packages.core.config.device_schema import CoderType, CODER_TYPE_NAMES_RU
from ui.ControllerSettings.command_builder.CommandBuilder import Ui_commands_GroupBox


class DeviceCommandBuilder(QGroupBox, Ui_commands_GroupBox):
    def __init__(self):
        super().__init__()
        self.init_cplt = False
        self.setupUi(self)
        self.commands_comboBox = upgradeComboBox(self.findChild(QComboBox, "commands_comboBox"))

        # Два раздельных ComboBox'а для типа кодера и декодера
        self.coder_format_comboBox = upgradeComboBox(self.findChild(QComboBox, "coder_format_comboBox"))
        self.decoder_format_comboBox = upgradeComboBox(self.findChild(QComboBox, "decoder_format_comboBox"))

        self.coder_stackedWidget = self.findChild(QStackedWidget, "coder_stackedWidget")
        self.decoder_stackedWidget = self.findChild(QStackedWidget, "decoder_stackedWidget")

        self.coder_dict = {}
        self.decoder_dict = {}

        self.last_coder_widget = None
        self.last_decoder_widget = None
        self.last_command_key = None
        self.commands = {}

        self.connection_init()

    def connection_init(self):
        self.commands_comboBox.currentIndexChanged.connect(self.on_commands_index_changed)
        self.coder_format_comboBox.currentIndexChanged.connect(self.coder_state_changed)
        self.decoder_format_comboBox.currentIndexChanged.connect(self.decoder_state_changed)

    def coder_state_changed(self):
        self.commands[self.last_command_key]['coder_type'] = self.coder_format_comboBox.currentData()
        self.coder_stackedWidget.setCurrentWidget(self.coder_dict[self.coder_format_comboBox.currentData()])
        self.set_current_config()

    def decoder_state_changed(self):
        self.commands[self.last_command_key]['decoder_type'] = self.decoder_format_comboBox.currentData()
        self.decoder_stackedWidget.setCurrentWidget(self.decoder_dict[self.decoder_format_comboBox.currentData()])
        self.set_current_config()

    def setUI(self):
        self.coder_dict = {
            CoderType.BIN: binCoder(),
            CoderType.ASCII: asciiCoder(),
        }
        self.decoder_dict = {
            CoderType.BIN: binCoder(),
            CoderType.ASCII: asciiCoder(),
        }

        for coder_type, widget in self.coder_dict.items():
            name_ru = CODER_TYPE_NAMES_RU.get(coder_type, str(coder_type))
            self.coder_format_comboBox.addItem(name_ru, coder_type)
            self.coder_stackedWidget.addWidget(widget)
            widget.coder_changed.connect(self.on_coder_changed)

        for coder_type, widget in self.decoder_dict.items():
            name_ru = CODER_TYPE_NAMES_RU.get(coder_type, str(coder_type))
            self.decoder_format_comboBox.addItem(name_ru, coder_type)
            self.decoder_stackedWidget.addWidget(widget)
            widget.coder_changed.connect(self.on_decoder_changed)

        self.init_cplt = True

        self.set_current_config()

    # ------------------------------------------------------------
    # Сохранение/восстановление при переключении команд
    # ------------------------------------------------------------

    def on_commands_index_changed(self):
        if self.last_command_key is not None and self.last_coder_widget is not None:
            coder_type, coder_data = self.last_coder_widget.get_params()
            self.commands[self.last_command_key]['coder_params'][str(coder_type)] = coder_data
            self.commands[self.last_command_key]['coder_type'] = str(coder_type)

        if self.last_command_key is not None and self.last_decoder_widget is not None:
            decoder_type, decoder_data = self.last_decoder_widget.get_params()
            self.commands[self.last_command_key]['decoder_params'][str(decoder_type)] = decoder_data
            self.commands[self.last_command_key]['decoder_type'] = str(decoder_type)

        # Загружаем новую команду
        self.last_command_key = self.commands_comboBox.currentData()

        self.set_current_config()

    def set_current_config(self):
        if self.last_command_key is None or self.init_cplt is False:
            return
        cmd_data = self.commands.get(self.last_command_key, {})
        # Восстанавливаем coder
        coder_type_str = cmd_data.get('coder_type', CoderType.BIN)
        coder_type = CoderType(coder_type_str)
        self._select_combo_by_data(self.coder_format_comboBox, coder_type)
        self.last_coder_widget = self.coder_stackedWidget.currentWidget()
        if self.last_coder_widget:
            coder_params = cmd_data.get('coder_params', {}).get(str(coder_type), {})
            self.last_coder_widget.set_params({str(coder_type): coder_params})

        # Восстанавливаем decoder
        decoder_type_str = cmd_data.get('decoder_type', str(CoderType.BIN))
        decoder_type = CoderType(decoder_type_str)
        self._select_combo_by_data(self.decoder_format_comboBox, decoder_type)
        self.last_decoder_widget = self.decoder_stackedWidget.currentWidget()
        if self.last_decoder_widget:
            decoder_params = cmd_data.get('decoder_params', {}).get(str(decoder_type), {})
            self.last_decoder_widget.set_params({str(decoder_type): decoder_params})

    def _select_combo_by_data(self, combo, data):
        """Выбирает элемент в ComboBox по data"""
        for i in range(combo.count()):
            if combo.itemData(i) == data:
                combo.setCurrentIndex(i)
                return

    # ------------------------------------------------------------
    # Сигналы от coder/decoder виджетов
    # ------------------------------------------------------------

    def coder_format_changed(self):
        index = self.coder_format_comboBox.currentIndex()
        self.coder_stackedWidget.setCurrentIndex(index)

    def decoder_format_changed(self):
        index = self.decoder_format_comboBox.currentIndex()
        self.decoder_stackedWidget.setCurrentIndex(index)

    def on_coder_changed(self, data):
        coder_type = data[0]
        param_key = data[1]
        param_value = data[2]

        if '_copy' in param_key:
            param_key = param_key.removesuffix('_copy')
            self.commands[self.last_command_key]['coder_params'][str(coder_type)][param_key] = param_value
            self.commands[self.last_command_key]['decoder_params'][str(coder_type)][param_key] = param_value
        else:
            for cmd in self.commands.values():
                cmd['coder_params'][str(coder_type)][param_key] = param_value
                cmd['decoder_params'][str(coder_type)][param_key] = param_value

        self.set_current_config()

    def on_decoder_changed(self, data):
        coder_type = data[0]
        param_key = data[1]
        param_value = data[2]
        for cmd in self.commands.values():
            cmd['decoder_params'][str(coder_type)][param_key] = param_value
            cmd['coder_params'][str(coder_type)][param_key] = param_value

        self.last_coder_widget.set_params({str(coder_type): {param_key: param_value}})
    # ------------------------------------------------------------
    # Публичный API
    # ------------------------------------------------------------

    def set_commands(self, commands: dict):
        self.commands = commands
        self.commands_comboBox.clear()
        for key in self.commands:
            self.commands_comboBox.addItem(key, key)
        self.last_command_key = self.commands_comboBox.currentData()
        self.set_current_config()

    def get_commands(self):
        # Сохраняем текущие параметры перед возвратом
        if self.init_cplt is True:
            if self.last_command_key and self.last_coder_widget:
                coder_type, coder_data = self.last_coder_widget.get_params()
                self.commands[self.last_command_key]['coder_params'][str(coder_type)] = coder_data
                self.commands[self.last_command_key]['coder_type'] = str(coder_type)

            if self.last_command_key and self.last_decoder_widget:
                decoder_type, decoder_data = self.last_decoder_widget.get_params()
                self.commands[self.last_command_key]['decoder_params'][str(decoder_type)] = decoder_data
                self.commands[self.last_command_key]['decoder_type'] = str(decoder_type)
        return self.commands
