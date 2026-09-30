from qtpy.QtWidgets import QSpinBox, QDoubleSpinBox
from qtpy.QtCore import Qt

def upgradeSpinBox(SpinBox: QSpinBox):
    sb = SpinBox
    sb.setStyleSheet("""
            QSpinBox::up-button {
                border: none;
                width: 20px;
                background-color: transparent;
            }
            QSpinBox::down-button {
                border: none;
                width: 20px;
                background-color: transparent;
            }
            QSpinBox::up-arrow {
                image: url(Icon/image/arrow_top.png);
                width: 10px;
                height: 10px;
            }
            QSpinBox::down-arrow {
                image: url(Icon/image/arrow_down.png);
                width: 10px;
                height: 10px;
            }
        """)
    sb.setFixedHeight(22)
    return sb


def upgradeDoubleSpinBox(DoubleSpinBox: QDoubleSpinBox):
    dsb = DoubleSpinBox
    dsb.setStyleSheet("""
            QDoubleSpinBox::up-button {
                border: none;
                width: 20px;
                background-color: transparent;
            }
            QDoubleSpinBox::down-button {
                border: none;
                width: 20px;
                background-color: transparent;
            }
            QDoubleSpinBox::up-arrow {
                image: url(Icon/image/arrow_top.png);
                width: 10px;
                height: 10px;
            }
            QDoubleSpinBox::down-arrow {
                image: url(Icon/image/arrow_down.png);
                width: 10px;
                height: 10px;
            }
        """)
    dsb.setFixedHeight(22)
    return dsb


class CustomSpinBox(QSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(22)
        self.setStyleSheet("""
            QSpinBox {
                background-color: #303030;

                color: #dddddd;
                border-radius: 4px;
                padding: 2px 8px;
                border: 1px solid #4a4a4a;
                font-size: 12px;
                font-weight: 500;
            }
            QSpinBox:hover {
                border: 1px solid #6a6a6a;
                background-color: #353535;
            }
            QSpinBox::up-button {
                border: none;
                width: 20px;
                background-color: transparent;
            }
            QSpinBox::down-button {
                border: none;
                width: 20px;
                background-color: transparent;
            }
            QSpinBox::up-arrow {
                image: url(Icon/image/arrow_top.png);
                width: 10px;
                height: 10px;
            }
            QSpinBox::down-arrow {
                image: url(Icon/image/arrow_down.png);
                width: 10px;
                height: 10px;
            }
        """)


class CustomDoubleSpinBox(QDoubleSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(22)
        self.setStyleSheet("""
            QDoubleSpinBox {
                background-color: #303030;
                color: #dddddd;
                border-radius: 4px;
                padding: 2px 8px;
                border: 1px solid #4a4a4a;
                font-size: 12px;
                font-weight: 500;
            }
            QDoubleSpinBox:hover {
                border: 1px solid #6a6a6a;
                background-color: #353535;
            }
            QDoubleSpinBox::up-button {
                border: none;
                width: 20px;
                background-color: transparent;
            }
            QDoubleSpinBox::down-button {
                border: none;
                width: 20px;
                background-color: transparent;
            }
            QDoubleSpinBox::up-arrow {
                image: url(Icon/image/arrow_top.png);
                width: 10px;
                height: 10px;
            }
            QDoubleSpinBox::down-arrow {
                image: url(Icon/image/arrow_down.png);
                width: 10px;
                height: 10px;
            }
        """)