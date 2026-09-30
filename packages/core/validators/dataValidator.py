import numpy as np


def detect_data_type(data):
    if data is None:
        return "empty"
    if isinstance(data, np.ndarray) and data.ndim == 2:
        return "matrix_2d"
    if isinstance(data, np.ndarray) and data.ndim == 3:
        return "matrix_3d"
    if isinstance(data, list) and all(isinstance(d, np.ndarray) and d.ndim == 2 for d in data):
        return "matrix_list_2d"
    if isinstance(data, list) and len(data) == 2:
        x, y = data
        if isinstance(x, (list, np.ndarray)) and isinstance(y, (list, np.ndarray)):
            return "spectrum"
    if isinstance(data, list) and all(isinstance(d, list) and len(d) == 2 for d in data):
        return "spectrum_list"
    if isinstance(data, (int, float, np.integer, np.floating)):
        return "number"
    if isinstance(data, list) and all(isinstance(d, (int, float)) for d in data):
        return "number_list"
    return f"unknown data type {type(data)}"