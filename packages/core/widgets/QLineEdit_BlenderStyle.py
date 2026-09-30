from PyQt6.QtWidgets import QWidget, QLineEdit, QLabel, QFrame, QHBoxLayout, QGraphicsView, QApplication, QPushButton
from PyQt6.QtCore import Qt, QEvent, QTimer, pyqtSignal
from PyQt6.QtGui import QCursor, QColor, QIcon
from Icon.IconName import *


class DragNumberInput(QWidget):
    valueChanged = pyqtSignal(dict)
    valueSet = pyqtSignal(dict)

    def __init__(self, label='', step=0.001, decimal=3, min_val=0.0, max_val=100.0, default=1.0):
        super().__init__()

        self.name = label
        self.step = step
        self.decimal = decimal
        self.min_val = min_val
        self.max_val = max_val
        self._drag_active = False
        self._last_mouse_x = 0
        self._current_value = default
        self._saved_cursor_pos = None
        self._drag_start_pos = None
        self._is_programmatic_move = False
        self._graphics_view = None
        self._click_started = False
        self._editing = False

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._wrapper = QWidget()
        self._wrapper.setFixedHeight(25)

        self._fill_frame = QFrame(self._wrapper)
        self._fill_frame.setAutoFillBackground(True)
        p = self._fill_frame.palette()
        p.setColor(self._fill_frame.backgroundRole(), QColor(255, 165, 0, 40))
        self._fill_frame.setPalette(p)
        self._fill_frame.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self._label = None
        if label:
            self._label = QLabel(label, self._wrapper)
            self._label.move(6, 4)
            self._label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self._line = QLineEdit(self._wrapper)
        self._line.setText(f"{default:.{decimal}f}")
        self._line.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._line.setStyleSheet("background: transparent;")
        self._line.setReadOnly(True)

        outer.addWidget(self._wrapper)

        # Property для QSS
        self.setProperty("dragInput", True)
        self._wrapper.setProperty("dragWrapper", True)
        self._fill_frame.setProperty("dragFill", True)
        self._line.setProperty("dragLine", True)
        if self._label:
            self._label.setProperty("dragLabel", True)

        self._line.installEventFilter(self)

        self._updateFillFrame()

        self._drag_check_timer = QTimer(self)
        self._drag_check_timer.setInterval(50)  # проверяем каждые 50мс
        self._drag_check_timer.timeout.connect(self._checkDragStart)

    def _findGraphicsView(self):
        if self._graphics_view:
            return self._graphics_view
        parent = self.parent()
        while parent:
            if isinstance(parent, QGraphicsView):
                self._graphics_view = parent
                return parent
            parent = parent.parent()
        return None

    def eventFilter(self, obj, event):
        if self._editing:
            if event.type() == QEvent.Type.MouseButtonPress:
                clicked_widget = QApplication.instance().widgetAt(event.globalPosition().toPoint())
                if not self.isAncestorOf(clicked_widget):
                    self._exitEditMode()
                    return False
            elif event.type() == QEvent.Type.KeyPress:
                if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                    self._exitEditMode()
                    return True
                elif event.key() == Qt.Key.Key_Escape:
                    self._line.setText(f"{self._current_value:.{self.decimal}f}")
                    self._exitEditMode()
                    return True

        if obj == self._line:
            if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
                if self._editing:
                    return False
                self._click_started = True
                self._press_pos = event.globalPosition().x()
                self._drag_check_timer.start()
                return True

            elif event.type() == QEvent.Type.MouseMove:
                if self._drag_active:
                    self._doDrag(event)
                    return True
                return True

            elif event.type() == QEvent.Type.MouseButtonRelease and event.button() == Qt.MouseButton.LeftButton:
                self._drag_check_timer.stop()  # ОСТАНАВЛИВАЕМ ТАЙМЕР

                if self._drag_active:
                    self._endDrag(event)
                elif self._click_started:
                    self._enterEditMode()
                return True

        return super().eventFilter(obj, event)

    def _checkDragStart(self):
        """Вызывается таймером каждые 50мс, пока зажата кнопка"""
        if self._click_started and not self._drag_active:
            current_x = QCursor.pos().x()
            if abs(current_x - self._press_pos) >= 2:
                self._drag_check_timer.stop()
                self._startDrag()

    def _startDrag(self):
        self._click_started = False

        view = self._findGraphicsView()
        if view:
            view.setInteractive(False)

        self._drag_active = True
        self._last_mouse_x = QCursor.pos().x()
        self._drag_start_pos = QCursor.pos()

        try:
            self._current_value = float(self._line.text())
        except ValueError:
            self._current_value = self.min_val

        self._saved_cursor_pos = QCursor.pos()
        QApplication.setOverrideCursor(Qt.CursorShape.BlankCursor)
        self._line.grabMouse()

    def _doDrag(self, event):
        if not self._is_programmatic_move:
            delta_x = event.globalPosition().x() - self._last_mouse_x
            pixel_range = self._wrapper.width()
            value_range = self.max_val - self.min_val
            self._current_value += delta_x * (value_range / pixel_range)

            self._current_value = max(self.min_val, min(self.max_val, self._current_value))
            self._line.setText(f"{self._current_value:.{self.decimal}f}")
            self._updateFillFrame()

            self.valueChanged.emit({'value': self._current_value})
        else:
            self._is_programmatic_move = False
        self._last_mouse_x = event.globalPosition().x()

    def _endDrag(self, event):
        view = self._findGraphicsView()
        if view:
            view.setInteractive(True)

        self._drag_active = False
        QApplication.restoreOverrideCursor()
        self._line.releaseMouse()

        if self._drag_start_pos:
            QCursor.setPos(self._drag_start_pos)

        self.valueSet.emit({'value': self._current_value})

    def _enterEditMode(self):
        self._click_started = False
        self._editing = True

        try:
            self._current_value = float(self._line.text())
        except ValueError:
            self._current_value = self.min_val

        self._fill_frame.hide()
        if self._label:
            self._label.hide()

        self._line.setReadOnly(False)
        self._line.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._line.setFocus()
        self._line.selectAll()

        QApplication.instance().installEventFilter(self)

    def _exitEditMode(self):
        if not self._editing:
            return

        self._editing = False
        QApplication.instance().removeEventFilter(self)

        try:
            val = float(self._line.text())
            val = max(self.min_val, min(self.max_val, val))
        except ValueError:
            val = self._current_value

        self._line.setText(f"{val:.{self.decimal}f}")
        self._line.setReadOnly(True)
        self._line.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._line.clearFocus()

        self._fill_frame.show()
        if self._label:
            self._label.show()

        self._updateFillFrame()

        self.valueSet.emit({'value': val})

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._line.setGeometry(0, 0, self._wrapper.width(), self._wrapper.height())
        self._updateFillFrame()

    def _updateFillFrame(self):
        w = self._wrapper.width()
        try:
            val = float(self._line.text())
        except ValueError:
            val = self.min_val
        ratio = (val - self.min_val) / (self.max_val - self.min_val) if self.max_val != self.min_val else 0
        ratio = max(0, min(1, ratio))
        self._fill_frame.setGeometry(2, 2, int((w - 4) * ratio), self._wrapper.height() - 4)

    def value(self):
        try:
            return float(self._line.text())
        except ValueError:
            return self.min_val

    def setValue(self, val):
        val = max(self.min_val, min(self.max_val, val))
        self._line.setText(f"{val:.{self.decimal}f}")
        self._updateFillFrame()

    def get_name(self):
        return self.name


