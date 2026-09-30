from packages.Floating_window.node_editor.nodes.node_import import *
from packages.Floating_window.NodeContentBuilder import NodeContentBuilder


class NoiseGeneratorGraphicsNode(CalcGraphicsNode):
    def initSizes(self):
        super().initSizes()
        self.height = 280


class NoiseGeneratorNode(CalcNode):
    icon = "Icon/image/noise.png"
    op_code = OP_NODE_NOISE_GENERATOR
    op_title = "Генератор шума"
    inputs = []
    outputs = [SOCKET_TYPES['matrix_3d']]
    GraphicsNode_class = NoiseGeneratorGraphicsNode
    NodeContent_class = NodeContentBuilder

    def __init__(self, scene, MP):
        super().__init__(scene, MP)
        self.content.buildUI(node_functions=[
            {
                'name': 'Гауссов шум',
                'params': [
                    {'name': 'Размеры:',
                     'parameter_property': {'widget': 'QLabel'}},
                    {'name': 'X',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 1, 'decimal': 0, 'min': 1,
                                            'max': 4096, 'def': 256}},
                    {'name': 'Y',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 1, 'decimal': 0, 'min': 1,
                                            'max': 4096, 'def': 256}},
                    {'name': 'Z',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 1, 'decimal': 0, 'min': 1,
                                            'max': 4096, 'def': 64}},
                    {'name': 'Параметры генерации:',
                     'parameter_property': {'widget': 'QLabel'}},

                    {'name': 'Интенсивность',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 0.01, 'decimal': 3, 'min': 0.001,
                                            'max': 10.0, 'def': 0.1}},
                    {'name': 'Сид',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 1, 'decimal': 0, 'min': 0,
                                            'max': 999999, 'def': 42}}
                ],
                'inputs': [],
                'outputs': SOCKET_TYPES['matrix_3d']
            },
            {
                'name': 'Пуассонов шум',
                'params': [
                    {'name': 'Размеры:',
                     'parameter_property': {'widget': 'QLabel'}},
                    {'name': 'X',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 1, 'decimal': 0, 'min': 1,
                                            'max': 4096, 'def': 256}},
                    {'name': 'Y',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 1, 'decimal': 0, 'min': 1,
                                            'max': 4096, 'def': 256}},
                    {'name': 'Z',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 1, 'decimal': 0, 'min': 1,
                                            'max': 4096, 'def': 64}},
                    {'name': 'Параметры генерации:',
                     'parameter_property': {'widget': 'QLabel'}},
                    {'name': 'Интенсивность',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 0.01, 'decimal': 3, 'min': 0.001,
                                            'max': 10.0, 'def': 0.1}},
                    {'name': 'Сид',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 1, 'decimal': 0, 'min': 0,
                                            'max': 999999, 'def': 42}}
                ],
                'inputs': [],
                'outputs': SOCKET_TYPES['matrix_3d']
            },
            {
                'name': 'Соль и перец',
                'params': [
                    {'name': 'Размеры:',
                     'parameter_property': {'widget': 'QLabel'}},
                    {'name': 'X',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 1, 'decimal': 0, 'min': 1,
                                            'max': 4096, 'def': 256}},
                    {'name': 'Y',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 1, 'decimal': 0, 'min': 1,
                                            'max': 4096, 'def': 256}},
                    {'name': 'Z',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 1, 'decimal': 0, 'min': 1,
                                            'max': 4096, 'def': 64}},
                    {'name': 'Параметры генерации:',
                     'parameter_property': {'widget': 'QLabel'}},
                    {'name': 'Интенсивность',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 0.01, 'decimal': 3, 'min': 0.001,
                                            'max': 1.0, 'def': 0.05}},
                    {'name': 'Сид',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 1, 'decimal': 0, 'min': 0,
                                            'max': 999999, 'def': 42}}
                ],
                'inputs': [],
                'outputs': SOCKET_TYPES['matrix_3d']
            },
            {
                'name': 'Спекл шум',
                'params': [
                    {'name': 'Размеры:',
                     'parameter_property': {'widget': 'QLabel'}},
                    {'name': 'X',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 1, 'decimal': 0, 'min': 1,
                                            'max': 4096, 'def': 256}},
                    {'name': 'Y',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 1, 'decimal': 0, 'min': 1,
                                            'max': 4096, 'def': 256}},
                    {'name': 'Z',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 1, 'decimal': 0, 'min': 1,
                                            'max': 4096, 'def': 64}},
                    {'name': 'Параметры генерации:',
                     'parameter_property': {'widget': 'QLabel'}},
                    {'name': 'Интенсивность',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 0.01, 'decimal': 3, 'min': 0.001,
                                            'max': 10.0, 'def': 0.1}},
                    {'name': 'Сид',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 1, 'decimal': 0, 'min': 0,
                                            'max': 999999, 'def': 42}}
                ],
                'inputs': [],
                'outputs': SOCKET_TYPES['matrix_3d']
            },
            {
                'name': 'Равномерный шум',
                'params': [
                    {'name': 'Размеры:',
                     'parameter_property': {'widget': 'QLabel'}},
                    {'name': 'X',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 1, 'decimal': 0, 'min': 1,
                                            'max': 4096, 'def': 256}},
                    {'name': 'Y',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 1, 'decimal': 0, 'min': 1,
                                            'max': 4096, 'def': 256}},
                    {'name': 'Z',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 1, 'decimal': 0, 'min': 1,
                                            'max': 4096, 'def': 64}},
                    {'name': 'Параметры генерации:',
                     'parameter_property': {'widget': 'QLabel'}},
                    {'name': 'Интенсивность',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 0.01, 'decimal': 3, 'min': 0.001,
                                            'max': 10.0, 'def': 0.1}},
                    {'name': 'Сид',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 1, 'decimal': 0, 'min': 0,
                                            'max': 999999, 'def': 42}}
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

        if op_name == 'Гауссов шум':
            size_x = int(params.get('X', 256))
            size_y = int(params.get('Y', 256))
            size_z = int(params.get('Z', 64))
            intensity = float(params.get('Интенсивность', 0.1))
            seed = int(params.get('Сид', 42))
            self.MP.run_process(func=self.generate_noise,
                                args=('Гауссов', size_x, size_y, size_z, intensity, seed),
                                callback=self.evalOperation_cplt)
        elif op_name == 'Пуассонов шум':
            size_x = int(params.get('X', 256))
            size_y = int(params.get('Y', 256))
            size_z = int(params.get('Z', 64))
            intensity = float(params.get('Интенсивность', 0.1))
            seed = int(params.get('Сид', 42))
            self.MP.run_process(func=self.generate_noise,
                                args=('Пуассонов', size_x, size_y, size_z, intensity, seed),
                                callback=self.evalOperation_cplt)
        elif op_name == 'Соль и перец':
            size_x = int(params.get('X', 256))
            size_y = int(params.get('Y', 256))
            size_z = int(params.get('Z', 64))
            intensity = float(params.get('Интенсивность', 0.05))
            seed = int(params.get('Сид', 42))
            self.MP.run_process(func=self.generate_noise,
                                args=('Соль и перец', size_x, size_y, size_z, intensity, seed),
                                callback=self.evalOperation_cplt)
        elif op_name == 'Спекл шум':
            size_x = int(params.get('X', 256))
            size_y = int(params.get('Y', 256))
            size_z = int(params.get('Z', 64))
            intensity = float(params.get('Интенсивность', 0.1))
            seed = int(params.get('Сид', 42))
            self.MP.run_process(func=self.generate_noise,
                                args=('Спекл', size_x, size_y, size_z, intensity, seed),
                                callback=self.evalOperation_cplt)
        elif op_name == 'Равномерный шум':
            size_x = int(params.get('X', 256))
            size_y = int(params.get('Y', 256))
            size_z = int(params.get('Z', 64))
            intensity = float(params.get('Интенсивность', 0.1))
            seed = int(params.get('Сид', 42))
            self.MP.run_process(func=self.generate_noise,
                                args=('Равномерный', size_x, size_y, size_z, intensity, seed),
                                callback=self.evalOperation_cplt)

    @staticmethod
    def generate_noise(noise_type, size_x, size_y, size_z, intensity, seed=42):
        np.random.seed(seed)
        shape = (size_z, size_y, size_x)

        if noise_type == 'Гауссов':
            return {'error': False, 'result': np.random.normal(0, intensity, shape)}
        elif noise_type == 'Пуассонов':
            return {'error': False, 'result': np.random.poisson(intensity * 100, shape).astype(float) / 100.0}
        elif noise_type == 'Соль и перец':
            result = np.zeros(shape)
            n_pixels = int(size_x * size_y * size_z * intensity)
            for _ in range(n_pixels):
                z = np.random.randint(0, size_z)
                y = np.random.randint(0, size_y)
                x = np.random.randint(0, size_x)
                result[z, y, x] = 1.0 if np.random.random() > 0.5 else -1.0
            return {'error': False, 'result': result}
        elif noise_type == 'Спекл':
            return {'error': False, 'result': np.random.gamma(1, intensity, shape)}
        elif noise_type == 'Равномерный':
            return {'error': False, 'result': np.random.uniform(-intensity, intensity, shape)}
        return {'error': True, 'result': f"Неизвестный тип шума: {noise_type}"}