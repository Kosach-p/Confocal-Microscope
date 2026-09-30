from packages.Floating_window.node_editor.nodes.node_import import *
from packages.core.widgets.ComboBox import upgradeComboBox
from PyQt6.QtWidgets import QComboBox, QStackedWidget
from packages.core.widgets.QLineEdit_BlenderStyle import DragNumberInput, DragButtonNumberInput
from packages.core.widgets.ComboBoxName import ComboBoxName
from packages.core.widgets.PlainTextEdit import PlainTextEdit


class NodeContentBuilder(QDMNodeContentWidget):
    valueChanged = pyqtSignal(dict)
    valueSet = pyqtSignal(dict)
    funcChanged = pyqtSignal(int)

    def initUI(self):
        pass

    def buildUI(self, node_functions=[{
            'name': 'Гаусс',
            'params': [],
            'inputs': SOCKET_TYPES['any'],
            'outputs': SOCKET_TYPES['any']
        }]):
        """Собирает UI по переданным параметрам"""

        self.params_UI_dict = {}
        self.sockets_dict = {}  # func_name -> (inputs, outputs)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 10, 15, 10)
        main_layout.setSpacing(2)

        self.last_params_UI_key = ''
        self.multi_mode = len(node_functions) > 1

        if self.multi_mode:
            h_layout = QHBoxLayout()
            self.left_icon = QLabel()
            self.left_icon.setFixedSize(25, 25)
            self.left_icon.setAlignment(Qt.AlignCenter)

            self.function_comboBox = upgradeComboBox(QComboBox())
            self.function_comboBox.setFixedHeight(25)

            self.right_icon = QLabel()
            self.right_icon.setFixedSize(25, 25)
            self.right_icon.setAlignment(Qt.AlignCenter)

            h_layout.addWidget(self.left_icon)
            h_layout.addWidget(self.function_comboBox)
            h_layout.addWidget(self.right_icon)

            main_layout.addLayout(h_layout)
            self.function_stack = QStackedWidget()
            main_layout.addWidget(self.function_stack)

        for node_function in node_functions:
            param_UI = []

            page = QWidget()
            page_layout = QVBoxLayout(page)
            page_layout.setContentsMargins(0, 10, 0, 0)

            func_name = node_function['name']
            params = node_function.get('params', [])

            inputs = node_function.get('inputs', [SOCKET_TYPES['any']])
            outputs = node_function.get('outputs', [SOCKET_TYPES['any']])
            self.sockets_dict[func_name] = (inputs, outputs)

            for param in params:
                param_name = param['name']
                param_property = param['parameter_property']

                widget = None

                if param_property['widget'] == 'DragNumberInput':
                    widget = DragNumberInput(label=param_name, step=param_property['step'],
                                             decimal=param_property['decimal'], min_val=param_property['min'],
                                             max_val=param_property['max'], default=param_property['def'])
                    page_layout.addWidget(widget)

                    param_UI.append(widget)
                    widget.valueChanged.connect(self.valueChanged)
                    widget.valueSet.connect(self.valueSet)

                if param_property['widget'] == 'DragButtonNumberInput':
                    widget = DragButtonNumberInput(label=param_name, step=param_property['step'], min_val=param_property.get('min', -2147483648),
                                             max_val=param_property.get('max', 2147483647), decimal=param_property['decimal'], default=param_property['def'])

                    page_layout.addWidget(widget)

                    param_UI.append(widget)
                    widget.valueChanged.connect(self.valueChanged)
                    widget.valueSet.connect(self.valueSet)

                if param_property['widget'] == 'QComboBox':
                    widget = ComboBoxName(label=param_name, name_list=param_property['name_list'], values=param_property['data_list'])

                    page_layout.addWidget(widget)

                    param_UI.append(widget)
                    widget.valueChanged.connect(self.valueChanged)
                    widget.valueSet.connect(self.valueSet)

                if param_property['widget'] == 'QPlainTextEdit':
                    widget = PlainTextEdit(label=param_name)

                    page_layout.addWidget(widget)

                    param_UI.append(widget)
                    widget.valueChanged.connect(self.valueChanged)
                    widget.valueSet.connect(self.valueSet)

                if param_property['widget'] == 'QLabel':
                    widget = QLabel()
                    widget.setText(param_name)

                    page_layout.addWidget(widget)

                if param_property['widget'] == 'self':
                    page_layout.addWidget(param_property['QWidget'])

            self.params_UI_dict[func_name] = param_UI
            self.last_params_UI_key = func_name

            page_layout.addStretch()

            if self.multi_mode:
                self.function_stack.addWidget(page)
                self.function_comboBox.addItem(func_name)
            else:
                main_layout.addWidget(page)

        if self.multi_mode:
            self.function_comboBox.currentIndexChanged.connect(self.function_stack.setCurrentIndex)
            self.function_comboBox.currentIndexChanged.connect(self.funcChanged)
            self.function_comboBox.currentIndexChanged.connect(self.set_socket_image)
            self.function_stack.setCurrentIndex(0)

            self.set_socket_image()

    def set_socket_image(self):
        input_type, output_type = self.get_sockets()

        if input_type == SOCKET_TYPES['matrix_2d'] or input_type == SOCKET_TYPES['matrix_3d'] or input_type == SOCKET_TYPES['matrix_list_2d']:
            input_path = 'Icon/image/matrix.png'
        elif input_type == SOCKET_TYPES['spectrum'] or input_type == SOCKET_TYPES['spectrum_list']:
            input_path = 'Icon/image/graph.png'
        elif input_type == SOCKET_TYPES['number'] or input_type == SOCKET_TYPES['number_list']:
            input_path = 'Icon/image/numeric.png'
        else:
            input_path = 'Icon/image/all.png'

        if output_type == SOCKET_TYPES['matrix_2d'] or output_type == SOCKET_TYPES['matrix_3d'] or output_type == SOCKET_TYPES['matrix_list_2d']:
            output_path = 'Icon/image/matrix.png'
        elif output_type == SOCKET_TYPES['spectrum'] or output_type == SOCKET_TYPES['spectrum_list']:
            output_path = 'Icon/image/graph.png'
        elif output_type == SOCKET_TYPES['number'] or output_type == SOCKET_TYPES['number_list']:
            output_path = 'Icon/image/numeric.png'
        else:
            output_path = 'Icon/image/all.png'

        self.left_icon.setPixmap(QPixmap(input_path).scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.right_icon.setPixmap(QPixmap(output_path).scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def get_func(self):
        if self.multi_mode:
            current_func = self.function_comboBox.currentText()
            return current_func
        else:
            return self.last_params_UI_key

    def get_params(self):
        params_dict = {}

        if self.multi_mode:
            current_func = self.function_comboBox.currentText()
            l = self.params_UI_dict.get(current_func, [])
        else:
            l = self.params_UI_dict[self.last_params_UI_key]

        for widget in l:
            params_dict[widget.get_name()] = widget.value()

        return params_dict

    def get_sockets(self):
        """Возвращает (inputs, outputs) для текущей функции"""
        func_name = self.get_func()
        return self.sockets_dict.get(func_name, ([SOCKET_TYPES['any']], [SOCKET_TYPES['any']]))