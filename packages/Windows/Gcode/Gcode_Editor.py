from PyQt6.QtWidgets import QFrame, QVBoxLayout
from PyQt6.Qsci import QsciScintilla
from PyQt6.QtGui import QColor, QFont


class GcodeEditorClass:
    def __init__(self, parent_frame):
        # Сохраняем ссылку на родительский фрейм
        self.parent_frame = parent_frame
        self.parent_frame.setFrameShape(QFrame.Shape.NoFrame)

        # Главный layout родительского фрейма
        main_layout = QVBoxLayout(self.parent_frame)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Создаем внутренний фрейм (как контейнер)
        self.frame = QFrame()
        self.frame.setFrameShape(QFrame.Shape.Box)  # Рамка для красоты
        self.frame.setLineWidth(1)

        # Применяем стиль для фрейма (переопределяем фон)
        self.frame.setStyleSheet("""
            QFrame {
                background-color: #2A2A2A;
                border: 1px solid #3A3A3A;
                border-radius: 4px;
            }
        """)

        # Layout внутри фрейма
        frame_layout = QVBoxLayout(self.frame)
        frame_layout.setContentsMargins(2, 2, 2, 2)
        frame_layout.setSpacing(0)

        # Создаем QsciScintilla с кастомным стилем
        self.editor = QsciScintilla()

        # Настройка редактора под Blender-стиль
        self.setup_editor_style()

        # Добавляем редактор во фрейм
        frame_layout.addWidget(self.editor)

        # Добавляем фрейм в главный layout
        main_layout.addWidget(self.frame)

    def setup_editor_style(self):
        """Настройка внешнего вида редактора"""

        # Настройка цветовой схемы (как в Blender)
        self.editor.setPaper(QColor(43, 43, 43))  # #2B2B2B фон
        self.editor.setColor(QColor(221, 221, 221))  # #DDDDDD текст

        # Настройка шрифта
        font = self.editor.font()
        font.setFamily("Consolas")
        font.setPointSize(10)
        self.editor.setFont(font)

        # Настройка нумерации строк (маргин 0)
        self.editor.setMarginType(0, QsciScintilla.MarginType.NumberMargin)
        self.editor.setMarginWidth(0, 40)  # ширина в пикселях

        # Настройка цвета фона и текста для маргина
        self.editor.setMarginsForegroundColor(QColor(153, 153, 153))
        self.editor.setMarginsBackgroundColor(QColor(37, 37, 37))

        # Включаем подсветку текущей строки
        self.editor.setCaretLineVisible(True)
        self.editor.setCaretLineBackgroundColor(QColor(53, 53, 53))  # #353535

        # Настройка курсора
        self.editor.setCaretForegroundColor(QColor(255, 255, 255))
        self.editor.setCaretWidth(2)

        # Настройка выделения
        self.editor.setSelectionForegroundColor(QColor(255, 255, 255))
        self.editor.setSelectionBackgroundColor(QColor(74, 107, 143))  # #4A6B8F

        # Настройка скроллбаров (будут использовать глобальный стиль)

        # Отключаем сворачивание кода для минимализма
        self.editor.setFolding(QsciScintilla.FoldStyle.NoFoldStyle)

        # Настройка переноса строк
        self.editor.setWrapMode(QsciScintilla.WrapMode.WrapNone)

        # Настройка отступов
        self.editor.setIndentationsUseTabs(False)
        self.editor.setIndentationWidth(4)
        self.editor.setTabWidth(4)

        # Применяем CSS-стиль через setStyleSheet
        self.editor.setStyleSheet("""
            QsciScintilla {
                background-color: #2B2B2B;
                border: none;
                border-radius: 3px;
            }

            /* Полоса прокрутки */
            QScrollBar:vertical {
                background-color: #2D2D2D;
                width: 12px;
                border: none;
                border-radius: 6px;
                margin: 2px;
            }

            QScrollBar::handle:vertical {
                background-color: #4A4A4A;
                border-radius: 5px;
                min-height: 20px;
            }

            QScrollBar::handle:vertical:hover {
                background-color: #5A5A5A;
            }

            QScrollBar::handle:vertical:pressed {
                background-color: #6C7D9D;
            }

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background-color: transparent;
                border: none;
                height: 0px;
            }

            QScrollBar:horizontal {
                background-color: #2D2D2D;
                height: 12px;
                border: none;
                border-radius: 6px;
                margin: 2px;
            }

            QScrollBar::handle:horizontal {
                background-color: #4A4A4A;
                border-radius: 5px;
                min-width: 20px;
            }

            QScrollBar::handle:horizontal:hover {
                background-color: #5A5A5A;
            }

            QScrollBar::handle:horizontal:pressed {
                background-color: #6C7D9D;
            }
        """)

    def get_text(self):
        """Возвращает весь текст из редактора"""
        return self.editor.text()

    def set_text(self, text):
        """Устанавливает текст в редактор"""
        self.editor.setText(text)

    def append_line(self, line):
        """Добавляет строку в конец"""
        current_text = self.editor.text()
        if current_text:
            self.editor.setText(current_text + '\n' + line)
        else:
            self.editor.setText(line)