from PyQt6.QtWidgets import QApplication, QLabel
from PyQt6.QtGui import QPixmap, QPainter
from PyQt6.QtCore import Qt, QTimer
import sys

# Глобальные переменные для управления
_app = None
_window = None
_timer = None
_timer_stop = None


class TransparentWindow(QLabel):
    def __init__(self, image_path):
        super().__init__()

        self.pixmap = QPixmap(image_path)
        self.setPixmap(self.pixmap)

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)

        self.setFixedSize(self.pixmap.size())
        self.center_window()

    def center_window(self):
        screen = QApplication.primaryScreen().availableGeometry()
        x = (screen.width() - self.pixmap.width()) // 2
        y = (screen.height() - self.pixmap.height()) // 2
        self.move(x, y)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.drawPixmap(0, 0, self.pixmap.width(), self.pixmap.height(), self.pixmap)


def _process_events():
    """Обрабатываем события PyQt без блокировки"""
    global _app
    if _app:
        _app.processEvents()


def show_image(image_path):
    """Показать изображение"""
    global _app, _window, _timer, _timer_stop

    # Закрываем предыдущее, если есть
    hide_image()

    # Создаём приложение, если нужно
    if not QApplication.instance():
        _app = QApplication(sys.argv)

    # Создаём окно
    _window = TransparentWindow(image_path)
    _window.show()

    # Запускаем таймер для обработки событий (неблокирующий)
    _timer = QTimer()
    _timer.timeout.connect(_process_events)
    _timer.start(10)  # Каждые 10мс обрабатываем события

    _timer_stop = QTimer()
    _timer_stop.timeout.connect(hide_image)
    _timer_stop.start(10000)  # закрываем через 10 сек в любом случае


def hide_image():
    """Скрыть изображение"""
    global _window, _timer, _timer_stop

    # Останавливаем таймер
    if _timer:
        _timer.stop()
        _timer = None

    if _timer_stop:
        _timer_stop.stop()
        _timer_stop = None

    # Закрываем окно
    if _window:
        _window.close()
        _window = None