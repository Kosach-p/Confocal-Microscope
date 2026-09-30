from qtpy.QtGui import QColor
from qtpy.QtWidgets import QLabel
from nodeeditor.node_node import Node
from nodeeditor.node_content_widget import QDMNodeContentWidget
from nodeeditor.node_graphics_node import QDMGraphicsNode
from nodeeditor.node_socket import *
from nodeeditor.utils import dumpException
from PyQt6.QtCore import QTimer, QPointF
from qtpy.QtCore import Qt
from packages.Floating_window.node_editor.calc_conf import NODE_COLORS
import numpy as np

def values_equal(a, b):
    """Рекурсивно сравнивает любые структуры данных"""

    # Если оба numpy массива
    if isinstance(a, np.ndarray) and isinstance(b, np.ndarray):
        return np.array_equal(a, b)

    # Если один numpy массив
    if isinstance(a, np.ndarray) or isinstance(b, np.ndarray):
        return False

    # Если оба списка или кортежа
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        if len(a) != len(b):
            return False
        return all(values_equal(x, y) for x, y in zip(a, b))

    # Если оба словаря
    if isinstance(a, dict) and isinstance(b, dict):
        if set(a.keys()) != set(b.keys()):
            return False
        return all(values_equal(a[k], b[k]) for k in a.keys())

    # Для всего остального
    return a == b


class CalcGraphicsNode(QDMGraphicsNode):
    def initSizes(self):
        super().initSizes()
        self.width = 240
        self.height = 145
        self.edge_roundness = 6
        self.edge_padding = 0
        self.title_horizontal_padding = 20
        self.title_vertical_padding = 20
        self._bg_color = QColor(240, 240, 240)
        self._text_color = QColor(240, 240, 240)

    def paint(self, painter, QStyleOptionGraphicsItem, widget=None):
        super().paint(painter, QStyleOptionGraphicsItem, widget)

        painter.setBrush(self._bg_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.boundingRect(), 5, 5)  # Со скруглением

        self.title_item.setDefaultTextColor(self._text_color)

        painter.setBrush(QColor("#7FFF00"))
        if self.node.isDirty(): painter.setBrush(QColor("#FF8C00"))
        if self.node.isInvalid(): painter.setBrush(QColor("#FF0000"))

        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(self.width - 10, 10), 5, 5)


class CalcContent(QDMNodeContentWidget):
    def initUI(self):
        lbl = QLabel(self.node.content_label, self)
        lbl.setObjectName(self.node.content_label_objname)


