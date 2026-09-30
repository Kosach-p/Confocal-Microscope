import numpy as np

from packages.Floating_window.node_editor.nodes.node_import import *
from packages.Floating_window.NodeContentBuilder import NodeContentBuilder


class AvgAdvancedGraphicsNode(CalcGraphicsNode):
    def initSizes(self):
        super().initSizes()
        self.height = 145


class AvgAdvancedNode(CalcNode):
    icon = "Icon/image/avg_advanced.png"
    op_code = OP_NODE_AVG_ADVANCED
    op_title = "Продвинутое усреднение"
    inputs = [SOCKET_TYPES['spectrum']]
    outputs = [SOCKET_TYPES['spectrum']]
    GraphicsNode_class = AvgAdvancedGraphicsNode
    NodeContent_class = NodeContentBuilder

    def __init__(self, scene, MP):
        super().__init__(scene, MP)
        self.content.buildUI(node_functions=[
            {
                'name': 'Адаптивное скользящее',
                'params': [
                    {'name': 'Мин. окно',
                     'parameter_property': {'widget': 'DragNumberInput', 'step': 1, 'decimal': 0, 'min': 1,
                                            'max': 10, 'def': 3}},
                    {'name': 'Макс. окно',
                     'parameter_property': {'widget': 'DragNumberInput', 'step': 1, 'decimal': 0, 'min': 5,
                                            'max': 50, 'def': 15}}
                ],
                'inputs': SOCKET_TYPES['spectrum'],
                'outputs': SOCKET_TYPES['spectrum']
            },
            {
                'name': 'Фильтр Калмана',
                'params': [
                    {'name': 'Q',
                     'parameter_property': {'widget': 'DragNumberInput', 'step': 0.01, 'decimal': 2, 'min': 0.001,
                                            'max': 1.0, 'def': 0.01}},
                    {'name': 'R',
                     'parameter_property': {'widget': 'DragNumberInput', 'step': 0.01, 'decimal': 2, 'min': 0.001,
                                            'max': 1.0, 'def': 0.1}}
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

        if op_name == 'Адаптивное скользящее':
            min_w = int(params.get('Мин. окно', 3))
            max_w = int(params.get('Макс. окно', 15))
            self.MP.run_process(func=self.adaptive_moving, args=(a, min_w, max_w), callback=self.evalOperation_cplt)
        elif op_name == 'Фильтр Калмана':
            q = params.get('Q', 0.01)
            r = params.get('R', 0.1)
            self.MP.run_process(func=self.kalman, args=(a, q, r), callback=self.evalOperation_cplt)

    @staticmethod
    def adaptive_moving(a, min_w=3, max_w=15):
        def _proc(y):
            result = np.zeros_like(y, dtype=float)
            for i in range(len(y)):
                window = min_w
                for w in range(min_w, max_w + 1, 2):
                    start = max(0, i - w // 2)
                    end = min(len(y), i + w // 2 + 1)
                    if end - start < w:
                        break
                    window = w
                start = max(0, i - window // 2)
                end = min(len(y), i + window // 2 + 1)
                result[i] = np.mean(y[start:end])
            return result

        return apply_to_1data(a, _proc)

    @staticmethod
    def kalman(a, q=0.01, r=0.1):
        def _proc(y):
            n = len(y)
            result = np.zeros_like(y, dtype=float)
            P = 1.0
            x = y[0]
            for i in range(n):
                x_pred = x
                P_pred = P + q
                K = P_pred / (P_pred + r)
                x = x_pred + K * (y[i] - x_pred)
                P = (1 - K) * P_pred
                result[i] = x
            return result

        return apply_to_1data(a, _proc)