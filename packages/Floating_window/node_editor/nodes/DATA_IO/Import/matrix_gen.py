from packages.Floating_window.node_editor.nodes.node_import import *
from packages.Floating_window.NodeContentBuilder import NodeContentBuilder


class FormulaGeneratorGraphicsNode(CalcGraphicsNode):
    def initSizes(self):
        super().initSizes()
        self.height = 470


class FormulaGeneratorNode(CalcNode):
    icon = "Icon/image/formula.png"
    op_code = OP_NODE_FORMULA_GENERATOR
    op_title = "Генератор по формуле"
    inputs = []
    outputs = [SOCKET_TYPES['matrix_3d']]
    GraphicsNode_class = FormulaGeneratorGraphicsNode
    NodeContent_class = NodeContentBuilder

    def __init__(self, scene, MP):
        super().__init__(scene, MP)
        self.content.buildUI(node_functions=[
            {
                'name': 'Формула',
                'params': [
                    {'name': 'Функция f(x,y,z):',
                     'parameter_property': {'widget': 'QLabel'}},
                    {'name': 'Формула',
                     'parameter_property': {'widget': 'QPlainTextEdit', 'height': 100}},
                    {'name': 'Размеры:',
                     'parameter_property': {'widget': 'QLabel'}},
                    {'name': 'X',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 1, 'decimal': 0, 'min': 1,
                                            'max': 4096, 'def': 128}},
                    {'name': 'Y',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 1, 'decimal': 0, 'min': 1,
                                            'max': 4096, 'def': 128}},
                    {'name': 'Z',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 1, 'decimal': 0, 'min': 1,
                                            'max': 4096, 'def': 128}},
                    {'name': 'Диапазоны:',
                     'parameter_property': {'widget': 'QLabel'}},
                    {'name': 'X мин',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 0.1, 'decimal': 2, 'min': -1000,
                                            'max': 1000, 'def': -5.0}},
                    {'name': 'X макс',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 0.1, 'decimal': 2, 'min': -1000,
                                            'max': 1000, 'def': 5.0}},
                    {'name': 'Y мин',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 0.1, 'decimal': 2, 'min': -1000,
                                            'max': 1000, 'def': -5.0}},
                    {'name': 'Y макс',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 0.1, 'decimal': 2, 'min': -1000,
                                            'max': 1000, 'def': 5.0}},
                    {'name': 'Z мин',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 0.1, 'decimal': 2, 'min': -1000,
                                            'max': 1000, 'def': -5.0}},
                    {'name': 'Z макс',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 0.1, 'decimal': 2, 'min': -1000,
                                            'max': 1000, 'def': 5.0}}
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

        if op_name == 'Формула':
            formula = params.get('Формула', 'sin(x/2) * cos(y/2) * sin(z/2)')
            size_x = int(params.get('X', 128))
            size_y = int(params.get('Y', 128))
            size_z = int(params.get('Z', 128))
            x_min = float(params.get('X мин', -5.0))
            x_max = float(params.get('X макс', 5.0))
            y_min = float(params.get('Y мин', -5.0))
            y_max = float(params.get('Y макс', 5.0))
            z_min = float(params.get('Z мин', -5.0))
            z_max = float(params.get('Z макс', 5.0))
            self.MP.run_process(func=self.generate_formula,
                                args=(formula, size_x, size_y, size_z, x_min, x_max, y_min, y_max, z_min, z_max),
                                callback=self.evalOperation_cplt)

    @staticmethod
    def generate_formula(formula, size_x, size_y, size_z, x_min, x_max, y_min, y_max, z_min, z_max):
        x = np.linspace(x_min, x_max, size_x)
        y = np.linspace(y_min, y_max, size_y)
        z = np.linspace(z_min, z_max, size_z)
        X, Y, Z = np.meshgrid(z, x, y, indexing='ij')

        namespace = {
            'x': Y,
            'y': Z,
            'z': X,
            'sin': np.sin,
            'cos': np.cos,
            'tan': np.tan,
            'exp': np.exp,
            'log': np.log,
            'sqrt': np.sqrt,
            'pi': np.pi,
            'abs': np.abs,
            'arcsin': np.arcsin,
            'arccos': np.arccos,
            'arctan': np.arctan,
            'sinh': np.sinh,
            'cosh': np.cosh,
            'tanh': np.tanh
        }

        try:
            result = eval(formula, {"__builtins__": {}}, namespace)
            return {'error': False, 'result': np.array(result, dtype=float)}
        except Exception as e:
            return {'error': True, 'result': f"Ошибка вычисления формулы: {str(e)}"}





























