import numpy as np

from packages.Floating_window.node_editor.nodes.node_import import *
from packages.Floating_window.NodeContentBuilder import NodeContentBuilder


class DenoisingGraphicsNode(CalcGraphicsNode):
    def initSizes(self):
        super().initSizes()
        self.height = 175


class DenoisingNode(CalcNode):
    icon = "Icon/image/denoising.png"
    op_code = OP_NODE_DENOISING
    op_title = "Шумоподавление"
    inputs = [SOCKET_TYPES['any']]
    outputs = [SOCKET_TYPES['any']]
    GraphicsNode_class = DenoisingGraphicsNode
    NodeContent_class = NodeContentBuilder

    def __init__(self, scene, MP):
        super().__init__(scene, MP)
        self.content.buildUI(node_functions=[
            {
                'name': 'Нелокальное среднее',
                'params': [
                    {'name': 'Сила',
                     'parameter_property': {'widget': 'DragNumberInput', 'step': 0.1, 'decimal': 1, 'min': 0.1,
                                            'max': 1.0, 'def': 0.3}}
                ],
                'inputs': SOCKET_TYPES['matrix_2d'],
                'outputs': SOCKET_TYPES['matrix_2d']
            },
            {
                'name': 'Вейвлет',
                'params': [
                    {'name': 'Вейвлет',
                     'parameter_property': {'widget': 'QComboBox',
                                            'name_list': ['Хаара', 'Добеши 2', 'Добеши 4', 'Добеши 8', 'Симлет 4', 'Симлет 8', 'Коифлет 2', 'Коифлет 4'],
                                            'data_list': ['haar', 'db2', 'db4', 'db8', 'sym4', 'sym8', 'coif2', 'coif4']}},
                    {'name': 'Режим',
                      'parameter_property': {'widget': 'QComboBox',
                                             'name_list': ['Мягкий порог', 'Жёсткий порог'],
                                             'data_list': ['soft', 'hard']}},
                    {'name': 'Порог',
                     'parameter_property': {'widget': 'DragNumberInput', 'step': 0.1, 'decimal': 1, 'min': 0.1,
                                            'max': 5.0, 'def': 1.0}}
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

        if op_name == 'Нелокальное среднее':
            strength = params.get('Сила', 0.3)
            self.MP.run_process(func=self.nl_means, args=(a, strength), callback=self.evalOperation_cplt)
        elif op_name == 'Вейвлет':
            wavelet_type = params.get('Вейвлет', 1.0)
            mode = params.get('Режим', 1.0)
            threshold = params.get('Порог', 1.0)
            self.MP.run_process(func=self.wavelet, args=(a, threshold, wavelet_type, mode), callback=self.evalOperation_cplt)

    @staticmethod
    def nl_means(a, strength=0.3):
        from skimage.restoration import denoise_nl_means, estimate_sigma
        dtype = detect_data_type(a)

        if dtype == "empty":
            return {'error': True, 'result': "Не переданы данные для расчёта"}

        if dtype == "matrix_2d":
            sigma = estimate_sigma(a)
            if sigma == 0:
                return {'error': False, 'result': a}
            return {'error': False, 'result': denoise_nl_means(a, h=sigma * strength, fast_mode=True)}
        if dtype == "matrix_3d":
            sigma = estimate_sigma(a)
            if sigma == 0:
                return {'error': False, 'result': a}
            return {'error': False, 'result': denoise_nl_means(a, h=sigma * strength, fast_mode=True)}
        if dtype == "matrix_list_2d":
            result = []
            for m in a:
                sigma = estimate_sigma(m)
                if sigma == 0:
                    result.append(m)
                else:
                    result.append(denoise_nl_means(m, h=sigma * strength, fast_mode=True))
            return {'error': False, 'result': result}

        return {'error': True, 'result': f"Неподдерживаемый тип данных: {dtype}"}

    @staticmethod
    def wavelet(a, threshold=1.0, wavelet_type='db4', mode='soft'):
        import pywt

        def _denoise_1d(y):
            y = np.array(y, dtype=float)
            lvl = pywt.dwt_max_level(len(y), wavelet_type)
            coeffs = pywt.wavedec(y, wavelet_type, level=lvl)
            coeffs_thresh = [coeffs[0]]
            for i in range(1, len(coeffs)):
                sigma = np.median(np.abs(coeffs[i])) / 0.6745
                thresh = sigma * threshold * np.sqrt(2 * np.log(len(coeffs[i])))
                coeffs_thresh.append(pywt.threshold(coeffs[i], thresh, mode=mode))
            return pywt.waverec(coeffs_thresh, wavelet_type)[:len(y)]

        def _denoise_2d(matrix):
            matrix = np.array(matrix, dtype=float)
            lvl = pywt.dwt_max_level(min(matrix.shape), wavelet_type)
            coeffs = pywt.wavedec2(matrix, wavelet_type, level=lvl)
            coeffs_thresh = [coeffs[0]]
            for i in range(1, len(coeffs)):
                cH, cV, cD = coeffs[i]
                sigma_H = np.median(np.abs(cH)) / 0.6745
                sigma_V = np.median(np.abs(cV)) / 0.6745
                sigma_D = np.median(np.abs(cD)) / 0.6745
                thresh_H = sigma_H * threshold * np.sqrt(2 * np.log(cH.size))
                thresh_V = sigma_V * threshold * np.sqrt(2 * np.log(cV.size))
                thresh_D = sigma_D * threshold * np.sqrt(2 * np.log(cD.size))
                coeffs_thresh.append((
                    pywt.threshold(cH, thresh_H, mode=mode),
                    pywt.threshold(cV, thresh_V, mode=mode),
                    pywt.threshold(cD, thresh_D, mode=mode)
                ))
            return pywt.waverec2(coeffs_thresh, wavelet_type)[:matrix.shape[0], :matrix.shape[1]]

        dtype = detect_data_type(a)

        if dtype == "empty":
            return {'error': True, 'result': "Не переданы данные для расчёта"}

        if dtype == "spectrum":
            x, y = a
            return {'error': False, 'result': [x, _denoise_1d(y)]}
        if dtype == "spectrum_list":
            return {'error': False, 'result': [[x, _denoise_1d(y)] for x, y in a]}
        if dtype == "matrix_2d":
            return {'error': False, 'result': _denoise_2d(a)}
        if dtype == "matrix_list_2d":
            return {'error': False, 'result': [_denoise_2d(m) for m in a]}
        if dtype == "number_list":
            return {'error': False, 'result': _denoise_1d(np.array(a)).tolist()}

        return {'error': True, 'result': f"Неподдерживаемый тип данных: {dtype}"}
