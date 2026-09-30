from packages.Floating_window.node_editor.calc_conf import *
from packages.Floating_window.node_editor.calc_node_base import CalcNode
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from nodeeditor.node_content_widget import QDMNodeContentWidget
from nodeeditor.node_graphics_node import QDMGraphicsNode

import numpy as np
from scipy.ndimage import gaussian_filter, median_filter, sobel, laplace
from Icon.IconName import *

from packages.core.validators.dataValidator import detect_data_type
from packages.core.widgets.ComboBox import CustomComboBox, upgradeComboBox
from packages.core.widgets.SpinBox import CustomSpinBox, CustomDoubleSpinBox
from packages.Floating_window.node_editor.NodeRegistry import NodeRegistry
import PyQt6.sip as sip
from qtpy.QtWidgets import QVBoxLayout, QComboBox, QFrame, QLabel, QHBoxLayout
from qtpy.QtCore import Qt
from qtpy.QtGui import QFont
from packages.Floating_window.node_editor.calc_node_base import CalcGraphicsNode

from scipy.signal import convolve, deconvolve
from skimage.restoration import wiener, richardson_lucy

# Для Denoising
from skimage.restoration import denoise_nl_means, denoise_wavelet

# Для Edge
from skimage.filters import sobel, prewitt, laplace
from skimage.feature import canny

# Для Morphology
from scipy.ndimage import binary_erosion, binary_dilation, binary_opening, binary_closing, grey_erosion, grey_dilation, grey_opening, grey_closing

# Для Frequency
from scipy.fft import fft, ifft, fft2, ifft2, fftfreq
from scipy.signal import butter, filtfilt, freqz


