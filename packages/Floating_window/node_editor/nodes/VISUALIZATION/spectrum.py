from packages.Floating_window.node_editor.nodes.node_import import *
from packages.Floating_window.node_editor.nodes.VISUALIZATION.VisualNodeContentBuilder import VisualNodeContentBuilder
from packages.core.widgets.SpectrumChartWidgetLite import SpectrumChart


class VisualizationLineNode(CalcGraphicsNode):
    def initSizes(self):
        super().initSizes()
        self.height = 400
        self.width = 400


class VisualizationLineNode(CalcNode):
    icon = "Icon/image/spectrum.png"
    op_code = OP_NODE_SPECTRUM
    op_title = "Отображение спектров"
    inputs = [SOCKET_TYPES['spectrum']]
    outputs = []
    GraphicsNode_class = VisualizationLineNode
    NodeContent_class = VisualNodeContentBuilder

    def __init__(self, scene, MP):
        super().__init__(scene, MP)

        self.editor = SpectrumChart()

        self.content.buildUI(widget=self.editor)

    def evalOperation(self, input_values):
        super().evalOperation(input_values)
        result = {'error': False, 'result': True}

        if not input_values:
            result = {'error': True, 'result': "Не переданы данные для отображения"}
            self.evalOperation_cplt(result)
            return True

        a = input_values[0]
        dtype = detect_data_type(a)

        if 'spectrum' in dtype:
            try:
                self.editor.plot(a)
                result = {'error': False, 'result': True}
            except Exception as e:
                self.close()
                result = {'error': True, 'result': str(e)}
        else:
            result = {'error': True, 'result': f"Не подходящий тип данных: {dtype}"}

        self.evalOperation_cplt(result)

        if result['error']:
            self.editor.plot(None)

        return True

    def close(self):
        self.remove()