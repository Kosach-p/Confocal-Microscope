import numpy as np
import json
import os
import re
import ast
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path


class BaseSaver(ABC):
    """Базовый класс с возможностью сохранения параметров в .inf файл"""
    default_file_path = "saved_data"

    def __init__(self):
        self.data = None
        self.parameters = {}
        self.current_filepath = None
        self.current_format = None

    def set_data(self, data: Any, parameters: Optional[Dict[str, Any]] = None):
        self.data = data
        if parameters:
            self.parameters.update(parameters)
        self._validate_data()
        return self

    def set_parameters(self, parameters: Dict[str, Any]):
        self.parameters.update(parameters)
        return self

    def save(self, filepath: str, format: str, include_header: bool = True, **kwargs):
        if self.data is None:
            print("Ошибка: нет данных для сохранения. Используйте set_data() сначала")
            return None

        try:
            if filepath.endswith("." + format):
                filepath = filepath.removesuffix("." + format)
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            self.current_filepath = filepath
            self.current_format = format

            result_path = self._save_impl(filepath, format, include_header=include_header, **kwargs)

            if self.parameters and result_path:
                self._save_inf_file(filepath)

            return result_path
        except Exception as e:
            print(f"Ошибка сохранения: {e}")
            import traceback
            traceback.print_exc()
            return None

    def load(self, filepath: str, with_inf: bool = True) -> Optional[Any]:
        """
        Загружает данные из файла.

        Returns:
            Если with_inf=True: tuple (data, params)
                data — чистый массив/список
                params — dict с параметрами или None
            Если with_inf=False: только data
            None при ошибке

        Приоритет параметров:
            1. .inf файл (если есть)
            2. Параметры из заголовка/метаданных файла (если формат поддерживает)
            3. None (если нет параметров)
        """
        if filepath is None:
            return None

        try:
            if not os.path.exists(filepath):
                print(f"Ошибка: файл не найден - {filepath}")
                return None

            ext = Path(filepath).suffix.lower()
            data = None
            header_params = None  # Параметры, извлечённые из самого файла

            # ========== ЗАГРУЗКА ДАННЫХ ==========
            if ext in {'.csv', '.dat', '.txt'}:
                data, header_params = self._load_text(filepath)

            elif ext == '.json':
                # JSON может содержать parameters
                data, header_params = self._load_json_with_params(filepath)

            elif ext == '.npy':
                # NPY — ТОЛЬКО массив, параметров нет
                data = self._load_npy(filepath)
                header_params = None

            elif ext == '.npz':
                # NPZ может содержать parameters
                data, header_params = self._load_npz_with_params(filepath)

            elif ext in {'.tif', '.tiff'}:
                # TIFF — массив (метаданные сложно извлечь)
                data = self._load_tiff(filepath)
                header_params = None

            elif ext in {'.h5', '.hdf5'}:
                # HDF5 умеет хранить параметры в атрибутах
                data, header_params = self._load_hdf5(filepath)

            elif ext == '.inf':
                data = self._load_inf(filepath)
                return data

            else:
                print(f"Ошибка: неподдерживаемый формат - {ext}")
                return None

            if data is None:
                print(f"Ошибка: не удалось загрузить данные из {filepath}")
                return None

            # ========== ВОЗВРАЩАЕМ РЕЗУЛЬТАТ ==========

            if with_inf:
                base, _ = os.path.splitext(filepath)
                inf_path = base + ".inf"

                # Приоритет 1: .inf файл
                if os.path.exists(inf_path):
                    params = self._load_inf(inf_path)
                    return (data, params)

                # Приоритет 2: параметры из заголовка файла
                if header_params is not None and len(header_params) > 0:
                    return (data, header_params)

                # Приоритет 3: нет параметров
                return (data, None)

            return data

        except Exception as e:
            print(f"Ошибка загрузки: {e}")
            import traceback
            traceback.print_exc()
            return None

    def load_all_from_folder(self, folder_path: str, with_inf: bool = True) -> Dict[str, Any]:
        """Загружает все поддерживаемые файлы из папки"""
        if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
            return {}

        supported_extensions = {'.csv', '.json', '.npy', '.npz', '.tif', '.tiff', '.h5', '.hdf5', '.dat', '.txt'}
        results = {}

        for filename in os.listdir(folder_path):
            filepath = os.path.join(folder_path, filename)
            if filename.endswith('.inf'):
                continue
            if Path(filename).suffix.lower() in supported_extensions:
                loaded = self.load(filepath, with_inf=with_inf)
                if loaded is not None:
                    results[filename] = loaded

        return results

    def _save_inf_file(self, filepath: str) -> str:
        """Сохраняет параметры в .inf файл (JSON)"""
        inf_path = f"{filepath}.inf"
        try:
            serializable_params = self._make_serializable(self.parameters)
            with open(inf_path, 'w', encoding='utf-8') as f:
                json.dump(serializable_params, f, indent=2, ensure_ascii=False)
            return inf_path
        except Exception as e:
            print(f"Ошибка сохранения .inf файла: {e}")
            return ""

    def _make_serializable(self, obj):
        """Рекурсивно преобразует numpy типы в Python типы для JSON"""
        if isinstance(obj, dict):
            return {str(k): self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj

    def _load_inf(self, filepath: str) -> Dict[str, Any]:
        """Загружает параметры из .inf файла (JSON)"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    @staticmethod
    def _parse_header_params(lines: List[str]) -> Optional[Dict[str, Any]]:
        """
        Извлекает параметры из строк заголовка (# key: value).
        Поддерживает вложенные dict'ы (value в кавычках).
        Возвращает None если параметров нет.

        Примеры:
            # temperature: 300           -> {'temperature': 300}
            # name: experiment_1         -> {'name': 'experiment_1'}
            # metadata: {'key': 'val'}   -> {'metadata': {'key': 'val'}}
        """
        params = {}
        for line in lines:
            if not line.startswith('#'):
                continue

            # Пропускаем служебные строки
            if any(skip in line for skip in ['=== DATA START ===', 'Layer']):
                continue

            # Парсим "# Shape: X Y Z"
            if line.startswith('# Shape:'):
                continue

            # Парсим "# key: value"
            match = re.match(r'#\s*([^:]+?):\s*(.+)', line)
            if not match:
                continue

            key, value_str = match.groups()
            key = key.strip()
            value_str = value_str.strip()

            # Пробуем распарсить value
            value = BaseSaver._parse_value(value_str)
            params[key] = value

        return params if len(params) > 0 else None

    @staticmethod
    def _parse_value(value_str: str) -> Any:
        """
        Парсит строковое значение из заголовка.
        Поддерживает:
            - числа: 300, 25.5, 1e-10
            - булевы: True, False
            - строки: experiment_1
            - dict'ы в виде строки: "{'key': 'val'}"
            - списки: [1, 2, 3]
        """
        if not value_str:
            return ""

        # Пробуем как число
        try:
            if '.' in value_str or 'e' in value_str.lower():
                return float(value_str)
            return int(value_str)
        except (ValueError, AttributeError):
            pass

        # Булевы
        if value_str.lower() == 'true':
            return True
        if value_str.lower() == 'false':
            return False
        if value_str.lower() == 'none':
            return None

        # Пробуем как dict/список через ast.literal_eval
        if (value_str.startswith('{') and value_str.endswith('}')) or \
                (value_str.startswith('[') and value_str.endswith(']')):
            try:
                return ast.literal_eval(value_str)
            except (ValueError, SyntaxError):
                pass

        # Пробуем как JSON
        if (value_str.startswith('{') and value_str.endswith('}')) or \
                (value_str.startswith('[') and value_str.endswith(']')):
            try:
                return json.loads(value_str.replace("'", '"'))
            except json.JSONDecodeError:
                pass

        # Возвращаем как строку
        return value_str

    @abstractmethod
    def _validate_data(self):
        pass

    @abstractmethod
    def _save_impl(self, filepath: str, format: str, include_header: bool = True, **kwargs) -> str:
        pass

    @abstractmethod
    def _load_text(self, filepath: str) -> Tuple[Optional[Any], Optional[Dict]]:
        """Загружает текстовый файл. Возвращает (данные, параметры_из_заголовка)"""
        pass

    def _load_json_with_params(self, filepath: str) -> Tuple[Any, Optional[Dict]]:
        """Загружает JSON, извлекая параметры если есть"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        params = None
        if isinstance(data, dict):
            if 'parameters' in data:
                params = data['parameters']
            if 'data' in data:
                data = data['data']

        return data, params

    def _load_npy(self, filepath: str) -> np.ndarray:
        return np.load(filepath, allow_pickle=True)

    def _load_npz_with_params(self, filepath: str) -> Tuple[np.ndarray, Optional[Dict]]:
        """Загружает NPZ, извлекая параметры если есть"""
        loaded = dict(np.load(filepath, allow_pickle=True))

        params = None
        if 'parameters' in loaded:
            params = loaded.pop('parameters').item() if isinstance(loaded['parameters'], np.ndarray) else loaded.pop(
                'parameters')

        if 'data' in loaded:
            data = loaded['data']
        else:
            data = next(v for v in loaded.values() if isinstance(v, np.ndarray))

        if data.ndim == 2:
            data = data[np.newaxis, :, :]

        return data, params

    def _load_tiff(self, filepath: str) -> np.ndarray:
        try:
            from tifffile import imread
            data = imread(filepath).astype(np.float64)
            if data.ndim == 2:
                data = data[np.newaxis, :, :]
            return data
        except ImportError:
            raise RuntimeError("Установите tifffile: pip install tifffile")

    def _load_hdf5(self, filepath: str) -> Tuple[np.ndarray, Optional[Dict]]:
        """Загружает HDF5. Возвращает (массив, параметры)"""
        try:
            import h5py
            with h5py.File(filepath, 'r') as f:
                data = f['data'][:]
                params = dict(f['data'].attrs) if f['data'].attrs else None
                return data, params
        except ImportError:
            raise RuntimeError("Установите h5py: pip install h5py")


class SpectrumSaver(BaseSaver):
    """Сохранение спектров: data = список [[x, y], ...]"""
    SUPPORTED_FORMATS = {'csv', 'dat', 'txt', 'json', 'npy', 'npz'}

    def _validate_data(self):
        if len(self.data) == 0:
            return
        if not isinstance(self.data[0], (list, tuple)):
            self.data = [self.data]
        for i, spectrum in enumerate(self.data):
            if not isinstance(spectrum, (list, tuple)) or len(spectrum) != 2:
                raise ValueError(f"Спектр {i} должен быть [x, y]")

    def _save_impl(self, filepath: str, format: str, include_header: bool = True, **kwargs) -> str:
        delimiter = kwargs.get('delimiter', '\t')

        if format in {'csv', 'dat', 'txt'}:
            return self._save_columnar(filepath, delimiter, format, include_header)
        elif format == 'json':
            return self._to_json(filepath)
        elif format == 'npy':
            return self._to_npy(filepath)
        elif format == 'npz':
            return self._to_npz(filepath)
        elif format == 'folder':
            return self._to_folder(filepath, kwargs.get('ext', 'txt'), delimiter, include_header)
        else:
            raise ValueError(f"Неподдерживаемый формат: {format}")

    def _save_columnar(self, filepath: str, delim: str, ext: str, include_header: bool) -> str:
        path = f"{filepath}.{ext}"
        n_spectra = len(self.data)
        lengths = [len(spectrum[0]) for spectrum in self.data]
        max_len = max(lengths)

        if len(set(lengths)) > 1:
            print(f"⚠️ Предупреждение: спектры разной длины {lengths}")

        with open(path, 'w', encoding='utf-8') as f:
            if include_header and self.parameters:
                for k, v in self.parameters.items():
                    f.write(f"# {k}: {v}\n")

            headers = []
            for i in range(n_spectra):
                headers.append(f"X{i + 1}")
                headers.append(f"Y{i + 1}")
            f.write(delim.join(headers) + "\n")

            for row_idx in range(max_len):
                row = []
                for spectrum in self.data:
                    x_data, y_data = spectrum
                    if row_idx < len(x_data):
                        row.append(f"{x_data[row_idx]:.6e}")
                        row.append(f"{y_data[row_idx]:.6e}")
                    else:
                        row.append("")
                        row.append("")
                f.write(delim.join(row) + "\n")

        return path

    def _to_folder(self, filepath: str, ext: str, delim: str, include_header: bool) -> str:
        folder_path = f"{filepath}_spectra"
        Path(folder_path).mkdir(parents=True, exist_ok=True)

        with open(os.path.join(folder_path, '_parameters.inf'), 'w', encoding='utf-8') as f:
            json.dump(self._make_serializable(self.parameters), f, indent=2, ensure_ascii=False)

        for i, (x, y) in enumerate(self.data):
            spectrum_path = os.path.join(folder_path, f'spectrum_{i:04d}.{ext}')
            with open(spectrum_path, 'w', encoding='utf-8') as f:
                if include_header:
                    f.write(f"# Spectrum {i + 1}\n")
                    for k, v in self.parameters.items():
                        f.write(f"# {k}: {v}\n")
                for j in range(len(x)):
                    f.write(f"{x[j]:.6e}{delim}{y[j]:.6e}\n")

        return folder_path

    def _to_json(self, filepath: str) -> str:
        path = f"{filepath}.json"
        serializable_data = []
        for x, y in self.data:
            serializable_data.append({
                'x': x.tolist() if hasattr(x, 'tolist') else list(x),
                'y': y.tolist() if hasattr(y, 'tolist') else list(y)
            })

        with open(path, 'w', encoding='utf-8') as f:
            json.dump({
                'parameters': self.parameters,
                'spectra': serializable_data,
                'n_spectra': len(self.data)
            }, f, indent=2, ensure_ascii=False)
        return path

    def _to_npy(self, filepath: str) -> str:
        path = f"{filepath}.npy"
        n_spectra = len(self.data)
        max_len = max(len(spectrum[0]) for spectrum in self.data)

        data_array = np.full((n_spectra * 2, max_len), np.nan, dtype=np.float64)
        for i, (x, y) in enumerate(self.data):
            data_array[2 * i, :len(x)] = x
            data_array[2 * i + 1, :len(y)] = y

        np.save(path, data_array)
        return path

    def _to_npz(self, filepath: str) -> str:
        path = f"{filepath}.npz"
        save_dict = {'parameters': np.array([self.parameters])}
        for i, (x, y) in enumerate(self.data):
            save_dict[f'X{i + 1}'] = x
            save_dict[f'Y{i + 1}'] = y
        np.savez_compressed(path, **save_dict)
        return path

    def _load_text(self, filepath: str) -> Tuple[Optional[list], Optional[Dict]]:
        """Загружает текстовый файл спектров"""
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        header_params = self._parse_header_params(lines)

        data_start = 0
        while data_start < len(lines) and lines[data_start].startswith('#'):
            data_start += 1

        if data_start >= len(lines):
            return None, header_params

        first_data_line = lines[data_start + 1] if data_start + 1 < len(lines) else ""
        if '\t' in first_data_line:
            delimiter = '\t'
        elif ',' in first_data_line:
            delimiter = ','
        else:
            delimiter = None

        headers = lines[data_start].strip().split(delimiter)
        n_spectra = len([h for h in headers if h.startswith('X') or h.startswith('Y')]) // 2

        spectra_x = [[] for _ in range(n_spectra)]
        spectra_y = [[] for _ in range(n_spectra)]

        for line in lines[data_start + 1:]:
            line = line.strip()
            if not line:
                continue
            parts = line.split(delimiter)
            for i in range(n_spectra):
                x_idx = 2 * i
                y_idx = 2 * i + 1
                if x_idx < len(parts) and parts[x_idx]:
                    spectra_x[i].append(float(parts[x_idx]))
                if y_idx < len(parts) and parts[y_idx]:
                    spectra_y[i].append(float(parts[y_idx]))

        result = []
        for i in range(n_spectra):
            result.append([np.array(spectra_x[i]), np.array(spectra_y[i])])

        return result, header_params

    def _load_json_with_params(self, filepath: str) -> Tuple[list, Optional[Dict]]:
        """Загружает JSON спектров"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        params = None
        if isinstance(data, dict):
            params = data.get('parameters')
            if 'spectra' in data:
                result = []
                for s in data['spectra']:
                    result.append([np.array(s['x']), np.array(s['y'])])
                return result, params

        return data, params

    def _load_npy(self, filepath: str) -> list:
        """Загружает NPY спектров"""
        data_array = np.load(filepath, allow_pickle=True)
        n_spectra = data_array.shape[0] // 2
        result = []
        for i in range(n_spectra):
            x = data_array[2 * i]
            y = data_array[2 * i + 1]
            mask = ~np.isnan(x)
            result.append([x[mask], y[mask]])
        return result

    def _load_npz_with_params(self, filepath: str) -> Tuple[list, Optional[Dict]]:
        """Загружает NPZ спектров"""
        loaded = dict(np.load(filepath, allow_pickle=True))

        params = None
        if 'parameters' in loaded:
            p = loaded.pop('parameters')
            if isinstance(p, np.ndarray) and p.ndim == 0:
                params = p.item()
            elif isinstance(p, np.ndarray):
                params = p

        n_spectra = len([k for k in loaded.keys() if k.startswith('X')])
        result = []
        for i in range(n_spectra):
            result.append([loaded[f'X{i + 1}'], loaded[f'Y{i + 1}']])

        return result, params


class ArraySaver(BaseSaver):
    """
    Универсальное сохранение массивов (2D и 3D).
    2D сохраняется как 3D с одним слоем.
    """
    SUPPORTED_FORMATS = {'csv', 'tif', 'tiff', 'h5', 'hdf5', 'npy', 'npz', 'dat', 'txt'}

    def _validate_data(self):
        self.data = np.asarray(self.data, dtype=np.float64)

        if self.data.ndim == 1:
            raise ValueError("Одномерные массивы не поддерживаются. Используйте SpectrumSaver")

        if self.data.ndim == 2:
            self.data = self.data[np.newaxis, :, :]

        if self.data.ndim != 3:
            raise ValueError(f"Поддерживаются только 2D и 3D массивы, получен {self.data.ndim}D")

    def _save_impl(self, filepath: str, format: str, include_header: bool = True, **kwargs) -> str:
        if format in {'csv', 'dat', 'txt'}:
            delimiter = kwargs.get('delimiter', '\t')
            return self._save_text_layers(filepath, format, delimiter, include_header)
        elif format in {'tif', 'tiff'}:
            return self._to_tiff(filepath)
        elif format in {'h5', 'hdf5'}:
            return self._to_hdf5(filepath, kwargs.get('compression', True))
        elif format == 'npy':
            return self._to_npy(filepath)
        elif format == 'npz':
            return self._to_npz(filepath)
        elif format == 'json':
            return self._to_json(filepath)
        elif format == 'folder':
            ext = kwargs.get('ext', 'dat')
            delimiter = kwargs.get('delimiter', '\t')
            return self._to_folder(filepath, ext, delimiter, include_header)
        else:
            raise ValueError(f"Неподдерживаемый формат: {format}")

    def _save_text_layers(self, filepath: str, ext: str, delimiter: str, include_header: bool) -> str:
        path = f"{filepath}.{ext}"
        n_layers, rows, cols = self.data.shape

        with open(path, 'w', encoding='utf-8') as f:
            if include_header and self.parameters:
                f.write(f"# Shape: {n_layers} {rows} {cols}\n")
                for k, v in self.parameters.items():
                    f.write(f"# {k}: {v}\n")
                f.write("# === DATA START ===\n")

            for z in range(n_layers):
                if n_layers > 1:
                    f.write(f"# Layer {z}\n")
                np.savetxt(f, self.data[z], delimiter=delimiter, fmt='%.6e')
                f.write("\n")

        return path

    def _to_folder(self, filepath: str, ext: str, delimiter: str, include_header: bool) -> str:
        folder_path = f"{filepath}_layers"
        Path(folder_path).mkdir(parents=True, exist_ok=True)

        with open(os.path.join(folder_path, '_parameters.inf'), 'w', encoding='utf-8') as f:
            all_params = {
                **self.parameters,
                'n_layers': self.data.shape[0],
                'rows': self.data.shape[1],
                'cols': self.data.shape[2]
            }
            json.dump(self._make_serializable(all_params), f, indent=2, ensure_ascii=False)

        for z in range(self.data.shape[0]):
            if ext in {'tif', 'tiff'}:
                try:
                    from tifffile import imwrite
                    layer_path = os.path.join(folder_path, f'layer_{z:04d}.tif')
                    imwrite(layer_path, self.data[z].astype(np.float32))
                    continue
                except ImportError:
                    ext = 'dat'

            layer_path = os.path.join(folder_path, f'layer_{z:04d}.{ext}')
            with open(layer_path, 'w') as f:
                if include_header:
                    f.write(f"# Layer {z}\n")
                    for k, v in self.parameters.items():
                        f.write(f"# {k}: {v}\n")
                np.savetxt(f, self.data[z], delimiter=delimiter, fmt='%.6e')

        return folder_path

    def _to_json(self, filepath: str) -> str:
        path = f"{filepath}.json"
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({
                'parameters': self.parameters,
                'data': self.data.tolist(),
                'shape': list(self.data.shape)
            }, f, indent=2, ensure_ascii=False)
        return path

    def _to_tiff(self, filepath: str) -> str:
        try:
            from tifffile import imwrite
            path = f"{filepath}.tif"
            imwrite(path, self.data.astype(np.float32), imagej=True, metadata=self.parameters)
            return path
        except ImportError:
            raise RuntimeError("Установите tifffile: pip install tifffile")

    def _to_hdf5(self, filepath: str, compress: bool) -> str:
        try:
            import h5py
            path = f"{filepath}.h5"
            with h5py.File(path, 'w') as f:
                dset = f.create_dataset('data', data=self.data,
                                        compression='gzip' if compress else None)
                for k, v in self.parameters.items():
                    dset.attrs[k] = v
            return path
        except ImportError:
            raise RuntimeError("Установите h5py: pip install h5py")

    def _to_npy(self, filepath: str) -> str:
        path = f"{filepath}.npy"
        np.save(path, self.data)
        return path

    def _to_npz(self, filepath: str) -> str:
        path = f"{filepath}.npz"
        np.savez_compressed(path, parameters=self.parameters, data=self.data)
        return path

    def _load_text(self, filepath: str) -> Tuple[Optional[np.ndarray], Optional[Dict]]:
        """Загружает текстовый файл с послойной структурой"""
        try:
            with open(filepath, 'r') as f:
                lines = f.readlines()

            header_params = self._parse_header_params(lines)

            has_shape = any('# Shape:' in line for line in lines)
            has_layer = any('# Layer' in line for line in lines)
            is_layered = has_shape or has_layer

            if is_layered:
                shape = None
                data_arrays = []
                current_layer = []

                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    if line.startswith('# Shape:'):
                        shape = tuple(map(int, line.replace('# Shape:', '').strip().split()))
                    elif line.startswith('# === DATA START ==='):
                        continue
                    elif line.startswith('# Layer'):
                        if current_layer:
                            data_arrays.append(np.array(current_layer, dtype=np.float64))
                            current_layer = []
                        continue
                    elif line.startswith('#'):
                        continue
                    else:
                        if '\t' in line:
                            row = [float(x) for x in line.split('\t') if x.strip()]
                        elif ',' in line:
                            row = [float(x) for x in line.split(',') if x.strip()]
                        else:
                            row = [float(x) for x in line.split() if x.strip()]
                        current_layer.append(row)

                if current_layer:
                    data_arrays.append(np.array(current_layer, dtype=np.float64))

                if data_arrays:
                    result = np.stack(data_arrays, axis=0)
                    if shape and result.shape != shape:
                        print(f"⚠️ Предупреждение: ожидалась форма {shape}, получена {result.shape}")
                    return result, header_params

            data = np.loadtxt(filepath, comments='#', dtype=np.float64)

            if data.ndim == 2:
                data = data[np.newaxis, :, :]

            return data, header_params

        except Exception as e:
            print(f"Ошибка загрузки текстового файла: {e}")
            return None, None

    def _load_json_with_params(self, filepath: str) -> Tuple[np.ndarray, Optional[Dict]]:
        """Загружает JSON массива"""
        with open(filepath, 'r') as f:
            data = json.load(f)

        params = None
        if isinstance(data, dict):
            params = data.get('parameters')
            if 'data' in data:
                arr = np.array(data['data'], dtype=np.float64)
            else:
                arr = np.array(data, dtype=np.float64)
        else:
            arr = np.array(data, dtype=np.float64)

        if arr.ndim == 2:
            arr = arr[np.newaxis, :, :]

        return arr, params

    def _load_npy(self, filepath: str) -> np.ndarray:
        """Загружает NPY массива"""
        data = np.load(filepath, allow_pickle=True)
        if data.ndim == 2:
            data = data[np.newaxis, :, :]
        return data

    def _load_npz_with_params(self, filepath: str) -> Tuple[np.ndarray, Optional[Dict]]:
        """Загружает NPZ массива"""
        loaded = dict(np.load(filepath, allow_pickle=True))

        params = None
        if 'parameters' in loaded:
            p = loaded.pop('parameters')
            if isinstance(p, np.ndarray):
                if p.ndim == 0:
                    params = p.item()
                else:
                    params = p

        if 'data' in loaded:
            data = loaded['data']
        else:
            data = next(v for v in loaded.values() if isinstance(v, np.ndarray))

        if data.ndim == 2:
            data = data[np.newaxis, :, :]

        return data, params

    def _load_tiff(self, filepath: str) -> np.ndarray:
        """Загружает TIFF массива"""
        try:
            from tifffile import imread
            data = imread(filepath).astype(np.float64)
            if data.ndim == 2:
                data = data[np.newaxis, :, :]
            return data
        except ImportError:
            raise RuntimeError("Установите tifffile: pip install tifffile")

    def _load_hdf5(self, filepath: str) -> Tuple[np.ndarray, Optional[Dict]]:
        """Загружает HDF5 массива"""
        try:
            import h5py
            with h5py.File(filepath, 'r') as f:
                data = f['data'][:]
                params = dict(f['data'].attrs) if f['data'].attrs else None
                return data, params
        except ImportError:
            raise RuntimeError("Установите h5py: pip install h5py")