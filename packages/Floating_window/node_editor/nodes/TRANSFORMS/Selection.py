import numpy as np

from packages.Floating_window.node_editor.nodes.node_import import *
from packages.Floating_window.NodeContentBuilder import NodeContentBuilder


class SelectionGraphicsNode(CalcGraphicsNode):
    def initSizes(self):
        super().initSizes()
        self.height = 145


class SelectionNode(CalcNode):
    icon = "Icon/image/selection.png"
    op_code = OP_NODE_SELECTION
    op_title = "Выделение"
    inputs = [SOCKET_TYPES['any']]
    outputs = [SOCKET_TYPES['any']]
    GraphicsNode_class = SelectionGraphicsNode
    NodeContent_class = NodeContentBuilder

    def __init__(self, scene, MP):
        super().__init__(scene, MP)
        self.content.buildUI(node_functions=[
            {
                'name': 'Индекс',
                'params': [
                    {'name': 'Индекс',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 1, 'decimal': 0, 'def': 0}}
                ],
                'inputs': SOCKET_TYPES['any'],
                'outputs': SOCKET_TYPES['any']
            },
            {
                'name': 'Фильтр по значению',
                'params': [
                    {'name': 'min',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 0.1, 'decimal': 2, 'min': -2147483648,
                                            'max': 2147483647, 'def': 0.0}},
                    {'name': 'max',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 0.1, 'decimal': 2, 'min': -2147483648,
                                            'max': 2147483647, 'def': 100.0}}
                ],
                'inputs': SOCKET_TYPES['any'],
                'outputs': SOCKET_TYPES['any']
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

        if op_name == 'Индекс':
            idx = int(params.get('Индекс', 0))
            self.MP.run_process(func=self.index_data, args=(a, idx), callback=self.evalOperation_cplt)
        elif op_name == 'Фильтр по значению':
            min_val = float(params.get('min', 0.0))
            max_val = float(params.get('max', 100.0))
            self.MP.run_process(func=self.filter_by_value, args=(a, min_val, max_val), callback=self.evalOperation_cplt)

    @staticmethod
    def index_data(a, idx=0):
        dtype = detect_data_type(a)
        if dtype == "empty":
            return {'error': True, 'result': "Не переданы данные для расчёта"}

        if dtype == "spectrum":
            x, y = a
            return {'error': False, 'result': [x[idx], y[idx]]}

        if dtype == "spectrum_list":
            return {'error': False, 'result': a[idx]}

        if dtype == "number_list":
            return {'error': False, 'result': a[idx]}

        if dtype == "matrix_2d":
            return {'error': False, 'result': a[idx, :]}

        if dtype == "matrix_3d":
            print(a[idx, :, :])
            return {'error': False, 'result': a[idx, :, :]}

        if dtype == "matrix_list_2d":
            return {'error': False, 'result': a[idx]}

        return {'error': True, 'result': f"Неподдерживаемый тип данных: {dtype}"}

    @staticmethod
    def filter_by_value(a, min_val=0.0, max_val=100.0):
        dtype = detect_data_type(a)

        if dtype == "empty":
            return {'error': True, 'result': "Не переданы данные для расчёта"}

        if dtype == "spectrum":
            x, y = a
            y = np.array(y)
            mask = (y >= min_val) & (y <= max_val)
            return {'error': False, 'result': [np.array(x)[mask], y[mask]]}

        if dtype == "spectrum_list":
            return {'error': False, 'result': [SelectionNode.filter_by_value(s, min_val, max_val) for s in a]}

        if dtype == "number_list":
            return {'error': False, 'result': [v for v in a if min_val <= v <= max_val]}

        if dtype == "matrix_2d":
            mask = (a >= min_val) & (a <= max_val)
            result = a.copy()
            result[~mask] = np.nan
            return {'error': False, 'result': result}

        if dtype == "matrix_3d":
            mask = (a >= min_val) & (a <= max_val)
            result = a.copy()
            result[~mask] = np.nan
            return {'error': False, 'result': result}

        if dtype == "matrix_list_2d":
            return {'error': False, 'result': [SelectionNode.filter_by_value(m, min_val, max_val) for m in a]}

        return {'error': True, 'result': f"Неподдерживаемый тип данных: {dtype}"}