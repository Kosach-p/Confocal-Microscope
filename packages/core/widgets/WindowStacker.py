from PyQt6.QtWidgets import QStackedWidget


class WindowStacker(QStackedWidget):
    """ Класс для работы со стаками окон """
    def set_window_list(self, window_list: list):
        """ Загрузка списка окон в StackedWidget """
        for Window in window_list:
            self.addWidget(Window)

    def show_window(self, name):
        """ Демонстрация окна, класс которого имеет имя name """
        for i in range(self.count()):
            if self.widget(i).name == name:
                obj = self.widget(i)
                obj.post_init()
                try:
                    obj.window_selected()
                except Exception as e:
                    print(f"WindowStacker::show_window::\n{name} не обладает функцией window_selected или она неисправна\nОшибка {e}")
                self.setCurrentIndex(i)
                return True

        return False