from packages.Floating_window.node_editor.nodes.node_import import *
from packages.Floating_window.node_editor.nodes.VISUALIZATION.VisualNodeContentBuilder import VisualNodeContentBuilder
from packages.core.widgets.ImageViewLite import ImageView


class VisualizationLineNode(CalcGraphicsNode):
    def initSizes(self):
        super().initSizes()
        self.height = 400
        self.width = 400


class VisualizationLineNode(CalcNode):
    icon = "Icon/image/line.png"
    op_code = OP_NODE_IMAGEVIEW
    op_title = "Отображение матриц"
    inputs = [SOCKET_TYPES['any']]
    outputs = []
    GraphicsNode_class = VisualizationLineNode
    NodeContent_class = VisualNodeContentBuilder

    def __init__(self, scene, MP):
        super().__init__(scene, MP)

        self.editor = ImageView()

        self.content.buildUI(widget=self.editor)

    def evalOperation(self, input_values):
        super().evalOperation(input_values)
        result = {'error': False, 'result': True}
        a = input_values[0]
        type = detect_data_type(a)
        print("просят отобразить")
        print(type)
        if 'matrix' in type:
            try:
                self.editor.imshow(a)
                result = {'error': False, 'result': True}
            except Exception as e:
                self.close()
                result = {'error': True, 'result': e}
        else:
            result = {'error': True, 'result': f"Не подходящий тип данных: {type}"}

        self.evalOperation_cplt(result)

        if result['error']:
            self.editor.imshow(None)
        return True

    def close(self):
        self.remove()