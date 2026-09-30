from packages.Floating_window.node_editor.nodes.node_import import *
from packages.core.widgets.QLineEdit_BlenderStyle import DragNumberInput, DragButtonNumberInput
from packages.core.widgets.QColorMapDialog import ColormapDialog, ColormapButton


class OutputGraphicsNode(CalcGraphicsNode):
    def initSizes(self):
        super().initSizes()
        self.height = 145


class OutputContent(QDMNodeContentWidget):
    def initUI(self):
        self.params_UI_dict = {}
        self.params_widget_dict = {}

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 14, 15, 10)
        main_layout.setSpacing(2)

        # Выбор виджета
        self.widget_combo = upgradeComboBox(QComboBox())
        self.widget_combo.setFixedHeight(25)

        main_layout.addWidget(self.widget_combo)
        # Стак для двух видов экспорта в виджета - матрицы и спектра
        self.function_stack = QStackedWidget()

        # Страница матрицы. Параметры - скрыть родителя, цветовая карта, прозрачность
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 10, 0, 0)

        layout = QHBoxLayout()

        chb = QCheckBox()
        chb.setText("Скрыть родителя")
        layout.addWidget(chb)

        self.color_map_btn = ColormapButton("magma")
        self.color_map_btn.setFixedSize(25, 25)
        self.color_map_btn.setProperty("color", "magma")
        layout.addWidget(self.color_map_btn)

        page_layout.addLayout(layout)

        DragNumber = DragNumberInput(label="alpha", min_val=0, max_val=1, step=0.01, decimal=2, default=1)
        page_layout.addWidget(DragNumber)

        self.params_UI_dict["matrix"] = page
        self.params_widget_dict["matrix"] = {"checkBox": chb, "color": self.color_map_btn, "DragNumber": DragNumber}
        self.function_stack.addWidget(page)

        main_layout.addWidget(self.function_stack)

        # Страница спектра. Параметры - скрыть родителя, цвет линии, слой линии
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 10, 0, 0)

        layout = QHBoxLayout()

        chb = QCheckBox()
        chb.setText("Скрыть родителя")
        layout.addWidget(chb)

        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(25, 25)
        self.color_btn.setStyleSheet("border-radius: 4px; background-color: #ffffff;")
        self.color_btn.setProperty("color", QColor(255, 255, 255))
        layout.addWidget(self.color_btn)

        page_layout.addLayout(layout)

        DragNumber = DragButtonNumberInput(label="Слой", step=1, decimal=0, default=5)
        page_layout.addWidget(DragNumber)

        self.params_UI_dict["spectrum"] = page
        self.params_widget_dict["spectrum"] = {"checkBox": chb, "color": self.color_btn, "DragNumber": DragNumber}
        self.function_stack.addWidget(page)

    def get_params(self, type):
        widgets = self.params_widget_dict[type]
        return {"hide_parent": widgets["checkBox"].isChecked(), "color": widgets["color"].property("color"), "value": widgets["DragNumber"].value()}


class OutputNode(CalcNode):
    icon = local_export_Icon
    op_code = OP_NODE_EXPORT_INT
    op_title = "Экспорт внутренний"
    inputs = [0]
    outputs = []
    GraphicsNode_class = OutputGraphicsNode
    NodeContent_class = OutputContent

    def __init__(self, scene, MP):
        super().__init__(scene, MP)
        self.content.color_btn.clicked.connect(self.pick_color)
        self.content.color_map_btn.clicked.connect(self.pick_color_map)
        self.content.widget_combo.currentIndexChanged.connect(self.update_widget_combo)

        self._func_dict = {}
        self.update_widget_combo()

        NodeRegistry.register_callback(self.update_widget_combo)

    def pick_color(self):
        color = QColorDialog.getColor(self.content.color_btn.property("color"), None, "Выберите цвет")
        if color.isValid():
            self.content.color_btn.setProperty("color", color)
            self.content.color_btn.setStyleSheet(f"border-radius: 4px; background-color: {color.name()};")
        self._apply_changes()

    def pick_color_map(self):
        """Открытие диалога выбора цветовой карты"""
        dialog = ColormapDialog()
        if dialog.exec() == QDialog.DialogCode.Accepted:
            cmap_name = dialog.get_selected_cmap()
            self.content.color_map_btn.setProperty("color", cmap_name)
            self.content.color_map_btn.cmap_name = cmap_name

        self._apply_changes()

    def update_widget_combo(self, index=None, user_name=None):
        """ Обновляем ComboBox с виджетами """
        try:
            current_text = self.content.widget_combo.currentText()
        except:
            NodeRegistry.unregister_callback(self.update_widget_combo)
            self.remove()
            return

        func_dict = NodeRegistry.get_all_output_func()

        if self._func_dict != func_dict:
            self._func_dict = dict(func_dict)
            self.content.widget_combo.clear()
            for name, data in self._func_dict.items():
                self.content.widget_combo.addItem(name, data)
            self.content.widget_combo.setCurrentText(current_text)

        type = NodeRegistry.get_type(current_text)
        if type is not None:
            self.content.function_stack.setCurrentWidget(self.content.params_UI_dict[type])
        self._apply_changes()

    def _changeSocketType(self, dtype):
        if dtype == "empty":
            self.inputs[0].changeSocketType(1)
        elif 'matrix' in dtype:
            self.inputs[0].changeSocketType(2)
        elif 'spectrum' in dtype:
            self.inputs[0].changeSocketType(3)

    def _apply_changes(self):
        """Применяем изменения - ОДНО обновление"""
        self._on_param_changed()

    def evalOperation(self, input_values):
        super().evalOperation(input_values)
        if input_values:
            data = input_values[0]

            if data is not False:
                target = self.content.widget_combo.currentText()
                func = NodeRegistry.get_output_func(target)
                type = NodeRegistry.get_type(target)

                params = self.content.get_params(type)

                if callable(func):
                    result, raise_text = func(data, params=params, id=self.id)
                    self.evalOperation_cplt(result)
                else:
                    self.evalOperation_cplt(None)
            self._changeSocketType(dtype=detect_data_type(data))
        else:
            self._changeSocketType(dtype="empty")