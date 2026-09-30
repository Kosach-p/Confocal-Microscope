import numpy as np

from packages.Floating_window.node_editor.nodes.node_import import *
from packages.Floating_window.NodeContentBuilder import NodeContentBuilder


class SelectionGraphicsNode(CalcGraphicsNode):
    def initSizes(self):
        super().initSizes()
        self.height = 285


class MatrixCropNode(CalcNode):
    icon = "Icon/image/matrix_crop.png"
    op_code = OP_NODE_MATRIX_CROP
    op_title = "Обрезка матрицы"
    inputs = [SOCKET_TYPES['matrix_2d']]
    outputs = [SOCKET_TYPES['matrix_2d']]
    GraphicsNode_class = SelectionGraphicsNode
    NodeContent_class = NodeContentBuilder

    def __init__(self, scene, MP):
        super().__init__(scene, MP)
        self.content.buildUI(node_functions=[
            {
                'name': 'Обрезка матрицы',
                'params': [
                    {'name': 'Начало:',
                     'parameter_property': {'widget': 'QLabel'}},
                    {'name': 'X start',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'min': -1e9, 'max': 1e9, 'step': 1, 'decimal': 0, 'def': 0}},
                    {'name': 'Y start',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'min': -1e9, 'max': 1e9, 'step': 1, 'decimal': 0, 'def': 0}},
                    {'name': 'Z start',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'min': -1e9, 'max': 1e9, 'step': 1, 'decimal': 0, 'def': 0}},
                    {'name': 'Конец:',
                     'parameter_property': {'widget': 'QLabel'}},
                    {'name': 'X end',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'min': -1e9, 'max': 1e9, 'step': 1, 'decimal': 0, 'def': 100}},
                    {'name': 'Y end',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'min': -1e9, 'max': 1e9, 'step': 1, 'decimal': 0, 'def': 100}},
                    {'name': 'Z end',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'min': -1e9, 'max': 1e9, 'step': 1, 'decimal': 0, 'def': 100}},

                ],
                'inputs': SOCKET_TYPES['matrix_2d'],
                'outputs': SOCKET_TYPES['matrix_2d']
            }
        ])
        self.MP = MP

    def evalOperation(self, input_values):
        super().evalOperation(input_values)
        if not input_values:
            return None

        a = input_values[0]
        params = self.content.get_params()

        x_start = int(params.get('X start', 0))
        y_start = int(params.get('Y start', 0))
        z_start = int(params.get('Z start', 0))
        x_end = int(params.get('X end', 100))
        y_end = int(params.get('Y end', 100))
        z_end = int(params.get('Z end', 100))
        self.MP.run_process(
            func=self.crop_data,
            args=(a, x_start, y_start, z_start, x_end, y_end, z_end),
            callback=self.evalOperation_cplt
        )

    @staticmethod
    def crop_data(a, x_start=0, y_start=0, z_start=0, x_end=-1, y_end=-1, z_end=-1):
        dtype = detect_data_type(a)

        if dtype == "empty":
            return {'error': True, 'result': "Не переданы данные для обрезки"}

        def _norm_end(end, length):
            if end == -1 or end > length:
                return length
            return end

        if dtype == "matrix_2d":
            xe = _norm_end(x_end, a.shape[1])
            ye = _norm_end(y_end, a.shape[0])
            return {'error': False, 'result': a[y_start:ye, x_start:xe]}

        if dtype == "matrix_3d":
            xe = _norm_end(x_end, a.shape[2])
            ye = _norm_end(y_end, a.shape[1])
            ze = _norm_end(z_end, a.shape[0])
            return {'error': False, 'result': a[z_start:ze, y_start:ye, x_start:xe]}

        if dtype == "matrix_list_2d":
            return {'error': False,
                    'result': [MatrixCropNode.crop_data(m, x_start, y_start, z_start, x_end, y_end, z_end) for m in a]}

        return {'error': True, 'result': f"Неподдерживаемый тип данных: {dtype}"}
