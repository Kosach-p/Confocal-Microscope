from skimage import morphology

from packages.Floating_window.node_editor.nodes.node_import import *
from packages.Floating_window.NodeContentBuilder import NodeContentBuilder


class MorphologyGraphicsNode(CalcGraphicsNode):
    def initSizes(self):
        super().initSizes()
        self.height = 145


class MorphologyNode(CalcNode):
    icon = "Icon/image/morphology.png"
    op_code = OP_NODE_MORPHOLOGY
    op_title = "Морфология"
    inputs = [SOCKET_TYPES['matrix_2d']]
    outputs = [SOCKET_TYPES['matrix_2d']]
    GraphicsNode_class = MorphologyGraphicsNode
    NodeContent_class = NodeContentBuilder

    def __init__(self, scene, MP):
        super().__init__(scene, MP)
        self.content.buildUI(node_functions=[
            {
                'name': 'Эрозия',
                'params': [
                    {'name': 'Размер',
                     'parameter_property': {'widget': 'DragNumberInput', 'step': 1, 'decimal': 0, 'min': 1, 'max': 15,
                                            'def': 3}}
                ],
                'inputs': SOCKET_TYPES['matrix_2d'],
                'outputs': SOCKET_TYPES['matrix_2d']
            },
            {
                'name': 'Дилатация',
                'params': [
                    {'name': 'Размер',
                     'parameter_property': {'widget': 'DragNumberInput', 'step': 1, 'decimal': 0, 'min': 1, 'max': 15,
                                            'def': 3}}
                ],
                'inputs': SOCKET_TYPES['matrix_2d'],
                'outputs': SOCKET_TYPES['matrix_2d']
            },
            {
                'name': 'Opening',
                'params': [
                    {'name': 'Размер',
                     'parameter_property': {'widget': 'DragNumberInput', 'step': 1, 'decimal': 0, 'min': 1, 'max': 15,
                                            'def': 3}}
                ],
                'inputs': SOCKET_TYPES['matrix_2d'],
                'outputs': SOCKET_TYPES['matrix_2d']
            },
            {
                'name': 'Closing',
                'params': [
                    {'name': 'Размер',
                     'parameter_property': {'widget': 'DragNumberInput', 'step': 1, 'decimal': 0, 'min': 1, 'max': 15,
                                            'def': 3}}
                ],
                'inputs': SOCKET_TYPES['matrix_2d'],
                'outputs': SOCKET_TYPES['matrix_2d']
            },
            {
                'name': 'Top-hat',
                'params': [
                    {'name': 'Размер',
                     'parameter_property': {'widget': 'DragNumberInput', 'step': 1, 'decimal': 0, 'min': 1, 'max': 15,
                                            'def': 3}}
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
        size = int(self.content.get_params().get('Размер', 3))

        if op_name == 'Эрозия':
            self.MP.run_process(func=self.erosion, args=(a, size), callback=self.evalOperation_cplt)
        elif op_name == 'Дилатация':
            self.MP.run_process(func=self.dilation, args=(a, size), callback=self.evalOperation_cplt)
        elif op_name == 'Opening':
            self.MP.run_process(func=self.opening, args=(a, size), callback=self.evalOperation_cplt)
        elif op_name == 'Closing':
            self.MP.run_process(func=self.closing, args=(a, size), callback=self.evalOperation_cplt)
        elif op_name == 'Top-hat':
            self.MP.run_process(func=self.tophat, args=(a, size), callback=self.evalOperation_cplt)

    @staticmethod
    def erosion(a, size=3):
        from skimage import morphology
        dtype = detect_data_type(a)

        if dtype == "empty":
            return {'error': True, 'result': "Не переданы данные для расчёта"}

        if dtype == "matrix_2d":
            return {'error': False, 'result': morphology.erosion(a, morphology.disk(size))}
        if dtype == "matrix_3d":
            return {'error': False, 'result': morphology.erosion(a, morphology.ball(size))}
        if dtype == "matrix_list_2d":
            return {'error': False, 'result': [morphology.erosion(m, morphology.disk(size)) for m in a]}

        return {'error': True, 'result': f"Неподдерживаемый тип данных: {dtype}"}

    @staticmethod
    def dilation(a, size=3):
        from skimage import morphology
        dtype = detect_data_type(a)

        if dtype == "empty":
            return {'error': True, 'result': "Не переданы данные для расчёта"}

        if dtype == "matrix_2d":
            return {'error': False, 'result': morphology.dilation(a, morphology.disk(size))}
        if dtype == "matrix_3d":
            return {'error': False, 'result': morphology.dilation(a, morphology.ball(size))}
        if dtype == "matrix_list_2d":
            return {'error': False, 'result': [morphology.dilation(m, morphology.disk(size)) for m in a]}

        return {'error': True, 'result': f"Неподдерживаемый тип данных: {dtype}"}

    @staticmethod
    def opening(a, size=3):
        from skimage import morphology
        dtype = detect_data_type(a)

        if dtype == "empty":
            return {'error': True, 'result': "Не переданы данные для расчёта"}

        if dtype == "matrix_2d":
            return {'error': False, 'result': morphology.opening(a, morphology.disk(size))}
        if dtype == "matrix_3d":
            return {'error': False, 'result': morphology.opening(a, morphology.ball(size))}
        if dtype == "matrix_list_2d":
            return {'error': False, 'result': [morphology.opening(m, morphology.disk(size)) for m in a]}

        return {'error': True, 'result': f"Неподдерживаемый тип данных: {dtype}"}

    @staticmethod
    def closing(a, size=3):
        from skimage import morphology
        dtype = detect_data_type(a)

        if dtype == "empty":
            return {'error': True, 'result': "Не переданы данные для расчёта"}

        if dtype == "matrix_2d":
            return {'error': False, 'result': morphology.closing(a, morphology.disk(size))}
        if dtype == "matrix_3d":
            return {'error': False, 'result': morphology.closing(a, morphology.ball(size))}
        if dtype == "matrix_list_2d":
            return {'error': False, 'result': [morphology.closing(m, morphology.disk(size)) for m in a]}

        return {'error': True, 'result': f"Неподдерживаемый тип данных: {dtype}"}

    @staticmethod
    def tophat(a, size=3):
        from skimage import morphology
        dtype = detect_data_type(a)

        if dtype == "empty":
            return {'error': True, 'result': "Не переданы данные для расчёта"}

        if dtype == "matrix_2d":
            return {'error': False, 'result': morphology.white_tophat(a, morphology.disk(size))}
        if dtype == "matrix_3d":
            return {'error': False, 'result': morphology.white_tophat(a, morphology.ball(size))}
        if dtype == "matrix_list_2d":
            return {'error': False, 'result': [morphology.white_tophat(m, morphology.disk(size)) for m in a]}

        return {'error': True, 'result': f"Неподдерживаемый тип данных: {dtype}"}