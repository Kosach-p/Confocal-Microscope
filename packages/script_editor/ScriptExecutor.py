import sys
import ast
import operator
import inspect
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QPlainTextEdit, QApplication, QSplitter)
from PyQt6.QtCore import Qt, QObject, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut, QFont



class ScriptExecutor(QObject):
    name = "ScriptExecutor"

    def __init__(self, modules, event_bus):
        super().__init__()
        self.__event_bus = event_bus
        self.Control = self.__event_bus.ScriptExecutorClass
        self.Control.connect(self.__event_process)

        self.__modules = modules
        self.__variables = {}
        self.__tree = []
        self.__node_ip_list = [0]
        self.__for_iterator = []
        self.__for_var_name = []
        self.__while_index = []
        self.__stop_flag = False

        self.__operators = {
            ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
            ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod,
            ast.Pow: operator.pow, ast.LShift: operator.lshift, ast.RShift: operator.rshift,
            ast.BitAnd: operator.and_, ast.BitOr: operator.or_, ast.BitXor: operator.xor,
        }

    def __event_process(self, transmitter, receiver, command, data):
        if receiver == self.name or receiver == "All":
            if command == "completed":
                try:
                    self.__stop_flag = False
                except Exception as e:
                    print(e)

    def execute_script(self, script_text):
        if self.__validate_script(script_text):
            self.__tree.append(ast.parse(script_text).body)
            self.__node_ip_list = [0]
        else:
            print("В коде есть ошибка или не обрабатываемый участок")
            return False
        while True:
            self.__stop_flag = True
            result = self.__execute_next_node()
            if result is True:
                return True
            else:
                return False

    def __validate_script(self, script_text):
        return True

    def __execute_next_node(self):
        while self.__node_ip_list[-1] >= len(self.__tree[-1]):
            self.__tree.pop()
            self.__node_ip_list.pop()
            if len(self.__node_ip_list) == 0:
                print("Скрипт выполнен")
                return True
        node = self.__tree[-1][self.__node_ip_list[-1]]
        method = 'execute_' + node.__class__.__name__
        executor = getattr(self, method, self.generic_visit)
        self.__node_ip_list[-1] += 1

        result = executor(node)
        if result is True:
            self.Control.emit(self.name, self.name, "completed", [])
        elif result is None:
            print(f"{node.__class__.__name__} не возвращает ничего")
            return False
        else:
            print(f"Ошибка выполнения {node.__class__.__name__}")
            return False

    def execute_Assign(self, node):
        try:
            namespace = {**self.__modules, **self.__variables}
            value = eval(ast.unparse(node.value), {"__builtins__": {}}, namespace)
            self.__variables[node.targets[0].id] = value
            return True
        except Exception as e:
            print(e)

    def execute_AugAssign(self, node):
        try:
            var_name = node.target.id
            current_value = self.__variables[var_name]
            namespace = {**self.__modules, **self.__variables}
            value = eval(ast.unparse(node.value), {"__builtins__": {}}, namespace)
            result = self.__apply_aug_assign(current_value, node.op, value)
            self.__variables[var_name] = result
            return True
        except Exception as e:
            print(e)

    def execute_Expr(self, node):
        try:
            if isinstance(node.value, ast.Call):
                self.execute_Call(node.value)
                return True
            return False
        except Exception as e:
            pass

    def execute_Call(self, node):
        try:
            if isinstance(node.func, ast.Attribute):
                namespace = {**self.__modules, **self.__variables}
                controller = node.func.value.id
                method = node.func.attr
                args = [eval(ast.unparse(arg), {"__builtins__": {}}, namespace) for arg in node.args]
                getattr(self.__modules[controller], method)(*args)
            return True
        except Exception as e:
            pass

    def execute_If(self, node):
        try:
            namespace = {**self.__modules, **self.__variables}
            condition = eval(ast.unparse(node.test), {"__builtins__": {}}, namespace)
            if condition:
                self.__tree.append(node.body)
                self.__node_ip_list.append(0)
            return True
        except Exception as e:
            print(e)

    def execute_While(self, node):
        try:
            namespace = {**self.__modules, **self.__variables}
            condition = eval(ast.unparse(node.test), {"__builtins__": {}}, namespace)
            if condition:
                if node.lineno not in self.__while_index:
                    self.__while_index.append(node.lineno)
                    looping_node_body = node.body + [node]
                    self.__tree.append(looping_node_body)
                    self.__node_ip_list.append(0)
                else:
                    self.__node_ip_list[-1] = 0
            else:
                if node.lineno in self.__while_index:
                    self.__while_index.pop()
            return True
        except Exception as e:
            print(e)

    def execute_For(self, node):
        try:
            first_time = node.target.id not in self.__for_var_name
            if first_time:
                iterable = eval(ast.unparse(node.iter), {"__builtins__": {}}, {**self.__modules, **self.__variables})
                self.__for_iterator.append(iter(iterable))
                self.__for_var_name.append(node.target.id)
            self.__variables[self.__for_var_name[-1]] = next(self.__for_iterator[-1])
            if first_time:
                looping_node_body = node.body + [node]
                self.__tree.append(looping_node_body)
                self.__node_ip_list.append(0)
            else:
                self.__node_ip_list[-1] = 0
            return True
        except StopIteration:
            self.__for_iterator.pop()
            self.__for_var_name.pop()
            return True
        except Exception as e:
            print(e)

    def execute_Break(self, node):
        try:
            self.__tree.pop()
            self.__node_ip_list.pop()
            return True
        except Exception as e:
            print(e)

    def execute_Continue(self, node):
        try:
            self.__tree[-1] = [self.__tree[-1][-1]]
            self.__node_ip_list[-1] = 0
            return True
        except Exception as e:
            print(e)

    def __apply_aug_assign(self, target, op, value):
        operator_type = type(op)
        if operator_type in self.__operators:
            return self.__operators[operator_type](target, value)
        raise TypeError(f"Неподдерживаемая операция: {operator_type}")

    def generic_visit(self, node):
        print(f"Нода ::{node.__class__.__name__}:: не добавлена в обработку")
        return True