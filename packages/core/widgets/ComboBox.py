from qtpy.QtWidgets import QComboBox


def upgradeComboBox(ComboBox: QComboBox):
    cb = ComboBox
    cb.setStyleSheet("""
            QComboBox::drop-down {
                border: none;
                width: 20px;
                background-color: transparent;  /* Прозрачная область */
            }
            QComboBox::down-arrow {
                image: url(Icon/image/arrow_down.png); 
            }
            QComboBox QAbstractItemView {
                outline: 0px;  /* Отключаем пунктирную рамку */
            }
        """)
    cb.setFixedHeight(22)
    return cb


class CustomComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(22)
        self.setStyleSheet("""
            QComboBox::drop-down {
                border: none;
                width: 20px;
                background-color: transparent;  /* Прозрачная область */
            }
            QComboBox::down-arrow {
                image: url(Icon/image/arrow_down.png); 
            }
            QComboBox QAbstractItemView {
                outline: 0px;  /* Отключаем пунктирную рамку */
            }
        """)

