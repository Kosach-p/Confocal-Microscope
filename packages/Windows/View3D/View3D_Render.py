import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal, QTimer, Qt
from PyQt6.QtWidgets import QPushButton, QFrame, QWidget
from PyQt6.QtGui import QIcon
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vedo.plotter import Plotter
from vedo.volume.core import Volume
from vedo.addons import Axes
from Icon.IconName import *
from packages.Floating_window.node_editor.NodeRegistry import NodeRegistry
from packages.core.widgets.QHistLUTWidget import QHistogramLUTWidget
from packages.core.validators.dataValidator import detect_data_type
from packages.core.widgets.QColorMapDialog import ColormapDialog, ColormapButton
from PyQt6.QtWidgets import QDialog


pg_to_vedo_cmap = {"inferno": "inferno",
                    "viridis": "viridis",
                    "magma": "magma",
                    "plasma": "plasma",
                    "turbo": "turbo",
                    "cividis": "cividis",
                    "CET-L1": "gist_gray",
                    "CET-L1": "gray",
                    "CET-L1": "grey",
                    "CET-L1": "gist_grey",
                    "CET-L1": "bone",
                    "CET-D1": "coolwarm",
                    "CET-L18": "Oranges",
                    "CET-L1": "cubehelix",
                    "CET-L18": "YlOrBr",
                    "CET-D1": "bwr",
                    "CET-CBL1": "gist_earth"}


class LegoThread(QThread):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._matrix = None
        self._vmin = 0
        self._vmax = 0

    def set_data(self, matrix, vmin, vmax):
        self._matrix = matrix.copy()
        self._vmin = vmin
        self._vmax = vmax

    def run(self):
        try:
            vol = Volume(self._matrix)
            lego = vol.legosurface(vmin=self._vmin, vmax=self._vmax)
            self.finished.emit(lego)
        except Exception as e:
            self.error.emit(str(e))


