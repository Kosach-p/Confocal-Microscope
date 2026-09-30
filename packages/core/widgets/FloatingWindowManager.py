class FloatingWindowManager:
    """ Класс для работы со стаками окон """
    def __init__(self):
        self.__list = list()

    def set_window_list(self, window_list: list):
        """ Загрузка списка окон в StackedWidget """
        self.__list = window_list

    def show_window(self, name):
        """ Демонстрация окна, класс которого имеет имя name """
        for obj in self.__list:
            if obj.name == name:
                try:
                    obj.post_init()
                    obj.show()
                except Exception as e:
                    print(f"FloatingWindowManager::show_window::\n{name} не обладает функцией show\nОшибка {e}")
                return True
        print(f"FloatingWindowManager::show_window::Не найдено плавающее окно с именем {name}")
        return False