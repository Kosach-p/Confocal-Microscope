import numpy as np

from packages.Floating_window.node_editor.nodes.node_import import *
from packages.Floating_window.NodeContentBuilder import NodeContentBuilder


class NormalizeGraphicsNode(CalcGraphicsNode):
    def initSizes(self):
        super().initSizes()
        self.height = 145


class NormalizeNode(CalcNode):
    icon = "Icon/image/normalize.png"
    op_code = OP_NODE_NORMALIZE
    op_title = "Нормализация"
    inputs = [SOCKET_TYPES['any']]
    outputs = [SOCKET_TYPES['any']]
    GraphicsNode_class = NormalizeGraphicsNode
    NodeContent_class = NodeContentBuilder

    def __init__(self, scene, MP):
        super().__init__(scene, MP)
        self.content.buildUI(node_functions=[
            {
                'name': 'Min-Max',
                'params': [
                    {'name': 'Минимум',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 0.1, 'decimal': 1,
                                            'def': 0.0}},
                    {'name': 'Максимум',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 0.1, 'decimal': 1,
                                            'def': 1.0}}
                ],
                'inputs': SOCKET_TYPES['any'],
                'outputs': SOCKET_TYPES['any']
            },
            {
                'name': 'Z-Score',
                'params': [],
                'inputs': SOCKET_TYPES['any'],
                'outputs': SOCKET_TYPES['any']
            },
            {
                'name': 'По площади',
                'params': [],
                'inputs': SOCKET_TYPES['any'],
                'outputs': SOCKET_TYPES['any']
            },
            {
                'name': 'По пику',
                'params': [],
                'inputs': SOCKET_TYPES['any'],
                'outputs': SOCKET_TYPES['any']
            },
            {
                'name': 'Blackbody',
                'params': [
                    {'name': 'Температура',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 100, 'decimal': 0,
                                            'def': 5000}}
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

        if op_name == 'Min-Max':
            min_val = params.get('Минимум', 0.0)
            max_val = params.get('Максимум', 1.0)
            self.MP.run_process(func=self.minmax, args=(a, min_val, max_val), callback=self.evalOperation_cplt)
        elif op_name == 'Z-Score':
            self.MP.run_process(func=self.zscore, args=(a,), callback=self.evalOperation_cplt)
        elif op_name == 'По площади':
            self.MP.run_process(func=self.area, args=(a,), callback=self.evalOperation_cplt)
        elif op_name == 'По пику':
            self.MP.run_process(func=self.peak, args=(a,), callback=self.evalOperation_cplt)
        elif op_name == 'Blackbody':
            temperature = params.get('Температура', 5000)
            self.MP.run_process(func=self.blackbody, args=(a, temperature), callback=self.evalOperation_cplt)

    @staticmethod
    def minmax(a, min_val=0.0, max_val=1.0):
        def _norm(x):
            x_min = np.min(x)
            x_max = np.max(x)
            if x_max - x_min == 0:
                return np.full_like(x, (min_val + max_val) / 2)
            return (x - x_min) / (x_max - x_min) * (max_val - min_val) + min_val

        return apply_to_1data(a, _norm)

    @staticmethod
    def zscore(a):
        def _norm(x):
            x_mean = np.mean(x)
            x_std = np.std(x)
            if x_std == 0:
                return np.zeros_like(x)
            return (x - x_mean) / x_std

        return apply_to_1data(a, _norm)

    @staticmethod
    def area(a):
        def _norm(x):
            area = np.sum(np.abs(x))
            if area == 0:
                return x
            return x / area

        return apply_to_1data(a, _norm)

    @staticmethod
    def peak(a):
        def _norm(x):
            peak = np.max(np.abs(x))
            if peak == 0:
                return x
            return x / peak

        return apply_to_1data(a, _norm)

    @staticmethod
    def blackbody(a, temperature=5000):
        dtype = detect_data_type(a)

        if dtype == "empty":
            return {'error': True, 'result': "Не переданы данные для расчёта"}

        if dtype == "spectrum":
            x, y = a
            wl = np.asarray(x)
            h = 6.626e-34
            c = 3.0e8
            k = 1.38e-23
            wl_m = wl * 1e-9
            planck = (2 * h * c ** 2) / (wl_m ** 5) / (np.exp(h * c / (wl_m * k * temperature)) - 1)
            planck = planck / np.max(planck)
            return {'error': False, 'result': [x, y / planck]}

        if dtype == "spectrum_list":
            return {'error': False, 'result': [NormalizeNode.blackbody(s, temperature) for s in a]}

        return {'error': True, 'result': f"Неподдерживаемый тип данных: {dtype}"}