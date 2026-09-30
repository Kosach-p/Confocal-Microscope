from packages.Floating_window.node_editor.nodes.node_import import *
from packages.Floating_window.node_editor.nodes.VISUALIZATION.VisualNodeContentBuilder import VisualNodeContentBuilder
from PyQt6.Qsci import QsciScintilla
import json


def convert_to_serializable(obj):
    """Рекурсивно конвертирует numpy типы в Python типы"""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_to_serializable(item) for item in obj]
    return obj


class VisualizationLineNode(CalcGraphicsNode):
    def initSizes(self):
        super().initSizes()
        self.height = 275
        self.width = 275


class VisualizationLineNode(CalcNode):
    icon = "Icon/image/line.png"
    op_code = OP_NODE_LINE
    op_title = "Текстовое отображение данных"
    inputs = [SOCKET_TYPES['any']]
    outputs = []
    GraphicsNode_class = VisualizationLineNode
    NodeContent_class = VisualNodeContentBuilder

    def __init__(self, scene, MP):
        super().__init__(scene, MP)

        self.editor = QsciScintilla()

        self.editor.setMarginWidth(0, 0)
        self.editor.setMarginWidth(1, 0)
        self.editor.setMarginWidth(2, 0)

        for margin in range(self.editor.margins()):
            self.editor.setMarginWidth(margin, 0)

        self.editor.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.editor.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.content.buildUI(widget=self.editor)

    def evalOperation(self, input_values):
        super().evalOperation(input_values)
        result = {'error': False, 'result': True}

        if not input_values:
            result = {'error': True, 'result': "Не переданы данные для отображения"}
            self.evalOperation_cplt(result)
            return True

        a = input_values[0]

        try:
            serializable = convert_to_serializable(a)
            text = json.dumps(serializable, indent=2, ensure_ascii=False)
            self.editor.setText(text)
            result = {'error': False, 'result': True}
        except Exception as e:
            self.close()
            result = {'error': True, 'result': str(e)}

        self.evalOperation_cplt(result)

        if result['error']:
            self.editor.setText("")

        return True

    def close(self):
        NodeRegistry.unregister_callback(self.update_block_combo)
        self.remove()
