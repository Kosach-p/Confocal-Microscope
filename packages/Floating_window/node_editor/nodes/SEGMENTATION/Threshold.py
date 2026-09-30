import numpy as np
from skimage import filters

from packages.Floating_window.node_editor.nodes.node_import import *
from packages.Floating_window.NodeContentBuilder import NodeContentBuilder


class ThresholdGraphicsNode(CalcGraphicsNode):
    def initSizes(self):
        super().initSizes()
        self.height = 145


class ThresholdNode(CalcNode):
    icon = "Icon/image/threshold.png"
    op_code = OP_NODE_THRESHOLD
    op_title = "Пороговая обработка"
    inputs = [SOCKET_TYPES['matrix_2d']]
    outputs = [SOCKET_TYPES['matrix_2d']]
    GraphicsNode_class = ThresholdGraphicsNode
    NodeContent_class = NodeContentBuilder

    def __init__(self, scene, MP):
        super().__init__(scene, MP)
        self.content.buildUI(node_functions=[
            {
                'name': 'Глобальный порог',
                'params': [
                    {'name': 'Порог',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 0.1, 'decimal': 1,
                                            'def': 0.5}}
                ],
                'inputs': SOCKET_TYPES['matrix_2d'],
                'outputs': SOCKET_TYPES['matrix_2d']
            },
            {
                'name': 'Адаптивный порог',
                'params': [
                    {'name': 'Размер блока',
                     'parameter_property': {'widget': 'DragNumberInput', 'step': 2, 'decimal': 0, 'min': 3,
                                            'max': 51, 'def': 15}}
                ],
                'inputs': SOCKET_TYPES['matrix_2d'],
                'outputs': SOCKET_TYPES['matrix_2d']
            },
            {
                'name': 'Otsu',
                'params': [],
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
        op_name = self.content.get_func()
        params = self.content.get_params()

        if op_name == 'Глобальный порог':
            thresh = params.get('Порог', 0.5)
            self.MP.run_process(func=self.global_threshold, args=(a, thresh), callback=self.evalOperation_cplt)
        elif op_name == 'Адаптивный порог':
            block = int(params.get('Размер блока', 15))
            self.MP.run_process(func=self.adaptive_threshold, args=(a, block), callback=self.evalOperation_cplt)
        elif op_name == 'Otsu':
            self.MP.run_process(func=self.otsu, args=(a,), callback=self.evalOperation_cplt)

    @staticmethod
    def global_threshold(a, thresh=0.5):
        def _proc(x):
            return (x > thresh).astype(float)

        return apply_to_1data(a, _proc)

    @staticmethod
    def adaptive_threshold(a, block=15):
        def _proc(x):
            from skimage.filters import threshold_local
            thresh = threshold_local(x, block_size=block)
            return (x > thresh).astype(float)

        return apply_to_1data(a, _proc)

    @staticmethod
    def otsu(a):
        def _proc(x):
            thresh = filters.threshold_otsu(x)
            return (x > thresh).astype(float)

        return apply_to_1data(a, _proc)