class View3DRenderClass:
    name = "View3DRenderClass"

    def __init__(self, widget, user_name: str, event_bus):
        if not isinstance(widget, QWidget):
            raise TypeError("widget must be a QWidget instance")

        self.user_name = user_name
        self.__widget = widget
        self.__event_bus = event_bus

        # UI элементы
        name = "View3D"
        self.__buttons = {
            'colorless_cube': self.__widget.findChild(QPushButton, f"{name}_colorless_cube"),
            'color_cube': self.__widget.findChild(QPushButton, f"{name}_color_cube"),
            'sphere': self.__widget.findChild(QPushButton, f"{name}_sphere"),
            'transparent_sphere': self.__widget.findChild(QPushButton, f"{name}_transparent_sphere")
        }

        self.__viewXYZ_frame = self.__widget.findChild(QFrame, "view3D_frame")
        self.__hist_frame = self.__widget.findChild(QFrame, "hist_frame")
        self.__color_map_btn_3d = self.__widget.findChild(QPushButton, "color_map_btn_3d")

        self.color_map_btn = ColormapButton("magma", parent=self.__color_map_btn_3d)
        self.color_map_btn.setFixedSize(20, 20)
        self.color_map_btn.setProperty("color", "magma")
        self.color_map_btn.clicked.connect(self.pick_color_map)

        # Настройки
        self.__settings = {
            "mode": "cube_borders",
            "data_range": [0, 1],
            "cmap": "plasma",
        }

        # Состояние
        self.__matrix = None
        self.__volume = None
        self.__plotter = None
        self.__lego_thread = None
        self.__is_rendering = False
        self.__first_render = True
        self.__hist_widget = None

        self.relative_min = 0.5
        self.relative_max = 1
        self.camera = None

        self.__init_view()
        self.__init_histogram()
        self.__init_connections()

        # Таймер для отложенного рендера
        self.__render_timer = QTimer()
        self.__render_timer.setSingleShot(True)
        self.__render_timer.timeout.connect(self.__process_render)

        NodeRegistry.register_output(self.node_out, self.user_name)
        NodeRegistry.register_type("matrix", self.user_name)

        self.set_matrix(self.__generate_demo_data())

    def pick_color_map(self):
        """Открытие диалога выбора цветовой карты"""
        dialog = ColormapDialog()
        if dialog.exec() == QDialog.DialogCode.Accepted:
            cmap_name = dialog.get_selected_cmap()
            self.color_map_btn.setProperty("color", cmap_name)
            self.color_map_btn.cmap_name = cmap_name
            self.__settings['cmap'] = cmap_name
            self.__hist_widget.set_colormap(self.__settings['cmap'])
            self.__render_volume()

    def __generate_demo_data(self):
        """Генерация демонстрационных данных интересной формы"""
        # Создаем пустой объем
        size = 50
        matrix = np.zeros((size, size, size))

        # Координаты центра
        cx, cy, cz = size // 2, size // 2, size // 2

        # Создаем несколько сфер
        spheres = [
            (cx, cy, cz, 10, 1.0),  # центральная сфера
            (cx - 15, cy - 10, cz, 5, 0.8),  # маленькая сфера слева
            (cx + 15, cy + 10, cz, 7, 0.9),  # сфера справа
            (cx + 5, cy - 15, cz, 4, 0.7),  # сфера снизу
            (cx - 5, cy + 15, cz, 6, 0.85),  # сфера сверху
        ]

        # Создаем координатную сетку
        x, y, z = np.mgrid[0:size, 0:size, 0:size]

        # Добавляем сферы
        for sx, sy, sz, radius, intensity in spheres:
            distance = np.sqrt((x - sx) ** 2 + (y - sy) ** 2 + (z - sz) ** 2)
            matrix[distance <= radius] = intensity

        # Добавляем "туннель" или "мостик" между сферами в плоскости XY
        tunnel_start = (cx - 15, cy - 10, cz)
        tunnel_end = (cx + 15, cy + 10, cz)

        # Создаем линию между точками
        t = np.linspace(0, 1, 20)
        for i in range(len(t) - 1):
            x1 = int(tunnel_start[0] + (tunnel_end[0] - tunnel_start[0]) * t[i])
            y1 = int(tunnel_start[1] + (tunnel_end[1] - tunnel_start[1]) * t[i])
            z1 = int(tunnel_start[2] + (tunnel_end[2] - tunnel_start[2]) * t[i])

            x2 = int(tunnel_start[0] + (tunnel_end[0] - tunnel_start[0]) * t[i + 1])
            y2 = int(tunnel_start[1] + (tunnel_end[1] - tunnel_start[1]) * t[i + 1])
            z2 = int(tunnel_start[2] + (tunnel_end[2] - tunnel_start[2]) * t[i + 1])

            # Рисуем толстую линию (мостик)
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    for dz in range(-2, 3):
                        px, py, pz = x1 + dx, y1 + dy, z1 + dz
                        if 0 <= px < size and 0 <= py < size and 0 <= pz < size:
                            matrix[px, py, pz] = 0.7

        # Добавляем тор в плоскости XY (лежит горизонтально, как бублик на столе)
        ring_radius = 15  # Радиус кольца в плоскости XY
        tube_radius = 2  # Радиус трубы тора
        ring_center = (cx, cy, cz)

        # Создаем тор в плоскости XY
        # Тор: кольцо в XY плоскости, высота по Z
        for i in range(size):
            for j in range(size):
                # Расстояние от центра в плоскости XY
                dist_xy = np.sqrt((i - ring_center[0]) ** 2 + (j - ring_center[1]) ** 2)

                # Если точка на кольце в XY плоскости
                if abs(dist_xy - ring_radius) <= tube_radius:
                    # Заполняем по Z (высоте)
                    for k in range(cz - tube_radius, cz + tube_radius + 1):
                        if 0 <= k < size:
                            matrix[i, j, k] = max(matrix[i, j, k], 0.6)

        return matrix

    def __init_view(self):
        """Инициализация 3D вьюпорта"""
        self.vtk_widget = QVTKRenderWindowInteractor(self.__viewXYZ_frame)

        if not self.__viewXYZ_frame.layout():
            from PyQt6.QtWidgets import QVBoxLayout
            layout = QVBoxLayout(self.__viewXYZ_frame)
            layout.setContentsMargins(0, 0, 0, 0)

        self.__viewXYZ_frame.layout().addWidget(self.vtk_widget)

        self.vtk_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.__plotter = Plotter(qt_widget=self.vtk_widget, bg='#1d1d1d', bg2='#303030')

        axes = Axes(self.__volume, xtitle='X', ytitle='Y', ztitle='Z', c='white', xygrid=True, xyalpha=0.15,
                    axes_linewidth=2, grid_linewidth=1, tip_size=0.1, title_font='Calibri', label_font='Calibri')
        self.__plotter.add(axes)

        self.__plotter.renderer.SetAmbient(0.5, 0.5, 0.5)
        self.__plotter.renderer.SetLightFollowCamera(True)
        self.__plotter.renderer.SetTwoSidedLighting(True)

    def __init_histogram(self):
        """Инициализация гистограммы"""
        if self.__hist_frame:
            self.__hist_widget = QHistogramLUTWidget(self.__hist_frame)
            self.__hist_widget.set_levels_callback(self.__hist_range_changed)
            self.__hist_widget.set_colormap('magma')

    def __init_connections(self):
        """Настройка всех соединений"""
        icons = {
            'colorless_cube': colorless_cube_Icon,
            'color_cube': color_cube_Icon,
            'sphere': sphere_Icon,
            'transparent_sphere': transparent_sphere_Icon
        }

        for key, icon in icons.items():
            if self.__buttons[key]:
                self.__buttons[key].setIcon(QIcon(icon))

        modes = {
            'colorless_cube': "cube_borders",
            'color_cube': "cube_volume",
            'sphere': "smooth",
            'transparent_sphere': "smooth_transparent"
        }

        for key, mode in modes.items():
            if self.__buttons[key]:
                self.__buttons[key].clicked.connect(lambda checked, m=mode: self.__change_mode(m))

    def __hist_range_changed(self, min_val, max_val):
        """Обработчик изменения диапазона гистограммы"""
        self.__settings["data_range"] = [min_val, max_val]
        self.__schedule_render()

    def __schedule_render(self):
        """Отложенный рендер для избежания множественных вызовов"""
        if not self.__render_timer.isActive():
            self.__render_timer.start(50)

    def __process_render(self):
        """Основной метод рендера"""
        if self.__is_rendering or self.__matrix is None:
            return

        self.__is_rendering = True
        try:
            self.__render_volume()
        finally:
            self.__is_rendering = False

    def __render_volume(self):
        """Создание и отображение объема"""
        matrix = np.copy(self.__matrix)
        matrix = np.swapaxes(matrix, 0, 2)

        # Получаем данные из гистограммы
        if self.__hist_widget:
            hist_levels = self.__hist_widget.get_levels()
            if hist_levels:
                vmin, vmax = hist_levels[0], hist_levels[1]
            else:
                vmin, vmax = self.__settings["data_range"]
        else:
            vmin, vmax = self.__settings["data_range"]

        max = np.max(matrix)

        self.relative_min = vmin / (max if max != 0 else 1)
        self.relative_max = vmax / (max if max != 0 else 1)

        # Обнуляем все что вне диапазона
        matrix[(matrix < vmin) | (matrix > vmax)] = 0

        # Очистка всех объектов
        if self.__plotter:
            self.__plotter.clear()

        self.__render_3d(matrix, vmin, vmax)

    def __render_3d(self, matrix, vmin, vmax):
        """Рендер 3D режимов"""
        mode = self.__settings["mode"]

        if mode in ("cube_borders", "cube_volume"):
            self.__render_lego(matrix, vmin, vmax, mode)
        elif mode == "smooth":
            self.__volume = Volume(matrix).isosurface(value=vmin)
            self.__volume.cmap(pg_to_vedo_cmap[self.__settings["cmap"]])
            self.__display_volume()
        elif mode == "smooth_transparent":
            self.__volume = Volume(matrix).mode(1)
            self.__volume.cmap(pg_to_vedo_cmap[self.__settings["cmap"]])
            self.__display_volume()

    def __render_lego(self, matrix, vmin, vmax, mode):
        """Рендер lego режимов в отдельном потоке"""
        if self.__lego_thread and self.__lego_thread.isRunning():
            self.__lego_thread.terminate()
            self.__lego_thread.wait()

        self.__lego_thread = LegoThread()
        self.__lego_thread.set_data(matrix, vmin, vmax)
        self.__lego_thread.finished.connect(
            lambda vol: self.__display_lego_volume(vol, mode)
        )
        self.__lego_thread.error.connect(lambda e: print(f"Lego error: {e}"))
        self.__lego_thread.start()

    def __display_lego_volume(self, volume, mode):
        """Отображение lego объема с правильной окраской"""
        if mode == "cube_borders":
            volume.color('white')
            volume.lw(0.5)
            volume.lc('black')
        elif mode == "cube_volume":
            volume.cmap(pg_to_vedo_cmap[self.__settings["cmap"]])

        self.__display_volume(volume)

    def __display_volume(self, volume=None):
        """Отображение готового объема"""
        if volume:
            self.__volume = volume

        if not self.__volume:
            return

        # Добавляем объем в плоттер
        if self.camera is not None:
            self.camera = self.__plotter.camera
        self.__plotter.add(self.__volume)
        axes = Axes(self.__volume, xtitle='X', ytitle='Y', ztitle='Z', c='white', xygrid=True, xyalpha=0.15,
                    axes_linewidth=2, grid_linewidth=1, tip_size=0.1, title_font='Calibri', label_font='Calibri')
        self.__plotter.add(axes)

        if self.__first_render:
            self.__plotter.add_shadows()  # Тени
            self.__plotter.add_ambient_occlusion(radius=20.0, samples=50)  # Ambient occlusion

            if self.camera is None:
                self.__plotter.show(viewup='z', azimuth=45, elevation=35.264)
                self.camera = self.__plotter.camera
            else:
                self.__plotter.show(viewup='z', camera=self.camera)
            self.__first_render = False
        else:
            self.__plotter.render()

    def __change_mode(self, mode):
        """Смена режима отображения"""
        if not self.__is_rendering:
            self.__settings["mode"] = mode
            self.__schedule_render()

    def clear(self):
        if self.__lego_thread and self.__lego_thread.isRunning():
            self.__lego_thread.terminate()
            self.__lego_thread.wait()
            self.__lego_thread = None

        # Очистка всех объектов из плоттера
        if self.__plotter:
            self.__plotter.clear()
            self.__volume = None

    def set_matrix(self, matrix):
        """Установка новой матрицы данных"""
        # Остановка работающего потока
        self.clear()

        self.__matrix = matrix

        if self.__hist_widget:
            self.__hist_widget.set_data(matrix)
            self.__hist_widget.set_levels(self.relative_min * np.max(matrix), self.relative_max * np.max(matrix))
            levels = self.__hist_widget.get_levels()
            if levels:
                self.__settings["data_range"] = list(levels)

        self.__first_render = True
        self.__schedule_render()

    def node_out(self, dataset, params, id):
        dtype = detect_data_type(dataset)

        if dtype == "empty":
            self.clear()
            return False, "Пустой датасет"
        show_data = list()

        if dtype == "matrix_list_2d":
            show_data = dataset
        elif dtype == "matrix_2d":
            show_data.append(dataset)
        elif dtype == "matrix_3d":
            show_data = dataset

        if show_data is not None:
            self.set_matrix(np.array(show_data))
            return True, ""

        self.clear()
        return False, "Требуется 2D numpy array или список 2D numpy arrays"

    def matrixshow_TreeData(self, data, reason):
        """ Стандартный метод преобразования данных от TreeModule в матрицу и отображения данных """
        if reason in ["selection", "clicked"]:
            return False

        self.__tree_data = data

        if not self.__tree_data:
            self.clear()
            return

        show_data = list()

        result = False
        for params, dataset_list, vis_list, select_list in data:
            if params["visibility"] is True:
                for dataset, visibility, select in zip(dataset_list, vis_list, select_list):
                    if visibility is True:
                        show_data.append(dataset)
                        result = True

        if result is False:
            print("Ошибка отображения")
            return

        self.set_matrix(np.array(show_data))
