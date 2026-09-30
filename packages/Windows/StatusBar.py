from PyQt6.QtWidgets import QLabel, QHBoxLayout, QFrame, QSpacerItem, QSizePolicy
from PyQt6.QtCore import QTimer, Qt


class StatusBarClass:
    """ Класс для работы со статус баром """
    name = "StatusBarClass"

    COLORS = {
        'info': '#2d3a4f',
        'success': '#2d4f3a',
        'warning': '#5f4a2d',
        'error': '#5f2d2d'
    }

    def __init__(self, statusBar, event_bus):
        self._statusBar = statusBar
        self._event_bus = event_bus

        self._statusBar_right_Label = QLabel()
        self._statusBar_right_Label.setAlignment(Qt.AlignRight)
        self._statusBar_center_Label = QLabel()
        self._statusBar_right_Label.setAlignment(Qt.AlignCenter)
        self._statusBar_left_Label = QLabel()
        self._statusBar_right_Label.setAlignment(Qt.AlignLeft)

        self._TIM_Init()
        self._init_statusBar()

    def _init_statusBar(self):

        """ Создаёт два Label, которые будут выполнять роли правого и левого StatusBar """
        container = QFrame()
        container.setStyleSheet("background: none; border: none;")
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self._statusBar_right_Label = QLabel("")
        self._statusBar_center_Label = QLabel("")

        layout.addWidget(self._statusBar_right_Label)
        layout.addItem(QSpacerItem(1920, 5, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding))
        layout.addWidget(self._statusBar_center_Label)
        layout.addItem(QSpacerItem(1920, 5, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding))
        layout.addWidget(self._statusBar_left_Label)

        container.setLayout(layout)
        self._statusBar.addPermanentWidget(container)

        self._event_bus.StatusBar.connect(self._event_process)

    def _TIM_Init(self):
        """ Инициализация таймер """
        self.TIM = QTimer()
        self.TIM.timeout.connect(lambda: self._TIM_Interruption())

    def _TIM_Interruption(self):
        """ Обработка прерываний по таймеру """
        self.TIM.stop()
        self.set_rightStatusBar_text("")

    def _event_process(self, text, AutoClearTime, msg_type):
        if AutoClearTime > 0:
            self.TIM.start(int(AutoClearTime * 1000))

        if msg_type is None:
            if "✅" in text:
                msg_type = "success"
            elif "❌" in text:
                msg_type = "error"
            elif "❗️" in text:
                msg_type = "warning"
            elif "status" in text:
                self.set_centerStatusBar_text(text=text)
                return True

        self._statusBar_right_Label.setStyleSheet(f"""QLabel {{background-color: {self.COLORS.get(msg_type)};}}""")

        self.set_rightStatusBar_text("    " + text + "    ")
            
    def set_leftStatusBar_text(self, text):
        """ Установка текста text в левый статус бар """
        if type(text) is str:
            self._statusBar_left_Label.setText(text)

    def set_centerStatusBar_text(self, text):
        """ Установка текста text в правый статус бар """
        if type(text) is str:
            self._statusBar_center_Label.setText(text)

    def set_rightStatusBar_text(self, text):
        """ Установка текста text в правый статус бар """
        if type(text) is str:
            self._statusBar_right_Label.setText(text)
    
    def reset_leftStatusBar_text(self):
        """ Сброс текста в левом статус бар """
        self._statusBar_left_Label.setText("")

    def reset_centerStatusBar_text(self):
        """ Сброс текста в правом статус бар """
        self._statusBar_center_Label.setText("")

    def reset_rightStatusBar_text(self):
        """ Сброс текста в правом статус бар """
        self._statusBar_right_Label.setText("")
        
        