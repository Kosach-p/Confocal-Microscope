from PyQt6.QtGui import QValidator
from simpleeval import simple_eval
import re


class FloatValidatorClass(QValidator):
    """
    Класс валидатора дробных чисел. Применяется к LineEdit через line_edit.setValidator(FloatValidator)
    Не позволяет вводить ничего, кроме дробных чисел и только!
    """
    def validate(self, text, pos):
        if text == "":
            return QValidator.State.Intermediate, text, pos

        # Заменяем запятые на точки для проверки
        normalized_text = text.replace(',', '.')

        # Проверяем валидность числа
        pattern = r'^[\d.,]+$'
        if re.match(pattern, normalized_text):
            return QValidator.State.Acceptable, normalized_text, pos
        else:
            return QValidator.State.Invalid, normalized_text, pos


class FloatCalcValidatorClass(QValidator):
    """
    Класс валидатора дробных чисел. Применяется к LineEdit через line_edit.setValidator(FloatCalcValidator)
    Позволяет вводить как дробные числа, так и математические операторы, такие как "+", "-", "*", "/", "(", ")"
    При использовании данного валидатора можно так же подключить функцию calc_str,
    для проведения вычислений прямо в lineEdit
    line_edit.editingFinished.connect(lambda checked=False, line=line_edit: line.setText(calc_str(line.text(), 0)))
    """
    def validate(self, text, pos):
        if text == "":
            return QValidator.State.Intermediate, text, pos

        # Заменяем запятые на точки для проверки
        normalized_text = text.replace(',', '.')

        # Проверяем валидность числа
        pattern = r'^[\d+\-*/().,\s]+$'
        if re.match(pattern, normalized_text):
            return QValidator.State.Acceptable, normalized_text, pos
        else:
            return QValidator.State.Invalid, normalized_text, pos


class IntValidatorClass(QValidator):
    """
    Класс валидатора целых чисел. Применяется к LineEdit через line_edit.setValidator(IntValidator)
    Не позволяет вводить ничего, кроме целых чисел и только!
    """
    def validate(self, text, pos):
        if text == "":
            return QValidator.State.Intermediate, text, pos

        # Проверяем валидность числа
        pattern = r'^[\d]+$'
        if re.match(pattern, text):
            return QValidator.State.Acceptable, text, pos
        else:
            return QValidator.State.Invalid, text, pos


class IntCalcValidatorClass(QValidator):
    """
    Класс валидатора целых чисел. Применяется к LineEdit через line_edit.setValidator(IntValidatorWithCalc)
    Позволяет вводить как целые числа, так и математические операторы, такие как "+", "-", "*", "/", "(", ")"
    При использовании данного валидатора можно так же подключить функцию calc_str,
    для проведения вычислений прямо в lineEdit
    line_edit.editingFinished.connect(lambda checked=False, line=line_edit: line.setText(calc_str(line.text(), 0)))
    """
    def validate(self, text, pos):
        """
        Функция validate вызывается QValidator каждый раз, когда меняется содержание LineEdit.
        Здесь мы редактируем строку, оставляя только то, что разрешено паттерном pattern
        :param text: строка, введённая в lineEdit
        :param pos: позиция курсора
        :return: верность текста, отредактированный текст, позиция курсора
        """
        if text == "":
            return QValidator.State.Intermediate, text, pos

        # Заменяем запятые на точки для проверки
        normalized_text = text.replace(',', '.')

        # Проверяем валидность числа
        pattern = r'^[\d+\-*/()\s]+$'
        if re.match(pattern, normalized_text):
            return QValidator.State.Acceptable, normalized_text, pos
        else:
            return QValidator.State.Invalid, normalized_text, pos


class ReadOnlyIntValidatorClass(QValidator):
    """
        Класс валидатора только для чтения. Делает вывод на LineEdit более читабельным, к примеру добавляет разделение
        выводимого числа каждые 3 цифры
        """

    def validate(self, text, pos):
        """
        Функция validate вызывается QValidator каждый раз, когда меняется содержание LineEdit.
        Здесь мы редактируем строку
        :param text: строка, введённая в lineEdit
        :param pos: позиция курсора
        :return: верность текста, отредактированный текст, позиция курсора
        """
        if text == "":
            return QValidator.State.Intermediate, text, pos

        # Заменяем запятые на точки для проверки
        normalized_text = text.replace(',', '.').replace(' ', '')

        # Проверяем валидность числа
        pattern = r'^[\d+\-*/()\s]+$'
        if re.match(pattern, normalized_text):
            return QValidator.State.Acceptable, '{:,}'.format(int(normalized_text)).replace(',', ' '), pos
        else:
            return QValidator.State.Invalid, normalized_text, pos


def calc_str(str, precision=0):
    """
    :param str: Строка, в которой надо провести вычисления
    :param precision: число знаков после запятой (0 - целочисленное вычисление)
    :return: строка - результат вычислений или без изменений, в случае недопустимого ввода
    """
    try:
        result = simple_eval(str)
        formatted = f"{result:.{precision}f}"
        if '.' in formatted:
            formatted = formatted.rstrip('0').rstrip('.')
        return formatted
    except:
        return str


FloatCalcValidator = FloatCalcValidatorClass()
FloatValidator = FloatValidatorClass()

IntCalcValidator = IntCalcValidatorClass()
IntValidator = IntValidatorClass()

ReadOnlyIntValidator = ReadOnlyIntValidatorClass()
