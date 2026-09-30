# ==================================================== КОДЫ НОД ====================================================
# ======================== 1. DATA_IO ========================
OP_NODE_INPUT_EXT = 11               # импорт (файл, HDF5, FITS, бинарный, буфер, синтетика)
OP_NODE_INPUT_INT = 12               # импорт из виджетов
OP_NODE_EXPORT_EXT = 13              # экспорт (.npy, .csv, HDF5, изображение, график, буфер)
OP_NODE_EXPORT_INT = 14              # экспорт в виджеты
OP_NODE_PSF_GENERATOR = 15
OP_NODE_NOISE_GENERATOR = 16
OP_NODE_FORMULA_GENERATOR = 17

# ======================== 2. MATH ========================
OP_NODE_ARITHMETIC = 21          # + - * / log exp power
OP_NODE_UNARY = 22               # сумма, среднее, std, min, max, cumsum
OP_NODE_NORMALIZE = 23           # min-max, z-score, area, peak, blackbody
OP_NODE_STATISTICS = 24          # гистограмма, процентили, корреляции, PCA, выбросы
OP_NODE_INTERPOLATION = 25       # линейная, кубическая, передискретизация
OP_NODE_PRODUCTS = 26            # dot, outer, matrix multiply

# ======================== 3. FILTERS ========================
OP_NODE_SMOOTHING = 31           # гаусс, медиана, Savitzky-Golay, LOWESS, EMA, bilateral
OP_NODE_DENOISING = 32           # нелокальное среднее, вейвлет
OP_NODE_EDGE = 33                # Sobel, Prewitt, Laplacian, Canny
OP_NODE_MORPHOLOGY = 34          # эрозия, дилатация, opening, closing, top-hat
OP_NODE_FREQUENCY = 35           # low-pass, high-pass, band-pass, notch FFT
OP_NODE_CONVOLUTION = 36         # свёртка, деконволюция (Люси-Ричардсон, Винер, Ван-Циттерт)

# ======================== 4. TRANSFORMS ========================
OP_NODE_GEOMETRIC = 41           # transpose, flip H/V, shear
OP_NODE_SELECTION = 42           # crop, slice, ROI, index selector
OP_NODE_SIGNAL = 43              # baseline, detrend, envelope, integration, diff
OP_NODE_MATRIX_CROP = 44
OP_NODE_SPECTRUM_CROP = 45

# ======================== 5. AVERAGING ========================
OP_NODE_AVG_SIMPLE = 51          # running mean, cumulative mean, block average
OP_NODE_AVG_WEIGHTED = 52        # EMA, gaussian weighted, custom weights
OP_NODE_AVG_ROBUST = 53          # median average, trimmed mean, Welford
OP_NODE_AVG_ADVANCED = 54        # adaptive moving, Kalman filter

# ======================== 6. SEGMENTATION ========================
OP_NODE_THRESHOLD = 61           # global, adaptive, Otsu
OP_NODE_WATERSHED = 62           # водораздел
OP_NODE_CONNECTED = 63           # label regions, region properties
OP_NODE_CLUSTERING = 64          # k-means

# ======================== 7. VISUALIZATION ========================
OP_NODE_HISTOGRAMS = 71          # 1D и 2D гистограммы
OP_NODE_IMAGEVIEW = 72            # 2D plot, image view, multi-plot
OP_NODE_SPECTRUM = 73              # slice viewer, time series
OP_NODE_LINE = 74

# ======================== 8. UTILS ========================
OP_NODE_DEBUG = 81               # data info, assert shape, NaN check, memory usage
OP_NODE_METADATA = 82            # add, read, copy metadata
OP_NODE_FLOW = 83                # split, merge, condition (if/else)

# ======================== 8. UTILS ========================
OP_NODE_NV_ODMR = 91

# ======================== Категории ========================
types = {
    1: "Данные",
    2: "Математика",
    3: "Фильтры",
    4: "Преобразования",
    5: "Усреднение",
    6: "Сегментация",
    7: "Визуализация",
    8: "Утилиты",
    9: "Специальные спектры",
}

SOCKET_TYPES = {
    "number": 0,
    "number_list": 1,
    "spectrum": 2,
    "spectrum_list": 3,
    "matrix_2d": 4,
    "matrix_3d": 5,
    "matrix_list_2d": 6,
    "any": 7,
    "boolean": 8,
    "string": 9,
}

NODE_COLORS = {
    1: {'bg': '#1a3a7a', 'text': '#8ab4ff'},     # DATA_IO - синий
    2: {'bg': '#1a6a3a', 'text': '#80ffa0'},     # MATH - зелёный
    3: {'bg': '#5a2a8a', 'text': '#d4a0ff'},     # FILTERS - фиолетовый
    4: {'bg': '#8a5a1a', 'text': '#ffcc80'},     # TRANSFORMS - оранжевый
    5: {'bg': '#1a7a7a', 'text': '#80ffe0'},     # AVERAGING - бирюзовый
    6: {'bg': '#8a1a1a', 'text': '#ffb0b0'},     # SEGMENTATION - красный
    7: {'bg': '#7a6a1a', 'text': '#ffe880'},     # VISUALIZATION - золотой
    8: {'bg': '#4a4a4a', 'text': '#c0c0c0'},      # UTILS - серый
    9: {'bg': '#FF1493', 'text': '#FFB6C1'}      # SPEC_SPECTRUM - Розовый
}
# ==================================================== РЕЕСТР ====================================================
CALC_NODES = {}


class ConfException(Exception): pass
class InvalidNodeRegistration(ConfException): pass
class OpCodeNotRegistered(ConfException): pass


def register_node_now(op_code, class_reference):
    if op_code in CALC_NODES:
        print(f"Duplicate node registration of '{op_code}'")
        return
    CALC_NODES[op_code] = class_reference


def register_node(op_code):
    def decorator(original_class):
        register_node_now(op_code, original_class)
        return original_class
    return decorator


def get_class_from_opcode(op_code):
    if op_code not in CALC_NODES: raise OpCodeNotRegistered("OpCode '%d' is not registered" % op_code)
    return CALC_NODES[op_code]


# ==================================================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================================================
def get_nodes_by_type(node_type: int):
    """Получить все ноды определённого типа"""
    return {code: cls for code, cls in CALC_NODES.items() if code // 10 == node_type}


def get_node_type_name(node_type: int) -> str:
    """Название типа ноды"""
    return types.get(node_type, "Другое")


# ==================================================== ИМПОРТ НОД ====================================================
from packages.Floating_window.node_editor.nodes import *
from packages.Floating_window.node_editor.nodes.DATA_IO.Import.Internal import *
#from packages.Floating_window.node_editor.nodes.DATA_IO.Import.External import *
from packages.Floating_window.node_editor.nodes.DATA_IO.Export.Internal import *
#from packages.Floating_window.node_editor.nodes.DATA_IO.Export.External import *
