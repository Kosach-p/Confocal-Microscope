import numpy as np
from scipy.ndimage import gaussian_filter, median_filter
from scipy.signal import savgol_filter

from packages.Floating_window.node_editor.nodes.node_import import *
from packages.Floating_window.NodeContentBuilder import NodeContentBuilder


class SmoothingGraphicsNode(CalcGraphicsNode):
    def initSizes(self):
        super().initSizes()
        self.height = 145


class SmoothingNode(CalcNode):
    icon = "Icon/image/smoothing.png"
    op_code = OP_NODE_SMOOTHING
    op_title = "Сглаживание"
    inputs = [SOCKET_TYPES['any']]
    outputs = [SOCKET_TYPES['any']]
    GraphicsNode_class = SmoothingGraphicsNode
    NodeContent_class = NodeContentBuilder

    def __init__(self, scene, MP):
        super().__init__(scene, MP)
        self.content.buildUI(node_functions=[
            {
                'name': 'Гаусс',
                'params': [
                    {'name': 'Сигма',
                     'parameter_property': {'widget': 'DragNumberInput', 'step': 0.1, 'decimal': 1, 'min': 0.1,
                                            'max': 10.0, 'def': 1.0}}
                ],
                'inputs': SOCKET_TYPES['any'],
                'outputs': SOCKET_TYPES['any']
            },
            {
                'name': 'Медиана',
                'params': [
                    {'name': 'Размер ядра',
                     'parameter_property': {'widget': 'DragNumberInput', 'step': 2, 'decimal': 0, 'min': 3, 'max': 15,
                                            'def': 3}}
                ],
                'inputs': SOCKET_TYPES['any'],
                'outputs': SOCKET_TYPES['any']
            },
            {
                'name': 'Savitzky-Golay',
                'params': [
                    {'name': 'Окно',
                     'parameter_property': {'widget': 'DragNumberInput', 'step': 2, 'decimal': 0, 'min': 3, 'max': 15,
                                            'def': 5}},
                    {'name': 'Порядок',
                     'parameter_property': {'widget': 'DragNumberInput', 'step': 1, 'decimal': 0, 'min': 1, 'max': 5,
                                            'def': 2}}
                ],
                'inputs': SOCKET_TYPES['any'],
                'outputs': SOCKET_TYPES['any']
            },
            {
                'name': 'LOWESS',
                'params': [
                    {'name': 'Frac',
                     'parameter_property': {'widget': 'DragNumberInput', 'step': 0.05, 'decimal': 2, 'min': 0.01,
                                            'max': 1.0, 'def': 0.3}},
                    {'name': 'It',
                     'parameter_property': {'widget': 'DragNumberInput', 'step': 1, 'decimal': 0, 'min': 0,
                                            'max': 10, 'def': 2}}
                ],
                'inputs': SOCKET_TYPES['spectrum'],
                'outputs': SOCKET_TYPES['spectrum']
            },
            {
                'name': 'EMA',
                'params': [
                    {'name': 'Alpha',
                     'parameter_property': {'widget': 'DragNumberInput', 'step': 0.05, 'decimal': 2, 'min': 0.15,
                                            'max': 1.0, 'def': 0.3}}
                ],
                'inputs': SOCKET_TYPES['spectrum'],
                'outputs': SOCKET_TYPES['spectrum']
            },
            {
                'name': 'Bilateral',
                'params': [
                    {'name': 'Spatial',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 0.1, 'decimal': 1, 'def': 1.0}},
                    {'name': 'Intensity',
                     'parameter_property': {'widget': 'DragNumberInput', 'step': 0.01, 'decimal': 2, 'min': 0.01,
                                            'max': 1.0, 'def': 0.1}}
                ],
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
        params = self.content.get_params()

        if op_name == 'Гаусс':
            sigma = params.get('Сигма', 1.0)
            self.MP.run_process(func=self.gaussian, args=(a, sigma), callback=self.evalOperation_cplt)
        elif op_name == 'Медиана':
            kernel = int(params.get('Размер ядра', 3))
            self.MP.run_process(func=self.median, args=(a, kernel), callback=self.evalOperation_cplt)
        elif op_name == 'Savitzky-Golay':
            window = int(params.get('Окно', 5))
            order = int(params.get('Порядок', 2))
            self.MP.run_process(func=self.savitzky, args=(a, window, order), callback=self.evalOperation_cplt)
        elif op_name == 'LOWESS':
            frac = params.get('Frac', 0.3)
            it = params.get('It', 2)
            self.MP.run_process(func=self.lowess, args=(a, frac, it), callback=self.evalOperation_cplt)
        elif op_name == 'EMA':
            alpha = params.get('Alpha', 0.3)
            self.MP.run_process(func=self.ema, args=(a, alpha), callback=self.evalOperation_cplt)
        elif op_name == 'Bilateral':
            spatial = params.get('Spatial', 1.0)
            intensity = params.get('Intensity', 1.0)
            self.MP.run_process(func=self.bilateral, args=(a, spatial, intensity), callback=self.evalOperation_cplt)

    @staticmethod
    def gaussian(a, sigma=1.0):
        return apply_to_1data(a, lambda x: gaussian_filter(x, sigma))

    @staticmethod
    def median(a, kernel_size=3):
        return apply_to_1data(a, lambda x: median_filter(x, kernel_size))

    @staticmethod
    def savitzky(a, window_size=5, order=2):
        def _savgol_1d(data):
            return savgol_filter(data, window_size, order)

        dtype = detect_data_type(a)

        if dtype == "empty":
            return {'error': True, 'result': "Не переданы данные для расчёта"}
        if "number" in dtype and "list" not in dtype:
            return {'error': True, 'result': f"Неподдерживаемый тип данных: {dtype}"}
        if dtype == "spectrum":
            x, y = a
            return {'error': False, 'result': [x, _savgol_1d(y)]}
        if dtype == "spectrum_list":
            return {'error': False, 'result': [[x, _savgol_1d(y)] for x, y in a]}
        if dtype == "matrix_2d":
            result = a.copy()
            for i in range(a.shape[0]):
                result[i] = savgol_filter(result[i], window_size, order)
            for j in range(a.shape[1]):
                result[:, j] = savgol_filter(result[:, j], window_size, order)
            return {'error': False, 'result': result}
        if dtype == "matrix_3d":
            result = a.copy()
            for i in range(a.shape[0]):
                for j in range(a.shape[1]):
                    result[i, j, :] = savgol_filter(result[i, j, :], window_size, order)
            for i in range(a.shape[0]):
                for k in range(a.shape[2]):
                    result[i, :, k] = savgol_filter(result[i, :, k], window_size, order)
            for j in range(a.shape[1]):
                for k in range(a.shape[2]):
                    result[:, j, k] = savgol_filter(result[:, j, k], window_size, order)
            return {'error': False, 'result': result}
        if dtype == "matrix_list_2d":
            data_3d = np.stack(a)
            result = SmoothingNode.savitzky(data_3d, window_size, order)
            if isinstance(result, dict) and result['error']:
                return result
            return {'error': False, 'result': [result['result'][i] for i in range(result['result'].shape[0])]}
        if dtype == "number_list":
            return {'error': False, 'result': _savgol_1d(np.array(a)).tolist()}

        return {'error': True, 'result': f"Неподдерживаемый тип данных: {dtype}"}

    @staticmethod
    def lowess(a, frac=0.3, it=2, delta=0.0):
        def _lowess_1d(y):
            from statsmodels.nonparametric.smoothers_lowess import lowess as sm_lowess
            x = np.arange(len(y))
            result = sm_lowess(y, x, frac=frac, it=int(it), delta=delta)
            return result[:, 1]

        dtype = detect_data_type(a)

        if dtype == "empty":
            return {'error': True, 'result': "Не переданы данные для расчёта"}
        if dtype == "spectrum":
            x, y = a
            return {'error': False, 'result': [x, _lowess_1d(y)]}
        if dtype == "spectrum_list":
            return {'error': False, 'result': [[x, _lowess_1d(y)] for x, y in a]}
        if dtype == "number_list":
            return {'error': False, 'result': _lowess_1d(np.array(a)).tolist()}

        return {'error': True, 'result': f"Неподдерживаемый тип данных: {dtype}"}

    @staticmethod
    def ema(a, alpha=0.3):
        def _ema_1d(data):
            result = np.zeros_like(data, dtype=float)
            result[0] = data[0]
            for i in range(1, len(data)):
                result[i] = alpha * data[i] + (1 - alpha) * result[i - 1]
            return result

        dtype = detect_data_type(a)

        if dtype == "empty":
            return {'error': True, 'result': "Не переданы данные для расчёта"}
        if dtype == "spectrum":
            x, y = a
            return {'error': False, 'result': [x, _ema_1d(y)]}
        if dtype == "spectrum_list":
            return {'error': False, 'result': [[x, _ema_1d(y)] for x, y in a]}
        if dtype == "number_list":
            return {'error': False, 'result': _ema_1d(np.array(a)).tolist()}

        return {'error': True, 'result': f"Неподдерживаемый тип данных: {dtype}"}

    @staticmethod
    def bilateral(a, spatial=1.0, intensity=0.1):
        from skimage.restoration import denoise_bilateral
        dtype = detect_data_type(a)

        if dtype == "empty":
            return {'error': True, 'result': "Не переданы данные для расчёта"}
        if dtype == "matrix_2d":
            y_min, y_max = np.min(a), np.max(a)
            if y_max != y_min:
                norm = (a - y_min) / (y_max - y_min)
                filtered = denoise_bilateral(norm, sigma_color=intensity, sigma_spatial=spatial)
                return {'error': False, 'result': filtered * (y_max - y_min) + y_min}
            return {'error': False, 'result': denoise_bilateral(a, sigma_color=intensity, sigma_spatial=spatial)}
        if dtype == "matrix_list_2d":
            result = []
            for m in a:
                y_min, y_max = np.min(m), np.max(m)
                if y_max != y_min:
                    norm = (m - y_min) / (y_max - y_min)
                    filtered = denoise_bilateral(norm, sigma_color=intensity, sigma_spatial=spatial)
                    result.append(filtered * (y_max - y_min) + y_min)
                else:
                    result.append(denoise_bilateral(m, sigma_color=intensity, sigma_spatial=spatial))
            return {'error': False, 'result': result}

        return {'error': True, 'result': f"Неподдерживаемый тип данных: {dtype}"}