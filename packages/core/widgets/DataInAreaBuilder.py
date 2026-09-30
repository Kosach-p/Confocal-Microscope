from packages.Floating_window.node_editor.nodes.node_import import *
from packages.core.widgets.ComboBox import upgradeComboBox
from PyQt6.QtWidgets import QComboBox, QStackedWidget, QGridLayout
from packages.core.widgets.QLineEdit_BlenderStyle import DragNumberInput, DragButtonNumberInput
from packages.core.widgets.ComboBoxName import ComboBoxName
from packages.core.widgets.PlainTextEdit import PlainTextEdit


class DataInAreaBuilder(QWidget):
    valueChanged = pyqtSignal(dict)
    valueSet = pyqtSignal(dict)
    funcChanged = pyqtSignal(int)

    def __init__(self, widgets=[{'class': QLabel, 'pos': (0, 0), 'params': {}}]):
        super().__init__()
        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setSpacing(4)

        for widget in widgets:
            w = widget['class'](**widget['params'])
            self._grid.addWidget(w, widget['pos'][0], widget['pos'][1])

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
