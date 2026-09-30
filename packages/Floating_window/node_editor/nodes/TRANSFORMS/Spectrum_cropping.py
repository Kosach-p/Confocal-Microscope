import numpy as np

from packages.Floating_window.node_editor.nodes.node_import import *
from packages.Floating_window.NodeContentBuilder import NodeContentBuilder


class SelectionGraphicsNode(CalcGraphicsNode):
    def initSizes(self):
        super().initSizes()
        self.height = 115


class SpectrumCropNode(CalcNode):
    icon = "Icon/image/spectrum_crop.png"
    op_code = OP_NODE_SPECTRUM_CROP
    op_title = "Обрезка спектра"
    inputs = [SOCKET_TYPES['spectrum']]
    outputs = [SOCKET_TYPES['spectrum']]
    GraphicsNode_class = SelectionGraphicsNode
    NodeContent_class = NodeContentBuilder

    def __init__(self, scene, MP):
        super().__init__(scene, MP)
        self.content.buildUI(node_functions=[
            {
                'name': 'Обрезка по X',
                'params': [
                    {'name': 'X start',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 0.1, 'decimal': 2, 'min': -1e9,
                                            'max': 1e9, 'def': 0.0}},
                    {'name': 'X end',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 0.1, 'decimal': 2, 'min': -1e9,
                                            'max': 1e9, 'def': 100.0}}
                ],
                'inputs': SOCKET_TYPES['spectrum'],
                'outputs': SOCKET_TYPES['spectrum']
            }
        ])
        self.MP = MP

    def evalOperation(self, input_values):
        super().evalOperation(input_values)
        if not input_values:
            return None

        a = input_values[0]
        op_name = self.content.get_func()
        params = self.content.get_params()

        if op_name == 'Обрезка по X':
            x_min = float(params.get('X start', 0.0))
            x_max = float(params.get('X end', 100.0))
            self.MP.run_process(func=self.crop_spectrum, args=(a, x_min, x_max), callback=self.evalOperation_cplt)

    @staticmethod
    def crop_spectrum(a, x_min=0.0, x_max=100.0):
        dtype = detect_data_type(a)

        if dtype == "empty":
            return {'error': True, 'result': "Не переданы данные для обрезки"}

        if dtype == "spectrum":
            x, y = a
            x = np.array(x)
            y = np.array(y)
            mask = (x >= x_min) & (x <= x_max)
            return {'error': False, 'result': [x[mask], y[mask]]}

        if dtype == "spectrum_list":
            return {'error': False, 'result': [SpectrumCropNode.crop_spectrum(s, x_min, x_max) for s in a]}

        return {'error': True, 'result': f"Неподдерживаемый тип данных: {dtype}"}