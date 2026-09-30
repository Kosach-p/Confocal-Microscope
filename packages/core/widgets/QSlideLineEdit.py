class QSlideLineEdit:
    """
    Класс для работы с элементами контроля координат
    Элементы контроля - Строка ввода, Слайдер, Кнопки увеличения и уменьшения координаты
    """
    def __init__(self, Slider, LineEdit, Border):
        # Параметры инициализации класса
        self.__LineEdit = LineEdit
        self.__Slider = Slider
        self.__Border = Border

        # Список подключённых прерываний (функций)
        self.__connection_list = list()

        self.__value = None
        self.__set_value(0)

        # Инициализация класса
        self.__connection_init()
        self.__set_SliderBorder()
        self.update_widget()

    def __connection_init(self):
        """ Подключаем триггеры к действиям с виджетами """
        self.__Slider.valueChanged.connect(self.__slider_changed)
        self.__LineEdit.editingFinished.connect(self.__lineEdit_changed)

    def __slider_changed(self):
        """ При изменении слайдера устанавливаем новую координату """
        self.__value_changed_flag = True
        self.__value = int(self.__Slider.value())
        self.update_widget()

    def __lineEdit_changed(self):
        """ При вводе данных меняем координату """
        self.__value_changed_flag = True
        self.__value = int(self.__LineEdit.text())
        self.update_widget()

    def update_widget(self):
        """ Обновление виджетов """
        self.__check_border()

        self.__LineEdit.blockSignals(True)
        self.__Slider.blockSignals(True)

        self.__LineEdit.setText(str(int(self.__value)))
        self.__Slider.setValue(int(self.__value))
        self.__set_value(self.__value)

        self.__LineEdit.blockSignals(False)
        self.__Slider.blockSignals(False)

    def __set_SliderBorder(self):
        """ Установка границ движения слайдера как виджета """
        self.__Slider.setMinimum(int(self.__Border[0]))
        self.__Slider.setMaximum(int(self.__Border[1]))

    def __check_border(self):
        """ Проверяем координату на предмет выхода за установленные границы """
        self.__value = max(self.__Border[0], min(self.__Border[1], self.__value))

    def set_value(self, value):
        """ Принудительное изменение координаты доступное извне """
        self.__set_value(int(value))
        self.update_widget()
    
    def __set_value(self, value):
        """ Устанавливается значение виджета value """
        self.__value = value
        self.__ValueChanged()
    
    def __ValueChanged(self):
        """ Вызывается, при изменении value """
        for func in self.__connection_list:
            func()
        
    def ValueChanged_connect(self, func):
        """ Добавляет функцию к прерыванию по изменению значения в виджете """
        self.__connection_list.append(func)

    def ValueChanged_disconnect(self, func):
        """ Удаляет функцию из прерывания по изменению значения в виджете """
        self.__connection_list.remove(func)
    
    @property
    def value(self):
        """ Возвращает текущее значение в виджетах """
        return self.__value
        
