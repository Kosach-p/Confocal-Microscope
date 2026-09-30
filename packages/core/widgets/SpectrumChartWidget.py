import numpy as np

import pyqtgraph as pg
from PyQt6.QtWidgets import QSizePolicy, QVBoxLayout, QLabel
from packages.Floating_window.node_editor.NodeRegistry import NodeRegistry
from packages.core.validators.dataValidator import detect_data_type
from PyQt6.QtGui import QColor


class SpectrumChart:
    def __init__(self, parent, user_name):
        self.parent = parent
        self.user_name = user_name
        self.plot_widget = pg.PlotWidget(parent=parent)

        self.coord_label = QLabel("x: --, y: --", self.plot_widget)
        self.coord_label.setStyleSheet("""
            QLabel {
                background: rgba(0, 0, 0, 185);
                color: white;
                padding: 5px;
                border-radius: 3px;
                font-family: monospace;
            }
        """)
        self.coord_label.hide()
        self.plot_widget.leaveEvent = self._on_leave

        self.plot_widget.scene().sigMouseMoved.connect(self._on_mouse_moved)

        self.plot_widget.setBackground(None)
        self.plot_widget.showGrid(x=True, y=True)

        self.plot_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(self.parent)
        layout.addWidget(self.plot_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        self.parent.setLayout(layout)

        self.__curves = list()
        self.__tree_data = list()

        # Настройка осей
        for axis in ['left', 'bottom']:
            self.ax = self.plot_widget.getAxis(axis)
            self.plot_widget.getAxis(axis).setPen('l')
            self.ax.setTextPen('l')

        NodeRegistry.register_input(self.node_in, self.user_name)
        NodeRegistry.register_output(self.node_out, self.user_name)
        NodeRegistry.register_type("spectrum", self.user_name)

    def node_in(self):
        """ функция возвращает данные для входной ноды """
        return self.__tree_data

    def node_out(self, dataset, params, id):
        dtype = detect_data_type(dataset)
        self.clear_by_source(id)
        if dtype == "empty":
            return False, "Пустой датасет"

        if dtype == "spectrum_list":
            for x, y in dataset:
                print("data x")
                print(x)
                print("data y")
                print(y)
                self.add_curve_smart(x, y, color=params["color"], removable=True, highlight=params["value"], source=id)
            return True, ""

        if dtype == "spectrum":
            x, y = dataset
            self.add_curve_smart(x, y, color=params["color"], removable=True, highlight=params["value"], source=id)
            return True, "Один спектр"

        return False, "Требуется [x, y] или список [[x, y], ...]"

    def _on_leave(self, event):
        self.coord_label.hide()
        pg.PlotWidget.leaveEvent(self.plot_widget, event)

    def _on_mouse_moved(self, pos):
        """Обработка движения мыши"""
        if self.plot_widget.sceneBoundingRect().contains(pos):
            mouse_point = self.plot_widget.plotItem.vb.mapSceneToView(pos)
            x = f"{mouse_point.x():,.2f}".replace(',', ' ')
            y = f"{mouse_point.y():,.2f}".replace(',', ' ')
            self.coord_label.setText(f"x: {x}, y: {y}")

            # Автоподгон размера под текст
            self.coord_label.adjustSize()

            # Позиция: правый верхний угол с отступом 10 пикселей
            label_width = self.coord_label.width()
            parent_width = self.plot_widget.width()

            self.coord_label.move(parent_width - label_width - 10, 10)
            self.coord_label.show()

    @staticmethod
    def __get_data_signature(x_data, y_data, source):
        x_sum = x_data.sum()
        y_sum = y_data.sum()
        x_first = x_data[0]
        x_last = x_data[-1]
        y_first = y_data[0]
        y_last = y_data[-1]
        length = len(x_data)

        # Создаём кортеж и хэшируем
        signature_data = (x_sum, y_sum, x_first, x_last, y_first, y_last, length, source)
        return hash(signature_data)

    def show_TreeData(self, data, reason):
        self.__tree_data = data
        NodeRegistry.send_signal(self.user_name)
        self.reset_curves_list()
        self.clear_removable_curve()
        for params, dataset_list, vis_list, select_list in self.__tree_data:
            if params["visibility"] is True:
                for dataset, visibility, select in zip(dataset_list, vis_list, select_list):
                    if visibility is True:
                        if params["selected"] is True:
                            select = True
                        if select is True:
                            self.add_curve_smart(dataset[0], dataset[1], color="white", highlight=1, source="tree")
                        else:
                            self.add_curve_smart(dataset[0], dataset[1], color="gray", highlight=0, source="tree")

                cord, data = self.calc_average(dataset_list, vis_list)
                if (cord is not None) and (data is not None):
                    self.add_curve_smart(cord, data, color="red", linewidth=3, highlight=2, source="average")

        self.clear()

    def calc_average(self, data, visibility):
        """Быстрое усреднение с разными сетками"""

        visible = [(c, m) for (c, m), v in zip(data, visibility) if v]

        if not visible:
            return None, None

        # Проверка на пустые массивы координат
        valid_curves = []
        for c, m in visible:
            if len(c) > 0 and len(m) > 0 and len(c) == len(m):
                valid_curves.append((c, m))

        if not valid_curves:
            return None, None

        # Создаем общую сетку на основе всех координат
        all_cords = np.concatenate([c for c, _ in valid_curves])

        # Проверка на случай, если все координаты одинаковые
        if all_cords.min() == all_cords.max():
            # Если все точки на одной координате, возвращаем среднее значение
            avg_value = np.mean([np.mean(m) for _, m in valid_curves])
            return np.array([all_cords.min()]), np.array([avg_value])

        # Создаем референсную сетку
        n_ref_points = max(len(valid_curves[0][0]) * 100, 100)  # минимум 100 точек
        ref_cord = np.linspace(all_cords.min(), all_cords.max(), n_ref_points)

        n_curves = len(valid_curves)
        n_points = len(ref_cord)
        interpolated = np.zeros((n_curves, n_points))

        for i, (cord, meas) in enumerate(valid_curves):
            # Проверка на монотонность координат (требование np.interp)
            if np.all(np.diff(cord) > 0):
                # Координаты возрастают - можно интерполировать напрямую
                interpolated[i] = np.interp(ref_cord, cord, meas)
            elif np.all(np.diff(cord) < 0):
                # Координаты убывают - переворачиваем для интерполяции
                interpolated[i] = np.interp(ref_cord, cord[::-1], meas[::-1])
            else:
                # Координаты не монотонны - сортируем
                sort_idx = np.argsort(cord)
                cord_sorted = cord[sort_idx]
                meas_sorted = meas[sort_idx]
                interpolated[i] = np.interp(ref_cord, cord_sorted, meas_sorted)

        avr = np.mean(interpolated, axis=0)

        return ref_cord, avr

    def add_curve_smart(self, x_data, y_data, l=None, color="white", linewidth=1, removable=False, target_curve=False, highlight=1, source="tree"):
        """
        Строит график данных. Если сигнатура данных есть в списке - не перестраивает.
        При отрисовке помечает график как активный, даже если он уже есть в списке.
        Активные графики не удаляются методом clear_curves_list.

        :param x_data: Одномерный массив данных по оси X
        :param y_data: Одномерный массив данных по оси Y
        :param l: Длинна данных (не обязательно)
        :param color: Цвет линии (не обязательно)
        :param linewidth: Толщина линии (не обязательно)
        :param removable: удалять ли график методом reset_curves_list
        :param highlight: поместить поверх других кривых
        :return:

        Некоторые графики меняют сигнатуру, но удалять их надо. К примеру, результат усреднения каждый раз меняется,
        но после каждого изменения, предыдущий надо удалять! Если это такой график, выставляется флаг removable
        """
        try:
            x_data = np.array(x_data)
            y_data = np.array(y_data)
            idx = np.argsort(x_data)
            y_data = y_data[idx]
            x_data = np.sort(x_data)

            if l is None:
                l = len(y_data)
            if l == 0:
                return False

            if not target_curve:
                signature = self.__get_data_signature(x_data, y_data, source)
                for curve in self.__curves[:]:
                    if curve["signature"] == signature:
                        curve["ready"] = True
                        curve["curve"].setZValue(highlight)

                        if curve["color"] != color:
                            pen = pg.mkPen(color, width=linewidth)
                            curve["curve"].setPen(pen)
                            curve["color"] = color
                        break
                else:
                    pen = pg.mkPen(color, width=linewidth)
                    curve = self.plot_widget.plot(x_data[:l], y_data[:l], pen=pen)
                    curve.setZValue(highlight)
                    self.__curves.append({"curve": curve, "signature": signature, "ready": True, "removable": removable, "color": color, "source": source})

            else:
                if target_curve is not None:
                    self.__curves.remove(target_curve)
                pen = pg.mkPen(color, width=linewidth)
                curve = self.plot_widget.plot(x_data[:l], y_data[:l], pen=pen)
                return curve
        except Exception as e:
            print("ERROR::SpectrumChart::add_curve_smart::", e)
            return False

    def reset_curves_list(self):
        """ Делает все записанные кривые неактивными """
        for curve in self.__curves:
            if curve["removable"]:
                self.__curves.remove(curve)
                self.plot_widget.removeItem(curve["curve"])
            else:
                curve["ready"] = False

    def clear_removable_curve(self):
        for curve in self.__curves[:]:
            if curve["removable"]:
                self.__curves.remove(curve)
                self.plot_widget.removeItem(curve["curve"])

    def clear(self):
        """ Удаляет все не активные кривые """
        for curve in self.__curves[:]:
            if not curve["ready"]:
                self.__curves.remove(curve)
                self.plot_widget.removeItem(curve["curve"])

    def clear_all(self):
        """ Удаляет все кривые """
        self.plot_widget.clear()

    def clear_by_source(self, source):
        """ Удаляет все кривые определённого источника """
        for curve in self.__curves[:]:
            if source == curve["source"]:
                self.__curves.remove(curve)
                self.plot_widget.removeItem(curve["curve"])
