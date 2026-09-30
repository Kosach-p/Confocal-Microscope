from packages.Floating_window.node_editor.nodes.node_import import *


class INintGraphicsNode(CalcGraphicsNode):
    def initSizes(self):
        super().initSizes()
        self.height = 115


class INintContent(QDMNodeContentWidget):
    def initUI(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 14, 15, 10)
        main_layout.setSpacing(2)

        # Выбор виджета
        self.widget_combo = upgradeComboBox(QComboBox())
        self.widget_combo.setFixedHeight(25)
        # Выбор блока
        self.block_combo = upgradeComboBox(QComboBox())
        self.block_combo.setFixedHeight(25)

        main_layout.addWidget(self.widget_combo)
        main_layout.addWidget(self.block_combo)


class INintNode(CalcNode):
    icon = local_import_Icon
    op_code = OP_NODE_INPUT_INT
    op_title = "Импорт внутренний"
    inputs = []
    outputs = [0]
    GraphicsNode_class = INintGraphicsNode
    NodeContent_class = INintContent

    def __init__(self, scene, MP):
        super().__init__(scene, MP)
        self._data = None
        self._func_dict = {}
        self._updating = False  # Флаг блокировки обновлений

        # Подключаем сигналы
        self.content.widget_combo.currentIndexChanged.connect(self._on_widget_changed)
        self.content.block_combo.currentIndexChanged.connect(self._on_block_changed)

        # Регистрируем внешние обновления
        NodeRegistry.register_callback(self._on_external_update)

        # Первоначальная инициализация
        self._update_all()

    def _on_widget_changed(self, index):
        """Обработчик смены виджета (источника)"""
        if self._updating:
            return

        self._updating = True
        try:
            self._update_block_list()
            if self.content.block_combo.count() > 0:
                self.content.block_combo.setCurrentIndex(0)
            self._apply_changes()
        finally:
            self._updating = False

    def _on_block_changed(self, index):
        """Обработчик смены блока (данных)"""
        if self._updating:
            return

        self._updating = True
        try:
            self._apply_changes()
        finally:
            self._updating = False

    def _on_external_update(self, name=None):
        """Обработчик внешнего обновления (из NodeRegistry)"""
        if self._updating:
            return

        self._updating = True
        try:
            self._update_all()
        finally:
            self._updating = False

    def _update_all(self):
        """Полное обновление всех комбобоксов"""
        # Сохраняем текущие значения для восстановления
        try:
            current_widget = self.content.widget_combo.currentText()
        except:
            self.close()
        current_block = self.content.block_combo.currentText()

        self._update_widget_list()

        if current_widget:
            idx = self.content.widget_combo.findText(current_widget)
            if idx >= 0:
                self.content.widget_combo.setCurrentIndex(idx)

        self._update_block_list()

        if current_block:
            idx = self.content.block_combo.findText(current_block)
            if idx >= 0:
                self.content.block_combo.setCurrentIndex(idx)

        self._apply_changes()

    def _update_widget_list(self):
        """Обновление списка виджетов"""
        func_dict = NodeRegistry.get_all_input_func()

        if self._func_dict != func_dict:
            self._func_dict = dict(func_dict)
            self.content.widget_combo.clear()
            for name, data in self._func_dict.items():
                self.content.widget_combo.addItem(name, data)

    def _update_block_list(self):
        """Обновление списка блоков на основе выбранного виджета"""
        func = self.content.widget_combo.currentData()

        if not callable(func):
            return
        current_block = self.content.block_combo.currentText()

        self.content.block_combo.clear()
        dataset = func()
        if not dataset:
            return None

        for params, dataset_list, vis_list, select_list in dataset:
            name = params['params']['name']
            self.content.block_combo.addItem(name, dataset_list)

        if current_block:
            idx = self.content.block_combo.findText(current_block)
            if idx >= 0:
                self.content.block_combo.setCurrentIndex(idx)
            else:
                self.content.block_combo.setCurrentIndex(0)
        else:
            self.content.block_combo.setCurrentIndex(0)

    def _apply_changes(self):
        """Применяем изменения - ОДНО обновление"""
        dtype = detect_data_type(self.content.block_combo.currentData())

        if dtype == "empty":
            self.outputs[0].changeSocketType(1)
        elif 'matrix' in dtype:
            self.outputs[0].changeSocketType(2)
        elif 'spectrum' in dtype:
            self.outputs[0].changeSocketType(3)

        self.onStateChanged()

    def evalOperation(self, input_values):
        super().evalOperation(input_values)
        self.evalOperation_cplt(self.content.block_combo.currentData())

    def close(self):
        NodeRegistry.unregister_callback(self.update_block_combo)
        self.remove()