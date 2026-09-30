from Icon.IconName import *
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLineEdit, QLabel, QApplication
)
from PyQt6.QtCore import Qt, QEvent, pyqtSignal
from PyQt6.QtGui import QIcon, QFont
import re
import weakref

from packages.core.validators.numeric_validator import calc_str


class DragButtonNumberInputStatic(QWidget):
    valueChanged = pyqtSignal(dict)   # {'value': <в LSB>}
    valueSet = pyqtSignal(dict)       # {'value': <в LSB>}

    # Все живые экземпляры (weakref, чтобы не течь)
    _instances = []

    # Единый размер шрифта для всех элементов виджета
    _FONT_SIZE = 11

    _ALIGN_RIGHT = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
    _ALIGN_CENTER = Qt.AlignmentFlag.AlignCenter

    _ARITH_RE = re.compile(r"[*/()]")
    _PAIR_RE = re.compile(
        r"(?P<sign>[-+])?"
        r"\s*"
        r"(?P<num>(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)"
        r"\s*"
        r"(?P<unit>[a-zа-яёµμ%]*)"
    )
    _EXPR_RE = re.compile(
        r"^\s*"
        r"(?:[-+]?\s*(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?\s*[a-zа-яёµμ%]*\s*)+"
        r"$"
    )

    # =================================================================
    # Классовый метод раздачи единиц
    # =================================================================

    @classmethod
    def apply_units_set(cls, units_all: dict, lang: str | None = None):
        """
        Раздаёт единицы ВСЕМ экземплярам класса из общего словаря units_all.

        units_all — полный словарь вида:
            {
                'beam_steerers': {
                    'display_unit': 'mm',
                    'lsb_unit': 'LSB',
                    'units': {...},
                },
                'positioners': {...},
                ...
            }

        Каждый экземпляр берёт свой набор по self.units_set_name.
        Если ключа нет — экземпляр остаётся без изменений.
        lang — 'ru' / 'en' / None. None = не менять язык.
        Заодно подчищает мёртвые weakref'ы.
        """
        alive = []
        for ref in cls._instances:
            obj = ref()
            if obj is None:
                continue
            alive.append(ref)

            units_set = units_all.get(obj.units_set_name)
            if units_set is None:
                continue

            if lang is not None:
                obj.lang = lang
            obj._set_units_from_dict(units_set)

        cls._instances = alive

    # =================================================================
    # Инициализация
    # =================================================================

    def __init__(self, label='', decimal=3,
                 min_val=0, max_val=None, default=0.0,
                 wheel_step_multiplier=1.0,
                 alignment='center',
                 units_set_name='default',
                 units_set=None,
                 lang='ru'):
        """
        units_set_name : ключ набора единиц (например, 'beam_steerers').
        units_set      : начальный словарь единиц (если известен сразу).
                         Если None — экземпляр стартует без единиц,
                         их можно раздать через apply_units_set(...).
        lang           : 'ru' / 'en' — язык ярлыков единиц.
        """
        super().__init__()

        self.name = label
        self.decimal = decimal
        self.wheel_step_multiplier = wheel_step_multiplier

        self.units_set_name = units_set_name
        self.lang = lang

        # --- Единицы ---
        self._units = {}
        self._units_meta = {}
        self._label_index = {}
        self._base_unit = None
        self._lsb_unit = 'lsb'
        self._display_unit = None

        # --- Границы и значение (в LSB) ---
        self.min_val = min_val
        self.max_val = max_val
        self._current_value = float(default)

        # --- Состояние ---
        self._drag_active = False
        self._click_started = False
        self._editing = False
        self._last_mouse_x = 0
        self._press_x = 0
        self._press_value = 0.0
        self._alignment_mode = 'right'
        self.step = 1.0

        # --- Шрифт ---
        self._font = QFont()
        self._font.setPointSize(self._FONT_SIZE)

        # --- UI ---
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._btn_minus = QPushButton()
        self._btn_minus.setIcon(QIcon(arrow_left_Icon))
        self._btn_minus.setFixedSize(24, 25)
        self._btn_minus.setFont(self._font)
        self._btn_minus.setProperty("dragBtn", True)
        self._btn_minus.setProperty("dragBtnLeft", True)
        self._btn_minus.pressed.connect(self._stepDown)
        outer.addWidget(self._btn_minus)

        self._wrapper = QWidget()
        self._wrapper.setFixedHeight(25)
        self._wrapper.setProperty("dragWrapper", True)

        # Подпись — прижата к левому краю
        self._label = None
        if label:
            self._label = QLabel(label, self._wrapper)
            self._label.setFont(self._font)
            self._label.setAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            )
            self._label.setGeometry(6, 0, self._wrapper.width(), self._wrapper.height())
            self._label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            self._label.setProperty("dragLabel", True)

        self._line = QLineEdit(self._wrapper)
        self._line.setFont(self._font)
        self._line.setStyleSheet("background: transparent; border: none; color: #ffffff; padding: 0px; margin: 0px;")
        self._line.setReadOnly(True)
        self._line.setProperty("dragLine", True)
        self._line.installEventFilter(self)
        self._line.editingFinished.connect(self._on_line_editing_finished)

        outer.addWidget(self._wrapper)

        self._btn_plus = QPushButton()
        self._btn_plus.setIcon(QIcon(arrow_right_Icon))
        self._btn_plus.setFixedSize(24, 25)
        self._btn_plus.setFont(self._font)
        self._btn_plus.setProperty("dragBtn", True)
        self._btn_plus.setProperty("dragBtnRight", True)
        self._btn_plus.pressed.connect(self._stepUp)
        outer.addWidget(self._btn_plus)

        self.setProperty("dragInput", True)

        self.setAlignmentMode(alignment)

        # Локальная инициализация единиц, если словарь известен сразу
        if units_set is not None:
            self._set_units_from_dict(units_set)

        # Регистрация в общем списке класса
        type(self)._instances.append(weakref.ref(self))
        self.apply_units_set(units_all=units_set)

    # =================================================================
    # Установка единиц (один экземпляр)
    # =================================================================

    def _set_units_from_dict(self, units_set: dict):
        """
        Устанавливает экземпляру единицы из словаря.
        Не меняет _current_value (оно в LSB), но обновляет отображение.
        """
        raw_units = units_set.get('units') or {}
        self._units = {}
        self._units_meta = {}
        for key, u in raw_units.items():
            key_l = str(key).lower()
            self._units[key_l] = float(u.get('coef', 1.0))
            self._units_meta[key_l] = {
                'step': u.get('step', 1),
                'decimal': u.get('decimal', self.decimal),
                'ru': u.get('ru', key_l),
                'en': u.get('en', key_l),
            }

        # LSB-единица (для калибровки), если её нет — добавляем
        self._lsb_unit = str(units_set.get('lsb_unit', 'lsb')).lower()
        if self._lsb_unit not in self._units:
            self._units[self._lsb_unit] = 1.0
            self._units_meta[self._lsb_unit] = {
                'step': 1, 'decimal': 0,
                'ru': self._lsb_unit, 'en': self._lsb_unit,
            }

        # Базовая физическая — та, у которой коэф == 1
        base_candidates = [n for n, c in self._units.items()
                           if abs(c - 1.0) < 1e-15]
        self._base_unit = base_candidates[0] if base_candidates else self._lsb_unit

        # Единица отображения
        disp = str(units_set.get('display_unit', self._base_unit)).lower()
        if disp not in self._units:
            disp = self._base_unit
        self._display_unit = disp

        # Индекс ярлыков для парсера
        self._build_label_index()

        # step и decimal под текущую единицу отображения
        self._sync_step_decimal()

        # Перерисовать
        self._refresh_display()

    def _build_label_index(self):
        """
        Строит обратный индекс: любой вариант ввода ('мм', 'mm', 'um', 'мкм')
        → технический ключ ('mm', 'um'). Регистронезависимо.
        """
        idx = {}
        for key, meta in self._units_meta.items():
            idx[key.lower()] = key
            for lg in ('ru', 'en'):
                lbl = meta.get(lg)
                if lbl:
                    idx[str(lbl).lower()] = key
        self._label_index = idx

    def _sync_step_decimal(self):
        """Подтянуть step и decimal под текущую единицу отображения."""
        meta = self._units_meta.get(self._display_unit)
        if meta is None:
            return
        self.step = meta['step']
        self.decimal = meta['decimal']

    # =================================================================
    # Публичный API единиц
    # =================================================================

    def display_unit(self) -> str:
        return self._display_unit

    def base_unit(self) -> str:
        return self._base_unit

    def lsb_unit(self) -> str:
        return self._lsb_unit

    def unit_label(self, unit_key: str | None = None, lang: str | None = None) -> str:
        """Ярлык единицы на нужном языке. По умолчанию — текущей, на self.lang."""
        key = (unit_key or self._display_unit).lower()
        meta = self._units_meta.get(key)
        if meta is None:
            return key
        lg = lang or self.lang
        return meta.get(lg) or meta.get('en') or key

    def set_display_unit(self, unit: str):
        """Принимает и технический ключ, и ярлык, в любом регистре."""
        key = self._label_index.get(str(unit).lower())
        if key is None:
            raise ValueError(f"Неизвестная единица: {unit!r}")
        self._display_unit = key
        self._sync_step_decimal()
        self._refresh_display()

    def set_lang(self, lang: str):
        self.lang = lang
        self._refresh_display()

    def _coef(self, unit: str) -> float:
        return self._units[unit]

    # =================================================================
    # Конвертация
    # =================================================================

    def to_base(self, value_in_display: float) -> float:
        return value_in_display * self._coef(self._display_unit)

    def from_base(self, value_lsb: float) -> float:
        return value_lsb / self._coef(self._display_unit)

    def _unit_to_lsb(self, value: float, unit_key: str) -> float:
        return value * self._coef(unit_key)

    # =================================================================
    # Парсинг
    # =================================================================

    def parse_input(self, text: str) -> float:
        if text is None:
            raise ValueError("Пустой ввод")
        text = text.strip().lower()
        if not text:
            raise ValueError("Пустой ввод")

        if self._ARITH_RE.search(text):
            return self._parse_with_calc(text)
        return self._parse_sum_of_pairs(text)

    def _resolve_unit(self, unit_raw: str) -> str:
        """'мм' / 'mm' / 'MM' → 'mm'. Бросает ValueError."""
        key = self._label_index.get(str(unit_raw).lower())
        if key is None:
            raise ValueError(f"Неизвестная единица: {unit_raw!r}")
        return key

    def _parse_with_calc(self, text: str) -> float:
        m = re.match(r"^(?P<expr>.*?)\s*(?P<unit>[a-zа-яёµμ%]+)\s*$", text)
        if not m:
            expr, unit_raw = text, None
        else:
            expr = m.group("expr").strip()
            unit_raw = m.group("unit").strip() or None

        result_str = calc_str(expr)
        try:
            value = float(result_str)
        except ValueError:
            raise ValueError(f"Не удалось вычислить: {expr!r}")

        if unit_raw is None:
            return self.to_base(value)
        key = self._resolve_unit(unit_raw)
        return self._unit_to_lsb(value, key)

    def _parse_sum_of_pairs(self, text: str) -> float:
        if not self._EXPR_RE.match(text):
            raise ValueError(f"Не удалось разобрать: {text!r}")

        total_lsb = 0.0
        pos = 0
        found_any = False
        for m in self._PAIR_RE.finditer(text):
            between = text[pos:m.start()].strip()
            if between not in ("", "+", "-"):
                raise ValueError(f"Непонятный фрагмент: {between!r}")
            sign = m.group("sign")
            if sign is None and between == "-":
                sign = "-"

            try:
                num = float(m.group("num"))
            except ValueError:
                raise ValueError(f"Не число: {m.group('num')!r}")

            unit_raw = m.group("unit") or None
            if unit_raw is None:
                term_lsb = self.to_base(num)
            else:
                key = self._resolve_unit(unit_raw)
                term_lsb = self._unit_to_lsb(num, key)

            if sign == "-":
                term_lsb = -term_lsb

            total_lsb += term_lsb
            pos = m.end()
            found_any = True

        tail = text[pos:].strip()
        if tail not in ("", "+", "-"):
            raise ValueError(f"Лишний хвост: {tail!r}")
        if not found_any:
            raise ValueError(f"Не удалось разобрать: {text!r}")

        return total_lsb

    # =================================================================
    # Выравнивание
    # =================================================================

    def alignment(self) -> str:
        return self._alignment_mode

    def setAlignmentMode(self, mode: str):
        if mode not in ('right', 'center'):
            raise ValueError("alignment must be 'right' or 'center'")
        self._alignment_mode = mode
        if not self._editing:
            self._apply_alignment()

    def _apply_alignment(self):
        if self._alignment_mode == 'center':
            self._line.setAlignment(self._ALIGN_CENTER)
        else:
            self._line.setAlignment(self._ALIGN_RIGHT)

    # =================================================================
    # Отображение
    # =================================================================

    def _format_value(self, value_lsb: float) -> str:
        display_val = self.from_base(value_lsb)
        return f"{display_val:.{self.decimal}f} {self.unit_label()}"

    def _refresh_display(self):
        self._line.setText(self._format_value(self._current_value))

    # =================================================================
    # Ограничения
    # =================================================================

    def _clamp(self, value_lsb: float) -> float:
        if self.min_val is not None:
            value_lsb = max(value_lsb, self.min_val)
        if self.max_val is not None:
            value_lsb = min(value_lsb, self.max_val)
        return value_lsb

    # =================================================================
    # Шаг / колесо
    # =================================================================

    def _stepUp(self):
        step_lsb = self.to_base(self.step)
        self._current_value = self._clamp(self._current_value + step_lsb)
        self._refresh_display()
        self.valueChanged.emit({'value': self._current_value})
        self.valueSet.emit({'value': self._current_value})

    def _stepDown(self):
        step_lsb = self.to_base(self.step)
        self._current_value = self._clamp(self._current_value - step_lsb)
        self._refresh_display()
        self.valueChanged.emit({'value': self._current_value})
        self.valueSet.emit({'value': self._current_value})

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta == 0:
            event.ignore()
            return

        step_lsb = self.to_base(self.step * self.wheel_step_multiplier)
        if delta > 0:
            self._current_value = self._clamp(self._current_value + step_lsb)
        else:
            self._current_value = self._clamp(self._current_value - step_lsb)

        self._refresh_display()
        self.valueChanged.emit({'value': self._current_value})
        self.valueSet.emit({'value': self._current_value})
        event.accept()

    # =================================================================
    # Фильтр событий
    # =================================================================

    def eventFilter(self, obj, event):
        if (self._editing
                and event.type() == QEvent.Type.MouseButtonPress
                and obj is not self._line):
            pressed = obj if isinstance(obj, QWidget) else None
            if pressed is not None and not (pressed is self or self.isAncestorOf(pressed)):
                self._exitEditMode()
                return False

        if obj != self._line:
            return super().eventFilter(obj, event)

        if self._editing and event.type() == QEvent.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self._exitEditMode()
                return True
            elif event.key() == Qt.Key.Key_Escape:
                self._current_value = self._press_value
                self._refresh_display()
                self._exitEditMode()
                return True

        if (event.type() == QEvent.Type.MouseButtonPress
                and event.button() == Qt.MouseButton.LeftButton):
            if self._editing:
                return False
            self._click_started = True
            self._drag_active = False
            self._press_x = event.globalPosition().x()
            self._last_mouse_x = self._press_x
            self._press_value = self._current_value
            return True

        if event.type() == QEvent.Type.MouseMove:
            if self._editing:
                return False

            if self._click_started and not self._drag_active:
                if abs(event.globalPosition().x() - self._press_x) >= 3:
                    self._drag_active = True
                    self._click_started = False

            if self._drag_active:
                delta_x = event.globalPosition().x() - self._last_mouse_x
                self._current_value += delta_x * self.to_base(self.step)
                self._current_value = self._clamp(self._current_value)
                self._refresh_display()
                self.valueChanged.emit({'value': self._current_value})
                self._last_mouse_x = event.globalPosition().x()
                return True

        if (event.type() == QEvent.Type.MouseButtonRelease
                and event.button() == Qt.MouseButton.LeftButton):
            if self._editing:
                return False

            if self._drag_active:
                self._drag_active = False
                self._click_started = False
                self.valueSet.emit({'value': self._current_value})
            elif self._click_started:
                self._click_started = False
                self._enterEditMode()
            return True

        return super().eventFilter(obj, event)

    # =================================================================
    # Режим редактирования
    # =================================================================

    def _enterEditMode(self):
        if self._editing:
            return
        self._editing = True
        self._press_value = self._current_value

        self._refresh_display()

        if self._label:
            self._label.hide()

        self._line.setReadOnly(False)
        self._line.setAlignment(self._ALIGN_CENTER)
        self._line.setFocus()

        # выделяем только число, суффикс единицы остаётся видимым
        text = self._line.text()
        space_idx = text.find(' ')
        if space_idx == -1:
            self._line.selectAll()
        else:
            self._line.setSelection(0, space_idx)

        QApplication.instance().installEventFilter(self)

        self.setProperty("editing", True)
        self._repolish()

    def _exitEditMode(self):
        if not self._editing:
            return

        self._editing = False

        app = QApplication.instance()
        if app is not None:
            app.removeEventFilter(self)

        try:
            val_lsb = self.parse_input(self._line.text())
            val_lsb = self._clamp(val_lsb)
        except ValueError:
            val_lsb = self._current_value

        self._current_value = val_lsb
        self._refresh_display()
        self._line.setReadOnly(True)
        self._line.clearFocus()
        self._apply_alignment()

        if self._label:
            self._label.show()

        self.valueSet.emit({'value': self._current_value})

        self.setProperty("editing", False)
        self._repolish()

    def _on_line_editing_finished(self):
        if self._editing:
            self._exitEditMode()

    # =================================================================
    # Геометрия / API
    # =================================================================

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._line.setGeometry(0, 0, self._wrapper.width(), self._wrapper.height())
        if self._label is not None:
            self._label.setGeometry(
                6, 0, self._wrapper.width() - 6, self._wrapper.height()
            )

    def value(self) -> float:
        """Значение в LSB."""
        return self._current_value

    def setValue(self, val):
        """Установить значение в LSB."""
        self._current_value = self._clamp(float(val))
        self._refresh_display()

    def value_display(self) -> float:
        """Значение в текущей единице отображения."""
        return self.from_base(self._current_value)

    def setValue_display(self, val):
        """Установить значение в текущей единице отображения."""
        self.setValue(self.to_base(float(val)))

    def get_name(self):
        return self.name

    def _repolish(self):
        """Переприменить QSS к себе и дочерним виджетам после смены свойства."""
        widgets = (self, self._wrapper, self._btn_minus, self._btn_plus, self._line)
        if self._label is not None:
            widgets = widgets + (self._label,)
        for w in widgets:
            w.style().unpolish(w)
            w.style().polish(w)
            w.update()