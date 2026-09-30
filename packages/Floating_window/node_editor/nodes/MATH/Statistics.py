import numpy as np
from scipy import stats

from packages.Floating_window.node_editor.nodes.node_import import *
from packages.Floating_window.NodeContentBuilder import NodeContentBuilder


class StatisticsGraphicsNode(CalcGraphicsNode):
    def initSizes(self):
        super().initSizes()
        self.height = 145


class StatisticsNode(CalcNode):
    icon = "Icon/image/statistics.png"
    op_code = OP_NODE_STATISTICS
    op_title = "Статистика"
    inputs = [SOCKET_TYPES['any']]
    outputs = [SOCKET_TYPES['any']]
    GraphicsNode_class = StatisticsGraphicsNode
    NodeContent_class = NodeContentBuilder

    def __init__(self, scene, MP):
        super().__init__(scene, MP)
        self.MP = MP

        self.content.buildUI(node_functions=[
            {
                'name': 'Гистограмма',
                'params': [
                    {'name': 'Бинов',
                     'parameter_property': {'widget': 'DragNumberInput', 'step': 10, 'decimal': 0, 'min': 5,
                                            'max': 500, 'def': 50}}
                ],
                'inputs': SOCKET_TYPES['any'],
                'outputs': SOCKET_TYPES['spectrum']
            },
            {
                'name': 'Процентили',
                'params': [
                    {'name': 'Процентиль',
                     'parameter_property': {'widget': 'DragNumberInput', 'step': 5, 'decimal': 0, 'min': 0,
                                            'max': 100, 'def': 95}}
                ],
                'inputs': SOCKET_TYPES['any'],
                'outputs': SOCKET_TYPES['number']
            },
            {
                'name': 'Корреляция',
                'params': [],
                'inputs': SOCKET_TYPES['matrix_2d'],
                'outputs': SOCKET_TYPES['matrix_2d']
            },
            {
                'name': 'Выбросы',
                'params': [
                    {'name': 'Z-порог',
                     'parameter_property': {'widget': 'DragNumberInput', 'step': 0.5, 'decimal': 1, 'min': 0.5,
                                            'max': 10.0, 'def': 3.0}}
                ],
                'inputs': SOCKET_TYPES['any'],
                'outputs': SOCKET_TYPES['any']
            }
        ])

    def evalOperation(self, input_values):
        super().evalOperation(input_values)
        if not input_values:
            return None

        a = input_values[0]
        op_name = self.content.get_func()
        params = self.content.get_params()

        if op_name == 'Гистограмма':
            bins = int(params.get('Бинов', 50))
            self.MP.run_process(func=self.histogram, args=(a, bins), callback=self.evalOperation_cplt)
        elif op_name == 'Процентили':
            percentile = int(params.get('Процентиль', 95))
            self.MP.run_process(func=self.percentile, args=(a, percentile), callback=self.evalOperation_cplt)
        elif op_name == 'Корреляция':
            self.MP.run_process(func=self.correlation, args=(a,), callback=self.evalOperation_cplt)
        elif op_name == 'Выбросы':
            z_thresh = params.get('Z-порог', 3.0)
            self.MP.run_process(func=self.outliers, args=(a, z_thresh), callback=self.evalOperation_cplt)

    @staticmethod
    def histogram(a, bins=50):
        dtype = detect_data_type(a)

        if dtype == "empty":
            return {'error': True, 'result': "Не переданы данные для расчёта"}

        if dtype == "spectrum":
            x, y = a
            hist, edges = np.histogram(y, bins=bins)
            centers = (edges[:-1] + edges[1:]) / 2
            return {'error': False, 'result': [centers, hist]}

        if dtype == "spectrum_list":
            return {'error': False, 'result': [StatisticsNode.histogram(s, bins) for s in a]}

        if dtype == "matrix_2d":
            hist, edges = np.histogram(a, bins=bins)
            centers = (edges[:-1] + edges[1:]) / 2
            return {'error': False, 'result': [centers, hist]}

        if dtype == "number_list":
            hist, edges = np.histogram(a, bins=bins)
            centers = (edges[:-1] + edges[1:]) / 2
            return {'error': False, 'result': [centers, hist]}

        if dtype == "number":
            return {'error': False, 'result': a}

        return {'error': True, 'result': f"Неподдерживаемый тип данных: {dtype}"}

    @staticmethod
    def percentile(a, percentile=95):
        def _proc(y):
            return np.percentile(y, percentile)

        return apply_to_1data(a, _proc)

    @staticmethod
    def correlation(a):
        dtype = detect_data_type(a)

        if dtype == "empty":
            return {'error': True, 'result': "Не переданы данные для расчёта"}

        if dtype == "matrix_2d":
            return {'error': False, 'result': np.corrcoef(a)}

        if dtype == "matrix_3d":
            n_slices = a.shape[0]
            flat = a.reshape(n_slices, -1)
            return {'error': False, 'result': np.corrcoef(flat)}

        if dtype == "spectrum_list":
            y_list = [y for _, y in a]
            data = np.array(y_list)
            return {'error': False, 'result': np.corrcoef(data)}

        return {'error': True, 'result': f"Неподдерживаемый тип данных: {dtype}"}

    @staticmethod
    def outliers(a, z_thresh=3.0):
        def _proc(y):
            y = np.array(y)
            z_scores = np.abs(stats.zscore(y))
            # Конвертируем boolean в int (0 и 1)
            return (z_scores > z_thresh).astype(np.uint8)

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

        if dtype == "matrix_2d":
            return {'error': False, 'result': _proc(a)}

        if dtype == "matrix_list_2d":
            return {'error': False, 'result': [_proc(m) for m in a]}

        return {'error': True, 'result': f"Неподдерживаемый тип данных: {dtype}"}