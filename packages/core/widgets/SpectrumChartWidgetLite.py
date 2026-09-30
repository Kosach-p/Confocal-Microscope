import numpy as np
import pyqtgraph as pg
from PyQt6 import QtWidgets


class SpectrumChart(QtWidgets.QWidget):
    """
    Простой виджет для отображения спектров.
    Можно поместить в любой layout.
    """

    def __init__(self):
        super().__init__()

        # Для блокировки QGraphicsView
        self._graphics_view = None

        # Основной layout
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # PlotWidget для графика
        self.plot_widget = pg.PlotWidget()
        layout.addWidget(self.plot_widget)

        # Настройка внешнего вида
        self.plot_widget.setBackground(None)
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding
        )

        # Настройка осей
        for axis in ['left', 'bottom']:
            ax = self.plot_widget.getAxis(axis)
            ax.setPen('w')
            ax.setTextPen('w')

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

    def plot(self, data, color='w', linewidth=1):
        """
        Построение графиков.
        Принимает:
        - [x, y] - одиночный спектр
        - [[x, y], [x, y], ...] - список спектров
        """
        # Очищаем предыдущие графики
        self.plot_widget.clear()

        # Проверяем, является ли data списком спектров
        if isinstance(data, list) and len(data) > 0:
            # Проверяем первый элемент
            first_element = data[0]

            # Если первый элемент - список/массив, и он содержит 2 элемента (x, y)
            if isinstance(first_element, (list, np.ndarray)) and len(first_element) == 2:
                # Проверяем, является ли это [[x, y], [x, y], ...]
                if isinstance(first_element[0], (list, np.ndarray)):
                    # Это список спектров [[x, y], [x, y], ...]
                    for spectrum in data:
                        if len(spectrum) >= 2:
                            self._plot_single(spectrum[0], spectrum[1], color, linewidth)
                else:
                    # Это одиночный спектр [x, y]
                    self._plot_single(first_element[0], first_element[1], color, linewidth)
            else:
                # Возможно, это просто [x, y] где x и y - списки
                if len(data) >= 2:
                    self._plot_single(data[0], data[1], color, linewidth)
        else:
            print("ERROR: Неверный формат данных")

    def _plot_single(self, x, y, color='w', linewidth=1):
        """Построение одного графика"""
        try:
            x = np.array(x)
            y = np.array(y)

            # Сортировка по x
            idx = np.argsort(x)
            x = x[idx]
            y = y[idx]

            pen = pg.mkPen(color, width=linewidth)
            self.plot_widget.plot(x, y, pen=pen)
            return True
        except Exception as e:
            print(f"ERROR::SpectrumChart::_plot_single:: {e}")
            return False

    def clear(self):
        """Очистка графика"""
        self.plot_widget.clear()