import numpy as np

from packages.Floating_window.node_editor.nodes.node_import import *
from packages.Floating_window.NodeContentBuilder import NodeContentBuilder


class ProductsGraphicsNode(CalcGraphicsNode):
    def initSizes(self):
        super().initSizes()
        self.height = 145


class ProductsNode(CalcNode):
    icon = "Icon/image/products.png"
    op_code = OP_NODE_PRODUCTS
    op_title = "Произведения"
    inputs = [SOCKET_TYPES['any'], SOCKET_TYPES['any']]
    outputs = [SOCKET_TYPES['any']]
    GraphicsNode_class = ProductsGraphicsNode
    NodeContent_class = NodeContentBuilder

    def __init__(self, scene, MP):
        super().__init__(scene, MP)
        self.content.buildUI(node_functions=[
            {
                'name': 'Скалярное (dot)',
                'params': [],
                'inputs': SOCKET_TYPES['number_list'],
                'outputs': SOCKET_TYPES['number']
            },
            {
                'name': 'Внешнее (outer)',
                'params': [],
                'inputs': SOCKET_TYPES['number_list'],
                'outputs': SOCKET_TYPES['matrix_2d']
            },
            {
                'name': 'Матричное (matmul)',
                'params': [],
                'inputs': SOCKET_TYPES['matrix_2d'],
                'outputs': SOCKET_TYPES['matrix_2d']
            }
        ])
        self.MP = MP

    def evalOperation(self, input_values):
        super().evalOperation(input_values)
        if not input_values or len(input_values) < 2:
            return None

        a, b = input_values[0], input_values[1]
        op_name = self.content.get_func()

        if op_name == 'Скалярное (dot)':
            self.MP.run_process(func=self.dot, args=(a, b), callback=self.evalOperation_cplt)
        elif op_name == 'Внешнее (outer)':
            self.MP.run_process(func=self.outer, args=(a, b), callback=self.evalOperation_cplt)
        elif op_name == 'Матричное (matmul)':
            self.MP.run_process(func=self.matmul, args=(a, b), callback=self.evalOperation_cplt)

    @staticmethod
    def dot(a, b):
        dtype_a = detect_data_type(a)
        dtype_b = detect_data_type(b)

        if dtype_a == "empty" or dtype_b == "empty":
            return {'error': True, 'result': "Не переданы данные для расчёта"}

        if dtype_a == "spectrum" and dtype_b == "spectrum":
            _, y1 = a
            _, y2 = b
            return {'error': False, 'result': np.dot(y1, y2)}

        if dtype_a == "spectrum_list" and dtype_b == "spectrum_list":
            if len(a) != len(b):
                return {'error': True, 'result': f"Разная длина списков: {len(a)} vs {len(b)}"}
            return {'error': False, 'result': [np.dot(y1, y2) for (_, y1), (_, y2) in zip(a, b)]}

        return apply_to_2_data(a, b, lambda x, y: np.dot(x, y))

    @staticmethod
    def outer(a, b):
        dtype_a = detect_data_type(a)
        dtype_b = detect_data_type(b)

        if dtype_a == "empty" or dtype_b == "empty":
            return {'error': True, 'result': "Не переданы данные для расчёта"}

        if dtype_a == "spectrum" and dtype_b == "spectrum":
            _, y1 = a
            _, y2 = b
            return {'error': False, 'result': np.outer(y1, y2)}

        if dtype_a == "number_list" and dtype_b == "number_list":
            return {'error': False, 'result': np.outer(np.array(a), np.array(b))}

        return apply_to_2_data(a, b, lambda x, y: np.outer(x, y))

    @staticmethod
    def matmul(a, b):
        dtype_a = detect_data_type(a)
        dtype_b = detect_data_type(b)

        if dtype_a == "empty" or dtype_b == "empty":
            return {'error': True, 'result': "Не переданы данные для расчёта"}

        if dtype_a == "matrix_2d" and dtype_b == "matrix_2d":
            return {'error': False, 'result': np.matmul(a, b)}

        if dtype_a == "matrix_list_2d" and dtype_b == "matrix_2d":
            return {'error': False, 'result': [np.matmul(m, b) for m in a]}

        if dtype_a == "matrix_2d" and dtype_b == "matrix_list_2d":
            return {'error': False, 'result': [np.matmul(a, m) for m in b]}

        if dtype_a == "matrix_list_2d" and dtype_b == "matrix_list_2d":
            if len(a) != len(b):
                return {'error': True, 'result': f"Разная длина списков: {len(a)} vs {len(b)}"}
            return {'error': False, 'result': [np.matmul(m1, m2) for m1, m2 in zip(a, b)]}

        return {'error': True, 'result': f"Неподдерживаемая пара типов: {dtype_a} + {dtype_b}"}