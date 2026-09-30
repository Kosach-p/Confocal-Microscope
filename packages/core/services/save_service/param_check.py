import re
from typing import Dict, Any, Optional
from packages.core.math.timeGen import *

# Дефолтные значения для матрицы
DEFAULT_MATRIX_PARAMS = {
    'x1': 0,
    'y1': 0,
    'z1': 0,
    'x2': 100,
    'y2': 100,
    'z2': 0,
    'step_x': 100,
    'step_y': 100,
    'step_z': 1,
    'accum_time': 100,
    'Np_x': 100,
    'Np_y': 100,
    'Np_z': 1,
    'Np_slice': 10000,
    'Np_total': 10000
}

# Дефолтные значения для спектра
DEFAULT_SPECTRUM_PARAMS = {
    'start_nm': 300.0,
    'end_nm': 1000.0,
    'step_nm': 1.0,
    'accum_time_ms': 100,
    'number_repetitions': 1,
    'data_points': 0
}


def _find_key_by_pattern(data: Dict[str, Any], patterns: list) -> Optional[str]:
    """
    Ищет ключ в словаре по паттернам (регистронезависимо).
    patterns - список строк, которые должны содержаться в ключе.
    """
    for key in data.keys():
        key_lower = str(key).lower()
        if all(pattern.lower() in key_lower for pattern in patterns):
            return key
    return None


def _extract_value(data: Dict[str, Any], patterns: list, default: Any) -> Any:
    """Извлекает значение по паттернам или возвращает дефолтное."""
    key = _find_key_by_pattern(data, patterns)
    if key is not None:
        return data[key]
    return default


def _calculate_step(min_val: float, max_val: float, num_points: int) -> Optional[float]:
    """
    Вычисляет шаг из минимального, максимального значения и количества точек.

    Args:
        min_val: Минимальное значение
        max_val: Максимальное значение
        num_points: Количество точек

    Returns:
        Шаг или None, если вычисление невозможно
    """
    if num_points is None or num_points <= 1:
        return None

    try:
        step = (max_val - min_val) / (num_points - 1)
        return abs(step)  # Шаг всегда положительный
    except (TypeError, ZeroDivisionError):
        return None


def _calculate_num_points(min_val: float, max_val: float, step: float) -> Optional[int]:
    """
    Вычисляет количество точек из минимального, максимального значения и шага.

    Args:
        min_val: Минимальное значение
        max_val: Максимальное значение
        step: Шаг

    Returns:
        Количество точек или None, если вычисление невозможно
    """
    if step is None or step == 0:
        return None

    try:
        num_points = int(abs(max_val - min_val) / abs(step)) + 1
        return num_points
    except (TypeError, ZeroDivisionError):
        return None


