import time

from PyQt6.QtWidgets import QPlainTextEdit, QTreeView, QAbstractItemView, QStyledItemDelegate, QHeaderView
from Icon.IconName import *
import os

from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, QEvent
import re

from packages.core.services.save_service.param_check import normalize_params


class TreeDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, tree_module=None):
        super().__init__(parent)
        self.tree_view = parent
        self.tree_module = tree_module
        self.icons = {
            'save': QIcon(save_Icon),
            'visible': QIcon(eye_Icon),
            'hidden': QIcon(closed_eye_Icon),
            'trash': QIcon(closed_trash_Icon),
            'trash_hover': QIcon(trash_Icon)
        }
        self.hovered_index = None

        self.btn_width = 16
        self.btn_height = 16
        self.btn_pressed_width = 16
        self.btn_pressed_height = 16
        self.btn_half_width = self.btn_width // 2
        self.btn_half_height = self.btn_height // 2
        self.btn_distance = 22

    def createEditor(self, parent, option, index):
        if index.column() == 1:
            return None  # запрещаем редактирование второй колонки
        return super().createEditor(parent, option, index)

    def paint(self, painter, option, index):
        super().paint(painter, option, index)

        if index.column() == 1:
            model = index.model()
            item = model.itemFromIndex(index.siblingAtColumn(0))

            rect = option.rect
            left = rect.left()
            right = rect.right()
            top = rect.top()
            bottom = rect.bottom()

            x_center = (right + left) // 2
            y_center = (top + bottom) // 2

            save_x = x_center - self.btn_distance - self.btn_half_width
            vision_x = x_center - self.btn_half_width
            trash_x = x_center + self.btn_distance - self.btn_half_width

            y = y_center - self.btn_half_height

            if item.hasChildren():
                self.icons['save'].paint(painter, save_x, y, self.btn_width, self.btn_height)

            visible = item.data(Qt.ItemDataRole.UserRole + 1) if item else True
            icon = self.icons['visible'] if visible else self.icons['hidden']
            icon.paint(painter, vision_x, y, self.btn_width, self.btn_height)

            is_hover = (self.hovered_index == index)
            trash_icon = self.icons['trash_hover'] if is_hover else self.icons['trash']
            trash_icon.paint(painter, trash_x, y, self.btn_width, self.btn_height)

    def editorEvent(self, event, model, option, index):
        if index.column() == 1:
            rect = option.rect
            left = rect.left()
            right = rect.right()
            top = rect.top()
            bottom = rect.bottom()

            x_center = (right + left) // 2
            y_center = (top + bottom) // 2

            save_x = x_center - self.btn_distance - self.btn_half_width
            vision_x = x_center - self.btn_half_width
            trash_x = x_center + self.btn_distance - self.btn_half_width

            y = y_center - self.btn_half_height

            pos = event.pos()

            if event.type() == QEvent.Type.MouseMove:
                if trash_x <= pos.x() < trash_x + self.btn_width and y <= pos.y() < y + self.btn_height:
                    self.hovered_index = index
                else:
                    self.hovered_index = None

                model.dataChanged.emit(index, index)

            if event.type() == QEvent.Type.MouseButtonPress:
                model = index.model()
                clicked_item = model.itemFromIndex(index.siblingAtColumn(0))
                selected_items = []
                for idx in self.tree_view.selectionModel().selectedIndexes():
                    if idx.column() == 0:
                        selected_items.append(model.itemFromIndex(idx))

                if y <= pos.y() < y + self.btn_pressed_height:
                    change = False
                    if save_x <= pos.x() < save_x + self.btn_pressed_width and clicked_item.hasChildren:
                        if clicked_item in selected_items:
                            index_list = list()
                            for item in selected_items:
                                index_list.append(model.indexFromItem(item))
                            self.on_save(index, clicked_item.text())
                        else:
                            index = model.indexFromItem(clicked_item)
                            self.on_save(index, clicked_item.text())

                    elif vision_x <= pos.x() < vision_x + self.btn_pressed_width:
                        current = clicked_item.data(Qt.ItemDataRole.UserRole + 1)
                        new_state = not current if current is not None else False
                        if clicked_item in selected_items:
                            for item in selected_items:
                                index = model.indexFromItem(item)
                                self.on_visibility(index, new_state)
                        else:
                            index = model.indexFromItem(clicked_item)
                            self.on_visibility(index, new_state)
                        change = True

                    elif trash_x <= pos.x() < trash_x + self.btn_pressed_width:
                        if clicked_item in selected_items:
                            for item in selected_items:
                                index = model.indexFromItem(item)
                                index = model.indexFromItem(item)
                                self.on_delete(index)
                        else:
                            index = model.indexFromItem(clicked_item)
                            self.on_delete(index)
                        change = True

                    self.tree_module.show_block = False
                    if change is True:
                        self.display_changes()

                    return True

        return super().editorEvent(event, model, option, index)

    def on_save(self, index, name):
        item = index.model().itemFromIndex(index.siblingAtColumn(0))
        id = item.data(Qt.ItemDataRole.UserRole)
        if self.tree_module:
            self.tree_module.on_save(id, name)

    def on_visibility(self, index, new_state):
        self.tree_module.show_block = True
        model = index.model()
        item = model.itemFromIndex(index.siblingAtColumn(0))
        if not item:
            return

        item.setData(new_state, Qt.ItemDataRole.UserRole + 1)

        if self.tree_module:
            item = item.data(Qt.ItemDataRole.UserRole)
            self.tree_module.on_visibility_toggle(item, new_state)

        model.dataChanged.emit(index, index)
        self.tree_module.show_block = False

    def on_delete(self, index):
        self.tree_module.show_block = True
        item = index.model().itemFromIndex(index.siblingAtColumn(0))
        id = item.data(Qt.ItemDataRole.UserRole)
        if self.tree_module:
            self.tree_module.on_delete(id)
        self.tree_module.show_block = False

    def display_changes(self):
        """ Вызывает метод, отображающий изменения данных """
        self.tree_module.show_data()