class CalcNode(Node):
    icon = ""
    op_code = 0
    op_title = "Undefined"
    content_label = ""
    content_label_objname = "calc_node_bg"

    NodeContent_class = CalcContent
    GraphicsNode_class = CalcGraphicsNode

    def __init__(self, scene, MP=None):
        super().__init__(scene, self.__class__.op_title, self.inputs, self.outputs)

        self.value = None
        self.__inputs_num = len(self.inputs)
        self.__outputs_num = len(self.outputs)
        self._calculated = False
        self._Modified = True
        self.last_inputs_val = []

        Colors = NODE_COLORS[self.op_code // 10]

        self.grNode._bg_color = QColor(Colors['bg'])
        self.grNode._text_color = QColor(Colors['text'])

        try:
            self.content.valueSet.connect(self._on_param_changed)
            self.content.funcChanged.connect(self._on_func_changed)
        except Exception as e:
            pass
        self.MP = MP

    def markModified(self, state=True):
        self._Modified = state

    def isModified(self):
        return self._Modified

    def markCalculated(self, state=True):
        self._calculated = state

    def isCalculated(self):
        return self._calculated

    def _on_param_changed(self):
        self.markDirty()
        self.markModified(True)
        self.eval()

    def _on_func_changed(self, index):
        """Обработчик смены функции — обновляет сокеты"""
        print("Ага")
        self.markModified(True)
        inputs, outputs = self.content.get_sockets()

        for i in self.inputs:
            i.changeSocketType(inputs)

        for o in self.outputs:
            o.changeSocketType(outputs)

        self._on_param_changed()

    def initSettings(self):
        super().initSettings()
        self.input_socket_position = LEFT_BOTTOM
        self.output_socket_position = RIGHT_TOP

    def evalOperation(self, input_values):
        """
        Вычисляет значение ноды по входным параметрам.

        Переопределяется в дочерних классах.
        В конце вычисления обязательно должен вызываться self.evalOperation_cplt(val),
        где val — результат вычислений.
        """
        self.markModified(False)
        self.markCalculated(True)

    def eval(self):
        """
        Вычисление значения ноды (ленивое, с отложенным досчётом зависимостей).

        Логика:
        ────────────────────────────────────────────────────────────
        1. Нода чистая и валидная → сразу отдаём кэшированное значение.
        2. Нода грязная:
           а) Проходим по всем входам.
           б) Если вход уже валиден — забираем его значение.
           в) Если вход невалиден — планируем его пересчёт через QTimer
              и выходим с None. Когда вход досчитается, он дёрнет
              onInputChanged, и eval запустится снова.
           г) Когда все входы собраны — выполняем evalOperation,
              помечаем ноду чистой и валидной, рассылаем сигнал
              потомкам (через markDescendantsDirty + evalChildren).
        ────────────────────────────────────────────────────────────
        Возвращает:
            значение ноды, если готово
            None, если требуется асинхронный досчёт зависимостей
        """
        if not self.isDirty() and not self.isInvalid() and not self.value is None: # Если чистое и не инвалидное, отправляем сообщение на выход
            #print(" _> returning cached %s value:" % self.__class__.__name__, self.value)
            return self.value
        #print(self.__class__.__name__, self.id, "1")
        if self.isDirty():
            #print(self.__class__.__name__, self.id, "2")
            if self.__inputs_num > 0:
                inputs_val = list()
                #print(self.__class__.__name__, self.id, "3")
                for i in range(self.__inputs_num):
                    socket = self.getInput(i)
                    if socket is not None:
                        #print(self.__class__.__name__, self.id, "4")
                        socket_val = socket.eval()

                        if socket_val is None:
                            #print(self.__class__.__name__, self.id, "5")
                            QTimer.singleShot(0, socket.onInputChanged)
                        else:
                            #print(self.__class__.__name__, self.id, "6")
                            inputs_val.append(socket_val)
                    else:
                        #print(self.__class__.__name__, self.id, "7")
                        self.grNode.setToolTip("Подключите все входы")
                        return None
                try:
                    if not values_equal(self.last_inputs_val, inputs_val) or self.isModified():
                        self.last_inputs_val = inputs_val
                        self.evalOperation(inputs_val)
                    else:
                        if not self.isCalculated():
                            self.markDirty(False)
                            self.markInvalid(False)
                        else:
                            pass
                except ValueError as e:
                    #print(self.__class__.__name__, self.id, "9"))
                    print(e)
                    self.markInvalid()
                    self.grNode.setToolTip(str(e))
                    self.markDescendantsDirty()
                except Exception as e:
                    #print(self.__class__.__name__, self.id, "10")
                    print(e)
                    self.markInvalid()
                    self.grNode.setToolTip(str(e))
                    dumpException(e)
            else:
                #print(self.__class__.__name__, self.id, "11")
                self.evalOperation(None)
            return False

    def onInputChanged(self, socket=None):
        """
        Сигнал: один из входных сокетов обновил своё значение.

        Помечает ноду как грязную и запускает её пересчёт.
        Когда пересчёт завершится, нода сама уведомит своих потомков
        (через markDescendantsDirty и evalChildren внутри evalOperation_cplt).
        """
        print("%s::__onInputChanged" % self.__class__.__name__)
        self.markDirty()
        self.eval()
        self.grNode.update()

    def onStateChanged(self):
        """
        Сигнал: один из параметров ноды изменился

        Помечает ноду как грязную и запускает её пересчёт.
        Когда пересчёт завершится, нода сама уведомит своих потомков
        (через markDescendantsDirty и evalChildren внутри evalOperation_cplt).
        """
        #print("%s::__onStateChanged" % self.__class__.__name__)
        self.markDirty()
        self.eval()
        self.grNode.update()

    def evalOperation_cplt(self, val):
        """
        Колбэк завершения evalOperation.

        Сохраняет вычисленное значение, помечает ноду чистой и валидной,
        затем уведомляет всех потомков о необходимости пересчёта:
        помечает их грязными и запускает eval для тех, у кого все входы готовы.
        """
        self.markCalculated(False)

        if isinstance(val, dict):
            if val.get("error", True):
                self.markDirty(True)
                self.markInvalid(True)
                self.grNode.setToolTip(val.get("result", val.get("error")))
            else:
                self.value = val.get("result")

                self.markDirty(False)
                self.markInvalid(False)
                self.grNode.setToolTip("")

                self.markDescendantsDirty()
                self.evalChildren()
        else:
            self.value = val
            if val is None:
                self.markDirty(True)
                self.markInvalid(True)
                self.grNode.setToolTip("Ошибка ноды")
            else:
                self.markDirty(False)
                self.markInvalid(False)
                self.grNode.setToolTip("")

                self.markDescendantsDirty()
                self.evalChildren()
        #print(self.__class__.__name__, "Посчитали ноду, получили", self.value is not None)
        self.grNode.update()

    def serialize(self):
        res = super().serialize()
        res['op_code'] = self.__class__.op_code
        return res

    def deserialize(self, data, hashmap={}, restore_id=True):
        res = super().deserialize(data, hashmap, restore_id)
        #print("Deserialized CalcNode '%s'" % self.__class__.__name__, "res:", res)
        return res