def normalize_matrix_params(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Нормализует параметры матрицы сканирования.
    Принимает словарь с произвольными ключами, возвращает стандартизированный.
    """
    # Если уже есть блок parameters - работаем с ним
    if 'parameters' in data:
        params = data['parameters']
    else:
        params = data

    result = {}

    # x1 - минимальная координата по X
    result['x1'] = _extract_value(params, ['x', 'min'], DEFAULT_MATRIX_PARAMS['x1'])
    # Если x1 не найден по min, пробуем x1 напрямую
    if result['x1'] == DEFAULT_MATRIX_PARAMS['x1'] and _find_key_by_pattern(params, ['x1']):
        result['x1'] = _extract_value(params, ['x1'], DEFAULT_MATRIX_PARAMS['x1'])

    # y1 - минимальная координата по Y
    result['y1'] = _extract_value(params, ['y', 'min'], DEFAULT_MATRIX_PARAMS['y1'])
    if result['y1'] == DEFAULT_MATRIX_PARAMS['y1'] and _find_key_by_pattern(params, ['y1']):
        result['y1'] = _extract_value(params, ['y1'], DEFAULT_MATRIX_PARAMS['y1'])

    # z1 - минимальная координата по Z
    result['z1'] = _extract_value(params, ['z', 'min'], DEFAULT_MATRIX_PARAMS['z1'])
    if result['z1'] == DEFAULT_MATRIX_PARAMS['z1'] and _find_key_by_pattern(params, ['z1']):
        result['z1'] = _extract_value(params, ['z1'], DEFAULT_MATRIX_PARAMS['z1'])

    # x2 - максимальная координата по X
    result['x2'] = _extract_value(params, ['x', 'max'], DEFAULT_MATRIX_PARAMS['x2'])
    if result['x2'] == DEFAULT_MATRIX_PARAMS['x2'] and _find_key_by_pattern(params, ['x2']):
        result['x2'] = _extract_value(params, ['x2'], DEFAULT_MATRIX_PARAMS['x2'])

    # y2 - максимальная координата по Y
    result['y2'] = _extract_value(params, ['y', 'max'], DEFAULT_MATRIX_PARAMS['y2'])
    if result['y2'] == DEFAULT_MATRIX_PARAMS['y2'] and _find_key_by_pattern(params, ['y2']):
        result['y2'] = _extract_value(params, ['y2'], DEFAULT_MATRIX_PARAMS['y2'])

    # z2 - максимальная координата по Z
    result['z2'] = _extract_value(params, ['z', 'max'], DEFAULT_MATRIX_PARAMS['z2'])
    if result['z2'] == DEFAULT_MATRIX_PARAMS['z2'] and _find_key_by_pattern(params, ['z2']):
        result['z2'] = _extract_value(params, ['z2'], DEFAULT_MATRIX_PARAMS['z2'])

    # Количество точек - сначала извлекаем
    result['Np_x'] = _extract_value(params, ['np', 'x'], DEFAULT_MATRIX_PARAMS['Np_x'])
    if result['Np_x'] == DEFAULT_MATRIX_PARAMS['Np_x']:
        result['Np_x'] = _extract_value(params, ['point', 'x'], DEFAULT_MATRIX_PARAMS['Np_x'])
    if result['Np_x'] == DEFAULT_MATRIX_PARAMS['Np_x'] and _find_key_by_pattern(params, ['np_x']):
        result['Np_x'] = _extract_value(params, ['np_x'], DEFAULT_MATRIX_PARAMS['Np_x'])
    if result['Np_x'] == DEFAULT_MATRIX_PARAMS['Np_x']:
        result['Np_x'] = _extract_value(params, ['sample', 'x'], DEFAULT_MATRIX_PARAMS['Np_x'])
    if result['Np_x'] == DEFAULT_MATRIX_PARAMS['Np_x']:
        result['Np_x'] = _extract_value(params, ['resolution'], DEFAULT_MATRIX_PARAMS['Np_x'])

    result['Np_y'] = _extract_value(params, ['np', 'y'], DEFAULT_MATRIX_PARAMS['Np_y'])
    if result['Np_y'] == DEFAULT_MATRIX_PARAMS['Np_y']:
        result['Np_y'] = _extract_value(params, ['point', 'y'], DEFAULT_MATRIX_PARAMS['Np_y'])
    if result['Np_y'] == DEFAULT_MATRIX_PARAMS['Np_y'] and _find_key_by_pattern(params, ['np_y']):
        result['Np_y'] = _extract_value(params, ['np_y'], DEFAULT_MATRIX_PARAMS['Np_y'])
    if result['Np_y'] == DEFAULT_MATRIX_PARAMS['Np_y']:
        result['Np_y'] = _extract_value(params, ['sample', 'y'], DEFAULT_MATRIX_PARAMS['Np_y'])

    result['Np_z'] = _extract_value(params, ['np', 'z'], DEFAULT_MATRIX_PARAMS['Np_z'])
    if result['Np_z'] == DEFAULT_MATRIX_PARAMS['Np_z']:
        result['Np_z'] = _extract_value(params, ['point', 'z'], DEFAULT_MATRIX_PARAMS['Np_z'])
    if result['Np_z'] == DEFAULT_MATRIX_PARAMS['Np_z'] and _find_key_by_pattern(params, ['np_z']):
        result['Np_z'] = _extract_value(params, ['np_z'], DEFAULT_MATRIX_PARAMS['Np_z'])
    if result['Np_z'] == DEFAULT_MATRIX_PARAMS['Np_z']:
        result['Np_z'] = _extract_value(params, ['sample', 'z'], DEFAULT_MATRIX_PARAMS['Np_z'])

    # Шаги - извлекаем или вычисляем
    result['step_x'] = _extract_value(params, ['step', 'x'], DEFAULT_MATRIX_PARAMS['step_x'])
    if result['step_x'] == DEFAULT_MATRIX_PARAMS['step_x'] and _find_key_by_pattern(params, ['step_x']):
        result['step_x'] = _extract_value(params, ['step_x'], DEFAULT_MATRIX_PARAMS['step_x'])
    # Если шаг не найден, пробуем вычислить из диапазона и количества точек
    if result['step_x'] == DEFAULT_MATRIX_PARAMS['step_x']:
        calculated_step = _calculate_step(result['x1'], result['x2'], result['Np_x'])
        if calculated_step is not None:
            result['step_x'] = calculated_step

    result['step_y'] = _extract_value(params, ['step', 'y'], DEFAULT_MATRIX_PARAMS['step_y'])
    if result['step_y'] == DEFAULT_MATRIX_PARAMS['step_y'] and _find_key_by_pattern(params, ['step_y']):
        result['step_y'] = _extract_value(params, ['step_y'], DEFAULT_MATRIX_PARAMS['step_y'])
    # Если шаг не найден, пробуем вычислить из диапазона и количества точек
    if result['step_y'] == DEFAULT_MATRIX_PARAMS['step_y']:
        calculated_step = _calculate_step(result['y1'], result['y2'], result['Np_y'])
        if calculated_step is not None:
            result['step_y'] = calculated_step

    result['step_z'] = _extract_value(params, ['step', 'z'], DEFAULT_MATRIX_PARAMS['step_z'])
    if result['step_z'] == DEFAULT_MATRIX_PARAMS['step_z'] and _find_key_by_pattern(params, ['step_z']):
        result['step_z'] = _extract_value(params, ['step_z'], DEFAULT_MATRIX_PARAMS['step_z'])
    # Если шаг не найден, пробуем вычислить из диапазона и количества точек
    if result['step_z'] == DEFAULT_MATRIX_PARAMS['step_z']:
        calculated_step = _calculate_step(result['z1'], result['z2'], result['Np_z'])
        if calculated_step is not None:
            result['step_z'] = calculated_step

    # Время накопления
    result['accum_time'] = _extract_value(
        params,
        ['accum', 'time'],
        DEFAULT_MATRIX_PARAMS['accum_time']
    )
    if result['accum_time'] == DEFAULT_MATRIX_PARAMS['accum_time']:
        # Пробуем другие варианты
        result['accum_time'] = _extract_value(
            params,
            ['time'],
            DEFAULT_MATRIX_PARAMS['accum_time']
        )

    # Вычисляем производные параметры, если они не заданы
    if result['Np_x'] != DEFAULT_MATRIX_PARAMS['Np_x'] and result['Np_y'] != DEFAULT_MATRIX_PARAMS['Np_y']:
        result['Np_slice'] = result['Np_x'] * result['Np_y']
        result['Np_total'] = result['Np_slice'] * result['Np_z']
    else:
        result['Np_slice'] = _extract_value(
            params, ['slice'], DEFAULT_MATRIX_PARAMS['Np_slice']
        )
        result['Np_total'] = _extract_value(
            params, ['total'], DEFAULT_MATRIX_PARAMS['Np_total']
        )

    # Дополнительная проверка: если Np_x и Np_y известны, но Np_slice нет
    if result['Np_slice'] == DEFAULT_MATRIX_PARAMS['Np_slice'] and \
            result['Np_x'] != DEFAULT_MATRIX_PARAMS['Np_x'] and \
            result['Np_y'] != DEFAULT_MATRIX_PARAMS['Np_y']:
        result['Np_slice'] = result['Np_x'] * result['Np_y']
        result['Np_total'] = result['Np_slice'] * result['Np_z']

    return result


def normalize_spectrum_params(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Нормализует параметры спектрального измерения.
    Принимает словарь с произвольными ключами, возвращает стандартизированный.
    """
    # Если уже есть блок parameters - работаем с ним
    if 'parameters' in data:
        params = data['parameters']
    else:
        params = data

    result = {}

    # Начальная длина волны
    result['start_nm'] = _extract_value(
        params, ['start'], DEFAULT_SPECTRUM_PARAMS['start_nm']
    )
    if result['start_nm'] == DEFAULT_SPECTRUM_PARAMS['start_nm']:
        result['start_nm'] = _extract_value(
            params, ['begin'], DEFAULT_SPECTRUM_PARAMS['start_nm']
        )
    if result['start_nm'] == DEFAULT_SPECTRUM_PARAMS['start_nm']:
        result['start_nm'] = _extract_value(
            params, ['min', 'nm'], DEFAULT_SPECTRUM_PARAMS['start_nm']
        )
    if result['start_nm'] == DEFAULT_SPECTRUM_PARAMS['start_nm'] and _find_key_by_pattern(params, ['start_nm']):
        result['start_nm'] = _extract_value(params, ['start_nm'], DEFAULT_SPECTRUM_PARAMS['start_nm'])

    # Конечная длина волны
    result['end_nm'] = _extract_value(
        params, ['end'], DEFAULT_SPECTRUM_PARAMS['end_nm']
    )
    if result['end_nm'] == DEFAULT_SPECTRUM_PARAMS['end_nm']:
        result['end_nm'] = _extract_value(
            params, ['stop'], DEFAULT_SPECTRUM_PARAMS['end_nm']
        )
    if result['end_nm'] == DEFAULT_SPECTRUM_PARAMS['end_nm']:
        result['end_nm'] = _extract_value(
            params, ['max', 'nm'], DEFAULT_SPECTRUM_PARAMS['end_nm']
        )
    if result['end_nm'] == DEFAULT_SPECTRUM_PARAMS['end_nm'] and _find_key_by_pattern(params, ['end_nm']):
        result['end_nm'] = _extract_value(params, ['end_nm'], DEFAULT_SPECTRUM_PARAMS['end_nm'])

    # Количество точек данных - сначала извлекаем
    result['data_points'] = _extract_value(
        params, ['data', 'point'], DEFAULT_SPECTRUM_PARAMS['data_points']
    )
    if result['data_points'] == DEFAULT_SPECTRUM_PARAMS['data_points']:
        result['data_points'] = _extract_value(
            params, ['point'], DEFAULT_SPECTRUM_PARAMS['data_points']
        )
    if result['data_points'] == DEFAULT_SPECTRUM_PARAMS['data_points'] and _find_key_by_pattern(params,
                                                                                                ['data_points']):
        result['data_points'] = _extract_value(params, ['data_points'], DEFAULT_SPECTRUM_PARAMS['data_points'])
    if result['data_points'] == DEFAULT_SPECTRUM_PARAMS['data_points']:
        result['data_points'] = _extract_value(
            params, ['sample'], DEFAULT_SPECTRUM_PARAMS['data_points']
        )
    if result['data_points'] == DEFAULT_SPECTRUM_PARAMS['data_points']:
        result['data_points'] = _extract_value(
            params, ['np'], DEFAULT_SPECTRUM_PARAMS['data_points']
        )

    # Шаг - извлекаем или вычисляем
    result['step_nm'] = _extract_value(
        params, ['step'], DEFAULT_SPECTRUM_PARAMS['step_nm']
    )
    if result['step_nm'] == DEFAULT_SPECTRUM_PARAMS['step_nm']:
        result['step_nm'] = _extract_value(
            params, ['resolution'], DEFAULT_SPECTRUM_PARAMS['step_nm']
        )
    if result['step_nm'] == DEFAULT_SPECTRUM_PARAMS['step_nm'] and _find_key_by_pattern(params, ['step_nm']):
        result['step_nm'] = _extract_value(params, ['step_nm'], DEFAULT_SPECTRUM_PARAMS['step_nm'])

    # Если шаг не найден, пробуем вычислить из диапазона и количества точек
    if result['step_nm'] == DEFAULT_SPECTRUM_PARAMS['step_nm']:
        calculated_step = _calculate_step(
            result['start_nm'],
            result['end_nm'],
            result['data_points']
        )
        if calculated_step is not None:
            result['step_nm'] = calculated_step

    # Если количество точек не найдено, но есть диапазон и шаг - вычисляем
    if result['data_points'] == 0 and \
            result['start_nm'] != DEFAULT_SPECTRUM_PARAMS['start_nm'] and \
            result['end_nm'] != DEFAULT_SPECTRUM_PARAMS['end_nm'] and \
            result['step_nm'] != DEFAULT_SPECTRUM_PARAMS['step_nm']:
        calculated_points = _calculate_num_points(
            result['start_nm'],
            result['end_nm'],
            result['step_nm']
        )
        if calculated_points is not None:
            result['data_points'] = calculated_points

    # Время накопления
    result['accum_time_ms'] = _extract_value(
        params, ['accum', 'time'], DEFAULT_SPECTRUM_PARAMS['accum_time_ms']
    )
    if result['accum_time_ms'] == DEFAULT_SPECTRUM_PARAMS['accum_time_ms']:
        result['accum_time_ms'] = _extract_value(
            params, ['integration', 'time'], DEFAULT_SPECTRUM_PARAMS['accum_time_ms']
        )
    if result['accum_time_ms'] == DEFAULT_SPECTRUM_PARAMS['accum_time_ms'] and _find_key_by_pattern(params,
                                                                                                    ['accum_time']):
        result['accum_time_ms'] = _extract_value(params, ['accum_time'], DEFAULT_SPECTRUM_PARAMS['accum_time_ms'])

    # Количество повторений
    result['number_repetitions'] = _extract_value(
        params, ['repetition'], DEFAULT_SPECTRUM_PARAMS['number_repetitions']
    )
    if result['number_repetitions'] == DEFAULT_SPECTRUM_PARAMS['number_repetitions']:
        result['number_repetitions'] = _extract_value(
            params, ['average'], DEFAULT_SPECTRUM_PARAMS['number_repetitions']
        )
    if result['number_repetitions'] == DEFAULT_SPECTRUM_PARAMS['number_repetitions'] and _find_key_by_pattern(params, [
        'number_repetitions']):
        result['number_repetitions'] = _extract_value(params, ['number_repetitions'],
                                                      DEFAULT_SPECTRUM_PARAMS['number_repetitions'])

    return result


def create_metadata(data_type: str, description: Optional[str] = None) -> Dict[str, str]:
    """
    Создает метаданные с текущей датой и временем.

    Args:
        data_type: Тип данных ('matrix' или 'spectrum')
        description: Описание (если None, генерируется автоматически)

    Returns:
        Словарь с метаданными
    """
    if description is None:
        if data_type == 'matrix':
            description = '3D scan'
        elif data_type == 'spectrum':
            description = 'Spectrum measurement'
        else:
            description = 'Measurement'

    return {
        'created': get_date_time(),
        'description': description
    }


def normalize_params(data: Dict[str, Any], data_type: str = 'auto',
                     preserve_metadata: bool = True) -> Dict[str, Any]:
    """
    Универсальная функция нормализации параметров.

    Args:
        data: Словарь с данными
        data_type: 'matrix', 'spectrum' или 'auto' (автоопределение)
        preserve_metadata: Сохранять ли метаданные (по умолчанию True)

    Returns:
        Нормализованный словарь с параметрами, комментарием и метаданными
    """
    # Определяем тип данных
    if data_type == 'auto':
        # Пытаемся определить тип данных
        data_str = str(data).lower()
        if 'spectrum' in data_str or 'nm' in data_str or 'wavelength' in data_str:
            data_type = 'spectrum'
        else:
            data_type = 'matrix'

    # Нормализуем параметры в зависимости от типа
    if data_type == 'matrix':
        normalized_params = normalize_matrix_params(data)
        description = '3D scan'
    elif data_type == 'spectrum':
        normalized_params = normalize_spectrum_params(data)
        description = 'Spectrum measurement'
    else:
        raise ValueError(f"Unknown data type: {data_type}")

    # Создаем результирующий словарь
    result = {
        'comment': '',  # Пустой комментарий по умолчанию
        'name': 'Группа',  # Имя по умолчанию
        'metadata': create_metadata(data_type, description),
        'parameters': normalized_params
    }

    # Если нужно сохранить оригинальные метаданные
    if preserve_metadata and 'metadata' in data:
        # Обновляем метаданные, сохраняя оригинальные значения
        original_metadata = data['metadata']
        if 'created' in original_metadata and original_metadata['created']:
            result['metadata']['created'] = original_metadata['created']
        if 'description' in original_metadata and original_metadata['description']:
            result['metadata']['description'] = original_metadata['description']

    # Сохраняем оригинальные комментарий и имя, если они есть
    if 'comment' in data and data['comment']:
        result['comment'] = data['comment']
    if 'name' in data and data['name']:
        result['name'] = data['name']

    return result


# Дополнительные функции для удобства
def normalize_matrix(data: Dict[str, Any]) -> Dict[str, Any]:
    """Нормализует параметры матрицы."""
    return normalize_params(data, 'matrix')


def normalize_spectrum(data: Dict[str, Any]) -> Dict[str, Any]:
    """Нормализует параметры спектра."""
    return normalize_params(data, 'spectrum')