class DragButtonNumberInput(QWidget):
    valueChanged = pyqtSignal(dict)
    valueSet = pyqtSignal(dict)

    def __init__(self, label='', step=0.001, decimal=3, min_val=0.0, max_val=100.0, default=1.0):
        super().__init__()

        self.name = label
        self.step = step
        self.decimal = decimal
        self.min_val = min_val
        self.max_val = max_val
        self._drag_active = False
        self._last_mouse_x = 0
        self._current_value = default
        self._saved_cursor_pos = None
        self._drag_start_pos = None
        self._is_programmatic_move = False
        self._graphics_view = None
        self._click_started = False
        self._editing = False

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Кнопка минус
        self._btn_minus = QPushButton()
        self._btn_minus.setIcon(QIcon(arrow_left_Icon))
        self._btn_minus.setFixedSize(24, 25)
        self._btn_minus.setProperty("dragBtn", True)
        self._btn_minus.setProperty("dragBtnLeft", True)
        self._btn_minus.clicked.connect(self._stepDown)
        outer.addWidget(self._btn_minus)

        # Поле ввода
        self._wrapper = QWidget()
        self._wrapper.setFixedHeight(25)
        self._wrapper.setProperty("dragWrapper", True)

        self._label = None
        if label:
            self._label = QLabel(label, self._wrapper)
            self._label.move(6, 4)
            self._label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            self._label.setProperty("dragLabel", True)

        self._line = QLineEdit(self._wrapper)
        self._line.setText(f"{default:.{decimal}f}")
        self._line.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._line.setStyleSheet("background: transparent; border: none;")
        self._line.setReadOnly(True)
        self._line.setProperty("dragLine", True)

        outer.addWidget(self._wrapper)

        # Кнопка плюс
        self._btn_plus = QPushButton()
        self._btn_plus.setIcon(QIcon(arrow_right_Icon))
        self._btn_plus.setFixedSize(24, 25)
        self._btn_plus.setProperty("dragBtn", True)
        self._btn_plus.setProperty("dragBtnRight", True)
        self._btn_plus.clicked.connect(self._stepUp)
        outer.addWidget(self._btn_plus)

        self.setProperty("dragInput", True)
        self._line.installEventFilter(self)

        # Единый фон и скругления только по краям
        self.setStyleSheet("""
            QPushButton[dragBtnLeft="true"] {
                background: #3a3a3a;
                border: none;
                border-top-left-radius: 6px;
                border-bottom-left-radius: 6px;
                border-top-right-radius: 0px;
                border-bottom-right-radius: 0px;
            }
            QPushButton[dragBtnRight="true"] {
                background: #3a3a3a;
                border: none;
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
                border-top-left-radius: 0px;
                border-bottom-left-radius: 0px;
            }
            QWidget[dragWrapper="true"] {
                background: #3a3a3a;
                border-radius: 0px;
            }
        """)

    def _stepUp(self):
        val = min(self.value() + self.step, self.max_val)
        self.setValue(val)
        self.valueChanged.emit({'value': val})
        self.valueSet.emit({'value': val})

    def _stepDown(self):
        val = max(self.value() - self.step, self.min_val)
        self.setValue(val)
        self.valueChanged.emit({'value': val})
        self.valueSet.emit({'value': val})

    def _findGraphicsView(self):
        if self._graphics_view:
            return self._graphics_view
        parent = self.parent()
        while parent:
            if isinstance(parent, QGraphicsView):
                self._graphics_view = parent
                return parent
            parent = parent.parent()
        return None

    def eventFilter(self, obj, event):
        if self._editing:
            if event.type() == QEvent.Type.MouseButtonPress:
                clicked_widget = QApplication.instance().widgetAt(event.globalPosition().toPoint())
                if not self.isAncestorOf(clicked_widget):
                    self._exitEditMode()
                    return False
            elif event.type() == QEvent.Type.KeyPress:
                if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                    self._exitEditMode()
                    return True
                elif event.key() == Qt.Key.Key_Escape:
                    self._line.setText(f"{self._current_value:.{self.decimal}f}")
                    self._exitEditMode()
                    return True

        if obj == self._line:
            if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
                if self._editing:
                    return False
                self._click_started = True
                self._press_pos = event.globalPosition().x()
                QTimer.singleShot(50, self._checkDragStart)
                return True

            elif event.type() == QEvent.Type.MouseMove and self._drag_active:
                self._doDrag(event)
                return True

            elif event.type() == QEvent.Type.MouseButtonRelease and event.button() == Qt.MouseButton.LeftButton:
                if self._drag_active:
                    self._endDrag(event)
                elif self._click_started:
                    self._enterEditMode()
                return True

        return super().eventFilter(obj, event)

    def _checkDragStart(self):
        if self._click_started and not self._drag_active:
            current_x = QCursor.pos().x()
            if abs(current_x - self._press_pos) >= 2:
                self._startDrag()

    def _startDrag(self):
        self._click_started = False

        view = self._findGraphicsView()
        if view:
            view.setInteractive(False)

        self._drag_active = True
        self._last_mouse_x = QCursor.pos().x()
        self._drag_start_pos = QCursor.pos()

        try:
            self._current_value = float(self._line.text())
        except ValueError:
            self._current_value = 0.0

        self._saved_cursor_pos = QCursor.pos()
        QApplication.setOverrideCursor(Qt.CursorShape.BlankCursor)
        self._line.grabMouse()

    def _doDrag(self, event):
        if not self._is_programmatic_move:
            delta_x = event.globalPosition().x() - self._last_mouse_x
            self._current_value += delta_x * self.step
            self._current_value = max(self.min_val, min(self.max_val, self._current_value))
            self._line.setText(f"{self._current_value:.{self.decimal}f}")

            self.valueChanged.emit({'value': self._current_value})
        else:
            self._is_programmatic_move = False
        self._last_mouse_x = event.globalPosition().x()

    def _endDrag(self, event):
        view = self._findGraphicsView()
        if view:
            view.setInteractive(True)

        self._drag_active = False
        QApplication.restoreOverrideCursor()
        self._line.releaseMouse()

        if self._drag_start_pos:
            QCursor.setPos(self._drag_start_pos)

        self.valueSet.emit({'value': self._current_value})

    def _enterEditMode(self):
        self._click_started = False
        self._editing = True

        try:
            self._current_value = float(self._line.text())
        except ValueError:
            self._current_value = 0.0

        if self._label:
            self._label.hide()

        self._line.setReadOnly(False)
        self._line.setFocus()
        self._line.selectAll()
        self._line.setAlignment(Qt.AlignmentFlag.AlignCenter)

        QApplication.instance().installEventFilter(self)

    def _exitEditMode(self):
        if not self._editing:
            return

        self._editing = False
        QApplication.instance().removeEventFilter(self)

        try:
            val = float(self._line.text())
            val = max(self.min_val, min(self.max_val, val))
        except ValueError:
            val = self._current_value

        self._line.setText(f"{val:.{self.decimal}f}")
        self._line.setReadOnly(True)
        self._line.clearFocus()
        self._line.setAlignment(Qt.AlignmentFlag.AlignRight)

        if self._label:
            self._label.show()

        self.valueSet.emit({'value': val})

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._line.setGeometry(0, 0, self._wrapper.width(), self._wrapper.height())

    def value(self) -> float:
        try:
            return float(self._line.text())
        except ValueError:
            return 0.0

    def setValue(self, val):
        val = max(self.min_val, min(self.max_val, val))
        self._line.setText(f"{val:.{self.decimal}f}")

    def get_name(self):
        return self.name


