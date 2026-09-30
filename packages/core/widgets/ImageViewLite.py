import numpy as np
import pyqtgraph as pg
from PyQt6 import QtWidgets


class ImageView(QtWidgets.QWidget):
    """
    Простой виджет для отображения 2D массивов.
    Можно поместить в любой layout.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Для блокировки QGraphicsView
        self._graphics_view = None

        # Основной layout
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # GraphicsLayoutWidget для изображения
        self.graphics_layout = pg.GraphicsLayoutWidget()
        layout.addWidget(self.graphics_layout)

        # PlotItem
        self.view = self.graphics_layout.addPlot(row=0, col=0)
        self.view.setAspectLocked(True)
        self.view.hideAxis('top')
        self.view.hideAxis('right')
        self.view.hideAxis('bottom')
        self.view.hideAxis('left')

        # Прозрачный фон
        self.graphics_layout.setBackground(None)
        self.view.getViewBox().setBackgroundColor(None)

        # ImageItem
        self.image_item = pg.ImageItem()
        self.view.addItem(self.image_item)

        self.view.invertY(False)

        # Включаем отслеживание мыши
        self.setMouseTracking(True)

    def _findGraphicsView(self):
        """Находит родительский QGraphicsView"""
        if self._graphics_view:
            return self._graphics_view

        parent = self.parent()
        while parent:
            if isinstance(parent, QtWidgets.QGraphicsView):
                self._graphics_view = parent
                return parent
            parent = parent.parent()
        return None

    def enterEvent(self, event):
        """Мышь вошла в виджет - блокируем перемещение"""
        view = self._findGraphicsView()
        if view:
            view.setInteractive(False)
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Мышь ушла с виджета - разблокируем перемещение"""
        view = self._findGraphicsView()
        if view:
            view.setInteractive(True)
        super().leaveEvent(event)

    def imshow(self, array, cmap="magma"):
        """Отображение 2D массива или первого из списка"""
        # Если передан список - берем первый элемент
        if array is None:
            self.clear()
            return False

        if isinstance(array, list):
            if len(array) == 0:
                self.clear()
                return False
            array = array[0]
        if array.ndim == 3:
            array = array[0, :, :]

        if not isinstance(array, np.ndarray):
            array = np.array(array)

        if array is None:
            self.clear()
            return False

        if np.isnan(array).all():
            self.clear()
            return False
        try:
            self.image_item.setImage(array)
            self.set_colormap(cmap)
        except Exception as e:
            return e
        return True

    def set_colormap(self, cmap_name="magma"):
        """Устанавливает цветовую карту"""
        try:
            import matplotlib.pyplot as plt

            matplotlib_cmap = plt.get_cmap(cmap_name)
            positions = np.linspace(0, 1, 256)
            colors = matplotlib_cmap(positions)[:, :3] * 255
            pg_cmap = pg.ColorMap(positions, colors.astype(np.uint8))
        except Exception as e:
            print(f"Ошибка загрузки colormap '{cmap_name}': {e}")
            pg_cmap = pg.colormap.get('magma')

        lookup_table = pg_cmap.getLookupTable(0.0, 1.0, 256)
        self.image_item.setLookupTable(lookup_table)

    def clear(self):
        """Очистка изображения"""
        self.image_item.clear()