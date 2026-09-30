import numpy as np
from skimage import measure
from skimage.segmentation import clear_border
from skimage.morphology import remove_small_objects

from packages.Floating_window.node_editor.nodes.node_import import *
from packages.Floating_window.NodeContentBuilder import NodeContentBuilder


class ConnectedGraphicsNode(CalcGraphicsNode):
    def initSizes(self):
        super().initSizes()
        self.height = 145


class ConnectedNode(CalcNode):
    icon = "Icon/image/connected.png"
    op_code = OP_NODE_CONNECTED
    op_title = "Связанные компоненты"
    inputs = [SOCKET_TYPES['matrix_2d']]
    outputs = [SOCKET_TYPES['matrix_2d']]
    GraphicsNode_class = ConnectedGraphicsNode
    NodeContent_class = NodeContentBuilder

    def __init__(self, scene, MP):
        super().__init__(scene, MP)
        self.content.buildUI(node_functions=[
            {
                'name': 'Маркировка',
                'params': [
                    {'name': 'Порог',
                     'parameter_property': {'widget': 'DragNumberInput', 'step': 0.01, 'decimal': 3, 'min': 0.0,
                                            'max': 1.0, 'def': 0.0}},
                    {'name': 'Минимальный размер',
                     'parameter_property': {'widget': 'DragNumberInput', 'step': 0.01, 'decimal': 3, 'min': 0.0,
                                            'max': 1.0, 'def': 0.0}}
                ],
                'inputs': SOCKET_TYPES['matrix_2d'],
                'outputs': SOCKET_TYPES['matrix_2d']
            },
            {
                'name': 'Свойства регионов',
                'params': [
                    {'name': 'Свойство',
                     'parameter_property': {'widget': 'ComboBox',
                                            'items': ['Площадь', 'Периметр', 'Центроид X', 'Центроид Y',
                                                      'Эксцентриситет', 'Ориентация', 'Компактность',
                                                      'Диаметр эквивалента'],
                                            'def': 'Площадь'}},
                    {'name': 'Порог',
                     'parameter_property': {'widget': 'DragNumberInput', 'step': 0.01, 'decimal': 3, 'min': 0.0,
                                            'max': 1.0, 'def': 0.0}}
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

        if op_name == 'Маркировка':
            threshold = float(params.get('Порог', 0.0))
            min_size = int(params.get('Минимальный размер', 0))
            self.MP.run_process(func=self.label_regions, args=(a, threshold, min_size),
                                callback=self.evalOperation_cplt)
        elif op_name == 'Свойства регионов':
            prop_map = {
                'Площадь': 'area',
                'Периметр': 'perimeter',
                'Центроид X': 'centroid_x',
                'Центроид Y': 'centroid_y',
                'Эксцентриситет': 'eccentricity',
                'Ориентация': 'orientation',
                'Компактность': 'compactness',
                'Диаметр эквивалента': 'equivalent_diameter'
            }
            prop_name = prop_map.get(params.get('Свойство', 'Площадь'), 'area')
            threshold = float(params.get('Порог', 0.0))
            self.MP.run_process(func=self.region_properties, args=(a, prop_name, threshold),
                                callback=self.evalOperation_cplt)

    @staticmethod
    def label_regions(a, threshold=0.0, min_size=0):
        dtype = detect_data_type(a)
        if dtype == "empty":
            return {'error': True, 'result': "Не переданы данные для расчёта"}
        if dtype == "matrix_2d":
            # Нормализация данных в диапазон [0, 1]
            a_min = a.min()
            a_max = a.max()
            if a_max > a_min:
                a_normalized = (a - a_min) / (a_max - a_min)
            else:
                a_normalized = np.zeros_like(a)

            # Пороговая обработка на нормализованных данных
            binary = a_normalized > threshold

            # Нормализация min_size: преобразуем относительный размер в абсолютный
            if min_size > 0:
                total_pixels = a.size
                absolute_min_size = int(min_size * total_pixels)
                binary = remove_small_objects(binary, min_size=absolute_min_size)

            # Маркировка областей
            labels = measure.label(binary, connectivity=2)
            return {'error': False, 'result': labels.astype(np.float64)}

        if dtype == "matrix_list_2d":
            return {'error': False, 'result': [ConnectedNode.label_regions(m, threshold, min_size) for m in a]}
        return {'error': True, 'result': f"Неподдерживаемый тип данных: {dtype}"}

    @staticmethod
    def region_properties(a, prop_name='area', threshold=0.0):
        dtype = detect_data_type(a)
        if dtype == "empty":
            return {'error': True, 'result': "Не переданы данные для расчёта"}
        if dtype == "matrix_2d":
            # Нормализация данных в диапазон [0, 1]
            a_min = a.min()
            a_max = a.max()
            if a_max > a_min:
                a_normalized = (a - a_min) / (a_max - a_min)
            else:
                a_normalized = np.zeros_like(a)

            # Пороговая обработка на нормализованных данных
            binary = a_normalized > threshold

            labels = measure.label(binary, connectivity=2)
            props = measure.regionprops(labels)

            result = np.zeros_like(a, dtype=float)

            if prop_name == 'centroid_x':
                for p in props:
                    result[labels == p.label] = p.centroid[1]
            elif prop_name == 'centroid_y':
                for p in props:
                    result[labels == p.label] = p.centroid[0]
            elif prop_name == 'compactness':
                for p in props:
                    if p.perimeter > 0:
                        compactness = (4 * np.pi * p.area) / (p.perimeter ** 2)
                        result[labels == p.label] = compactness
                    else:
                        result[labels == p.label] = 1.0
            elif prop_name == 'area':
                # Нормализуем площадь относительно общего размера
                total_pixels = a.size
                for p in props:
                    normalized_area = p.area / total_pixels
                    result[labels == p.label] = normalized_area
            else:
                for p in props:
                    value = getattr(p, prop_name)
                    result[labels == p.label] = value

            return {'error': False, 'result': result}

        if dtype == "matrix_list_2d":
            return {'error': False, 'result': [ConnectedNode.region_properties(m, prop_name, threshold) for m in a]}
        return {'error': True, 'result': f"Неподдерживаемый тип данных: {dtype}"}