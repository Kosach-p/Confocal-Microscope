import numpy as np
from scipy.signal import hilbert, detrend, savgol_filter

from packages.Floating_window.node_editor.nodes.node_import import *
from packages.Floating_window.NodeContentBuilder import NodeContentBuilder


class SignalGraphicsNode(CalcGraphicsNode):
    def initSizes(self):
        super().initSizes()
        self.height = 145


class SignalNode(CalcNode):
    icon = "Icon/image/signal.png"
    op_code = OP_NODE_SIGNAL
    op_title = "Обработка сигнала"
    inputs = [SOCKET_TYPES['spectrum']]
    outputs = [SOCKET_TYPES['spectrum']]
    GraphicsNode_class = SignalGraphicsNode
    NodeContent_class = NodeContentBuilder

    def __init__(self, scene, MP):
        super().__init__(scene, MP)
        self.content.buildUI(node_functions=[
            {
                'name': 'Базовая линия',
                'params': [
                    {'name': 'Порядок',
                     'parameter_property': {'widget': 'DragNumberInput', 'step': 1, 'decimal': 0, 'min': 0,
                                            'max': 32, 'def': 3}}
                ],
                'inputs': SOCKET_TYPES['spectrum'],
                'outputs': SOCKET_TYPES['spectrum']
            },
            {
                'name': 'Удаление тренда',
                'params': [
                    {'name': 'Порядок',
                     'parameter_property': {'widget': 'DragNumberInput', 'step': 1, 'decimal': 0, 'min': 0, 'max': 32,
                                            'def': 1}}
                ],
                'inputs': SOCKET_TYPES['any'],
                'outputs': SOCKET_TYPES['any']
            },
            {
                'name': 'Огибающая',
                'params': [],
                'inputs': SOCKET_TYPES['spectrum'],
                'outputs': SOCKET_TYPES['spectrum']
            },
            {
                'name': 'Интегрирование',
                'params': [],
                'inputs': SOCKET_TYPES['spectrum'],
                'outputs': SOCKET_TYPES['spectrum']
            },
            {
                'name': 'Дифференцирование',
                'params': [],
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

        if op_name == 'Базовая линия':
            order = int(self.content.get_params().get('Порядок', 3))
            self.MP.run_process(func=self.baseline, args=(a, order), callback=self.evalOperation_cplt)
        elif op_name == 'Удаление тренда':
            order = int(self.content.get_params().get('Порядок', 1))
            self.MP.run_process(func=self.detrend_data, args=(a, order), callback=self.evalOperation_cplt)
        elif op_name == 'Огибающая':
            self.MP.run_process(func=self.envelope, args=(a,), callback=self.evalOperation_cplt)
        elif op_name == 'Интегрирование':
            self.MP.run_process(func=self.integrate, args=(a,), callback=self.evalOperation_cplt)
        elif op_name == 'Дифференцирование':
            self.MP.run_process(func=self.differentiate, args=(a,), callback=self.evalOperation_cplt)

    @staticmethod
    def baseline(a, order=3):
        def _proc(y):
            from scipy.interpolate import UnivariateSpline
            from scipy.signal import argrelextrema
            x = np.arange(len(y))
            minima_idx = argrelextrema(y, np.less)[0]
            if len(minima_idx) < order + 1:
                coeffs = np.polyfit(x, y, order)
                baseline = np.polyval(coeffs, x)
            else:
                spline = UnivariateSpline(minima_idx, y[minima_idx], k=min(order, 3))
                baseline = spline(x)
            return y - baseline

        dtype = detect_data_type(a)
        if dtype == "empty":
            return {'error': True, 'result': "Не переданы данные для расчёта"}
        if dtype == "spectrum":
            x, y = a
            return {'error': False, 'result': [x, _proc(y)]}
        if dtype == "spectrum_list":
            return {'error': False, 'result': [[x, _proc(y)] for x, y in a]}
        if dtype == "number_list":
            return {'error': False, 'result': _proc(np.array(a)).tolist()}
        return {'error': True, 'result': f"Неподдерживаемый тип данных: {dtype}"}

    @staticmethod
    def detrend_data(a, order=1):
        def _proc(y):
            x = np.arange(len(y))
            coeffs = np.polyfit(x, y, order)
            trend = np.polyval(coeffs, x)
            return y - trend

        return apply_to_1data(a, _proc)

    @staticmethod
    def envelope(a):
        def _proc(y):
            analytic = hilbert(y)
            return np.abs(analytic)

        return apply_to_1data(a, _proc)

    @staticmethod
    def integrate(a):
        def _proc(y):
            return np.cumsum(y) - y[0]

        return apply_to_1data(a, _proc)

    @staticmethod
    def differentiate(a):
        def _proc(y):
            return np.gradient(y)

        return apply_to_1data(a, _proc)