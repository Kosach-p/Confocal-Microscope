class AxesController:
    """
    Класс для сбора объектов класса AxeController и добавления остальных виджетов
    """
    def __init__(self, LineEdit_list, Slider_list, ButtonPlus_list, ButtonMinus_list, ButtonHome, AxeBorder_list, ComboBox):
        # Параметры инициализации класса
        self.__LineEdit_list = LineEdit_list
        self.__Slider_list = Slider_list
        self.__ButtonPlus_list = ButtonPlus_list
        self.__ButtonMinus_list = ButtonMinus_list
        self.__ButtonHome = ButtonHome
        self.__AxisBorder_list = AxeBorder_list
        self.__ComboBox = ComboBox

        self.__number_of_axes = 0

        # Корни класса
        self.__axes = list()

        # Инициализация класса
        self.__connection_init()
        self.__comboBox_init()
        self.__axes_init()

    def __connection_init(self):
        self.__ButtonHome.clicked.connect(self.__button_click_home)

    def __comboBox_init(self):
        """ Заполняем комбобокс и прикрепляем к изменение выбора триггер """
        Step_Items = list()
        power = 1
        for _ in range(5):
            Step_Items.append(str(power * 1))
            Step_Items.append(str(power * 2))
            Step_Items.append(str(power * 5))
            power *= 10

        self.__ComboBox.addItems(Step_Items)
        self.__ComboBox.currentTextChanged.connect(self.__button_click_step_changed)

    def __axes_init(self):
        """ Подключаем все оси, для которых были заданы виджеты """
        self.__number_of_axes = min(len(self.__LineEdit_list), len(self.__Slider_list), len(self.__ButtonPlus_list), len(self.__ButtonMinus_list))

        for index in range(0, self.__number_of_axes):
            self.__axes.append(AxisController(self.__LineEdit_list[index], self.__Slider_list[index],
                                             self.__ButtonPlus_list[index], self.__ButtonMinus_list[index],
                                             self.__AxisBorder_list[index]))
            self.__axes[index].button_click_step = int(self.__ComboBox.currentText())

    def __button_click_step_changed(self):
        """ Изменился шаг при нажатии кнопки. Сообщаем это всем объектам осей """
        for axis in self.__axes:
            axis.button_click_step = int(self.__ComboBox.currentText())

    def __button_click_home(self):
        """ Нажата кнопка "ДОМ" """
        for index in range(0, self.__number_of_axes):
            center = self.__AxisBorder_list[index][0] + (self.__AxisBorder_list[index][1] - self.__AxisBorder_list[index][0]) // 2
            self.__axes[index].set_cord(center)

    def update_axes(self):
        """ Обновление состояний виджетов по установленным координатам """
        for axis in self.__axes:
            axis.update_widget()

    def reset_cord_changed(self):
        """ Очистить флаг изменившейся координаты у всех объектов осей """
        for axis in self.__axes:
            axis.cord_changed_flag = False

    def is_cord_changed(self) -> bool:
        """
        Функция вернёт True, если хотя бы одна координата оси находится в статусе изменившейся
        (статус надо сбрасывать с помощью функции clear_cord_changed_log)
        """
        for axis in self.__axes:
            if axis.cord_changed_flag:
                return True
        return False

    def set_cord(self, cords):
        """ Принудительная установка координаты для всех осей (вход в виде списка) """
        for index in range(0, self.__number_of_axes):
            self.__axes[index].set_cord(cords[index])

        self.update_axes()

    def get_cord(self) -> list:
        """ Получение координат от всех осей (выход в виде списка) """
        self.update_axes()

        cords = list()
        for axis in self.__axes:
            cords.append(axis.cord)
            axis.cord_changed_flag = False
        return cords

    def set_AxesBorder(self, AxisBorder_list):
        """ Принудительная установка границ для всех осей (вход в виде списка [[min1, max1], [min2, max2]]) """
        self.__AxisBorder_list = AxisBorder_list
        for index in range(0, self.__number_of_axes):
            self.__axes[index].set_AxisBorder(self.__AxisBorder_list[index])

    def enable_widgets(self, status):
        """ Блокирует и разблокирует все доступные классу виджеты """
        for index in range(0, self.__number_of_axes):
            self.__LineEdit_list[index].setEnabled(status)
            self.__Slider_list[index].setEnabled(status)
            self.__ButtonPlus_list[index].setEnabled(status)
            self.__ButtonMinus_list[index].setEnabled(status)

        self.__ButtonHome.setEnabled(status)
        self.__ComboBox.setEnabled(status)


class AxisController:
    """
    Класс для работы с элементами контроля координат
    Элементы контроля - Строка ввода, Слайдер, Кнопки увеличения и уменьшения координаты
    """
    def __init__(self, LineEdit, Slider, ButtonPlus, ButtonMinus, AxisBorder):
        # Параметры инициализации класса
        self.__LineEdit = LineEdit
        self.__Slider = Slider
        self.__ButtonPlus = ButtonPlus
        self.__ButtonMinus = ButtonMinus
        self.__AxisBorder = AxisBorder

        # Вход класса
        self.button_click_step = 1

        # Выход класса
        self.cord_changed_flag = False
        self.cord = 0

        # Инициализация класса
        self.__connection_init()
        self.__set_SliderBorder()

    def __connection_init(self):
        """ Подключаем триггеры к действиям с виджетами """
        self.__ButtonPlus.clicked.connect(lambda: self.__button_clicked(1))
        self.__ButtonMinus.clicked.connect(lambda: self.__button_clicked(-1))
        self.__Slider.valueChanged.connect(self.__slider_changed)
        self.__LineEdit.editingFinished.connect(self.__lineEdit_changed)

    def __button_clicked(self, direction):
        """ При нажатии кнопки меняем координату на шаг self._Button_click_step """
        self.cord_changed_flag = True
        self.cord += direction * self.button_click_step
        self.update_widget()

    def __slider_changed(self):
        """ При изменении слайдера устанавливаем новую координату """
        self.cord_changed_flag = True
        self.cord = int(self.__Slider.value())
        self.update_widget()

    def __lineEdit_changed(self):
        """ При вводе данных меняем координату """
        self.cord_changed_flag = True
        self.cord = int(self.__LineEdit.text())
        self.update_widget()

    def update_widget(self):
        """ Обновление виджетов """
        self.__check_border()

        self.__LineEdit.blockSignals(True)
        self.__Slider.blockSignals(True)

        self.__LineEdit.setValue(self.cord)
        self.__Slider.setValue(int(self.cord))

        self.__LineEdit.blockSignals(False)
        self.__Slider.blockSignals(False)

    def __check_border(self):
        """ Проверяем координату на предмет выхода за установленные границы """
        self.cord = max(self.__AxisBorder[0], min(self.__AxisBorder[1], self.cord))

    def __set_SliderBorder(self):
        """ Установка границ движения слайдера как виджета """
        self.__Slider.setMinimum(int(self.__AxisBorder[0]))
        self.__Slider.setMaximum(int(self.__AxisBorder[1]))

    def set_cord(self, cord):
        """ Принудительное изменение координаты доступное извне """
        self.cord_changed_flag = True
        self.cord = int(cord)
        self.update_widget()

    def set_AxisBorder(self, AxisBorder):
        """ Принудительное изменение границ (вход в виде списка [min, max])"""
        self.__AxisBorder = AxisBorder
        self.__set_SliderBorder()
