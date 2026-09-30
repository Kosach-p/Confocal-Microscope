from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QFrame, QDialog, QCheckBox,
                             QDialogButtonBox, QSpinBox, QGroupBox, QGridLayout,
                             QDoubleSpinBox)
from PyQt6.QtCore import Qt, pyqtSignal
import numpy as np
import pyqtgraph as pg
from Icon.IconName import *
from PyQt6.QtGui import QIcon

# ========== Константы ==========
_STATS_KEYS = ['mean', 'std', 'min', 'max']
_STATS_NAMES = {
    'mean': 'Среднее', 'std': 'СКО',
    'min': 'Минимум', 'max': 'Максимум'
}

# ========== Тема ==========
LIGHT_THEME = {
    'plot_bg': '#ffffff',
    'axis_pen': '#000000',
    'axis_text': '#000000',
    'grid_alpha': 0.2,
    'curve': '#000000',
    'sma_curve': '#ff6600',
    'mean_line': '#cc0000',
}

DARK_THEME = {
    'plot_bg': '#3d3d3d',
    'axis_pen': '#ffffff',
    'axis_text': '#ffffff',
    'grid_alpha': 0.3,
    'curve': '#ffffff',
    'sma_curve': '#ff8800',
    'mean_line': '#ffcc00',
}


