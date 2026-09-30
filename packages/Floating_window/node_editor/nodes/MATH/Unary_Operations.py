import numpy as np

from packages.Floating_window.node_editor.nodes.node_import import *
from packages.Floating_window.NodeContentBuilder import NodeContentBuilder


class UnaryGraphicsNode(CalcGraphicsNode):
    def initSizes(self):
        super().initSizes()
        self.height = 145


class UnaryNode(CalcNode):
    icon = "Icon/image/unary.png"
    op_code = OP_NODE_UNARY
    op_title = "Унарные операции"
    inputs = [SOCKET_TYPES['any']]
    outputs = [SOCKET_TYPES['any']]
    GraphicsNode_class = UnaryGraphicsNode
    NodeContent_class = NodeContentBuilder

    def __init__(self, scene, MP):
        super().__init__(scene, MP)
        self.content.buildUI(node_functions=[
            {
                'name': 'Сумма',
                'params': [],
                'inputs': SOCKET_TYPES['any'],
                'outputs': SOCKET_TYPES['number']
            },
            {
                'name': 'Среднее',
                'params': [],
                'inputs': SOCKET_TYPES['any'],
                'outputs': SOCKET_TYPES['number']
            },
            {
                'name': 'Стд. отклонение',
                'params': [],
                'inputs': SOCKET_TYPES['any'],
                'outputs': SOCKET_TYPES['number']
            },
            {
                'name': 'Минимум',
                'params': [],
                'inputs': SOCKET_TYPES['any'],
                'outputs': SOCKET_TYPES['number']
            },
            {
                'name': 'Максимум',
                'params': [],
                'inputs': SOCKET_TYPES['any'],
                'outputs': SOCKET_TYPES['number']
            }
        ])
        self.MP = MP

    def evalOperation(self, input_values):
        super().evalOperation(input_values)
        if not input_values:
            return None

        a = input_values[0]
        op_name = self.content.get_func()

        if op_name == 'Сумма':
            self.MP.run_process(func=self.sum, args=(a,), callback=self.evalOperation_cplt)
        elif op_name == 'Среднее':
            self.MP.run_process(func=self.mean, args=(a,), callback=self.evalOperation_cplt)
        elif op_name == 'Стд. отклонение':
            self.MP.run_process(func=self.std, args=(a,), callback=self.evalOperation_cplt)
        elif op_name == 'Минимум':
            self.MP.run_process(func=self.min, args=(a,), callback=self.evalOperation_cplt)
        elif op_name == 'Максимум':
            self.MP.run_process(func=self.max, args=(a,), callback=self.evalOperation_cplt)

    @staticmethod
    def sum(a):
        return apply_to_1data(a, np.sum)

    @staticmethod
    def mean(a):
        return apply_to_1data(a, np.mean)

    @staticmethod
    def std(a):
        return apply_to_1data(a, np.std)

    @staticmethod
    def min(a):
        return apply_to_1data(a, np.min)

    @staticmethod
    def max(a):
        return apply_to_1data(a, np.max)
