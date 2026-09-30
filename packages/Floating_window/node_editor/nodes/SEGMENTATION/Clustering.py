import numpy as np
from sklearn.cluster import KMeans

from packages.Floating_window.node_editor.nodes.node_import import *
from packages.Floating_window.NodeContentBuilder import NodeContentBuilder
from sklearn.cluster import DBSCAN
from scipy import ndimage
from skimage.segmentation import watershed
from skimage.feature import peak_local_max


class ClusteringGraphicsNode(CalcGraphicsNode):
    def initSizes(self):
        super().initSizes()
        self.height = 145


class ClusteringNode(CalcNode):
    icon = "Icon/image/clustering.png"
    op_code = OP_NODE_CLUSTERING
    op_title = "Кластеризация"
    inputs = [SOCKET_TYPES['matrix_2d']]
    outputs = [SOCKET_TYPES['matrix_2d']]
    GraphicsNode_class = ClusteringGraphicsNode
    NodeContent_class = NodeContentBuilder

    def __init__(self, scene, MP):
        super().__init__(scene, MP)
        # В buildUI добавляем:
        self.content.buildUI(node_functions=[
            {
                'name': 'K-Means',
                'params': [
                    {'name': 'Кластеры',
                     'parameter_property': {'widget': 'DragNumberInput', 'step': 1, 'decimal': 0, 'min': 1,
                                            'max': 100, 'def': 3}}
                ],
                'inputs': SOCKET_TYPES['matrix_2d'],
                'outputs': SOCKET_TYPES['matrix_2d']
            },
            {
                'name': 'Watershed',
                'params': [
                    {'name': 'min_distance',
                     'parameter_property': {'widget': 'DragNumberInput', 'step': 1, 'decimal': 0, 'min': 1,
                                            'max': 100, 'def': 10}},
                    {'name': 'threshold_rel',
                     'parameter_property': {'widget': 'DragNumberInput', 'step': 0.01, 'decimal': 2, 'min': 0.0,
                                            'max': 1.0, 'def': 0.3}}
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

        if op_name == 'K-Means':
            n_clusters = int(params.get('Кластеры', 3))
            self.MP.run_process(func=self.kmeans, args=(a, n_clusters), callback=self.evalOperation_cplt)
        elif op_name == 'Watershed':
            min_distance = int(params.get('min_distance', 10))
            threshold_rel = float(params.get('threshold_rel', 0.3))
            self.MP.run_process(func=self.watershed_segmentation, args=(a, min_distance, threshold_rel),
                                callback=self.evalOperation_cplt)

    @staticmethod
    def kmeans(a, n_clusters=3):
        dtype = detect_data_type(a)

        if dtype == "empty":
            return {'error': True, 'result': "Не переданы данные для расчёта"}

        if dtype == "matrix_2d":
            pixels = a.reshape(-1, 1)
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            labels = kmeans.fit_predict(pixels)
            return {'error': False, 'result': labels.reshape(a.shape)}

        if dtype == "matrix_3d":
            pixels = a.reshape(-1, 1)
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            labels = kmeans.fit_predict(pixels)
            return {'error': False, 'result': labels.reshape(a.shape)}

        if dtype == "matrix_list_2d":
            return {'error': False, 'result': [ClusteringNode.kmeans(m, n_clusters) for m in a]}

        if dtype == "matrix_list_3d":
            return {'error': False, 'result': [ClusteringNode.kmeans(m, n_clusters) for m in a]}

        return {'error': True, 'result': f"Неподдерживаемый тип данных: {dtype}"}

    @staticmethod
    def watershed_segmentation(a, min_distance=10, threshold_rel=0.3):
        dtype = detect_data_type(a)

        if dtype == "empty":
            return {'error': True, 'result': "Не переданы данные для расчёта"}

        if dtype == "matrix_2d":
            # Нормализация данных
            a_min, a_max = a.min(), a.max()
            if a_max > a_min:
                a_normalized = (a - a_min) / (a_max - a_min)
            else:
                a_normalized = np.zeros_like(a)

            # Создаём маску объектов
            mask = a_normalized > threshold_rel

            if mask.sum() == 0:
                return {'error': False, 'result': np.zeros_like(a, dtype=int)}

            # Вычисляем карту расстояний
            distance = ndimage.distance_transform_edt(mask)

            # Находим локальные максимумы как маркеры
            coordinates = peak_local_max(
                distance,
                min_distance=min_distance,
                labels=mask
            )

            if len(coordinates) == 0:
                return {'error': False, 'result': mask.astype(int)}

            # Создаём маркеры
            markers = np.zeros_like(a, dtype=int)
            for i, coord in enumerate(coordinates, 1):
                markers[coord[0], coord[1]] = i

            # Применяем watershed
            labels = watershed(-a_normalized, markers, mask=mask)

            return {'error': False, 'result': labels}

        if dtype == "matrix_list_2d":
            return {'error': False,
                    'result': [ClusteringNode.watershed_segmentation(m, min_distance, threshold_rel) for m in a]}
        return {'error': True, 'result': f"Неподдерживаемый тип данных: {dtype}"}
