from skimage import filters

from packages.Floating_window.node_editor.nodes.node_import import *
from packages.Floating_window.NodeContentBuilder import NodeContentBuilder


class EdgeGraphicsNode(CalcGraphicsNode):
    def initSizes(self):
        super().initSizes()
        self.height = 145


class EdgeNode(CalcNode):
    icon = "Icon/image/edge.png"
    op_code = OP_NODE_EDGE
    op_title = "Границы"
    inputs = [SOCKET_TYPES['matrix_2d']]
    outputs = [SOCKET_TYPES['matrix_2d']]
    GraphicsNode_class = EdgeGraphicsNode
    NodeContent_class = NodeContentBuilder

    def __init__(self, scene, MP):
        super().__init__(scene, MP)
        self.content.buildUI(node_functions=[
            {
                'name': 'Собель',
                'params': [],
                'inputs': SOCKET_TYPES['matrix_2d'],
                'outputs': SOCKET_TYPES['matrix_2d']
            },
            {
                'name': 'Прюитт',
                'params': [],
                'inputs': SOCKET_TYPES['matrix_2d'],
                'outputs': SOCKET_TYPES['matrix_2d']
            },
            {
                'name': 'Лапласиан',
                'params': [],
                'inputs': SOCKET_TYPES['matrix_2d'],
                'outputs': SOCKET_TYPES['matrix_2d']
            },
            {
                'name': 'Фарид',
                'params': [],
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
        if op_name == 'Собель':
            self.MP.run_process(func=self.sobel, args=(a,), callback=self.evalOperation_cplt)
        elif op_name == 'Прюитт':
            self.MP.run_process(func=self.prewitt, args=(a,), callback=self.evalOperation_cplt)
        elif op_name == 'Лапласиан':
            self.MP.run_process(func=self.laplacian, args=(a,), callback=self.evalOperation_cplt)
        elif op_name == 'Фарид':
            self.MP.run_process(func=self.farid, args=(a,), callback=self.evalOperation_cplt)

    @staticmethod
    def sobel(a):
        return apply_to_1data(a, filters.sobel)

    @staticmethod
    def prewitt(a):
        return apply_to_1data(a, filters.prewitt)

    @staticmethod
    def laplacian(a):
        return apply_to_1data(a, filters.laplace)

    @staticmethod
    def farid(a):
        return apply_to_1data(a, filters.farid)