def apply_to_2_data(a, b, func, **kwargs):
    """Применяет func(a, b, **kwargs) ко всем поддерживаемым типам данных"""
    dtype_a = detect_data_type(a)
    dtype_b = detect_data_type(b)

    if dtype_a == "empty" or dtype_b == "empty":
        return {'error': True, 'result': "Не переданы данные для расчёта"}

    # Оба — матрицы
    if dtype_a in ("matrix_2d", "matrix_3d") and dtype_b in ("matrix_2d", "matrix_3d"):
        return {'error': False, 'result': func(a, b, **kwargs)}

    # Матрица + число
    if dtype_a in ("matrix_2d", "matrix_3d") and dtype_b == "number":
        return {'error': False, 'result': func(a, b, **kwargs)}
    if dtype_a == "number" and dtype_b in ("matrix_2d", "matrix_3d"):
        return {'error': False, 'result': func(a, b, **kwargs)}

    # Список матриц + число
    if dtype_a == "matrix_list_2d" and dtype_b == "number":
        data_3d = np.stack(a)
        result = func(data_3d, b)
        return {'error': False, 'result': [result[i] for i in range(result.shape[0])]}
    if dtype_a == "number" and dtype_b == "matrix_list_2d":
        data_3d = np.stack(b)
        result = func(a, data_3d)
        return {'error': False, 'result': [result[i] for i in range(result.shape[0])]}

    # Два списка матриц одинаковой длины
    if dtype_a == "matrix_list_2d" and dtype_b == "matrix_list_2d":
        if len(a) != len(b):
            return {'error': True, 'result': f"Разная длина списков: {len(a)} vs {len(b)}"}
        return {'error': False, 'result': [func(a[i], b[i]) for i in range(len(a))]}

    # Список матриц + матрица 3D
    if dtype_a == "matrix_list_2d" and dtype_b == "matrix_3d":
        data_3d = np.stack(a)
        result = func(data_3d, b)
        return {'error': False, 'result': [result[i] for i in range(result.shape[0])]}
    if dtype_a == "matrix_3d" and dtype_b == "matrix_list_2d":
        data_3d = np.stack(b)
        result = func(a, data_3d)
        return {'error': False, 'result': [result[i] for i in range(result.shape[0])]}

    # Спектр + спектр
    if dtype_a == "spectrum" and dtype_b == "spectrum":
        x1, y1 = a
        x2, y2 = b
        return {'error': False, 'result': [x1, func(y1, y2)]}

    # Спектр + число
    if dtype_a == "spectrum" and dtype_b == "number":
        x, y = a
        return {'error': False, 'result': [x, func(y, b)]}
    if dtype_a == "number" and dtype_b == "spectrum":
        x, y = b
        return {'error': False, 'result': [x, func(a, y)]}

    # Список спектров + спектр
    if dtype_a == "spectrum_list" and dtype_b == "spectrum":
        _, y2 = b
        return {'error': False, 'result': [[x, func(y, y2)] for x, y in a]}
    if dtype_a == "spectrum" and dtype_b == "spectrum_list":
        _, y1 = a
        return {'error': False, 'result': [[x, func(y1, y)] for x, y in b]}

    # Список спектров + число
    if dtype_a == "spectrum_list" and dtype_b == "number":
        return {'error': False, 'result': [[x, func(y, b)] for x, y in a]}
    if dtype_a == "number" and dtype_b == "spectrum_list":
        return {'error': False, 'result': [[x, func(a, y)] for x, y in b]}

    # Два списка спектров одинаковой длины
    if dtype_a == "spectrum_list" and dtype_b == "spectrum_list":
        if len(a) != len(b):
            return {'error': True, 'result': f"Разная длина списков: {len(a)} vs {len(b)}"}
        return {'error': False, 'result': [[x1, func(y1, y2)] for (x1, y1), (_, y2) in zip(a, b)]}

    # Число + число
    if dtype_a == "number" and dtype_b == "number":
        return {'error': False, 'result': func(a, b, **kwargs)}

    # Число + список чисел
    if dtype_a == "number" and dtype_b == "number_list":
        return {'error': False, 'result': func(a, np.array(b)).tolist()}
    if dtype_a == "number_list" and dtype_b == "number":
        return {'error': False, 'result': func(np.array(a), b).tolist()}

    # список чисел + список чисел
    if dtype_a == "number_list" and dtype_b == "number_list":
        return {'error': False, 'result': func(np.array(a), np.array(b)).tolist()}

    return {'error': True, 'result': f"math: неподдерживаемая пара типов {dtype_a} + {dtype_b}"}

def apply_to_1data(a, func):
    """Применяет func(a) ко всем типам данных"""
    dtype = detect_data_type(a)
    if dtype == "empty":
        return {'error': True, 'result': "Не переданы данные для расчёта"}
    if dtype in ("matrix_2d", "matrix_3d"):
        return {'error': False, 'result': func(a)}
    if dtype == "matrix_list_2d":
        data_3d = np.stack(a)
        result = func(data_3d)

        if result.ndim == 0:
            return {'error': False, 'result': result.item()}

        return {'error': False, 'result': [result[i] for i in range(result.shape[0])]}
    if dtype == "spectrum":
        x, y = a
        result = func(y)
        if np.isscalar(result) or (isinstance(result, np.ndarray) and result.ndim == 0):
            return result.item() if hasattr(result, 'item') else result
        return {'error': False, 'result': [x, result]}

    if dtype == "spectrum_list":
        first_x, first_y = a[0]
        first_result = func(first_y)

        if np.isscalar(first_result) or (isinstance(first_result, np.ndarray) and first_result.ndim == 0):
            return {'error': False, 'result': [func(y).item() if hasattr(func(y), 'item') else func(y) for x, y in a]}
        return [[x, func(y)] for x, y in a]
    if dtype == "number":
        return {'error': False, 'result': func(np.array([a]))[0]}
    if dtype == "number_list":
        return {'error': False, 'result': func(np.array(a)).tolist()}

    return {'error': True, 'result': f"math: неподдерживаемый тип {dtype}"}
