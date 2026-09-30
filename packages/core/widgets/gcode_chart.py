import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import QVBoxLayout
from PyQt6.QtGui import QColor


class GcodeChart:
    def __init__(self, parent, workspace_size):
        self.__parent = parent
        self.__size_x = workspace_size['x']
        self.__size_y = workspace_size['y']

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('#303030')
        self.plot_widget.getViewBox().setAspectLocked(True, ratio=1)

        layout = QVBoxLayout(self.__parent)
        layout.addWidget(self.plot_widget)
        self.__parent.setLayout(layout)

        self.add_axes()
        self.lines = []

    def add_axes(self):
        step_x = self.__size_x / 16
        step_y = self.__size_y / 16

        # Оси
        self.plot_widget.plot([0, self.__size_x], [0, 0], pen=pg.mkPen('r', width=2))
        self.plot_widget.plot([0, 0], [0, self.__size_y], pen=pg.mkPen('b', width=2))

        # Сетка
        x = 0
        while x < self.__size_x:
            x += step_x
            self.plot_widget.plot([x, x], [0, self.__size_y],
                                  pen=pg.mkPen(color=(255, 255, 255, 50), width=1))

        y = 0
        while y < self.__size_y:
            y += step_y
            self.plot_widget.plot([0, self.__size_x], [y, y],
                                  pen=pg.mkPen(color=(255, 255, 255, 50), width=1))

    def show_data(self, X, Y, colors=None):
        # Удаляем старые линии
        for line in self.lines:
            self.plot_widget.removeItem(line)
        self.lines.clear()

        # Просто рисуем одну линию белым цветом
        points = np.column_stack([X, Y])
        line = self.plot_widget.plot(points[:, 0], points[:, 1],
                                     pen=pg.mkPen('w', width=1))
        self.lines.append(line)

        if len(X) > 0:
            self.plot_widget.autoRange()