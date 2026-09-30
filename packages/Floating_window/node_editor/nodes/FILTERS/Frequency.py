import numpy as np
from scipy import fft

from packages.Floating_window.node_editor.nodes.node_import import *
from packages.Floating_window.NodeContentBuilder import NodeContentBuilder


class FrequencyGraphicsNode(CalcGraphicsNode):
    def initSizes(self):
        super().initSizes()
        self.height = 145


class FrequencyNode(CalcNode):
    icon = "Icon/image/frequency.png"
    op_code = OP_NODE_FREQUENCY
    op_title = "Частотная фильтрация"
    inputs = [SOCKET_TYPES['any']]
    outputs = [SOCKET_TYPES['any']]
    GraphicsNode_class = FrequencyGraphicsNode
    NodeContent_class = NodeContentBuilder

    def __init__(self, scene, MP):
        super().__init__(scene, MP)
        self.content.buildUI(node_functions=[
            {
                'name': 'Низкочастотный',
                'params': [
                    {'name': 'Частота среза',
                     'parameter_property': {'widget': 'DragNumberInput', 'step': 0.001, 'decimal': 3, 'min': 0.00,
                                            'max': 1.0, 'def': 0.3}}
                ],
                'inputs': SOCKET_TYPES['any'],
                'outputs': SOCKET_TYPES['any']
            },
            {
                'name': 'Высокочастотный',
                'params': [
                    {'name': 'Частота среза',
                     'parameter_property': {'widget': 'DragNumberInput', 'step': 0.001, 'decimal': 3, 'min': 0.00,
                                            'max': 1.0, 'def': 0.3}}
                ],
                'inputs': SOCKET_TYPES['any'],
                'outputs': SOCKET_TYPES['any']
            },
            {
                'name': 'Полосовой',
                'params': [
                    {'name': 'Нижняя',
                     'parameter_property': {'widget': 'DragNumberInput', 'step': 0.001, 'decimal': 3, 'min': 0.00,
                                            'max': 1.0, 'def': 0.2}},
                    {'name': 'Верхняя',
                     'parameter_property': {'widget': 'DragNumberInput', 'step': 0.001, 'decimal': 3, 'min': 0.00,
                                            'max': 1.0, 'def': 0.6}}
                ],
                'inputs': SOCKET_TYPES['any'],
                'outputs': SOCKET_TYPES['any']
            },
            {
                'name': 'Режекторный',
                'params': [
                    {'name': 'Центр',
                     'parameter_property': {'widget': 'DragNumberInput', 'step': 0.001, 'decimal': 3, 'min': 0.00,
                                            'max': 1.0, 'def': 0.4}},
                    {'name': 'Ширина',
                     'parameter_property': {'widget': 'DragNumberInput', 'step': 0.001, 'decimal': 3, 'min': 0.00,
                                            'max': 0.5, 'def': 0.1}}
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

        if op_name == 'Низкочастотный':
            cutoff = params.get('Частота среза', 0.3)
            self.MP.run_process(func=self.lowpass, args=(a, cutoff), callback=self.evalOperation_cplt)
        elif op_name == 'Высокочастотный':
            cutoff = params.get('Частота среза', 0.3)
            self.MP.run_process(func=self.highpass, args=(a, cutoff), callback=self.evalOperation_cplt)
        elif op_name == 'Полосовой':
            low = params.get('Нижняя', 0.2)
            high = params.get('Верхняя', 0.6)
            self.MP.run_process(func=self.bandpass, args=(a, low, high), callback=self.evalOperation_cplt)
        elif op_name == 'Режекторный':
            center = params.get('Центр', 0.4)
            width = params.get('Ширина', 0.1)
            self.MP.run_process(func=self.notch, args=(a, center, width), callback=self.evalOperation_cplt)

    @staticmethod
    def lowpass(a, cutoff=0.3):
        dtype = detect_data_type(a)

        if dtype == "empty":
            return {'error': True, 'result': "Не переданы данные для расчёта"}

        if dtype == "spectrum":
            x, y = a
            mask = FrequencyNode._make_mask_1d(len(y), low=0.0, high=cutoff)
            return {'error': False, 'result': [x, FrequencyNode._fft_filter_1d(y, mask)]}
        if dtype == "spectrum_list":
            return {'error': False, 'result': [
                [x, FrequencyNode._fft_filter_1d(y, FrequencyNode._make_mask_1d(len(y), low=0.0, high=cutoff))] for x, y
                in a]}
        if dtype == "number_list":
            y = np.array(a)
            mask = FrequencyNode._make_mask_1d(len(y), low=0.0, high=cutoff)
            return {'error': False, 'result': FrequencyNode._fft_filter_1d(y, mask).tolist()}
        if dtype == "matrix_2d":
            mask = FrequencyNode._make_mask_2d(a.shape, low=0.0, high=cutoff)
            return {'error': False, 'result': FrequencyNode._fft_filter_2d(a, mask)}
        if dtype == "matrix_3d":
            mask = FrequencyNode._make_mask_3d(a.shape, low=0.0, high=cutoff)
            return {'error': False, 'result': FrequencyNode._fft_filter_3d(a, mask)}
        if dtype == "matrix_list_2d":
            return {'error': False, 'result': [
                FrequencyNode._fft_filter_2d(m, FrequencyNode._make_mask_2d(m.shape, low=0.0, high=cutoff)) for m in a]}

        return {'error': True, 'result': f"Неподдерживаемый тип данных: {dtype}"}

    @staticmethod
    def highpass(a, cutoff=0.3):
        dtype = detect_data_type(a)

        if dtype == "empty":
            return {'error': True, 'result': "Не переданы данные для расчёта"}

        if dtype == "spectrum":
            x, y = a
            mask = FrequencyNode._make_mask_1d(len(y), low=cutoff, high=0.5)
            return {'error': False, 'result': [x, FrequencyNode._fft_filter_1d(y, mask)]}
        if dtype == "spectrum_list":
            return {'error': False, 'result': [
                [x, FrequencyNode._fft_filter_1d(y, FrequencyNode._make_mask_1d(len(y), low=cutoff, high=0.5))] for x, y
                in a]}
        if dtype == "number_list":
            y = np.array(a)
            mask = FrequencyNode._make_mask_1d(len(y), low=cutoff, high=0.5)
            return {'error': False, 'result': FrequencyNode._fft_filter_1d(y, mask).tolist()}
        if dtype == "matrix_2d":
            mask = FrequencyNode._make_mask_2d(a.shape, low=cutoff, high=0.5)
            return {'error': False, 'result': FrequencyNode._fft_filter_2d(a, mask)}
        if dtype == "matrix_3d":
            mask = FrequencyNode._make_mask_3d(a.shape, low=cutoff, high=0.5)
            return {'error': False, 'result': FrequencyNode._fft_filter_3d(a, mask)}
        if dtype == "matrix_list_2d":
            return {'error': False, 'result': [
                FrequencyNode._fft_filter_2d(m, FrequencyNode._make_mask_2d(m.shape, low=cutoff, high=0.5)) for m in a]}

        return {'error': True, 'result': f"Неподдерживаемый тип данных: {dtype}"}

    @staticmethod
    def bandpass(a, low=0.2, high=0.6):
        dtype = detect_data_type(a)

        if dtype == "empty":
            return {'error': True, 'result': "Не переданы данные для расчёта"}

        if dtype == "spectrum":
            x, y = a
            mask = FrequencyNode._make_mask_1d(len(y), low=low, high=high)
            return {'error': False, 'result': [x, FrequencyNode._fft_filter_1d(y, mask)]}
        if dtype == "spectrum_list":
            return {'error': False, 'result': [
                [x, FrequencyNode._fft_filter_1d(y, FrequencyNode._make_mask_1d(len(y), low=low, high=high))] for x, y
                in a]}
        if dtype == "number_list":
            y = np.array(a)
            mask = FrequencyNode._make_mask_1d(len(y), low=low, high=high)
            return {'error': False, 'result': FrequencyNode._fft_filter_1d(y, mask).tolist()}
        if dtype == "matrix_2d":
            mask = FrequencyNode._make_mask_2d(a.shape, low=low, high=high)
            return {'error': False, 'result': FrequencyNode._fft_filter_2d(a, mask)}
        if dtype == "matrix_3d":
            mask = FrequencyNode._make_mask_3d(a.shape, low=low, high=high)
            return {'error': False, 'result': FrequencyNode._fft_filter_3d(a, mask)}
        if dtype == "matrix_list_2d":
            return {'error': False,
                    'result': [FrequencyNode._fft_filter_2d(m, FrequencyNode._make_mask_2d(m.shape, low=low, high=high))
                               for m in a]}

        return {'error': True, 'result': f"Неподдерживаемый тип данных: {dtype}"}

    @staticmethod
    def notch(a, center=0.4, width=0.1):
        dtype = detect_data_type(a)

        if dtype == "empty":
            return {'error': True, 'result': "Не переданы данные для расчёта"}

        if dtype == "spectrum":
            x, y = a
            mask = FrequencyNode._make_mask_1d(len(y), low=0.0, high=0.5, notch_center=center, notch_width=width)
            return {'error': False, 'result': [x, FrequencyNode._fft_filter_1d(y, mask)]}
        if dtype == "spectrum_list":
            return {'error': False, 'result': [[x, FrequencyNode._fft_filter_1d(y, FrequencyNode._make_mask_1d(len(y),
                                                                                                               low=0.0,
                                                                                                               high=0.5,
                                                                                                               notch_center=center,
                                                                                                               notch_width=width))]
                                               for x, y in a]}
        if dtype == "number_list":
            y = np.array(a)
            mask = FrequencyNode._make_mask_1d(len(y), low=0.0, high=0.5, notch_center=center, notch_width=width)
            return {'error': False, 'result': FrequencyNode._fft_filter_1d(y, mask).tolist()}
        if dtype == "matrix_2d":
            mask = FrequencyNode._make_mask_2d(a.shape, low=0.0, high=0.5, notch_center=center, notch_width=width)
            return {'error': False, 'result': FrequencyNode._fft_filter_2d(a, mask)}
        if dtype == "matrix_3d":
            mask = FrequencyNode._make_mask_3d(a.shape, low=0.0, high=0.5, notch_center=center, notch_width=width)
            return {'error': False, 'result': FrequencyNode._fft_filter_3d(a, mask)}
        if dtype == "matrix_list_2d":
            return {'error': False, 'result': [FrequencyNode._fft_filter_2d(m, FrequencyNode._make_mask_2d(m.shape,
                                                                                                           low=0.0,
                                                                                                           high=0.5,
                                                                                                           notch_center=center,
                                                                                                           notch_width=width))
                                               for m in a]}

        return {'error': True, 'result': f"Неподдерживаемый тип данных: {dtype}"}