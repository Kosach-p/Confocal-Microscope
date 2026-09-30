from packages.Floating_window.node_editor.nodes.node_import import *
from packages.core.widgets.ComboBox import upgradeComboBox
from PyQt6.QtWidgets import QComboBox, QStackedWidget
from packages.core.widgets.QLineEdit_BlenderStyle import DragNumberInput, DragButtonNumberInput
from packages.core.widgets.ComboBoxName import ComboBoxName


class VisualNodeContentBuilder(QDMNodeContentWidget):
    def initUI(self):
        pass

    def buildUI(self, widget):
        """Собирает UI по переданным параметрам"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(widget)
