from PyQt6.QtWidgets import QLabel


class GcodeStatisticClass:
    name = "GcodeStatisticClass"

    def __init__(self, frame, event_bus):
        name = "statistic_"
        self.__frame = frame
        self.__event_bus = event_bus

        # Находим виджеты внутри frame
        self.__X_origin_label = frame.findChild(QLabel, name + "X_origin_label")
        self.__Y_origin_label = frame.findChild(QLabel, name + "Y_origin_label")
        self.__X_size_label = frame.findChild(QLabel, name + "X_size_label")
        self.__Y_size_label = frame.findChild(QLabel, name + "Y_size_label")
        self.__time_label = frame.findChild(QLabel, name + "time_label")

        self.__label_list = [self.__X_origin_label, self.__Y_origin_label, self.__X_size_label, self.__Y_size_label]
        self.__number_of_label = len(self.__label_list)

    def display_statistics(self, statistic):
        """
        Выводит переданные списком элементы статистики
        :param statistic: [X_origin, Y_origin, X_size, Y_size, time]
        :return:
        """
        time = statistic[4]
        time_min = int(time // 60)
        time_sec = time % 60
        time_ms = (time_sec * 1000) % 1000
        for index in range(self.__number_of_label):
            self.__label_list[index].setText(f"{statistic[index]:.3f}")

        self.__time_label.setText(f"{time_min:.0f}:{time_sec:.0f}:{time_ms:.0f}")
