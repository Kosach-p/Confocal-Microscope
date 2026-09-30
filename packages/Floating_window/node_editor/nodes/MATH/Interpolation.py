import numpy as np
from scipy.interpolate import interp1d
from scipy.signal import resample

from packages.Floating_window.node_editor.nodes.node_import import *
from packages.Floating_window.NodeContentBuilder import NodeContentBuilder


class InterpolationGraphicsNode(CalcGraphicsNode):
    def initSizes(self):
        super().initSizes()
        self.height = 145


class InterpolationNode(CalcNode):
    icon = "Icon/image/interpolation.png"
    op_code = OP_NODE_INTERPOLATION
    op_title = "Интерполяция"
    inputs = [SOCKET_TYPES['any']]
    outputs = [SOCKET_TYPES['any']]
    GraphicsNode_class = InterpolationGraphicsNode
    NodeContent_class = NodeContentBuilder

    def __init__(self, scene, MP):
        super().__init__(scene, MP)
        self.content.buildUI(node_functions=[
            {
                'name': 'Линейная',
                'params': [
                    {'name': 'Точек',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 100, 'decimal': 0,
                                            'def': 1000}}
                ],
                'inputs': SOCKET_TYPES['spectrum'],
                'outputs': SOCKET_TYPES['spectrum']
            },
            {
                'name': 'Кубическая',
                'params': [
                    {'name': 'Точек',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 100, 'decimal': 0,
                                            'def': 1000}}
                ],
                'inputs': SOCKET_TYPES['spectrum'],
                'outputs': SOCKET_TYPES['spectrum']
            },
            {
                'name': 'Передискретизация',
                'params': [
                    {'name': 'Точек',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 100, 'decimal': 0,
                                            'def': 1000}}
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
        n_points = int(params.get('Точек', 1000))

        if op_name == 'Линейная':
            self.MP.run_process(func=self.linear, args=(a, n_points), callback=self.evalOperation_cplt)
        elif op_name == 'Кубическая':
            self.MP.run_process(func=self.cubic, args=(a, n_points), callback=self.evalOperation_cplt)
        elif op_name == 'Передискретизация':
            self.MP.run_process(func=self.resample_data, args=(a, n_points), callback=self.evalOperation_cplt)

    @staticmethod
    def linear(a, n_points=1000):
        def _interp_1d(y):
            x_old = np.linspace(0, 1, len(y))
            x_new = np.linspace(0, 1, n_points)
            return interp1d(x_old, y, kind='linear')(x_new)

        dtype = detect_data_type(a)

        if dtype == "empty":
            return {'error': True, 'result': "Не переданы данные для расчёта"}

        if dtype == "spectrum":
            x, y = a
            x_new = np.linspace(x[0], x[-1], n_points)
            y_new = interp1d(x, y, kind='linear')(x_new)
            return {'error': False, 'result': [x_new, y_new]}

        if dtype == "spectrum_list":
            return {'error': False, 'result': [InterpolationNode.linear(s, n_points) for s in a]}

        return apply_to_1data(a, _interp_1d)

    @staticmethod
    def cubic(a, n_points=1000):
        def _interp_1d(y):
            x_old = np.linspace(0, 1, len(y))
            x_new = np.linspace(0, 1, n_points)
            return interp1d(x_old, y, kind='cubic')(x_new)

        dtype = detect_data_type(a)

        if dtype == "empty":
            return {'error': True, 'result': "Не переданы данные для расчёта"}

        if dtype == "spectrum":
            x, y = a
            x_new = np.linspace(x[0], x[-1], n_points)
            y_new = interp1d(x, y, kind='cubic')(x_new)
            return {'error': False, 'result': [x_new, y_new]}

        if dtype == "spectrum_list":
            return {'error': False, 'result': [InterpolationNode.cubic(s, n_points) for s in a]}

        return apply_to_1data(a, _interp_1d)

    @staticmethod
    def resample_data(a, n_points=1000):
        def _resample_1d(y):
            return resample(y, n_points)

        dtype = detect_data_type(a)

        if dtype == "empty":
            return {'error': True, 'result': "Не переданы данные для расчёта"}

        if dtype == "spectrum":
            x, y = a
            y_new = resample(y, n_points)
            x_new = np.linspace(x[0], x[-1], n_points)
            return {'error': False, 'result': [x_new, y_new]}

        if dtype == "spectrum_list":
            return {'error': False, 'result': [InterpolationNode.resample_data(s, n_points) for s in a]}

        return apply_to_1data(a, _resample_1d)