class DataStore:
    def __init__(self):
        self.__branches = {}  # {branch_id: {params: [], leaf_ids: [], visibility: bool}}
        self.__data_store = {}  # {leaf_id: {data: nparray, visibility: bool}}
        self._next_branch_id = -1
        self._next_leaf_id = 1

    def add_data(self, params: dict, data_list) -> tuple:
        leaf_id_list = list()
        leaf_name_list = list()
        branch_id, branch = self.find_branch(params)
        if branch is None:
            branch = {"params": params, "leaf_ids": [], "visibility": True, "selected": False}
            branch_id = self._next_branch_id
            self._next_branch_id -= 1

        for data in data_list:
            leaf_id_list.append(self._next_leaf_id)
            name = f"{branch['params'].get('metadata', {}).get('description', '')} № {self._next_leaf_id:04d}"
            leaf_name_list.append(name)
            self._next_leaf_id += 1

            branch["leaf_ids"].append(leaf_id_list[-1])

            self.__data_store[leaf_id_list[-1]] = {"data": data, "visibility": True, "selected": False, "params": {"name": name}}

        self.__branches[branch_id] = branch

        name = branch['params'].get('name')
        if name is None:
            name = branch['params'].get('metadata', {}).get('created', 'Группа')

        self.set_name(branch_id, f"{name}")

        return branch_id, leaf_id_list, leaf_name_list

    @property
    def data(self):
        """ Собирает все данные дерева и возвращает его в формате [[param, data, vis], [param, data, vis], ...] """
        ret = list()
        for branch in self.__branches.values():
            ret.append(self.branch_data(branch))
        return ret

    @property
    def vis_data(self):
        """ Собирает все видимые данные дерева и возвращает его в формате [[param, data, vis], [param, data, vis], ...] """
        ret = list()
        for branch in self.__branches.values():
            param, data_list, vis_list, select_list = self.branch_data(branch)
            if param.get("visibility") is True:
                filtered_data = list()
                filtered_vis = list()
                for data, vis in zip(data_list, vis_list):
                    if vis is True:
                        filtered_data.append(data)
                        filtered_vis.append(True)
                ret.append([param, filtered_data, filtered_vis])
        return ret

    def data_by_id(self, id):
        if id > 0:
            branch = self.get_branch_by_leaf(id)
            leaf = self.get_leaf(id)
            data_list = [leaf["data"]]
            visibility_list = [leaf["visibility"]]
            return [{"params": branch.get("params"), "visibility": branch.get("visibility")}, data_list, visibility_list]
        elif id < 0:
            branch = self.__branches.get(id)
            return self.branch_data(branch)

    def data_by_ids(self, ids_list):
        ids_list.sort()
        added_ids = list()
        ret = list()
        for id in ids_list:
            if id > 0:
                if id not in added_ids:
                    branch = self.get_branch_by_leaf(id)
                    leaf = self.get_leaf(id)
                    data_list = [leaf["data"]]
                    visibility_list = [leaf["visibility"]]
                    ret.append([{"params": branch.get("params"), "visibility": branch.get("visibility")}, data_list, visibility_list])
            elif id < 0:
                branch = self.__branches.get(id)
                added_ids.extend(branch.get("leaf_ids"))
                ret.append(self.branch_data(branch))

        return ret

    def branch_data(self, branch):
        if branch is not None:
            leafs = self.get_leafs(branch.get("leaf_ids"))
            data_list = [item["data"] for item in leafs]
            visibility_list = [item["visibility"] for item in leafs]
            selected_list = [item["selected"] for item in leafs]
            name_list = [item["params"]["name"] for item in leafs]
            return [{"params": branch.get("params"), "visibility": branch.get("visibility"),
                     "selected": branch.get("selected"), "leaf_names": name_list},
                    data_list, visibility_list, selected_list]
        return False

    def find_branch(self, params):
        for branch_id, branch in self.__branches.items():
            if self.comparing_params_criteria(branch["params"], params):
                return branch_id, branch
        return None, None

    @staticmethod
    def comparing_params_criteria(params_1, params_2):
        return params_1["parameters"] == params_2["parameters"] and params_1["comment"] == params_2["comment"]

    def get_by_id(self, id):
        if id > 0:
            return self.get_leaf(id)
        elif id < 0:
            return self.get_branch(id)

    def get_leaf(self, leaf_id):
        return self.__data_store.get(leaf_id)

    def get_leafs(self, leaf_ids):
        leafs = list()
        for leaf_id in leaf_ids:
            leafs.append(self.__data_store.get(leaf_id))
        return leafs

    def get_branch(self, branch_id):
        return self.__branches.get(branch_id)

    def get_branch_by_leaf(self, leaf_id):
        for branch in self.__branches.values():
            if leaf_id in branch.get("leaf_ids"):
                return branch

    def get_branches(self, branch_ids):
        branches = list()
        for branch_id in branch_ids:
            branches.append(self.__branches.get(branch_id))
        return branches

    def get_branch_leafs(self, branch):
        if branch is int:
            return self.get_leafs(self.__branches.get(branch)["leaf_ids"])
        else:
            return self.get_leafs(branch["leaf_ids"])

    def get_branches_leafs(self, branch_ids):
        return self.get_branch_leafs(self.get_branches(branch_ids))

    def delete_by_id(self, id):
        if id > 0:
            return self.delete_leaf(id)
        elif id < 0:
            return self.delete_branch(id)

    def delete_leaf(self, leaf_id):
        if self.__data_store.get(leaf_id) is not None:
            branch = self.get_branch_by_leaf(leaf_id)
            branch["leaf_ids"].remove(leaf_id)
            del self.__data_store[leaf_id]
            return True
        else:
            return False

    def delete_leafs(self, leaf_ids):
        result = list()
        for leaf_id in leaf_ids:
            result.append(self.delete_leaf(leaf_id))
        return result

    def delete_branch(self, branch_id):
        result = self.delete_leafs(self.__branches.get(branch_id)["leaf_ids"])
        if False in result:
            return result
        else:
            if self.__branches.get(branch_id) is not None:
                del self.__branches[branch_id]
                return True
            else:
                return False

    def get_visibility(self, id):
        return self.get_by_id(id)["visibility"]

    def set_visibility(self, id, state):
        self.get_by_id(id)["visibility"] = state

    def set_selected_by_ids(self, ids_list):
        for branch in self.__branches.values():
            branch["selected"] = False
            leafs = self.get_branch_leafs(branch)
            for leaf in leafs:
                leaf["selected"] = False

        for id in ids_list:
            element = self.get_by_id(id)
            element["selected"] = True

    def set_comment(self, branch_id, comment_text):
        if self.__branches.get(branch_id) is not None:
            self.__branches[branch_id]["params"]["comment"] = comment_text

    def set_name(self, id, name):
        if name == "":
            name = "Группа"

        name_list = list()
        if self.get_by_id(id) is not None:
            if id < 0:
                for branch_id, branch in self.__branches.items():
                    if branch_id != id:
                        name_list.append(branch["params"]["name"])
            elif id > 0:
                branch = self.get_branch_by_leaf(id)
                for leaf_id, leaf in zip(branch.get("leaf_ids"), self.get_leafs(branch.get("leaf_ids"))):
                    if leaf_id != id:
                        name_list.append(leaf["params"]["name"])

            i = 1
            if name in name_list:
                name = re.sub(r'.\d+$', '', name)
                while f"{name}.{i:03d}" in name_list:
                    i += 1
                self.get_by_id(id)["params"]["name"] = f"{name}.{i:03d}"
            else:
                self.get_by_id(id)["params"]["name"] = name

            return self.get_by_id(id)["params"]["name"]
        else:
            return "ERROR"

    def get_comment(self, branch_id):
        if self.__branches.get(branch_id) is not None:
            return self.__branches[branch_id]["params"]["comment"]


