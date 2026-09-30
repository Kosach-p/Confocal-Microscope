import numpy as np
from packages.Floating_window.node_editor.nodes.node_import import *
from packages.Floating_window.NodeContentBuilder import NodeContentBuilder


class PSFGeneratorGraphicsNode(CalcGraphicsNode):
    def initSizes(self):
        super().initSizes()
        self.height = 280


class PSFGeneratorNode(CalcNode):
    icon = "Icon/image/psf.png"
    op_code = OP_NODE_PSF_GENERATOR
    op_title = "Генератор PSF"
    inputs = []
    outputs = [SOCKET_TYPES['matrix_3d']]
    GraphicsNode_class = PSFGeneratorGraphicsNode
    NodeContent_class = NodeContentBuilder

    def __init__(self, scene, MP):
        super().__init__(scene, MP)
        self.content.buildUI(node_functions=[
            {
                'name': 'Гауссова PSF',
                'params': [
                    {'name': 'Размеры:',
                     'parameter_property': {'widget': 'QLabel'}},
                    {'name': 'X',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 1, 'decimal': 0, 'min': 1,
                                            'max': 4096, 'def': 64}},
                    {'name': 'Y',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 1, 'decimal': 0, 'min': 1,
                                            'max': 4096, 'def': 64}},
                    {'name': 'Z',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 1, 'decimal': 0, 'min': 1,
                                            'max': 4096, 'def': 64}},
                    {'name': 'Параметры генерации:',
                     'parameter_property': {'widget': 'QLabel'}},
                    {'name': 'Сигма',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 0.1, 'decimal': 2, 'min': 0.1,
                                            'max': 100.0, 'def': 2.0}},
                    {'name': 'Амплитуда',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 0.1, 'decimal': 2, 'min': 0.1,
                                            'max': 10.0, 'def': 1.0}}
                ],
                'inputs': [],
                'outputs': SOCKET_TYPES['matrix_3d']
            },
            {
                'name': 'Эйри PSF',
                'params': [
                    {'name': 'Размеры:',
                     'parameter_property': {'widget': 'QLabel'}},
                    {'name': 'X',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 1, 'decimal': 0, 'min': 1,
                                            'max': 4096, 'def': 64}},
                    {'name': 'Y',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 1, 'decimal': 0, 'min': 1,
                                            'max': 4096, 'def': 64}},
                    {'name': 'Z',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 1, 'decimal': 0, 'min': 1,
                                            'max': 4096, 'def': 64}},
                    {'name': 'Параметры генерации:',
                     'parameter_property': {'widget': 'QLabel'}},
                    {'name': 'Сигма',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 0.1, 'decimal': 2, 'min': 0.1,
                                            'max': 100.0, 'def': 2.0}},
                    {'name': 'Амплитуда',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 0.1, 'decimal': 2, 'min': 0.1,
                                            'max': 10.0, 'def': 1.0}}
                ],
                'inputs': [],
                'outputs': SOCKET_TYPES['matrix_3d']
            },
            {
                'name': 'Лоренцева PSF',
                'params': [
                    {'name': 'Размеры:',
                     'parameter_property': {'widget': 'QLabel'}},
                    {'name': 'X',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 1, 'decimal': 0, 'min': 1,
                                            'max': 4096, 'def': 64}},
                    {'name': 'Y',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 1, 'decimal': 0, 'min': 1,
                                            'max': 4096, 'def': 64}},
                    {'name': 'Z',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 1, 'decimal': 0, 'min': 1,
                                            'max': 4096, 'def': 64}},
                    {'name': 'Параметры генерации:',
                     'parameter_property': {'widget': 'QLabel'}},
                    {'name': 'Сигма',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 0.1, 'decimal': 2, 'min': 0.1,
                                            'max': 100.0, 'def': 2.0}},
                    {'name': 'Амплитуда',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 0.1, 'decimal': 2, 'min': 0.1,
                                            'max': 10.0, 'def': 1.0}}
                ],
                'inputs': [],
                'outputs': SOCKET_TYPES['matrix_3d']
            },
            {
                'name': 'Двойная гауссова PSF',
                'params': [
                    {'name': 'Размеры:',
                     'parameter_property': {'widget': 'QLabel'}},
                    {'name': 'X',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 1, 'decimal': 0, 'min': 1,
                                            'max': 4096, 'def': 64}},
                    {'name': 'Y',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 1, 'decimal': 0, 'min': 1,
                                            'max': 4096, 'def': 64}},
                    {'name': 'Z',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 1, 'decimal': 0, 'min': 1,
                                            'max': 4096, 'def': 64}},
                    {'name': 'Параметры генерации:',
                     'parameter_property': {'widget': 'QLabel'}},
                    {'name': 'Сигма',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 0.1, 'decimal': 2, 'min': 0.1,
                                            'max': 100.0, 'def': 2.0}},
                    {'name': 'Амплитуда',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 0.1, 'decimal': 2, 'min': 0.1,
                                            'max': 10.0, 'def': 1.0}}
                ],
                'inputs': [],
                'outputs': SOCKET_TYPES['matrix_3d']
            }
        ])
        self.MP = MP

    def evalOperation(self, input_values):
        super().evalOperation(input_values)
        params = self.content.get_params()
        op_name = self.content.get_func()

        if op_name == 'Гауссова PSF':
            size_z = int(params.get('Z', 64))
            size_y = int(params.get('Y', 64))
            size_x = int(params.get('X', 64))
            sigma = float(params.get('Сигма', 2.0))
            amplitude = float(params.get('Амплитуда', 1.0))
            self.MP.run_process(func=self.generate_psf,
                                args=('Гауссова', size_z, size_y, size_x, sigma, amplitude),
                                callback=self.evalOperation_cplt)
        elif op_name == 'Эйри PSF':
            size_z = int(params.get('Z', 64))
            size_y = int(params.get('Y', 64))
            size_x = int(params.get('X', 64))
            sigma = float(params.get('Сигма', 2.0))
            amplitude = float(params.get('Амплитуда', 1.0))
            self.MP.run_process(func=self.generate_psf,
                                args=('Эйри', size_z, size_y, size_x, sigma, amplitude),
                                callback=self.evalOperation_cplt)
        elif op_name == 'Лоренцева PSF':
            size_z = int(params.get('Z', 64))
            size_y = int(params.get('Y', 64))
            size_x = int(params.get('X', 64))
            sigma = float(params.get('Сигма', 2.0))
            amplitude = float(params.get('Амплитуда', 1.0))
            self.MP.run_process(func=self.generate_psf,
                                args=('Лоренцева', size_z, size_y, size_x, sigma, amplitude),
                                callback=self.evalOperation_cplt)
        elif op_name == 'Двойная гауссова PSF':
            size_z = int(params.get('Z', 64))
            size_y = int(params.get('Y', 64))
            size_x = int(params.get('X', 64))
            sigma = float(params.get('Сигма', 2.0))
            amplitude = float(params.get('Амплитуда', 1.0))
            self.MP.run_process(func=self.generate_psf,
                                args=('Двойная гауссова', size_z, size_y, size_x, sigma, amplitude),
                                callback=self.evalOperation_cplt)

    @staticmethod
    def generate_psf(psf_type, size_z, size_y, size_x, sigma, amplitude):
        z = np.arange(size_z) - size_z // 2
        y = np.arange(size_y) - size_y // 2
        x = np.arange(size_x) - size_x // 2
        Z, Y, X = np.meshgrid(z, y, x, indexing='ij')
        R = np.sqrt(X ** 2 + Y ** 2 + Z ** 2)

        if psf_type == 'Гауссова':
            return {'error': False, 'result': amplitude * np.exp(-R ** 2 / (2 * sigma ** 2))}
        elif psf_type == 'Лоренцева':
            return {'error': False, 'result': amplitude / (1 + (R / sigma) ** 2)}
        elif psf_type == 'Двойная гауссова':
            inner = amplitude * np.exp(-R ** 2 / (2 * sigma ** 2))
            outer = 0.3 * amplitude * np.exp(-R ** 2 / (2 * (sigma * 3) ** 2))
            return {'error': False, 'result': inner + outer}
        elif psf_type == 'Эйри':
            from scipy.special import j1
            r_scaled = R / max(sigma, 0.1)
            with np.errstate(divide='ignore', invalid='ignore'):
                airy = (2 * j1(r_scaled) / r_scaled) ** 2
                airy = np.nan_to_num(airy, nan=1.0)
            return {'error': False, 'result': amplitude * airy}
        return {'error': True, 'result': f"Неизвестный тип PSF: {psf_type}"}