from PyQt6.QtWidgets import QLineEdit, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor


class QLineEditBlenderStyle(QLineEdit):
    def __init__(self, parent, label='', step=0.001, decimal=3):
        super().__init__(parent)

        self._drag_active = False
        self._last_mouse_x = 0
        self._current_value = 0
        self._saved_cursor_pos = None
        self._is_programmatic_move = False
        self.step = step
        self.decimal = decimal
        self.Enable = False

        # Добавляем label внутрь lineedit
        if label:
            self._label = QLabel(label, self)
            self._label.setStyleSheet("color: black; background: transparent;")
            self._label.move(5, (self.height() - self._label.height()) // 2)
            self.setAlignment(Qt.AlignmentFlag.AlignRight)
        else:
            self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_label'):
            self._label.move(5, (self.height() - self._label.height()) // 2)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.Enable:
            self._drag_active = True
            self._last_mouse_x = event.globalPosition().x()
            self._current_value = float(self.text()) if self.text() else 0
            self._saved_cursor_pos = QCursor.pos()
            self.setCursor(Qt.CursorShape.BlankCursor)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_active and self.Enable:
            if not self._is_programmatic_move:
                delta_x = event.globalPosition().x() - self._last_mouse_x
                delta_value = delta_x * self.step
                self._current_value += delta_value
                self.setText(str(f"{self._current_value:.{self.decimal}f}"))

                self._is_programmatic_move = True
                QCursor.setPos(self._saved_cursor_pos)
                event.accept()
            else:
                self._is_programmatic_move = False

            self._last_mouse_x = event.globalPosition().x()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._drag_active:
            self._drag_active = False
            self.setCursor(Qt.CursorShape.IBeamCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)