class SettingsDialog(QDialog):
    """Диалог настроек виджета счётчика фотонов"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки счётчика фотонов")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        # Основной фрейм
        main_frame = QFrame()
        main_layout = QVBoxLayout(main_frame)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Группа отображения
        group = QGroupBox("Отображение")
        grid = QGridLayout(group)

        # Сетка 2x2: чекбоксы слева, параметры справа
        self.show_main_curve_cb = QCheckBox("Показывать основной график")
        self.show_main_curve_cb.setChecked(parent._show_main_curve)
        grid.addWidget(self.show_main_curve_cb, 0, 0)

        self.show_mean_cb = QCheckBox("Показывать линию среднего")
        self.show_mean_cb.setChecked(parent._show_mean_line)
        grid.addWidget(self.show_mean_cb, 1, 0)

        self.show_sma_cb = QCheckBox("Показывать скользящее среднее")
        self.show_sma_cb.setChecked(parent._show_sma)
        grid.addWidget(self.show_sma_cb, 0, 1)

        # Параметры СМА (окно)
        hbox = QHBoxLayout()
        self.sma_window = QSpinBox()
        self.sma_window.setRange(2, 100)
        self.sma_window.setValue(parent._sma_window)
        hbox.addWidget(self.sma_window)
        hbox.addWidget(QLabel("точек"))
        hbox.addStretch()
        grid.addLayout(hbox, 1, 1)

        main_layout.addWidget(group)

        # Группа сглаживания статистики (EMA)
        group = QGroupBox("Сглаживание статистики (EMA)")
        grid = QGridLayout(group)

        self.smooth_alpha = QDoubleSpinBox()
        self.smooth_alpha.setRange(0.01, 1)
        self.smooth_alpha.setSingleStep(0.05)
        self.smooth_alpha.setValue(parent._smooth_alpha)
        self.smooth_alpha.setDecimals(2)

        grid.addWidget(QLabel("Коэффициент сглаживания (α):"), 0, 0)
        grid.addWidget(self.smooth_alpha, 0, 1)
        grid.addWidget(QLabel("1 = без сглаживания, 0.01 = сильное сглаживание"), 1, 0, 1, 2)
        main_layout.addWidget(group)

        # Группа статистики
        group = QGroupBox("Отображаемая статистика")
        grid = QGridLayout(group)
        self.stats_cb = {}
        for i, key in enumerate(_STATS_KEYS):
            cb = QCheckBox(_STATS_NAMES[key])
            cb.setChecked(parent._visible_stats.get(key, True))
            self.stats_cb[key] = cb
            grid.addWidget(cb, i // 2, i % 2)
        main_layout.addWidget(group)

        # Кнопки
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                   QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        for btn in buttons.buttons():
            btn.setMinimumWidth(100)
            btn.setMinimumHeight(30)

        main_layout.addWidget(buttons)

        dialog_layout = QVBoxLayout(self)
        dialog_layout.setContentsMargins(0, 0, 0, 0)
        dialog_layout.addWidget(main_frame)

    def get_settings(self):
        return {
            'show_main_curve': self.show_main_curve_cb.isChecked(),
            'show_mean': self.show_mean_cb.isChecked(),
            'show_sma': self.show_sma_cb.isChecked(),
            'sma_window': self.sma_window.value(),
            'smooth_alpha': self.smooth_alpha.value(),
            'stats': {k: cb.isChecked() for k, cb in self.stats_cb.items()}
        }


class PhotonCounterWidget(QWidget):
    """
    Виджет для отображения счётчика фотонов в реальном времени.
    Содержит график, крупное текущее значение и статистику.
    """

    value_changed = pyqtSignal(int)
    reset_clicked = pyqtSignal()
    name = "PhotonCounter"

    def __init__(self, parent=None, event_bus=None):
        super().__init__(parent)
        self._event_bus = event_bus
        self._current_theme = DARK_THEME  # По умолчанию тёмная

        if event_bus:
            event_bus.PhotonCounterControl.connect(self._event_process)
            event_bus.Settings.connect(self._event_process)

        # Параметры
        self._points_count = 100
        self._step_x = 0.1
        self._polling_time_ms = 100
        self._show_main_curve = True
        self._show_mean_line = True
        self._show_sma = False
        self._sma_window = 5
        self._visible_stats = {k: True for k in _STATS_KEYS}
        self._smooth_alpha = 0.3
        self._paused = False

        self.btn_size = 30

        # Данные (кольцевой буфер)
        self._data = np.full(self._points_count, np.nan)
        self._sma_data = np.full(self._points_count, np.nan)
        self._index = 0
        self._x_data = np.arange(self._points_count) * self._step_x
        self._last_value = 0

        # Сглаженные значения статистики (EMA)
        self._smoothed_mean = None
        self._smoothed_std = None

        # Настройка родительского контейнера
        if parent and parent.layout() is None:
            parent.setLayout(QVBoxLayout(parent))
            parent.layout().setContentsMargins(0, 0, 0, 0)
        if parent:
            parent.layout().addWidget(self)

        self._setup_ui()

    # ========== Обработка событий ==========

    def _event_process(self, transmitter, receiver, command, data):
        if transmitter == self.name or receiver not in (self.name, "All"):
            return

        if transmitter == "PhotonCounterControlClass":
            if command == "RegularPhotonCount" and not self._event_bus.ProgramBusy:
                self.set_value(data[0]['count'])
            elif command == "new_polling_time_ms":
                self.set_polling_time(data[0])

        elif command == "qss_update":
            # Определяем тему
            theme_name = data[0]["General"]["theme"]
            if theme_name == "dark":
                self._current_theme = DARK_THEME
            elif theme_name == "light":
                self._current_theme = LIGHT_THEME

            # Применяем тему
            self._apply_theme()

    def _apply_theme(self):
        """Применяет текущую тему к графику"""
        t = self._current_theme

        # Обновляем фон
        self._plot.setBackground(t['plot_bg'])

        # Обновляем фон ViewBox
        view_box = self._plot.getPlotItem().getViewBox()
        view_box.setBackgroundColor(t['plot_bg'])

        # Обновляем перья кривых
        self._curve.setPen(pg.mkPen(color=t['curve'], width=1))
        self._sma_curve.setPen(pg.mkPen(color=t['sma_curve'], width=2, style=Qt.PenStyle.DashLine))
        self._mean_line.setPen(pg.mkPen(color=t['mean_line'], width=2, style=Qt.PenStyle.DashLine))

        # Обновляем оси
        for axis_name in ['left', 'bottom']:
            ax = self._plot.getAxis(axis_name)
            ax.setPen(t['axis_pen'])
            ax.setTextPen(t['axis_text'])

        # Обновляем сетку
        self._plot.showGrid(x=True, y=True, alpha=t['grid_alpha'])

        # Принудительное обновление
        self._plot.update()
        self._plot.repaint()

        if self._plot.scene():
            self._plot.scene().update()

    # ========== Публичные методы ==========

    def set_text(self, text: str):
        self._value_display.setText(text)

    def set_value(self, value: int):
        if self._paused or value is None:
            return

        self._last_value = value
        self._data[self._index] = value

        # Расчёт скользящего среднего для графика
        if self._show_sma:
            start = max(0, self._index - self._sma_window + 1)
            window = self._data[start:self._index + 1]
            valid = window[~np.isnan(window)]
            self._sma_data[self._index] = np.mean(valid) if len(valid) > 0 else np.nan

        self._index = (self._index + 1) % self._points_count
        self._update_display()
        self._update_statistics()

    def set_polling_time(self, time_ms: int):
        self._polling_time_ms = time_ms
        self._step_x = time_ms / 1000
        self._x_data = np.arange(self._points_count) * self._step_x
        self._update_display()

    def reset(self):
        self._data.fill(np.nan)
        self._sma_data.fill(np.nan)
        self._index = 0
        self._last_value = 0
        self._smoothed_mean = None
        self._smoothed_std = None
        self._update_display()
        self._update_statistics()
        self.reset_clicked.emit()

    def toggle_pause(self):
        self._paused = not self._paused
        if self._paused:
            self._pause_btn.setIcon(QIcon(play_Icon))
        else:
            self._pause_btn.setIcon(QIcon(pause_Icon))

    def open_settings(self):
        dialog = SettingsDialog(self)
        if dialog.exec():
            s = dialog.get_settings()
            self._show_main_curve = s['show_main_curve']
            self._show_mean_line = s['show_mean']
            self._show_sma = s['show_sma']
            self._sma_window = s['sma_window']
            self._smooth_alpha = s['smooth_alpha']
            self._visible_stats = s['stats']

            self._curve.setVisible(self._show_main_curve)
            self._mean_line.setVisible(self._show_mean_line)
            self._sma_curve.setVisible(self._show_sma)

            self._smoothed_mean = None
            self._smoothed_std = None

            self._update_statistics()
            if not self._show_sma:
                self._sma_data.fill(np.nan)

    # ========== Приватные методы ==========

    def _get_ring_data(self, arr):
        if self._index == 0:
            return arr
        return np.concatenate([arr[self._index:], arr[:self._index]])

    def _ema(self, prev, current, alpha):
        if prev is None:
            return current
        return alpha * current + (1 - alpha) * prev

    def _update_display(self):
        if not np.isnan(self._last_value):
            formatted = f"{self._last_value:,.0f}".replace(',', ' ')
            self._value_display.setText(formatted)
        else:
            self._value_display.setText("0")

        data = self._get_ring_data(self._data)
        self._curve.setData(self._x_data, data)

        if self._show_sma:
            sma = self._get_ring_data(self._sma_data)
            self._sma_curve.setData(self._x_data, sma)

    def _update_statistics(self):
        valid = self._data[~np.isnan(self._data)]
        if len(valid) < 2:
            for lbl in self._stats_labels.values():
                lbl.setText("--")
            self._mean_line.setVisible(False)
            return

        current_mean = np.mean(valid)
        current_std = np.std(valid)
        current_min = np.min(valid)
        current_max = np.max(valid)

        self._smoothed_mean = self._ema(self._smoothed_mean, current_mean, self._smooth_alpha)
        self._smoothed_std = self._ema(self._smoothed_std, current_std, self._smooth_alpha)

        stats = {
            'mean': self._smoothed_mean,
            'std': self._smoothed_std,
            'min': current_min,
            'max': current_max,
        }

        for key, lbl in self._stats_labels.items():
            if self._visible_stats.get(key, True):
                val = stats[key]
                if key in ['min', 'max']:
                    formatted = f"{val:,.0f}".replace(',', ' ')
                else:
                    formatted = f"{val:,.3f}".replace(',', ' ').rstrip('0').rstrip('.')
                lbl.setText(formatted)
                lbl.setVisible(True)
            else:
                lbl.setVisible(False)

        if self._show_mean_line and self._smoothed_mean is not None:
            self._mean_line.setValue(self._smoothed_mean)
            self._mean_line.setVisible(True)

    # ========== UI построение ==========

    def _setup_ui(self):
        main = QVBoxLayout(self)
        main.setSpacing(5)
        main.setContentsMargins(5, 5, 5, 5)

        top = QHBoxLayout()

        self._plot = pg.PlotWidget()
        self._plot.setLabel('left', 'Счёт', units='фотоны')
        self._plot.setLabel('bottom', 'Время', units='сек')
        self._plot.setMinimumHeight(150)

        for axis in ['left', 'bottom']:
            ax = self._plot.getAxis(axis)
            ax.autoSIPrefix = False

        self._curve = self._plot.plot()
        self._sma_curve = self._plot.plot()
        self._sma_curve.setVisible(False)
        self._mean_line = pg.InfiniteLine(angle=0)
        self._mean_line.setVisible(False)
        self._plot.addItem(self._mean_line)

        # Применяем тему по умолчанию
        self._apply_theme()

        top.addWidget(self._plot)

        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(8)

        self._reset_btn = QPushButton()
        self._reset_btn.setFixedSize(self.btn_size, self.btn_size)
        self._reset_btn.setIcon(QIcon(clear_Icon))
        self._reset_btn.clicked.connect(self.reset)

        self._pause_btn = QPushButton()
        self._pause_btn.setFixedSize(self.btn_size, self.btn_size)
        self._pause_btn.setIcon(QIcon(pause_Icon))
        self._pause_btn.clicked.connect(self.toggle_pause)

        self._settings_btn = QPushButton()
        self._settings_btn.setFixedSize(self.btn_size, self.btn_size)
        self._settings_btn.setIcon(QIcon(settings_Icon))
        self._settings_btn.clicked.connect(self.open_settings)

        btn_layout.addWidget(self._reset_btn)
        btn_layout.addWidget(self._pause_btn)
        btn_layout.addWidget(self._settings_btn)
        btn_layout.addStretch()
        top.addLayout(btn_layout)
        main.addLayout(top)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        main.addWidget(line)

        bottom = QHBoxLayout()

        left_frame = QFrame()
        left_frame.setFixedWidth(180)
        left_layout = QVBoxLayout(left_frame)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._value_display = QLabel("0")
        self._value_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._value_display.setMinimumWidth(150)
        self._value_display.setStyleSheet("font-size: 30px;")
        left_layout.addWidget(self._value_display)

        bottom.addWidget(left_frame)

        vline = QFrame()
        vline.setFrameShape(QFrame.Shape.VLine)
        bottom.addWidget(vline)

        stats_frame = QFrame()
        stats_frame.setMaximumWidth(400)
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setSpacing(20)
        stats_layout.setContentsMargins(10, 5, 10, 5)

        self._stats_labels = {}

        for col_idx, keys in enumerate([['mean', 'std'], ['min', 'max']]):
            col = QVBoxLayout()
            col.setSpacing(3)
            for key in keys:
                name = _STATS_NAMES[key]
                label = QLabel(f"{name}:")
                col.addWidget(label)
                lbl = QLabel("--")
                lbl.setMinimumWidth(80)
                self._stats_labels[key] = lbl
                col.addWidget(lbl)
            stats_layout.addLayout(col)

        bottom.addWidget(stats_frame)
        main.addLayout(bottom)