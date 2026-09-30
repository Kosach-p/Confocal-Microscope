import numpy as np

from packages.Floating_window.node_editor.nodes.node_import import *
from packages.Floating_window.NodeContentBuilder import NodeContentBuilder


class AvgSimpleGraphicsNode(CalcGraphicsNode):
    def initSizes(self):
        super().initSizes()
        self.height = 115


class AvgSimpleNode(CalcNode):
    icon = "Icon/image/avg_simple.png"
    op_code = OP_NODE_AVG_SIMPLE
    op_title = "Простое усреднение"
    inputs = [SOCKET_TYPES['spectrum']]
    outputs = [SOCKET_TYPES['spectrum']]
    GraphicsNode_class = AvgSimpleGraphicsNode
    NodeContent_class = NodeContentBuilder

    def __init__(self, scene, MP):
        super().__init__(scene, MP)
        self.content.buildUI(node_functions=[
            {
                'name': 'Скользящее среднее',
                'params': [
                    {'name': 'Окно',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 1, 'decimal': 0, 'min': 1,
                                            'max': 1e9, 'def': 5}}
                ],
                'inputs': SOCKET_TYPES['spectrum'],
                'outputs': SOCKET_TYPES['spectrum']
            },
            {
                'name': 'Кумулятивное среднее',
                'params': [],
                'inputs': SOCKET_TYPES['spectrum'],
                'outputs': SOCKET_TYPES['spectrum']
            },
            {
                'name': 'Блочное среднее',
                'params': [
                    {'name': 'Размер блока',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 1, 'decimal': 0, 'min': 1,
                                            'max': 1e9, 'def': 10}}
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

        if op_name == 'Скользящее среднее':
            window = int(params.get('Окно', 5))
            self.MP.run_process(func=self.running_mean, args=(a, window), callback=self.evalOperation_cplt)
        elif op_name == 'Кумулятивное среднее':
            self.MP.run_process(func=self.cumulative_mean, args=(a,), callback=self.evalOperation_cplt)
        elif op_name == 'Блочное среднее':
            block = int(params.get('Размер блока', 10))
            self.MP.run_process(func=self.block_mean, args=(a, block), callback=self.evalOperation_cplt)

    @staticmethod
    def running_mean(a, window=5):
        def _proc(y):
            y = np.array(y, dtype=float)
            result = np.zeros_like(y)
            half = window // 2
            for i in range(len(y)):
                start = max(0, i - half)
                end = min(len(y), i + half + 1)
                result[i] = np.mean(y[start:end])
            return result

        return apply_to_1data(a, _proc)

    @staticmethod
    def cumulative_mean(a):
        def _proc(y):
            return np.cumsum(y) / np.arange(1, len(y) + 1)

        return apply_to_1data(a, _proc)

    @staticmethod
    def block_mean(a, block=10):
        def _proc(y):
            n = len(y) // block
            result = np.zeros(len(y))
            for i in range(n):
                result[i * block:(i + 1) * block] = np.mean(y[i * block:(i + 1) * block])
            if len(y) % block != 0:
                result[n * block:] = np.mean(y[n * block:])
            return result

        return apply_to_1data(a, _proc)