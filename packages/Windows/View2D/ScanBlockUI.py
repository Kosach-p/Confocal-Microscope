class ScanAxesParamController:
    """
    Класс для сбора объектов класса AxisController и добавления остальных виджетов
    """

    def __init__(self, axes_config, borders, accum_time_lineedit, button, progress_bar, progressive_scan_checkbox):
        # Параметры инициализации класса
        self.__axes_config = axes_config  # dict вида: {'x': [lineedit1, lineedit2, lineedit3], 'y': [...], 'z': [...]}
        self.__borders = borders  # dict вида: {'x': [min, max], 'y': [min, max], 'z': [min, max], 'accum': [min, max]}
        self.__accum_time_lineedit = accum_time_lineedit
        self.__button = button
        self.__progress_bar = progress_bar
        self.__progressive_scan_checkbox = progressive_scan_checkbox

        self.__axes = {}  # dict для хранения контроллеров осей
        self.__accum_time_border = self.__borders.get('accum', [1, 10000])

        # Выход класса
        self.waiting_scan_start = False
        self.waiting_scan_stop = False
        self.__scan_parameters = {}  # теперь dict

        # Инициализация класса
        self.__connection_init()
        self.__scan_axes_init()

        # Проверка LineEdit значений
        self.__check_border()

    def __connection_init(self):
        """ Подключаем триггеры к действиям с виджетами """
        self.__accum_time_lineedit.editingFinished.connect(self.__check_border)
        self.__button.clicked.connect(self.__button_start_clicked)
        self.__progress_bar.setValue(100)

    def __scan_axes_init(self):
        """ Подключаем все оси, для которых были заданы виджеты """
        for axis_name, lines in self.__axes_config.items():
            border = self.__borders.get(axis_name, [0, 4095])
            self.__axes[axis_name] = ScanAxisParamController(lines, border)

    def __check_border(self):
        """ Проверка границ AccumTime """
        try:
            value = int(self.__accum_time_lineedit.text())
        except ValueError:
            value = self.__accum_time_border[0]
        value = max(self.__accum_time_border[0], min(self.__accum_time_border[1], value))
        self.__accum_time_lineedit.setText(str(value))

    def __button_start_clicked(self):
        """
        При нажатии на кнопку начала сканирования все параметры из объектов параметров сканирования осей,
        переносятся в объект параметров сканирования. Флаг ожидания начала сканирования поднимается
        Флаг ожидания окончания сканирования опускается. Состояние кнопки меняется на противоположное
        """
        self.__check_border()
        self.__scan_parameters = {}

        for axis_name, axis_controller in self.__axes.items():
            self.__scan_parameters[axis_name] = {
                'origin': axis_controller.origin,
                'size': axis_controller.size,
                'step': axis_controller.step
            }

        self.__scan_parameters['accum_time'] = int(self.__accum_time_lineedit.text())
        self.__scan_parameters['progressive_scan'] = self.__progressive_scan_checkbox.isChecked()

        self.waiting_scan_start = True
        self.waiting_scan_stop = False

        self.__button.setText("...сканирование...")
        self.__button.clicked.disconnect()
        self.__button.clicked.connect(self.__button_stop_clicked)

    def __button_stop_clicked(self):
        """ Сброс состояния кнопки сканирования в начальное. Нужно для правильной обработки завершения сканирования """
        self.waiting_scan_start = False
        self.waiting_scan_stop = True

        self.__button.setText("начать сканирование")
        self.__button.clicked.disconnect()
        self.__button.clicked.connect(self.__button_start_clicked)

    def button_status_reset(self):
        """ Сброс состояния кнопки сканирования в начальное. Нужно для правильной обработки завершения сканирования """
        self.__button.setText("начать сканирование")
        self.__button.clicked.disconnect()
        self.__button.clicked.connect(self.__button_start_clicked)

    def enable_widgets(self, status):
        """ Блокирует и разблокирует все доступные классу виджеты """
        for lines in self.__axes_config.values():
            for lineedit in lines:
                lineedit.setEnabled(status)
        self.__accum_time_lineedit.setEnabled(status)

    def get_scan_param(self):
        """ Возвращает dict с параметрами сканирования """
        return self.__scan_parameters

    def set_scan_param(self, scan_parameters):
        """ Устанавливает параметры сканирования из dict вида:
        {
            'x': {'origin': 0, 'size': 10, 'step': 1},
            'y': {'origin': 0, 'size': 10, 'step': 1},
            'z': {'origin': 0, 'size': 10, 'step': 1},
            'accum_time': 100,
            'progressive_scan': True
        }
        """
        for axis_name, params in scan_parameters.items():
            if axis_name == 'accum_time':
                if params is not None:
                    self.__accum_time_lineedit.setText(str(params))
            elif axis_name == 'progressive_scan':
                if params is not None:
                    self.__progressive_scan_checkbox.setChecked(params)
            elif axis_name in self.__axes:
                axis_values = [params.get('origin', 0), params.get('size', 0), params.get('step', 0)]
                self.__axes[axis_name].set_values(axis_values)

        return self.__scan_parameters

    def progressBar_setValue(self, value):
        """ Устанавливает значение прогресс бара """
        self.__progress_bar.setValue(int(max(0, min(100, value))))


class ScanAxisParamController:
    """
    Класс для работы с элементами контроля параметров сканирования по конкретной оси
    Элементы контроля - Строка ввода origin, Строка ввода size, Строка ввода step
    структура LinesEdit = [cord1, cord2, step]
    """

    def __init__(self, lines_edit, borders):
        # Параметры инициализации класса
        self.__lines_edit = lines_edit  # [origin, size, step]
        self.__borders = borders  # [min, max]

        self.__values = [0, 0, 0]

        # Выход класса
        self.origin = 0
        self.size = 0
        self.step = 0

        # Инициализация класса
        self.__connection_init()

        # Принудительное обновление строк ввода
        self.__line_edit_changed()

    def __connection_init(self):
        """ Подключаем триггеры к действиям с виджетами """
        for line_edit in self.__lines_edit:
            line_edit.editingFinished.connect(self.__line_edit_changed)

    def __line_edit_changed(self):
        """ При вводе данных проверяем их и, если надо, обновляем """
        for index in range(3):
            try:
                self.__values[index] = int(self.__lines_edit[index].text())
            except ValueError:
                self.__values[index] = 0

        self.__update_widget()

        self.origin = self.__values[0]
        self.size = self.__values[1]
        self.step = self.__values[2]

    def __check_border(self):
        """
        Проверка границ каждого отдельно
        Проверка, что origin + size не выходит за границу
        Проверка, что шаг меньше ширины скана
        """
        for index in range(3):
            self.__values[index] = max(self.__borders[0], min(self.__borders[1], self.__values[index]))

    def __update_widget(self):
        """ Обновление виджетов """
        self.__check_border()
        for index in range(3):
            self.__lines_edit[index].blockSignals(True)
            self.__lines_edit[index].setText(str(self.__values[index]))
            self.__lines_edit[index].blockSignals(False)

    def set_values(self, values: list):
        """ Установка значений извне в порядке [cord1, cord2, step] """
        for i, v in enumerate(values):
            if v is not None:
                self.__values[i] = v
        self.__update_widget()
        self.__line_edit_changed()
