from PyQt6.QtWidgets import (QCheckBox, QSpinBox, QTreeWidgetItem, QButtonGroup, QHeaderView, QAbstractItemView,
                             QWidget, QHBoxLayout)

from packages.core.widgets.ComboBox import upgradeComboBox
from packages.core.widgets.SpinBox import upgradeSpinBox
from packages.core.widgets.Animated_button import add_simple_click_feedback

from packages.core.config.device_schema import (Block, ByteOrder, CoderType, BLOCK_NAMES_RU, LENGTH_SOURCES,
                                                CRC_ALGORITHMS, CRC_SOURCES)

from packages.Сommunication.interface_controllers.CommandCalc import bin_coder, sources
from packages.Windows.Settings.DeviceSettingsBlock.comand_builder.bin.order_manager import OrderListManager

from ui.ControllerSettings.command_builder.bin_coder import Ui_Frame
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon

from Icon.IconName import *
from functools import partial


class binCoder(QWidget, Ui_Frame):
    _ui_bytes = None
    coder_changed = pyqtSignal(list)

    def __init__(self):
        self.init_cplt = False
        self.setting_parameters = False
        super().__init__()
        self.setupUi(self)

        # ==================================================================
        # CheckBox'ы — прямой доступ
        # ==================================================================
        self.check_box_dict = {
            Block.START_BYTE: self.start_byte_use_checkBox,
            Block.ADDRESS: self.address_use_checkBox,
            Block.COMMAND_CODE: self.command_use_checkBox,
            Block.END_BYTE: self.end_byte_use_checkBox,
            Block.LENGTH_FIELD: self.len_field_use_checkBox,
            Block.CHECKSUM: self.checksum_use_checkBox,
        }

        # ==================================================================
        # PushButton'ы — ALL (применить ко всем)
        # ==================================================================
        self.start_byte_all_pushButton = add_simple_click_feedback(
            self.start_byte_all_pushButton, QIcon(apply_to_all_Icon), QIcon(check_mark_Icon))
        self.address_all_pushButton = add_simple_click_feedback(
            self.address_all_pushButton, QIcon(apply_to_all_Icon), QIcon(check_mark_Icon))
        self.command_all_pushButton = add_simple_click_feedback(
            self.command_all_pushButton, QIcon(apply_to_all_Icon), QIcon(check_mark_Icon))
        self.end_byte_all_pushButton = add_simple_click_feedback(
            self.end_byte_all_pushButton, QIcon(apply_to_all_Icon), QIcon(check_mark_Icon))
        self.length_field_all_pushButton = add_simple_click_feedback(
            self.len_field_all_pushButton, QIcon(apply_to_all_Icon), QIcon(check_mark_Icon))
        self.checksum_all_pushButton = add_simple_click_feedback(
            self.checksum_all_pushButton, QIcon(apply_to_all_Icon), QIcon(check_mark_Icon))
        self.byteorder_all_pushButton = add_simple_click_feedback(
            self.byteorder_all_pushButton, QIcon(apply_to_all_Icon), QIcon(check_mark_Icon))
        self.order_all_pushButton = add_simple_click_feedback(
            self.order_all_pushButton, QIcon(apply_to_all_Icon), QIcon(check_mark_Icon))

        self.push_button_dict = {
            Block.START_BYTE: self.start_byte_all_pushButton,
            Block.ADDRESS: self.address_all_pushButton,
            Block.COMMAND_CODE: self.command_all_pushButton,
            Block.END_BYTE: self.end_byte_all_pushButton,
            Block.LENGTH_FIELD: self.length_field_all_pushButton,
            Block.CHECKSUM: self.checksum_all_pushButton,
            'byteorder': self.byteorder_all_pushButton,
            'order': self.order_all_pushButton,
        }

        # ==================================================================
        # PushButton'ы — COPY (скопировать)
        # ==================================================================
        self.start_byte_copy_pushButton = add_simple_click_feedback(
            self.start_byte_copy_pushButton, QIcon(apply_to_all_Icon), QIcon(check_mark_Icon))
        self.address_copy_pushButton = add_simple_click_feedback(
            self.address_copy_pushButton, QIcon(apply_to_all_Icon), QIcon(check_mark_Icon))
        self.command_copy_pushButton = add_simple_click_feedback(
            self.command_copy_pushButton, QIcon(apply_to_all_Icon), QIcon(check_mark_Icon))
        self.end_byte_copy_pushButton = add_simple_click_feedback(
            self.end_byte_copy_pushButton, QIcon(apply_to_all_Icon), QIcon(check_mark_Icon))
        self.length_field_copy_pushButton = add_simple_click_feedback(
            self.len_field_copy_pushButton, QIcon(apply_to_all_Icon), QIcon(check_mark_Icon))
        self.checksum_copy_pushButton = add_simple_click_feedback(
            self.checksum_copy_pushButton, QIcon(apply_to_all_Icon), QIcon(check_mark_Icon))
        self.byteorder_copy_pushButton = add_simple_click_feedback(
            self.byteorder_copy_pushButton, QIcon(apply_to_all_Icon), QIcon(check_mark_Icon))
        self.order_copy_pushButton = add_simple_click_feedback(
            self.order_copy_pushButton, QIcon(apply_to_all_Icon), QIcon(check_mark_Icon))

        self.push_button_copy_dict = {
            Block.START_BYTE: self.start_byte_copy_pushButton,
            Block.ADDRESS: self.address_copy_pushButton,
            Block.COMMAND_CODE: self.command_copy_pushButton,
            Block.END_BYTE: self.end_byte_copy_pushButton,
            Block.LENGTH_FIELD: self.length_field_copy_pushButton,
            Block.CHECKSUM: self.checksum_copy_pushButton,
            'byteorder': self.byteorder_copy_pushButton,
            'order': self.order_copy_pushButton,
        }

        # ==================================================================
        # SpinBox'ы — VAL (значения)
        # ==================================================================
        self.start_byte_val_spinBox = upgradeSpinBox(self.start_byte_val_spinBox)
        self.address_val_spinBox = upgradeSpinBox(self.address_val_spinBox)
        self.command_val_spinBox = upgradeSpinBox(self.command_val_spinBox)
        self.end_byte_val_spinBox = upgradeSpinBox(self.end_byte_val_spinBox)

        self.spin_box_val = {
            Block.START_BYTE: self.start_byte_val_spinBox,
            Block.ADDRESS: self.address_val_spinBox,
            Block.COMMAND_CODE: self.command_val_spinBox,
            Block.END_BYTE: self.end_byte_val_spinBox,
        }

        # ==================================================================
        # SpinBox'ы — LEN (размеры)
        # ==================================================================
        self.start_byte_len_spinBox = upgradeSpinBox(self.start_byte_len_spinBox)
        self.address_len_spinBox = upgradeSpinBox(self.address_len_spinBox)
        self.command_len_spinBox = upgradeSpinBox(self.command_len_spinBox)
        self.end_byte_len_spinBox = upgradeSpinBox(self.end_byte_len_spinBox)
        self.length_field_len_spinBox = upgradeSpinBox(self.len_field_len_spinBox)

        self.spin_box_len = {
            Block.START_BYTE: self.start_byte_len_spinBox,
            Block.ADDRESS: self.address_len_spinBox,
            Block.COMMAND_CODE: self.command_len_spinBox,
            Block.END_BYTE: self.end_byte_len_spinBox,
            Block.LENGTH_FIELD: self.length_field_len_spinBox,
        }

        # ==================================================================
        # ComboBox'ы
        # ==================================================================
        self.length_field_include_comboBox = upgradeComboBox(self.len_field_include_comboBox)
        self.checksum_algo_comboBox = upgradeComboBox(self.checksum_algo_comboBox)
        self.checksum_source_comboBox = upgradeComboBox(self.checksum_source_comboBox)

        # ==================================================================
        # RadioButton'ы
        # ==================================================================
        self.byteorder_little_radioButton.setProperty("val", ByteOrder.LITTLE)
        self.byteorder_big_radioButton.setProperty("val", ByteOrder.BIG)

        self.group1 = QButtonGroup(self)
        self.group1.addButton(self.byteorder_little_radioButton)
        self.group1.addButton(self.byteorder_big_radioButton)

        self.group2 = QButtonGroup(self)
        self.group2.addButton(self.hex_radioButton)
        self.group2.addButton(self.bin_radioButton)
        self.group2.addButton(self.dec_radioButton)

        # ==================================================================
        # Остальные виджеты
        # ==================================================================
        self.param_rows = {}

        # ==================================================================
        # Финальная инициализация
        # ==================================================================
        self.ui_init()
        self.connection_init()
        self.init_cplt = True

    # ==================================================================
    # UI Init
    # ==================================================================

    def ui_init(self):
        """Заполняем UI данными из настроек"""
        self.params_TreeWidget.setColumnCount(4)
        self.params_TreeWidget.setHeaderLabels(["Переменная", "Значение", "Размер", "Знаковый"])

        self.params_TreeWidget.setRootIsDecorated(False)
        self.params_TreeWidget.setIndentation(0)
        self.params_TreeWidget.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.params_TreeWidget.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        header = self.params_TreeWidget.header()
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        self.params_TreeWidget.setStyleSheet("""QTreeWidget::item {padding: 4px 5px; margin: 2px 0px; min-height: 20px;}""")

        # Заполняем ComboBox'ы из Enum-словарей
        for key, val in LENGTH_SOURCES.items():
            self.length_field_include_comboBox.addItem(val, key)

        for key, val in CRC_ALGORITHMS.items():
            self.checksum_algo_comboBox.addItem(key, val)

        for key, val in CRC_SOURCES.items():
            self.checksum_source_comboBox.addItem(val, key)

        for key, val in self.push_button_dict.items():
            val.clicked.connect(partial(self.on_all_button_clicked, btn_name=key))

        for key, val in self.push_button_copy_dict.items():
            val.clicked.connect(partial(self.on_copy_button_clicked, btn_name=key))

        # Order List
        self.order_manager = OrderListManager(list_widget=self.order_listWidget)
        self.order_manager.order_changed.connect(self.on_command_param_changed)
        self.order_manager.add_block(BLOCK_NAMES_RU[Block.DATA], Block.DATA)

    # ==================================================================
    # Обработчики кнопок
    # ==================================================================

    def on_all_button_clicked(self, btn_name):
        """Реакция на нажатие кнопки 'Применить ко всем'"""
        data = self.get_params()[1][btn_name]
        self.coder_changed.emit([CoderType.BIN, btn_name, data])

    def on_copy_button_clicked(self, btn_name):
        """Реакция на нажатие кнопки 'Применить к команде'"""
        data = self.get_params()[1][btn_name]
        self.coder_changed.emit([CoderType.BIN, btn_name + '_copy', data])
    # ==================================================================
    # Управление строками параметров
    # ==================================================================

    def add_row(self, var_name="", value=0, bytes_count=1, signed=False):
        item = QTreeWidgetItem(self.params_TreeWidget)
        flags = item.flags()
        #flags &= ~QtCore.Qt.ItemIsDropEnabled
        item.setFlags(flags)
        item.setText(0, var_name)

        value_spin = upgradeSpinBox(QSpinBox())
        value_spin.setValue(value)
        value_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_spin.valueChanged.connect(self.on_command_param_changed)
        self.params_TreeWidget.setItemWidget(item, 1, value_spin)

        len_spin = upgradeSpinBox(QSpinBox())
        len_spin.setValue(bytes_count)
        len_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        len_spin.setRange(0, 4)
        len_spin.valueChanged.connect(self.on_spinbox_len_changed)
        self.params_TreeWidget.setItemWidget(item, 2, len_spin)

        sign = QCheckBox()
        sign.setChecked(signed)
        sign.toggled.connect(self.on_spinbox_len_changed)

        container = QWidget()
        container.setStyleSheet("background-color: transparent;")
        layout = QHBoxLayout(container)
        layout.addWidget(sign)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.params_TreeWidget.setItemWidget(item, 3, container)

        self.param_rows[var_name] = {
            'item': item,
            'value_spin': value_spin,
            'len_spin': len_spin,
            'sign': sign
        }

    def remove_row(self, var_name):
        if var_name in self.param_rows:
            item = self.param_rows[var_name]['item']
            root = self.params_TreeWidget.invisibleRootItem()
            root.removeChild(item)
            del self.param_rows[var_name]

    def get_params_data(self):
        params = []
        for key, val in self.param_rows.items():
            params.append({
                'name': key,
                'value': val.get('value_spin').value(),
                'length': val.get('len_spin').value(),
                'sign': val.get('sign').isChecked()
            })
        return params

    # ==================================================================
    # Сигналы / слоты
    # ==================================================================

    def connection_init(self):
        self.byteorder_little_radioButton.toggled.connect(self.on_command_param_changed)
        self.byteorder_big_radioButton.toggled.connect(self.on_command_param_changed)

        self.hex_radioButton.toggled.connect(self.on_calculus_system_changed)
        self.bin_radioButton.toggled.connect(self.on_calculus_system_changed)
        self.dec_radioButton.toggled.connect(self.on_calculus_system_changed)

        for val in self.spin_box_len.values():
            val.valueChanged.connect(self.on_spinbox_len_changed)
        self.on_spinbox_len_changed()

        for block, val in self.check_box_dict.items():
            val.toggled.connect(lambda checked, b=block: self.on_check_box_used_toggled(b))
        self.on_check_box_used_toggled(None)

        for val in self.spin_box_val.values():
            val.valueChanged.connect(self.on_command_param_changed)

        self.length_field_include_comboBox.currentIndexChanged.connect(self.on_command_param_changed)
        self.checksum_algo_comboBox.currentIndexChanged.connect(self.on_command_param_changed)
        self.checksum_source_comboBox.currentIndexChanged.connect(self.on_command_param_changed)

    def on_check_box_used_toggled(self, block):
        if block is None:
            for b in Block:
                if b in self.check_box_dict:
                    self._update_block_ui_state(b)
        else:
            self._update_block_ui_state(block)
        self.on_command_param_changed()

    def _update_block_ui_state(self, block: Block):
        state = self.check_box_dict[block].isChecked()

        # SpinBox'ы val/len
        if block in self.spin_box_val:
            self.spin_box_val[block].setEnabled(state)
        if block in self.spin_box_len:
            self.spin_box_len[block].setEnabled(state)

        # PushButton
        if block in self.push_button_dict:
            self.push_button_dict[block].setEnabled(state)

        # ComboBox'ы
        if block == Block.LENGTH_FIELD:
            self.length_field_include_comboBox.setEnabled(state)
        elif block == Block.CHECKSUM:
            self.checksum_algo_comboBox.setEnabled(state)
            self.checksum_source_comboBox.setEnabled(state)

        # Order list
        if state:
            self.order_manager.add_block(BLOCK_NAMES_RU[block], block)
        else:
            self.order_manager.remove_block(BLOCK_NAMES_RU[block])

    def on_spinbox_len_changed(self):
        for block, spin_len in self.spin_box_len.items():
            if block in self.spin_box_val:
                max_val = 2 ** (spin_len.value() * 8) - 1
                max_val = min(max_val, 2147483647)
                self.spin_box_val[block].setRange(0, max_val)

        for val in self.param_rows.values():
            sig = val.get('sign').isChecked()
            max_val = 2 ** (val.get('len_spin').value() * 8 - sig) - 1
            max_val = min(max_val, 2147483647)
            min_val = (-2 ** (val.get('len_spin').value() * 8) * sig) // 2
            min_val = max(min_val, -2147483648)
            val.get('value_spin').setRange(min_val, max_val)

        self.on_command_param_changed()

    def on_calculus_system_changed(self):
        val = 0
        prefix = ''
        if self.hex_radioButton.isChecked():
            val = 16
            prefix = '0x'
        elif self.bin_radioButton.isChecked():
            val = 2
            prefix = '0b'
        elif self.dec_radioButton.isChecked():
            val = 10

        for spin in self.spin_box_val.values():
            spin.setPrefix(prefix)
            spin.setDisplayIntegerBase(val)

        for val_dict in self.param_rows.values():
            val_dict.get('value_spin').setPrefix(prefix)
            val_dict.get('value_spin').setDisplayIntegerBase(val)

        self.on_command_param_changed()

    def on_command_param_changed(self):
        if self.init_cplt is False or self.setting_parameters is True:
            return

        coder_type, kwargs = self.get_params()
        result = bin_coder(**kwargs)

        if result['error'] is False:
            sep = ' | '
            if self.hex_radioButton.isChecked():
                text = result['result'].hex(sep[1])
            elif self.bin_radioButton.isChecked():
                text = sep.join(f'{b:08b}' for b in result['result'])
            elif self.dec_radioButton.isChecked():
                text = sep.join(str(b) for b in result['result'])

            l = len(result["result"])
            if l % 100 in (11, 12, 13, 14):
                word = 'байт'
            else:
                last_digit = l % 10
                if last_digit == 1:
                    word = 'байт'
                elif last_digit in (2, 3, 4):
                    word = 'байта'
                else:
                    word = 'байт'

            self.command_example_label.setText(text)
            self.command_example_comment_label.setText(f'Пример команды ({l} {word}):')
        else:
            self.command_example_label.setText(result['result'])
            self.command_example_comment_label.setText('Ошибка:')

    # ==================================================================
    # get_params / set_params
    # ==================================================================

    def get_params(self):
        """Возвращает dict со всеми параметрами кодировки"""
        byteorder = ByteOrder.BIG if self.byteorder_big_radioButton.isChecked() else ByteOrder.LITTLE

        order = []
        for block in self.order_manager.get_order():
            order.append(block.get('data'))

        result = {
            'byteorder': byteorder,
            'params': self.get_params_data(),
            'order': order,
        }

        for block in Block:
            if block == Block.DATA:
                continue
            if block in self.check_box_dict:
                use = self.check_box_dict[block].isChecked()
                length = self.spin_box_len.get(block).value() if block in self.spin_box_len else 1
                value = self.spin_box_val.get(block).value() if block in self.spin_box_val else 0

                if block == Block.LENGTH_FIELD:
                    result[block] = {
                        'use': use,
                        'length': length,
                        'include': self.length_field_include_comboBox.currentData(),
                    }
                elif block == Block.CHECKSUM:
                    result[block] = {
                        'use': use,
                        'length': self.checksum_algo_comboBox.currentData(),
                        'algorithm': self.checksum_algo_comboBox.currentText(),
                        'source': self.checksum_source_comboBox.currentData(),
                    }
                else:
                    result[block] = {'use': use, 'length': length, 'value': value}
        return (CoderType.BIN, result)

    def set_params(self, params):
        """Устанавливает параметры кодировки из словаря"""
        self.setting_parameters = True
        params = params.get(CoderType.BIN, params)

        for block in Block:
            if block == Block.DATA:
                continue
            if block in params:
                block_data = params[block]
                if block in self.check_box_dict:
                    self.check_box_dict[block].setChecked(block_data.get('use', False))
                if block in self.spin_box_len:
                    self.spin_box_len[block].setValue(block_data.get('length', 1))
                if block in self.spin_box_val:
                    self.spin_box_val[block].setValue(block_data.get('value', 0))

        # Length field include
        if Block.LENGTH_FIELD in params:
            include_value = params[Block.LENGTH_FIELD].get('include')
            if include_value is not None:
                index = self.length_field_include_comboBox.findData(include_value)
                if index >= 0:
                    self.length_field_include_comboBox.setCurrentIndex(index)

        # Checksum algorithm / source
        if Block.CHECKSUM in params:
            algorithm = params[Block.CHECKSUM].get('algorithm')
            if algorithm:
                self.checksum_algo_comboBox.setCurrentText(algorithm)

            source_value = params[Block.CHECKSUM].get('source')

            if source_value is not None:
                self.checksum_source_comboBox.setCurrentText(sources.get(source_value))

        # Byteorder
        if 'byteorder' in params:
            if params['byteorder'] == ByteOrder.BIG:
                self.byteorder_big_radioButton.setChecked(True)
            else:
                self.byteorder_little_radioButton.setChecked(True)

        # Params
        if 'params' in params:
            keys = list(self.param_rows.keys())
            for key in keys:
                self.remove_row(key)
            self.param_rows = {}
            for param in params['params']:
                self.add_row(
                    var_name=param.get('name', ''),
                    value=param.get('value', 0),
                    bytes_count=param.get('length', 1),
                    signed=param.get('sign', False)
                )

        # Order
        if 'order' in params:
            self.order_manager.clear()
            for block_name in params['order']:
                self.order_manager.add_block(BLOCK_NAMES_RU.get(block_name, block_name), block_name)

        self.on_check_box_used_toggled(None)
        self.on_spinbox_len_changed()

        self.setting_parameters = False
        self.on_command_param_changed()