import numpy as np
import pyqtgraph as pg
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtWidgets import QLabel
from PyQt6.QtGui import QTransform
from packages.Floating_window.node_editor.NodeRegistry import NodeRegistry
from packages.core.validators.dataValidator import detect_data_type
from PyQt6.QtWidgets import QApplication


class ImageView:
    """
    Встраивает pyqtgraph ImageView в существующий frame.
    """

    def __init__(self, frame: QtWidgets.QWidget, user_name: str, event_bus):
        layout = QtWidgets.QVBoxLayout()
        frame.setLayout(layout)
        self.user_name = user_name
        self.event_bus = event_bus

        self.graphics_layout = pg.GraphicsLayoutWidget()
        layout.addWidget(self.graphics_layout)

        # Добавляем PlotItem с осями
        self.view = self.graphics_layout.addPlot(row=0, col=0)
        self.view.setAspectLocked(True)
        self.view.showAxis('top')
        self.view.showAxis('right')
        self.view.setLabel('bottom', "X, LSB", **{'color': 'w', 'size': '12pt'})
        self.view.setLabel('left', "Y, LSB", **{'color': 'w', 'size': '12pt'})

        # Белые оси
        for axis in ['left', 'bottom', 'top', 'right']:
            ax = self.view.getAxis(axis)
            ax.setPen(pg.mkPen('w'))
            ax.setTextPen('w')

        # Прозрачный фон
        self.graphics_layout.setBackground(None)
        self.view.getViewBox().setBackgroundColor(None)

        # Добавляем ImageItem в PlotItem
        self.image_item = pg.ImageItem()
        self.view.addItem(self.image_item)

        # Добавляем HistogramLUTItem внизу (вторая строка)
        self.hist = pg.HistogramLUTItem(orientation='horizontal')
        self.graphics_layout.addItem(self.hist, row=1, col=0)
        self.hist.setImageItem(self.image_item)
        self.hist.gradient.setColorMap(pg.colormap.get('magma'))
        self.hist.setFixedHeight(100)

        self.view.invertY(False)

        # === КООРДИНАТЫ ===
        self.coord_label = QLabel("x: --, y: --, val: --", self.graphics_layout)
        self.coord_label.hide()

        # Подключаем движение мыши
        self.view.scene().sigMouseMoved.connect(self._on_mouse_moved)
        self.graphics_layout.leaveEvent = self._on_leave

        # === ВЫБОР ОБЛАСТИ ПО CTRL+ЛКМ ===
        self.selecting = False
        self.start_pos = None
        self.callback = None
        self.roi = pg.RectROI(
            [0, 0], [1, 1],
            pen=pg.mkPen('w', width=1, style=QtCore.Qt.PenStyle.DashLine),
            movable=True,
            removable=True
        )
        self.roi.hide()
        self.roi.sigRegionChanged.connect(self._on_roi_changed)
        self.view.addItem(self.roi)

        self.view.scene().sigMouseClicked.connect(self._on_mouse_clicked)
        self.on_roi_selected = None

        self.__tree_data = []

        NodeRegistry.register_input(self.node_in, self.user_name)
        NodeRegistry.register_output(self.node_out, self.user_name)
        NodeRegistry.register_type("matrix", self.user_name)

        self.event_bus.Settings.connect(self.__event_process)

    def __event_process(self, transmitter, receiver, command, data):
        """ Обработчик emit в выбранном канале """
        if receiver == "All":
            if command == "qss_update":
                self.graphics_layout.setBackground(None)
                self.view.getViewBox().setBackgroundColor(None)

                self.graphics_layout.update()
                self.view.update()

                if self.view.scene():
                    self.view.scene().update()

    def node_in(self):
        """ функция возвращает данные для входной ноды """
        return self.__tree_data

    def node_out(self, dataset, params, id):
        dtype = detect_data_type(dataset)
        print("Выход ноды")
        if dtype == "empty":
            self.imshow(None)
            return False, "Пустой датасет"
        data = None

        if dtype == "matrix_list_2d":
            data = dataset[0]
        elif dtype == "matrix_2d":
            data = dataset
        elif dtype == "matrix_3d":
            data = dataset[0, :, :]

        if data is not None:
            self.imshow(data, cmap=params.get("color"))
            return True, ""

        self.imshow(None)
        return False, "Требуется 2D numpy array или список 2D numpy arrays"

    def _on_mouse_moved(self, pos):
        """Показ координат и значения пикселя"""
        if self.view.sceneBoundingRect().contains(pos):
            mouse_point = self.view.getViewBox().mapSceneToView(pos)
            x = f"{mouse_point.x():,.2f}".replace(',', ' ')
            y = f"{mouse_point.y():,.2f}".replace(',', ' ')
            self.coord_label.setText(f"x: {x}, y: {y}")
            self.coord_label.adjustSize()

            parent_width = self.graphics_layout.width()
            parent_height = self.graphics_layout.height()
            self.coord_label.move(parent_width - self.coord_label.width() - 40, 40)
            self.coord_label.show()

            if self.selecting and self.start_pos is not None:
                self._update_roi(pos)
        else:
            self.coord_label.hide()

    def _on_leave(self, event):
        """Мышь ушла с виджета"""
        self.coord_label.hide()
        pg.GraphicsLayoutWidget.leaveEvent(self.graphics_layout, event)

    def _on_mouse_clicked(self, ev):
        """Обработка кликов"""
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        ctrl_pressed = bool(modifiers & QtCore.Qt.KeyboardModifier.ControlModifier)

        if ev.button() == QtCore.Qt.MouseButton.LeftButton:
            if ctrl_pressed or self.selecting:
                if self.selecting:
                    self.selecting = False
                    self.start_pos = None
                    return
                self.selecting = True
                self.start_pos = ev.scenePos()
                self.roi.show()
                self._update_roi(self.start_pos)
            else:
                if self.roi is not None:
                    self.roi.hide()

    def _on_roi_changed(self):
        pos = self.roi.pos()
        size = self.roi.size()

        x1, y1 = pos.x(), pos.y()
        x2, y2 = pos.x() + size.x(), pos.y() + size.y()

        # Округляем до целых
        x1, y1 = int(round(x1)), int(round(y1))
        x2, y2 = int(round(x2)), int(round(y2))
        if self.callback is not None:
            self.callback(x1, y1, x2, y2)

    def set_roi_callback(self, callback):
        """ Устанавливает callback по изменению roi """
        self.callback = callback

    def _update_roi(self, current_pos):
        """Обновление прямоугольника выделения"""
        if self.start_pos is None:
            return

        start_point = self.view.getViewBox().mapSceneToView(self.start_pos)
        end_point = self.view.getViewBox().mapSceneToView(current_pos)

        x1, y1 = start_point.x(), start_point.y()
        x2, y2 = end_point.x(), end_point.y()

        x_min, x_max = min(x1, x2), max(x1, x2)
        y_min, y_max = min(y1, y2), max(y1, y2)

        self.roi.setPos([x_min, y_min])
        self.roi.setSize([x_max - x_min, y_max - y_min])

    def imshow_TreeData(self, data, reason):
        """ Стандартный метод преобразования данных от TreeModule в X, Y координаты и проверку видимости данных """
        self.__tree_data = data

        if not self.__tree_data:
            self.clear()
            return

        NodeRegistry.send_signal(self.user_name)
        for params, dataset_list, vis_list, select_list in data:
            if params["visibility"] is True:
                for dataset, visibility, select in zip(dataset_list, vis_list, select_list):
                    if visibility is True and select is True:
                        self.clear()
                        parameters = params.get('params', {}).get('parameters', {})
                        self.imshow(dataset, scale_x=parameters.get('step_x', 1), scale_y=parameters.get('step_y', 1),
                                    offset_x=parameters.get('x1', 0), offset_y=parameters.get('y1', 0))
                        return True

        for params, dataset_list, vis_list, select_list in data:
            if params["visibility"] is True:
                for dataset, visibility, select in zip(dataset_list, vis_list, select_list):
                    if visibility is True:
                        if params["selected"] is True:
                            parameters = params.get('params', {}).get('parameters', {})
                            self.imshow(dataset, scale_x=parameters.get('step_x', 1), scale_y=parameters.get('step_y', 1),
                                        offset_x=parameters.get('x1', 0), offset_y=parameters.get('y1', 0))
                            return True

        self.clear()

    def imshow(self, array: np.ndarray, scale_x=1, scale_y=1, offset_x=0, offset_y=0, cmap="magma"):
        if array is None:
            self.clear()
            return False

        if np.isnan(array).all():
            self.clear()
            return False

        array = array.astype(np.float32)
        self.image_item.setImage(array)
        self.image_item.setPos(offset_x, offset_y)

        # Создаём трансформацию масштаба
        tr = QTransform()
        tr.scale(scale_x, scale_y)
        self.image_item.setTransform(tr)

        # Применяем цветовую карту
        self.set_colormap(cmap)

        return True

    def set_colormap(self, cmap_name="magma"):
        """
        Устанавливает цветовую карту для изображения
        """
        # Получаем colormap из pyqtgraph
        pg_cmap = pg.colormap.get(cmap_name)

        if pg_cmap is None:
            print(f"Colormap '{cmap_name}' не найдена, используется 'magma'")
            pg_cmap = pg.colormap.get('magma')

        # Применяем colormap к изображению
        lookup_table = pg_cmap.getLookupTable(0.0, 1.0, 256)
        self.image_item.setLookupTable(lookup_table)

        # Обновляем градиент в HistogramLUTItem
        self.hist.gradient.setColorMap(pg_cmap)

    def Scale_axes(self, scale_x: float, scale_y: float):
        self.view.getAxis("bottom").setScale(scale_x)
        self.view.getAxis("top").setScale(scale_x)
        self.view.getAxis("left").setScale(scale_y)
        self.view.getAxis("right").setScale(scale_y)

    def set_axes_label(self, x_axe="x", y_axe="y"):
        self.view.setLabel('bottom', x_axe, color='w', size='12pt')
        self.view.setLabel('left', y_axe, color='w', size='12pt')

    def clear(self):
        self.image_item.clear()