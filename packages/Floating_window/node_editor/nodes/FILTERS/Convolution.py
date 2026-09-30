from skimage import restoration
import RedLionfishDeconv as RLD

from packages.Floating_window.node_editor.nodes.node_import import *
from packages.Floating_window.NodeContentBuilder import NodeContentBuilder
from RedLionfishDeconv import RLDeconvolve


class ConvolutionGraphicsNode(CalcGraphicsNode):
    def initSizes(self):
        super().initSizes()
        self.height = 145


class ConvolutionNode(CalcNode):
    icon = "Icon/image/convolution.png"
    op_code = OP_NODE_CONVOLUTION
    op_title = "Деконволюция"
    inputs = [SOCKET_TYPES['any'], SOCKET_TYPES['any']]
    outputs = [SOCKET_TYPES['any']]
    GraphicsNode_class = ConvolutionGraphicsNode
    NodeContent_class = NodeContentBuilder

    def __init__(self, scene, MP):
        super().__init__(scene, MP)
        self.content.buildUI(node_functions=[
            {
                'name': 'Свёртка',
                'params': [],
                'inputs': SOCKET_TYPES['any'],
                'outputs': SOCKET_TYPES['any']
            },
            {
                'name': 'Ричардсон-Люси',
                'params': [
                    {'name': 'Итерации',
                     'parameter_property': {'widget': 'DragNumberInput', 'step': 1, 'decimal': 0, 'min': 1,
                                            'max': 100, 'def': 30}}
                ],
                'inputs': SOCKET_TYPES['any'],
                'outputs': SOCKET_TYPES['any']
            },
            {
                'name': 'Винер',
                'params': [
                    {'name': 'Баланс',
                     'parameter_property': {'widget': 'DragNumberInput', 'step': 0.01, 'decimal': 3, 'min': 0.001,
                                            'max': 1.0, 'def': 0.1}}
                ],
                'inputs': SOCKET_TYPES['any'],
                'outputs': SOCKET_TYPES['any']
            },
            {
                'name': 'Винер без PSF',
                'params': [],
                'inputs': SOCKET_TYPES['any'],
                'outputs': SOCKET_TYPES['any']
            }
        ])
        self.MP = MP

    def evalOperation(self, input_values):
        super().evalOperation(input_values)
        if not input_values or len(input_values) < 2:
            return None

        a, b = input_values[0], input_values[1]
        op_name = self.content.get_func()

        if op_name == 'Свёртка':
            self.MP.run_process(func=self.convolve_data, args=(a, b), callback=self.evalOperation_cplt)
        elif op_name == 'Ричардсон-Люси':
            iterations = int(self.content.get_params().get('Итерации', 30))
            self.MP.run_process(func=self.deconvolve_rl, args=(a, b, iterations), callback=self.evalOperation_cplt)
        elif op_name == 'Винер':
            balance = float(self.content.get_params().get('Баланс', 0.1))
            self.MP.run_process(func=self.deconvolve_wiener, args=(a, b, balance), callback=self.evalOperation_cplt)
        elif op_name == 'Винер без PSF':
            self.MP.run_process(func=self.deconvolve_wiener_unsupervised, args=(a, b), callback=self.evalOperation_cplt)

    @staticmethod
    def convolve_data(a, b):
        def _conv(x, y):
            return convolve(x, y, mode='same')

        return apply_to_2_data(a, b, _conv)

    @staticmethod
    def deconvolve_rl(a, b, iterations=30):
        dtype_a = detect_data_type(a)
        dtype_b = detect_data_type(b)

        if dtype_a == "empty" or dtype_b == "empty":
            return {'error': True, 'result': "Не переданы данные для расчёта"}

        if 'matrix' in dtype_a and 'matrix' in dtype_b:
            if dtype_a == "matrix_list_2d":
                a = np.stack(a)
            if dtype_b == "matrix_list_2d":
                b = np.stack(b)

            result = RLD.doRLDeconvolutionFromNpArrays(a, b, niter=iterations)

            return {'error': False, 'result': result}

        if dtype_a == "spectrum" and dtype_b == "spectrum":
            x, y = a
            _, kernel = b
            result = restoration.richardson_lucy(y, kernel, num_iter=iterations)
            return {'error': False, 'result': [x, result]}

        return {'error': True, 'result': f"Неподдерживаемая пара типов: {dtype_a} + {dtype_b}"}

    @staticmethod
    def deconvolve_wiener(a, b, balance=0.1):
        dtype_a = detect_data_type(a)
        dtype_b = detect_data_type(b)

        if dtype_a == "empty" or dtype_b == "empty":
            return {'error': True, 'result': "Не переданы данные для расчёта"}

        if "matrix" in dtype_a and "matrix" in dtype_b:
            return apply_to_2_data(a=a, b=b, func=restoration.richardson_lucy, balance=balance)
        if dtype_a == "spectrum" and dtype_b == "spectrum":
            x, y = a
            _, kernel = b
            result = restoration.wiener(y, kernel, balance=balance)
            return {'error': False, 'result': [x, result]}

        return {'error': True, 'result': f"Неподдерживаемая пара типов: {dtype_a} + {dtype_b}"}

    @staticmethod
    def deconvolve_wiener_unsupervised(a, b):
        dtype_a = detect_data_type(a)
        dtype_b = detect_data_type(b)

        if dtype_a == "empty" or dtype_b == "empty":
            return {'error': True, 'result': "Не переданы данные для расчёта"}

        if dtype_a == "matrix_2d" and dtype_b == "matrix_2d":
            return {'error': False, 'result': restoration.unsupervised_wiener(a, b)}
        if dtype_a == "spectrum" and dtype_b == "spectrum":
            x, y = a
            _, kernel = b
            result = restoration.unsupervised_wiener(y, kernel)
            return {'error': False, 'result': [x, result]}

        return {'error': True, 'result': f"Неподдерживаемая пара типов: {dtype_a} + {dtype_b}"}