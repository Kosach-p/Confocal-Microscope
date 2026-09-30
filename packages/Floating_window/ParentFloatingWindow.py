from PyQt6.QtWidgets import QMainWindow


class FloatingWindowRegistry:
    """ Словарь всех добавленных окон """
    __registry = {}

    @classmethod
    def register(cls, window):
        """ Добавляем ссылку на окно в общий словарь """
        cls.__registry[window.name] = window

    @classmethod
    def get(cls, name):
        """ Возвращаем ссылку на устройство с именем name """
        obj = cls.__registry.get(name)
        return obj

    @classmethod
    def get_all(cls):
        """ Возвращаем список всех name, которые были добавлены """
        name_list = list()
        window_list = list()
        for name, window in cls.__registry.items():
            name_list.append(name)
            window_list.append(window)

        return name_list, window_list


class ParentFloatingWindow(QMainWindow):
    name = "ParentWindow"

    def __init__(self, parent=None):
        super().__init__()
        FloatingWindowRegistry.register(self)

        self.parent = parent
        self.initialized = False

    def post_init(self):
        """ Извне можно запросить инициализацию объекта. Если он ещё не был инициализирован, вызывается __post_init """
        if not self.initialized:
            self._post_init()
            self.initialized = True

    def _post_init(self):
        """
        Вызывается либо самим объектом, либо извне, через метод post_init
        Реализует, полную инициализацию объекта окна, включая загрузку всего UI
        """

    def Window_Selected(self):
        """ Действия, при выборе данного окна """

    def Set_Widget_Settings(self):
        """ Установка настроек виджетов """

    def __TIM_Init(self):
        """ Инициализация таймеров """

    def __TIM_Interruption(self, TIMx):
        """ Обработчик прерываний от таймеров """

    def Process_ModBus_Packet(self, ModBus_Packet):
        """ Обработчик сообщений """

    def saveFile(self):
        """ Общая функция сохранения данных на окне в файл """
        print("FastSave метод не поддерживается для", self.name)

    def openFile(self):
        """ Общая функция открытия данных на окне в файл """
        print("FastOpen метод не поддерживается для", self.name)