class TreeModule:
    name = "TreeModule"

    def __init__(self, Tree_frame, file_manager, event_bus, tmp_save=True):
        self.__TreeView = Tree_frame.findChild(QTreeView, "treeView")
        self.__saving_comment = Tree_frame.findChild(QPlainTextEdit, "saving_comment")

        # Настройка модели
        self.model = QStandardItemModel()
        self.model.setColumnCount(2)
        self.__TreeView.setModel(self.model)

        # Настройка внешнего вида
        self.__TreeView.setHeaderHidden(True)
        self.__TreeView.setColumnWidth(1, 80)
        self.__TreeView.header().setStretchLastSection(False)
        self.__TreeView.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.__TreeView.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.__TreeView.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.__TreeView.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.__TreeView.verticalScrollBar().setSingleStep(50)
        self.__TreeView.verticalScrollBar().setPageStep(50)
        self.__TreeView.selectionModel().selectionChanged.connect(self.__on_selection_changed)
        self.model.itemChanged.connect(self.__on_item_changed)
        # Настройка взаимодействия
        self.__TreeView.setItemDelegate(TreeDelegate(self.__TreeView, self))
        self.__TreeView.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked |
            QAbstractItemView.EditTrigger.EditKeyPressed
        )

        # Подключение сигналов
        self.__saving_comment.textChanged.connect(self.__comment_text_changed)

        # Инициализация данных
        self.branch_items = {}  # {branch_id: branch_item}
        self.__store = DataStore()
        self.__file_manager = file_manager
        self.__event_bus = event_bus
        self.__tmp_save = tmp_save
        self.__active_branch_id = None
        self.__active_leaf_id = None
        self.show_block = False

    def Add_dataset(self, dataset):
        """ Массово добавляет данные. Структура dataset: [[params, data],[params, data],...].
            Главное отличие от обычного Add_branch - в начале всё добавляем,
            а потом уже вызываем все обновляющие прерывания """
        result = False
        self.show_block = True
        try:
            branch_index = None
            for params, data in dataset:
                branch_index = self.__Add_branch(params, data)
            if branch_index is not None:
                self.__TreeView.setCurrentIndex(branch_index)
                self.__on_item_clicked(branch_index)
                result = True

        except Exception as e:
            print("TreeModule::Add_dataset::ERROR::", e)

        self.show_block = False
        return result

    def Add_branch(self, params, data):
        """ Добавляет одну ветку. Принимает Json ветки и данные, которые надо добавить """
        self.show_block = True
        branch_index = self.__Add_branch(params, data)
        self.__TreeView.selectionModel().clearSelection()
        self.__TreeView.setCurrentIndex(branch_index)
        self.__on_item_clicked(branch_index)
        self.show_block = False

    def check_params(self, params):
        params = normalize_params(params, 'matrix')

        return params

    def __Add_branch(self, params, data):
        """ Добавляет одну ветку. Принимает Json ветки и данные, которые надо добавить """
        params = self.check_params(params)

        branch_id, leaf_ids, leaf_names = self.__store.add_data(params, data)
        branch_name = params.get("name") if params else "Без названия"
        if branch_id in self.branch_items:
            branch_item = self.branch_items[branch_id]
        else:
            # Создаем новую ветку
            branch_item = QStandardItem(branch_name)
            branch_item.setData(branch_id, Qt.ItemDataRole.UserRole)
            branch_item.setData(True, Qt.ItemDataRole.UserRole + 1)  # visible state
            branch_item.setEditable(True)
            self.model.appendRow([branch_item, QStandardItem()])
            self.branch_items[branch_id] = branch_item
        branch_index = self.model.indexFromItem(branch_item)
        self.__TreeView.setExpanded(branch_index, True)
        for leaf_name, leaf_id in zip(leaf_names, leaf_ids):
            item = QStandardItem(leaf_name)
            item.setData(leaf_id, Qt.ItemDataRole.UserRole)
            item.setData(True, Qt.ItemDataRole.UserRole + 1)  # visible state
            item.setEditable(True)
            branch_item.appendRow([item, QStandardItem()])
        return branch_index

    def on_save(self, id, name):
        """Вызывается при нажатии Save"""
        data = self.__store.data_by_id(id)
        self.__event_bus.emit(self.name, "All", "save_data", data)

    def on_visibility_toggle(self, id, new_state):
        """Вызывается при нажатии Visibility"""
        self.__store.set_visibility(id, new_state)

    def on_delete(self, id):
        """Вызывается при нажатии Delete"""
        if self.__store.delete_by_id(id) is True:
            if self._remove_by_id(id) is True:
                self.__saving_comment.setPlainText('')

    def _remove_by_id(self, id):
        """Удалить элемент дерева по id """
        if id > 0:
            for branch_item in self.branch_items.values():
                for row in range(branch_item.rowCount()):
                    item = branch_item.child(row, 0)
                    if item.data(Qt.ItemDataRole.UserRole) == id:
                        branch_item.removeRow(row)
                        return True
        elif id < 0:
            item = self.branch_items[id]
            index = self.model.indexFromItem(item)
            self.model.removeRow(index.row(), index.parent())
            del self.branch_items[id]
            return True

    @property
    def all_data(self):
        """ Возвращает все данные, что есть """
        if len(self.__store.data) == 0:
            return None
        return self.__store.data

    @property
    def vis_data(self):
        """ Возвращает все данные, что видны в дереве """
        if len(self.__store.vis_data) == 0:
            return None
        return self.__store.vis_data

    def show_data(self):
        """ Вызов функции запрашивает отправить родительскому event_bus данные для их отображения """
        self.__send_show_data()

    def get_selected_items(self):
        """Возвращает список выделенных id (и branch_id отрицательные, и leaf_id положительные)"""
        selected_ids = []

        indexes = self.__TreeView.selectionModel().selectedIndexes()
        for idx in indexes:
            if idx.column() == 0:  # берём только первую колонку
                item = self.model.itemFromIndex(idx)
                if item:
                    id_ = item.data(Qt.ItemDataRole.UserRole)
                    if id_ is not None:
                        selected_ids.append(id_)

        return selected_ids

    def __send_show_data(self, reason="general"):
        """ Отправляет сигнал получателю о необходимости показать данные """
        """ Структура отправляемых данных
            [[params, data], [params, data], ...]
            """

        if self.show_block is False:
            self.__store.set_selected_by_ids(self.get_selected_items())

            self.__event_bus.emit(self.name, "All", "show_data", [{'data': self.__store.data, 'reason': reason}])

    def __on_item_clicked(self, index):
        """ Обработчик клика по элементу """
        item = self.model.itemFromIndex(index.siblingAtColumn(0))
        if item is None:
            return
        if item.hasChildren():
            self.__active_branch_id = item.data(Qt.ItemDataRole.UserRole)
            comment_text = self.__store.get_comment(self.__active_branch_id)
            self.__saving_comment.setPlainText(comment_text)
        else:
            self.__active_leaf_id = item.data(Qt.ItemDataRole.UserRole)
        self.__send_show_data(reason="clicked")

    def __on_selection_changed(self, selected, deselected):
        """ Обработчик выделения по элементу """
        indexes = selected.indexes()
        if indexes:
            index = indexes[0]
            item = self.model.itemFromIndex(index.siblingAtColumn(0))
            if item is None:
                return

            if item.hasChildren():
                self.__active_branch_id = item.data(Qt.ItemDataRole.UserRole)
                comment_text = self.__store.get_comment(self.__active_branch_id)
                self.__saving_comment.setPlainText(comment_text)
            else:
                self.__active_leaf_id = item.data(Qt.ItemDataRole.UserRole)
        self.__send_show_data(reason="selection")

    def __on_item_changed(self, item):
        if item.data(Qt.ItemDataRole.UserRole) is None:
            return

        name = item.text()

        new_name = self.__store.set_name(id=item.data(Qt.ItemDataRole.UserRole), name=name)
        self.__send_show_data()

        self.model.itemChanged.disconnect(self.__on_item_changed)
        item.setText(new_name)
        self.model.itemChanged.connect(self.__on_item_changed)

    def __comment_text_changed(self):
        """ Реакция на изменение текста комментария """
        if self.__active_branch_id is None:
            return
        self.__store.set_comment(self.__active_branch_id, self.__saving_comment.toPlainText())
    
    def save_tmp(self):
        """ Сохраняет все данные в temp папку, чтобы избежать потери данных """
        if self.__tmp_save:
            data = self.__store.data
            for block in data:
                params = block[0]["params"]
                dataset = block[1]
                for i in range(len(dataset)):
                    data_block = dataset[:][i]
                    file_path = f'tmp/{params.get("metadata", {}).get("description", "")}/{params.get("metadata", {}).get("created", "")}'
                    os.makedirs(file_path, exist_ok=True)
                    file_name = file_path + "/" + params.get("name", '') + f"_{i:03d}"
                    self.__file_manager.set_data(data_block, params)
                    saved_path = self.__file_manager.save(file_name, "dat", delimiter='\t')
        self.__send_show_data()
