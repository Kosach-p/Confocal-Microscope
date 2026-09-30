import numpy as np
from sklearn.cluster import KMeans

from packages.Floating_window.node_editor.nodes.node_import import *
from packages.Floating_window.NodeContentBuilder import NodeContentBuilder
from sklearn.cluster import DBSCAN
from scipy import ndimage
from skimage.segmentation import watershed
from skimage.feature import peak_local_max
import packages.core.math.NV_Calc.simulate_TStrength_NV_ensemble as simnv


class ClusteringGraphicsNode(CalcGraphicsNode):
    def initSizes(self):
        super().initSizes()
        self.height = 145


class NV_ODMR_Node(CalcNode):
    icon = "Icon/image/NV_ODMR.png"
    op_code = OP_NODE_NV_ODMR
    op_title = "Спектр ОДМР NV центров алмаза"
    inputs = []
    outputs = [SOCKET_TYPES['spectrum']]
    GraphicsNode_class = ClusteringGraphicsNode
    NodeContent_class = NodeContentBuilder

    def __init__(self, scene, MP):
        super().__init__(scene, MP)
        # В buildUI добавляем:
        self.content.buildUI(node_functions=[
            {
                'name': 'Ансамбль NV-VN центров',
                'params': [
                    {'name': 'Частота СВЧ', 'parameter_property': {'widget': 'QLabel'}},
                    {'name': 'Левая граница, МГц:', 'parameter_property': {'widget': 'QLabel'}},
                    {'name': 'MWf_left', 'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 1,
                                                                     'decimal': 3, 'def': 2850,
                                                                     'min': 0, 'max': 2147483647}},
                    {'name': 'Правая граница, МГц:', 'parameter_property': {'widget': 'QLabel'}},
                    {'name': 'MWf_right', 'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 1,
                                                                      'decimal': 3, 'def': 2890,
                                                                      'min': 0, 'max': 2147483647}},
                    {'name': 'Шаг частоты, МГц:', 'parameter_property': {'widget': 'QLabel'}},
                    {'name': 'MWf_step', 'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 0.1,
                                                                     'decimal': 6, 'def': 1,
                                                                     'min': 0, 'max': 2147483647}},
                    {'name': 'thetaMW',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 0.01, 'decimal': 3, 'def': 0,
                                            'min': 0, 'max': np.pi}},
                    {'name': 'phiMW',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 0.01, 'decimal': 3, 'def': 0,
                                            'min': 0, 'max': 2*np.pi}},
                    {'name': 'B0',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 0.01, 'decimal': 3, 'def': 0}},
                    {'name': 'thetaB',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 0.01, 'decimal': 3, 'def': 0, 'min': 0,
                                            'max': np.pi}},
                    {'name': 'phiB',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 0.01, 'decimal': 3, 'def': 0, 'min': 0,
                                            'max': 2*np.pi}},
                    {'name': 'E0',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 1, 'decimal': 3, 'def': 0}},
                    {'name': 'thetaE',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 0.01, 'decimal': 3, 'def': 0, 'min': 0,
                                            'max': np.pi}},
                    {'name': 'phiE',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 0.01, 'decimal': 3, 'def': 0, 'min': 0,
                                            'max': 2*np.pi}},
                    {'name': 'Linewidth',
                     'parameter_property': {'widget': 'DragButtonNumberInput', 'step': 0.1, 'decimal': 2, 'def': 1,
                                            'min': 0, 'max': 2147483647}}
                ],
                'inputs': SOCKET_TYPES['matrix_2d'],
                'outputs': SOCKET_TYPES['matrix_2d']
            }
        ])
        self.MP = MP

    def evalOperation(self, input_values):
        super().evalOperation(input_values)

        op_name = self.content.get_func()
        params = self.content.get_params()

        if op_name == 'Ансамбль NV-VN центров':
            print("Мы тут были")
            print(params)
            self.MP.run_process(func=self.ESR_NV_VN, args=(params,), callback=self.evalOperation_cplt)

    @staticmethod
    def ESR_NV_VN(params):
        MWfreq = np.arange(params.get('MWf_left'), params.get('MWf_right'), params.get('MWf_step'))
        thetaB_lab, phiB_lab = simnv.transform_spherical_nv_to_lab_frame(params.get('thetaB'), params.get('phiB'))
        thetaE_lab, phiE_lab = simnv.transform_spherical_nv_to_lab_frame(params.get('thetaE'), params.get('phiE'))
        spec_model = simnv.ESR_NV_VN_ensemble(
            MWfreq, params.get('thetaMW'), params.get('phiMW'), params.get('B0'), thetaB_lab, phiB_lab,
            params.get('E0'), thetaE_lab, phiE_lab, params.get('Linewidth')
        )
        return {'error': False, 'result': [MWfreq, -spec_model]}
