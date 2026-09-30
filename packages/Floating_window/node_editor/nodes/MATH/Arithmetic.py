import numpy as np

from packages.Floating_window.node_editor.nodes.node_import import *
from packages.Floating_window.NodeContentBuilder import NodeContentBuilder


class ArithmeticGraphicsNode(CalcGraphicsNode):
    def initSizes(self):
        super().initSizes()
        self.height = 95


class ArithmeticNode(CalcNode):
    icon = "Icon/image/all.png"
    op_code = OP_NODE_ARITHMETIC
    op_title = "Арифметика"
    inputs = [SOCKET_TYPES['any'], SOCKET_TYPES['any']]
    outputs = [SOCKET_TYPES['any']]
    GraphicsNode_class = ArithmeticGraphicsNode
    NodeContent_class = NodeContentBuilder

    def __init__(self, scene, MP):
        super().__init__(scene, MP)
        self.content.buildUI(node_functions=[
            {
                'name': 'Сложение (+)',
                'params': [],
                'inputs': SOCKET_TYPES['any'],
                'outputs': SOCKET_TYPES['any']
            },
            {
                'name': 'Вычитание (-)',
                'params': [],
                'inputs': SOCKET_TYPES['any'],
                'outputs': SOCKET_TYPES['any']
            },
            {
                'name': 'Умножение (*)',
                'params': [],
                'inputs': SOCKET_TYPES['any'],
                'outputs': SOCKET_TYPES['any']
            },
            {
                'name': 'Деление (/)',
                'params': [],
                'inputs': SOCKET_TYPES['any'],
                'outputs': SOCKET_TYPES['any']
            }
        ])
        self.MP = MP

    def evalOperation(self, input_values):
        super().evalOperation(input_values)
        if not input_values or len(input_values) < 2:
            return None

        a, b = input_values[0], input_values[1]
        op_name = self.content.get_func()

        if op_name == 'Сложение (+)':
            self.MP.run_process(func=self.add, args=(a, b), callback=self.evalOperation_cplt)
        elif op_name == 'Вычитание (-)':
            self.MP.run_process(func=self.subtract, args=(a, b), callback=self.evalOperation_cplt)
        elif op_name == 'Умножение (*)':
            self.MP.run_process(func=self.multiply, args=(a, b), callback=self.evalOperation_cplt)
        elif op_name == 'Деление (/)':
            self.MP.run_process(func=self.divide, args=(a, b), callback=self.evalOperation_cplt)

    @staticmethod
    def add(a, b):
        return apply_to_2_data(a, b, lambda x, y: x + y)

    @staticmethod
    def subtract(a, b):
        return apply_to_2_data(a, b, lambda x, y: x - y)

    @staticmethod
    def multiply(a, b):
        return apply_to_2_data(a, b, lambda x, y: x * y)

    @staticmethod
    def divide(a, b):
        with np.errstate(divide='ignore', invalid='ignore'):
            return apply_to_2_data(a, b, lambda x, y: x / y)