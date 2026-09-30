import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QGridLayout, QWidget, QLabel, QScrollArea, QFrame
from PyQt6.QtGui import QColor, QPainter, QLinearGradient, QBrush, QPen


class ColormapButton(QPushButton):
    """Кнопка с градиентом цветовой карты"""

    def __init__(self, cmap_name, parent=None):
        super().__init__(parent)
        self.cmap_name = cmap_name
        self.setFixedSize(80, 25)
        self.setCheckable(True)
        self.setToolTip(cmap_name)
        self.setFlat(True)

    def paintEvent(self, event):
        """Рисуем градиент на кнопке"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Получаем цветовую карту из pyqtgraph
        cmap = pg.colormap.get(self.cmap_name)
        if cmap is None:
            cmap = pg.colormap.get('viridis')

        # Создаем градиент
        gradient = QLinearGradient(0, 0, self.width(), 0)
        for i in range(10):
            position = i / 9.0
            color = cmap.map(position)
            qcolor = QColor(int(color[0]), int(color[1]), int(color[2]), 255)
            gradient.setColorAt(position, qcolor)

        # Рисуем градиент
        painter.setBrush(QBrush(gradient))

        # Рамка для выбранной кнопки
        if self.isChecked():
            painter.setPen(QPen(QColor(255, 255, 255), 2))
        else:
            painter.setPen(QPen(QColor(80, 80, 80), 1))

        painter.drawRect(1, 1, self.width() - 2, self.height() - 2)


class ColormapDialog(QDialog):
    """Диалог выбора цветовой карты"""

    def __init__(self, parent=None, cmap=None):
        super().__init__(parent)
        self.setWindowTitle("Выбор цветовой карты")
        self.setMinimumSize(400, 250)
        self.selected_cmap = 'viridis'

        self.cmap = cmap

        self.create_demo_data()
        self.initUI()

    def initUI(self):
        """Инициализация интерфейса"""
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Левая часть - список цветовых карт
        left_frame = QFrame()
        left_frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Sunken)
        left_layout = QVBoxLayout(left_frame)
        left_layout.setSpacing(5)
        left_layout.setContentsMargins(5, 5, 5, 5)

        # Скролл область для кнопок
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameStyle(QFrame.Shape.NoFrame)
        scroll_widget = QWidget()
        self.grid_layout = QGridLayout(scroll_widget)
        self.grid_layout.setSpacing(3)
        self.grid_layout.setContentsMargins(3, 3, 3, 3)
        scroll_area.setWidget(scroll_widget)

        # Популярные цветовые карты

        if self.cmap is None:
            colormaps = ["inferno", "viridis", "magma", "plasma", "turbo", "cividis", "CET-L1", "CET-D1",
                     "CET-L18", "CET-D1", "CET-CBL1",]
        else:
            colormaps = self.cmap

        self.cmap_buttons = []
        row, col = 0, 0
        for cmap_name in colormaps:
            button = ColormapButton(cmap_name)
            button.clicked.connect(lambda checked, name=cmap_name: self.on_cmap_selected(name))
            self.grid_layout.addWidget(button, row, col)
            self.cmap_buttons.append(button)

            col += 1
            if col >= 3:  # 3 кнопки в ряд
                col = 0
                row += 1

        left_layout.addWidget(scroll_area)

        # Правая часть - предпросмотр
        right_frame = QFrame()
        right_frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Sunken)
        right_layout = QVBoxLayout(right_frame)
        right_layout.setSpacing(5)
        right_layout.setContentsMargins(5, 5, 5, 5)

        # График для предпросмотра с прозрачным фоном
        self.graphics_view = pg.GraphicsLayoutWidget()
        self.graphics_view.setBackground(None)

        self.plot = self.graphics_view.addPlot()
        self.plot.setAspectLocked(True)
        self.plot.setMouseEnabled(x=False, y=False)
        self.plot.hideButtons()

        self.image_item = pg.ImageItem()
        self.plot.addItem(self.image_item)

        self.plot.hideAxis('left')
        self.plot.hideAxis('bottom')

        # Colorbar
        self.colorbar = pg.ColorBarItem(
            values=(0, 1),
            colorMap=pg.colormap.get('viridis'),
            width=10
        )
        self.colorbar.setImageItem(self.image_item)

        right_layout.addWidget(self.graphics_view)

        # Информация и кнопки
        bottom_layout = QHBoxLayout()
        self.info_label = QLabel("viridis")
        bottom_layout.addWidget(self.info_label)
        bottom_layout.addStretch()

        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        ok_button.setFixedWidth(60)
        cancel_button.setFixedWidth(60)
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)

        bottom_layout.addWidget(ok_button)
        bottom_layout.addWidget(cancel_button)

        right_layout.addLayout(bottom_layout)

        # Добавляем панели в главный layout
        main_layout.addWidget(left_frame, 2)
        main_layout.addWidget(right_frame, 3)

        # Выбираем первую цветовую карту по умолчанию
        if self.cmap_buttons:
            self.cmap_buttons[0].setChecked(True)
            self.on_cmap_selected('viridis')

    def create_demo_data(self):
        """Создание демонстрационных данных"""
        x = np.linspace(-2, 2, 100)
        y = np.linspace(-2, 2, 100)
        X, Y = np.meshgrid(x, y)

        self.demo_data = (
                np.sin(X) * np.cos(Y) +
                0.5 * np.sin(2 * X) * np.cos(2 * Y) +
                0.3 * np.cos(3 * X) * np.sin(3 * Y)
        )

        self.demo_data = (self.demo_data - self.demo_data.min()) / (self.demo_data.max() - self.demo_data.min())

    def on_cmap_selected(self, cmap_name):
        """Обработка выбора цветовой карты"""
        self.selected_cmap = cmap_name

        for button in self.cmap_buttons:
            button.setChecked(button.cmap_name == cmap_name)

        self.update_preview(cmap_name)
        self.info_label.setText(cmap_name)

    def update_preview(self, cmap_name):
        """Обновление предпросмотра с новой цветовой картой"""
        pg_cmap = pg.colormap.get(cmap_name)
        if pg_cmap is None:
            pg_cmap = pg.colormap.get('viridis')

        self.image_item.setImage(self.demo_data.T)
        self.image_item.setLookupTable(pg_cmap.getLookupTable(0.0, 1.0, 256))
        self.colorbar.setColorMap(pg_cmap)

    def get_selected_cmap(self):
        """Возвращает выбранную цветовую карту"""
        return self.selected_cmap