import os
os.environ['MPLBACKEND'] = 'Agg'  # Использовать неинтерактивный бэкенд
os.environ['PYQTGRAPH_QT_LIB'] = 'PyQt6'  # Укажите вашу библиотеку Qt

import numpy as np
from PyQt6.QtWidgets import QVBoxLayout, QWidget, QSizePolicy
import pyqtgraph as pg



class QHistogramLUTWidget:
    """
    Виджет-обёртка для HistogramLUTItem.
    Встраивается в переданный frame и управляет гистограммой внутри него.
    """

    def __init__(self, frame):
        """
        Args:
            frame: QFrame или любой QWidget, в который будет встроена гистограмма
        """
        self.frame = frame

        layout = QVBoxLayout()
        frame.setLayout(layout)

        # Создаём GraphicsLayoutWidget
        self.graphics_layout = pg.GraphicsLayoutWidget()
        self.graphics_layout.setBackground((0, 0, 0, 0))
        layout.addWidget(self.graphics_layout)

        # Создаём HistogramLUTItem
        self.__hist_lut = pg.HistogramLUTItem(orientation='horizontal')

        # Добавляем в GraphicsLayout
        self.graphics_layout.addItem(self.__hist_lut)

        # Принудительно задаём размеры для ViewBox
        self.__hist_lut.vb.setMaximumWidth(16777215)
        self.__hist_lut.vb.setMaximumHeight(16777215)
        self.__hist_lut.vb.setSizePolicy(
            pg.QtWidgets.QSizePolicy.Expanding,
            pg.QtWidgets.QSizePolicy.Expanding
        )

        self._image_item = pg.ImageItem()
        self.__hist_lut.setImageItem(self._image_item)
        #self.__hist_lut.gradient.setColorMap(pg.colormap.get('magma'))
        self._levels_callback = None

        self.__hist_lut.region.sigRegionChanged.connect(self._on_levels_changed)

    def _update_size(self):
        """Принудительно обновляем размеры гистограммы"""
        if hasattr(self, 'hist_lut'):
            new_width = self.frame.width()
            new_height = self.frame.height()

            if new_width > 0 and new_height > 0:
                # Принудительно устанавливаем размеры
                self.__hist_lut.setGeometry(0, 0, new_width, new_height)

                # Обновляем размер ViewBox
                if hasattr(self.__hist_lut, 'vb'):
                    self.__hist_lut.vb.setGeometry(0, 0, new_width, new_height - 30)

                # Обновляем размер gradient
                if hasattr(self.__hist_lut, 'gradient'):
                    gradient_height = 20
                    self.__hist_lut.gradient.setGeometry(0, new_height - gradient_height,
                                                       new_width, gradient_height)

                self.__hist_lut.updateGeometry()
                self.graphics_layout.updateGeometry()

    def set_data(self, data: np.ndarray):
        """
        Устанавливает данные для построения гистограммы.

        Args:
            data: 1D или 2D numpy массив
        """
        if data.ndim == 1:
            size = int(np.sqrt(len(data)))
            data = data[:size * size].reshape(size, size)

        self._image_item.setImage(data)
        self._data_min = data.min()
        self._data_max = data.max()
        self.__hist_lut.setLevels(self._data_min, self._data_max)
        self._update_size()

    def set_data_3d(self, volume: np.ndarray):
        """ Устанавливает 3D данные — строит гистограмму по всем вокселям. """

        matrix2D = volume.reshape((volume.shape[0], volume.shape[1] * volume.shape[2]))
        self._image_item.setImage(matrix2D)

        self._data_min = volume.min()
        self._data_max = volume.max()
        self.__hist_lut.setLevels(self._data_min, self._data_max)
        self._update_size()

    def _on_levels_changed(self):
        """Внутренний обработчик изменения уровней"""
        if self._levels_callback is not None:
            min_val, max_val = self.get_levels()
            self._levels_callback(min_val, max_val)

    def set_levels_callback(self, callback):
        """Устанавливает callback-функцию, вызываемую при изменении порогов."""
        self._levels_callback = callback

    def get_levels(self):
        """Возвращает текущие уровни (min, max)"""
        return self.__hist_lut.getLevels()

    def set_levels(self, min_val, max_val):
        """Устанавливает уровни"""
        self.__hist_lut.setLevels(min_val, max_val)

    def set_colormap(self, cmap_name: str):
        """Устанавливает цветовую карту"""
        #self.__hist_lut.gradient.setColorMap(pg.colormap.get(cmap_name))

    def set_log_mode(self, x=False, y=False):
        """Устанавливает логарифмический масштаб для гистограммы"""
        self.__hist_lut.plot.setLogMode(x=x, y=y)

    def set_background(self, color):
        """Устанавливает цвет фона"""
        self.graphics_layout.setBackground(color)
