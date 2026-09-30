from PyQt6.QtWidgets import QComboBox, QLabel, QWidget, QVBoxLayout, QPushButton, QLineEdit, QFrame
from PyQt6.QtCore import pyqtSignal, QByteArray
from PyQt6.QtGui import QIcon

from packages.Windows.Settings.DeviceSettingsBlock.comand_builder.ascii.tree_manager import ParamsTreeWidget
from packages.Сommunication.interface_controllers.CommandCalc import ascii_coder
from packages.core.widgets.ComboBox import upgradeComboBox
from packages.core.widgets.Animated_button import add_simple_click_feedback

from packages.core.config.device_schema import CoderType, ASCII_ENCODING_NAMES_RU
from packages.core.config.path import ui

from functools import partial
from Icon.IconName import *
import codecs


class asciiCoder(QWidget):
    _ui_bytes = None
    coder_changed = pyqtSignal(list)

    def __init__(self):
        super().__init__()

        if asciiCoder._ui_bytes is None:
            with open(ui("ascii_coder.ui"), 'rb') as f:
                asciiCoder._ui_bytes = QByteArray(f.read())

        from PyQt6.uic import loadUi
        from io import BytesIO

        frame = loadUi(BytesIO(asciiCoder._ui_bytes.data()))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(frame)

        self.cmd_prefix_lineEdit = frame.findChild(QLineEdit, "cmd_prefix_lineEdit")
        self.cmd_suffix_lineEdit = frame.findChild(QLineEdit, "cmd_suffix_lineEdit")
        self.frame_terminator_lineEdit = frame.findChild(QLineEdit, "frame_terminator_lineEdit")
        self.cmd_separator_lineEdit = frame.findChild(QLineEdit, "cmd_separator_lineEdit")

        self.address_prefix_lineEdit = frame.findChild(QLineEdit, "address_prefix_lineEdit")
        self.address_lineEdit = frame.findChild(QLineEdit, "address_lineEdit")
        self.address_suffix_lineEdit = frame.findChild(QLineEdit, "address_suffix_lineEdit")

        self.command_prefix_lineEdit = frame.findChild(QLineEdit, "command_prefix_lineEdit")
        self.command_lineEdit = frame.findChild(QLineEdit, "command_lineEdit")
        self.command_suffix_lineEdit = frame.findChild(QLineEdit, "command_suffix_lineEdit")

        self.line_edit_dict = {
            "cmd_prefix": self.cmd_prefix_lineEdit,
            "cmd_suffix": self.cmd_suffix_lineEdit,
            "frame_terminator": self.frame_terminator_lineEdit,
            "cmd_separator": self.cmd_separator_lineEdit,
            "address_prefix": self.address_prefix_lineEdit,
            "address": self.address_lineEdit,
            "address_suffix": self.address_suffix_lineEdit,
            "command_prefix": self.command_prefix_lineEdit,
            "command": self.command_lineEdit,
            "command_suffix": self.command_suffix_lineEdit,
        }

        self.cmd_prefix_all_pushButton = add_simple_click_feedback(frame.findChild(QPushButton, "cmd_prefix_all_pushButton"), QIcon(apply_to_all_Icon), QIcon(check_mark_Icon))
        self.cmd_suffix_all_pushButton = add_simple_click_feedback(frame.findChild(QPushButton, "cmd_suffix_all_pushButton"), QIcon(apply_to_all_Icon), QIcon(check_mark_Icon))
        self.frame_terminator_all_pushButton = add_simple_click_feedback(frame.findChild(QPushButton, "frame_terminator_all_pushButton"), QIcon(apply_to_all_Icon), QIcon(check_mark_Icon))
        self.cmd_separator_all_pushButton = add_simple_click_feedback(frame.findChild(QPushButton, "cmd_separator_all_pushButton"), QIcon(apply_to_all_Icon), QIcon(check_mark_Icon))
        self.enc_all_pushButton = add_simple_click_feedback(frame.findChild(QPushButton, "enc_all_pushButton"), QIcon(apply_to_all_Icon), QIcon(check_mark_Icon))
        self.address_all_pushButton = add_simple_click_feedback(frame.findChild(QPushButton, "address_all_pushButton"), QIcon(apply_to_all_Icon), QIcon(check_mark_Icon))
        self.command_all_pushButton = add_simple_click_feedback(frame.findChild(QPushButton, "command_all_pushButton"), QIcon(apply_to_all_Icon), QIcon(check_mark_Icon))

        self.cmd_prefix_copy_pushButton = add_simple_click_feedback(frame.findChild(QPushButton, "cmd_prefix_copy_pushButton"), QIcon(apply_to_all_Icon), QIcon(check_mark_Icon))
        self.cmd_suffix_copy_pushButton = add_simple_click_feedback(frame.findChild(QPushButton, "cmd_suffix_copy_pushButton"), QIcon(apply_to_all_Icon), QIcon(check_mark_Icon))
        self.frame_terminator_copy_pushButton = add_simple_click_feedback(frame.findChild(QPushButton, "frame_terminator_copy_pushButton"), QIcon(apply_to_all_Icon),QIcon(check_mark_Icon))
        self.cmd_separator_copy_pushButton = add_simple_click_feedback(frame.findChild(QPushButton, "cmd_separator_copy_pushButton"), QIcon(apply_to_all_Icon),QIcon(check_mark_Icon))
        self.enc_copy_pushButton = add_simple_click_feedback(frame.findChild(QPushButton, "enc_copy_pushButton"),QIcon(apply_to_all_Icon), QIcon(check_mark_Icon))
        self.address_copy_pushButton = add_simple_click_feedback(frame.findChild(QPushButton, "address_copy_pushButton"),QIcon(apply_to_all_Icon), QIcon(check_mark_Icon))
        self.command_copy_pushButton = add_simple_click_feedback(frame.findChild(QPushButton, "command_copy_pushButton"),QIcon(apply_to_all_Icon), QIcon(check_mark_Icon))

        self.push_button_dict = {
            "cmd_prefix": self.cmd_prefix_all_pushButton,
            "cmd_suffix": self.cmd_suffix_all_pushButton,
            "frame_terminator": self.frame_terminator_all_pushButton,
            "cmd_separator": self.cmd_separator_all_pushButton,
            "enc": self.enc_all_pushButton,
            "address": self.address_all_pushButton,
            "command": self.command_all_pushButton,
        }

        self.push_button_copy_dict = {
            "cmd_prefix": self.cmd_prefix_copy_pushButton,
            "cmd_suffix": self.cmd_suffix_copy_pushButton,
            "frame_terminator": self.frame_terminator_copy_pushButton,
            "cmd_separator": self.cmd_separator_copy_pushButton,
            "enc": self.enc_copy_pushButton,
            "address": self.address_copy_pushButton,
            "command": self.command_copy_pushButton,
        }

        self.enc_comboBox = upgradeComboBox(frame.findChild(QComboBox, "enc_comboBox"))

        target_frame = frame.findChild(QFrame, "params_TreeWidget_Frame")

        if target_frame:
            self.params_treeWidget = ParamsTreeWidget()
            self.params_treeWidget.setMinimumHeight(150)

            if not target_frame.layout():
                layout = QVBoxLayout(target_frame)
                layout.setContentsMargins(0, 0, 0, 0)
                layout.setSpacing(0)

            target_frame.layout().addWidget(self.params_treeWidget)

            self.params_treeWidget.show()

        self.command_example_label = frame.findChild(QLabel, "command_example_label")
        self.coded_command_example_label = frame.findChild(QLabel, "coded_command_example_label")
        self.command_example_error_label = frame.findChild(QLabel, "command_example_error_label")
        self.command_example_comment_label = frame.findChild(QLabel, "command_example_comment_label")

        self.param_rows = {}

        self.ui_init()
        self.connection_init()

    # ==================================================================
    # UI Init
    # ==================================================================

    def ui_init(self):
        """Заполняем UI данными из настроек"""
        # Заполняем ComboBox'ы из Enum-словарей
        for key, val in ASCII_ENCODING_NAMES_RU.items():
            self.enc_comboBox.addItem(val, key)

    # ==================================================================
    # Обработчики кнопок
    # ==================================================================

    def on_all_button_clicked(self, btn_name):
        """Реакция на нажатие кнопки 'Применить ко всем'"""
        data = self.get_params()[1].get(btn_name)
        self.coder_changed.emit([CoderType.ASCII, btn_name, data])

    def on_copy_button_clicked(self, btn_name):
        """Реакция на нажатие кнопки 'Применить к команде'"""
        data = self.get_params()[1][btn_name]
        self.coder_changed.emit([CoderType.ASCII, btn_name + '_copy', data])
    # ==================================================================
    # Сигналы / слоты
    # ==================================================================

    def connection_init(self):
        self.enc_comboBox.currentIndexChanged.connect(self.on_command_param_changed)

        for key, val in self.push_button_dict.items():
            val.clicked.connect(partial(self.on_all_button_clicked, btn_name=key))

        for key, val in self.push_button_copy_dict.items():
            val.clicked.connect(partial(self.on_copy_button_clicked, btn_name=key))

        for key, val in self.line_edit_dict.items():
            val.textChanged.connect(self.on_command_param_changed)

        self.params_treeWidget.params_changed.connect(self.on_command_param_changed)

    def on_command_param_changed(self):
        _, kwargs = self.get_params()
        result = ascii_coder(**kwargs)
        self.command_example_label.setText(repr(result["result"].decode(kwargs['enc']))[1:-1])
        self.coded_command_example_label.setText(result["result"].hex("|"))
        self.command_example_error_label.setText("")

    # ==================================================================
    # get_params / set_params
    # ==================================================================

    def decode_escape_sequences(self, text):
        """Декодирует escape-последовательности в строке"""
        if not isinstance(text, str):
            return text
        try:
            return codecs.decode(text, "unicode_escape")
        except Exception:
            return text

    def get_params(self):
        """Возвращает dict со всеми параметрами кодировки"""
        kwargs = {}

        for key, lineEdit in self.line_edit_dict.items():
            if "address" not in key and "command" not in key:
                text = lineEdit.text()
                kwargs[key] = self.decode_escape_sequences(text)

        kwargs['enc'] = self.enc_comboBox.currentData()

        kwargs['address'] = {
            'value': self.decode_escape_sequences(self.address_lineEdit.text()),
            'fmt': 's',
            'prefix': self.decode_escape_sequences(self.address_prefix_lineEdit.text()),
            'suffix': self.decode_escape_sequences(self.address_suffix_lineEdit.text())
        }

        kwargs['command'] = {
            'value': self.decode_escape_sequences(self.command_lineEdit.text()),
            'fmt': 's',
            'prefix': self.decode_escape_sequences(self.command_prefix_lineEdit.text()),
            'suffix': self.decode_escape_sequences(self.command_suffix_lineEdit.text())
        }

        kwargs['params'] = self.params_treeWidget.get_all_params()

        return CoderType.ASCII, kwargs

    def encode_to_escape(self, text):
        """Кодирует строку в escape-последовательности для отображения"""
        if not isinstance(text, str):
            return text
        return text.encode('unicode_escape').decode('ascii')

    def set_params(self, params):
        """Устанавливает параметры кодировки из словаря"""
        if isinstance(params, tuple) and len(params) == 2:
            coder_type, params = params
        elif CoderType.ASCII in params:
            params = params.get(CoderType.ASCII, params)

        # Устанавливаем кодировку
        if 'enc' in params:
            index = self.enc_comboBox.findData(params['enc'])
            if index >= 0:
                self.enc_comboBox.setCurrentIndex(index)

        # Устанавливаем параметры line_edit_dict (все кроме address и command)
        for key, lineEdit in self.line_edit_dict.items():
            if key in params and "address" not in key and "command" not in key:
                text = params[key]
                lineEdit.setText(str(self.encode_to_escape(text)) if text is not None else '')

        # Устанавливаем address
        if 'address' in params:
            addr = params['address']
            self.address_lineEdit.setText(str(self.encode_to_escape(addr.get('value', ''))))
            self.address_prefix_lineEdit.setText(str(self.encode_to_escape(addr.get('prefix', ''))))
            self.address_suffix_lineEdit.setText(str(self.encode_to_escape(addr.get('suffix', ''))))

        # Устанавливаем command
        if 'command' in params:
            cmd = params['command']
            self.command_lineEdit.setText(str(self.encode_to_escape(cmd.get('value', ''))))
            self.command_prefix_lineEdit.setText(str(self.encode_to_escape(cmd.get('prefix', ''))))
            self.command_suffix_lineEdit.setText(str(self.encode_to_escape(cmd.get('suffix', ''))))

        # Устанавливаем параметры
        if 'params' in params:
            self.params_treeWidget.clear()

            for param in params['params']:
                self.params_treeWidget.add_row(
                    var_name=param.get('name', 'A'),
                    value=param.get('value', 0),
                    prefix=self.encode_to_escape(param.get('param_prefix', '')),
                    suffix=self.encode_to_escape(param.get('param_suffix', '')),
                    fmt=param.get('param_fmt', ''),
                    space=param.get('param_space', 10),
                    alignment=param.get('param_alignment', 'right')
                )

        self.on_command_param_changed()