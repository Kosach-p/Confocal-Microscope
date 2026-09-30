import numpy as np

from packages.Floating_window.node_editor.nodes.node_import import *
from packages.Floating_window.NodeContentBuilder import NodeContentBuilder


class GeometricGraphicsNode(CalcGraphicsNode):
    def initSizes(self):
        super().initSizes()
        self.height = 145


class GeometricNode(CalcNode):
    icon = "Icon/image/geometric.png"
    op_code = OP_NODE_GEOMETRIC
    op_title = "Геометрические операции"
    inputs = [SOCKET_TYPES['matrix_2d']]
    outputs = [SOCKET_TYPES['matrix_2d']]
    GraphicsNode_class = GeometricGraphicsNode
    NodeContent_class = NodeContentBuilder

    def __init__(self, scene, MP):
        super().__init__(scene, MP)
        self.content.buildUI(node_functions=[
            {
                'name': 'Транспонировать',
                'params': [],
                'inputs': SOCKET_TYPES['matrix_2d'],
                'outputs': SOCKET_TYPES['matrix_2d']
            },
            {
                'name': 'Отразить H',
                'params': [],
                'inputs': SOCKET_TYPES['matrix_2d'],
                'outputs': SOCKET_TYPES['matrix_2d']
            },
            {
                'name': 'Отразить V',
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

        if op_name == 'Транспонировать':
            self.MP.run_process(func=self.transpose, args=(a,), callback=self.evalOperation_cplt)
        elif op_name == 'Отразить H':
            self.MP.run_process(func=self.flip_h, args=(a,), callback=self.evalOperation_cplt)
        elif op_name == 'Отразить V':
            self.MP.run_process(func=self.flip_v, args=(a,), callback=self.evalOperation_cplt)

    @staticmethod
    def transpose(a):
        dtype = detect_data_type(a)
        if dtype == "empty":
            return {'error': True, 'result': "Не переданы данные для расчёта"}
        if dtype == "matrix_2d":
            return {'error': False, 'result': a.T}
        if dtype == "matrix_list_2d":
            return {'error': False, 'result': [m.T for m in a]}
        return {'error': True, 'result': f"Неподдерживаемый тип данных: {dtype}"}

    @staticmethod
    def flip_h(a):
        dtype = detect_data_type(a)
        if dtype == "empty":
            return {'error': True, 'result': "Не переданы данные для расчёта"}
        if dtype == "matrix_2d":
            return {'error': False, 'result': np.fliplr(a)}
        if dtype == "matrix_list_2d":
            return {'error': False, 'result': [np.fliplr(m) for m in a]}
        return {'error': True, 'result': f"Неподдерживаемый тип данных: {dtype}"}

    @staticmethod
    def flip_v(a):
        dtype = detect_data_type(a)
        if dtype == "empty":
            return {'error': True, 'result': "Не переданы данные для расчёта"}
        if dtype == "matrix_2d":
            return {'error': False, 'result': np.flipud(a)}
        if dtype == "matrix_list_2d":
            return {'error': False, 'result': [np.flipud(m) for m in a]}
        return {'error': True, 'result': f"Неподдерживаемый тип данных: {dtype}"}