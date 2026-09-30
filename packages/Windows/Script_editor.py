import ast
from PyQt6.QtCore import QObject
import operator

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from PyQt6.Qsci import QsciScintilla, QsciLexerPython, QsciAPIs


class ScriptEditor(QsciScintilla):
    """Редактор скриптов с автодополнением"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_editor()
        self.setup_autocomplete()

    def setup_editor(self):
        """Настройка редактора"""
        # Устанавливаем лексер Python
        self.setFont(QFont("Consolas", 10))
        self.lexer = QsciLexerPython()
        self.lexer.setDefaultFont(QFont("Consolas", 10))

        # ЦВЕТА ДЛЯ ЛЕКСЕРА
        self.lexer.setDefaultPaper(QColor("#2E3440"))  # Фон
        self.lexer.setDefaultColor(QColor("#D8DEE9"))  # Текст
        # Настройка цветов для ВСЕХ стилей Python
        self.lexer.setColor(QColor("#FFFFFF"), QsciLexerPython.Default)  # 0 - Обычный текст (белый)
        self.lexer.setColor(QColor("#ffa500"), QsciLexerPython.Comment)  # 1 - Комментарии (оранжевый)
        self.lexer.setColor(QColor("#faeb36"), QsciLexerPython.Number)  # 2 - Числа (желтый)
        self.lexer.setColor(QColor("#79c314"), QsciLexerPython.DoubleQuotedString)  # 3 - Строки "" (зеленый)
        self.lexer.setColor(QColor("#79c314"), QsciLexerPython.SingleQuotedString)  # 4 - Строки '' (зеленый)
        self.lexer.setColor(QColor("#ffa500"), QsciLexerPython.Keyword)  # 5 - Ключевые слова (оранжевый)
        self.lexer.setColor(QColor("#79c314"), QsciLexerPython.TripleSingleQuotedString)  # 6 - Строки ''' (зеленый)
        self.lexer.setColor(QColor("#79c314"), QsciLexerPython.TripleDoubleQuotedString)  # 7 - Строки """ (зеленый)
        self.lexer.setColor(QColor("#FF7F50"), QsciLexerPython.ClassName)  # 8 - Классы (коралловый)
        self.lexer.setColor(QColor("#FF7F50"), QsciLexerPython.FunctionMethodName)  # 9 - Функции (коралловый)
        self.lexer.setColor(QColor("#FFFFFF"), QsciLexerPython.Operator)  # 10 - Операторы (красный)
        self.lexer.setColor(QColor("#FFFFFF"), QsciLexerPython.Identifier)  # 11 - Идентификаторы (белый)
        self.lexer.setColor(QColor("#ffa500"), QsciLexerPython.CommentBlock)  # 12 - Блочные комментарии (оранжевый)
        self.lexer.setColor(QColor("#ff4444"), QsciLexerPython.UnclosedString)  # 13 - Незакрытые строки (красный)
        self.lexer.setColor(QColor("#FFFFFF"), QsciLexerPython.HighlightedIdentifier)  # 14 - Выделенные идентификаторы (белый)
        self.lexer.setColor(QColor("#b19cd9"), QsciLexerPython.Decorator)  # 15 - Декораторы (фиолетовый)
        self.lexer.setColor(QColor("#79c314"), QsciLexerPython.DoubleQuotedFString)  # 16 - f-строки "" (зеленый)
        self.lexer.setColor(QColor("#79c314"), QsciLexerPython.SingleQuotedFString)  # 17 - f-строки '' (зеленый)
        self.lexer.setColor(QColor("#79c314"), QsciLexerPython.TripleSingleQuotedFString)  # 18 - f-строки ''' (зеленый)
        self.lexer.setColor(QColor("#79c314"), QsciLexerPython.TripleDoubleQuotedFString)  # 19 - f-строки """ (зеленый)

        self.setLexer(self.lexer)

        # Настройка внешнего вида
        self.setMarginLineNumbers(1, True)  # Номера строк
        self.setMarginWidth(1, "0000")
        self.setMarginsBackgroundColor(QColor("#3B4252"))  # Фон номеров строк
        self.setMarginsForegroundColor(QColor("#81A1C1"))  # Цвет номеров строк

        self.setIndentationsUseTabs(True)
        self.setIndentationWidth(4)
        self.setTabWidth(4)
        self.setAutoIndent(True)
        self.setBraceMatching(QsciScintilla.BraceMatch.SloppyBraceMatch)

        # Цвета редактора
        self.setCaretLineVisible(True)
        self.setCaretLineBackgroundColor(QColor("#383838"))  # Фон текущей строки
        self.setCaretForegroundColor(QColor("#FFFFFF"))  # Цвет курсора
        self.setMatchedBraceBackgroundColor(QColor("#575757"))
        self.setMatchedBraceForegroundColor(QColor("#FFFFFF"))

        # Настройка завершения кода
        self.setAutoCompletionSource(QsciScintilla.AutoCompletionSource.AcsAll)
        self.setAutoCompletionCaseSensitivity(False)
        self.setAutoCompletionReplaceWord(True)
        self.setAutoCompletionUseSingle(QsciScintilla.AutoCompletionUseSingle.AcusNever)
        self.setAutoCompletionThreshold(2)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def setup_autocomplete(self):
        """Настройка автодополнения"""
        # Создаем API для автодополнения
        apis = QsciAPIs(self.lexer)
        # Добавляем кастомные команды
        custom_commands = [
            # Galvo команды
            "galvo.G00(x, y)",
            "galvo.G01(x, y)",
            "galvo.F(F)",
            # Piezo команды
            "piezo.G01(x, y, z)",
            "piezo.F(F)",
            # Laser команды
            "laser.on()",
            "laser.off()",
            # GCode команды
            "gcode.start_current()",
            "gcode.load_file(file_path)",
            "gcode.set_F_in_gcode(F)",
            # Команды реализатора скрипта
            "delay(time_ms)"
        ]

        # Добавляем встроенные Python функции
        python_builtins = [
            # Встроенные функции
            "print()", "len()", "range()", "str()", "int()", "float()", "list()", "dict()",
            "tuple()", "set()", "bool()", "type()", "isinstance()", "enumerate()", "zip()",
            "map()", "filter()", "sorted()", "reversed()", "sum()", "min()", "max()",
            "abs()", "round()", "divmod()", "pow()", "bin()", "hex()", "oct()",
            "chr()", "ord()", "id()", "hash()", "callable()", "hasattr()", "getattr()",
            "setattr()", "delattr()", "isinstance()", "issubclass()", "super()",
            "globals()", "locals()", "vars()", "dir()", "eval()", "exec()", "compile()",
            "repr()", "ascii()", "format()", "breakpoint()",

            # Методы строк
            "str.lower()", "str.upper()", "str.strip()", "str.replace()", "str.split()",
            "str.join()", "str.find()", "str.startswith()", "str.endswith()",
            "str.format()", "str.isdigit()", "str.isalpha()",

            # Методы списков
            "list.append()", "list.extend()", "list.insert()", "list.remove()",
            "list.pop()", "list.clear()", "list.index()", "list.count()", "list.sort()",
            "list.reverse()", "list.copy()",

            # Методы словарей
            "dict.keys()", "dict.values()", "dict.items()", "dict.get()", "dict.update()",
            "dict.pop()", "dict.popitem()", "dict.clear()", "dict.copy()",

            # Ключевые слова и конструкции
            "for", "while", "if", "elif", "else", "def", "class", "import", "from",
            "try", "except", "finally", "with", "as", "return", "yield", "assert",
            "pass", "break", "continue", "del", "in", "is", "and", "or", "not",
            "True", "False", "None", "self"
        ]

        # Добавляем все команды в API
        for command in custom_commands + python_builtins:
            apis.add(command)

        # Загружаем API
        apis.prepare()

    def keyPressEvent(self, event):
        """Обработка нажатий клавиш"""
        # Автоматическое дополнение при нажатии Ctrl+Space
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_Space:
            self.autoCompleteFromAll()
            return

        super().keyPressEvent(event)


class ScriptExecutor(QObject):
    name = "ScriptExecutor"

    def __init__(self, modules, event_bus):
        super().__init__()
        self.__event_bus = event_bus
        self.Control = self.__event_bus.ScriptExecutorClass
        self.Control.connect(self.__event_process)

        self.__modules = modules  # реестр контроллеров
        self.__variables = {}  # реестр переменных
        self.__tree = []  # корень дерева
        self.__node_ip_list = [0]  # указатель инструкций

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
        """ Обработка сигналов """
        if receiver == self.name or receiver == "All":
            if command == "completed":
                try:
                    self.__stop_flag = False
                    # self.__execute_next_node()
                except Exception as e:
                    print(e)

    def execute_script(self, script_text):
        """ Подготовка строки к выполнению """
        if self.__validate_script(script_text):
            self.__tree.append(ast.parse(script_text).body)
            self.__node_ip_list = [0]

        else:
            return False

        while True:
            self.__stop_flag = True
            result = self.__execute_next_node()
            if result is True:
                return True
            while self.__stop_flag:
                pass

    def __validate_script(self, script_text):
        """ Проверка полученного скрипта на валидность """
        return True

    def __execute_next_node(self):
        """ Выполнение следующей по списку ноды """
        while self.__node_ip_list[-1] >= len(self.__tree[-1]):
            """ Если блок был выполнен до конца, удаляем его список и его индекс """
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
        """ Присваивание """
        try:
            namespace = {**self.__modules, **self.__variables}
            value = eval(ast.unparse(node.value), {"__builtins__": {}}, namespace)
            self.__variables[node.targets[0].id] = value
            return True

        except Exception as e:
            print(e)
            return e

    def execute_AugAssign(self, node):
        """ Присваивание с операцией """
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
            return e

    def execute_Expr(self, node):
        """ Обрабатываем выражения (вызовы функций) """
        try:
            self.counter_0 += 1
            if isinstance(node.value, ast.Call):
                self.execute_Call(node.value)
                self.counter_0 -= 1
                return True

            return True

        except Exception as e:
            pass  # print(e)
            return e

    def execute_Call(self, node):
        """ Вызов функции """
        try:
            if isinstance(node.func, ast.Attribute):
                namespace = {**self.__modules, **self.__variables}
                controller = node.func.value.id
                method = node.func.attr
                args = [eval(ast.unparse(arg), {"__builtins__": {}}, namespace) for arg in node.args]
                getattr(self.__modules[controller], method)(*args)
            return True

        except Exception as e:
            pass  # print(e)
            return e

    def execute_If(self, node):
        """ Ветвление по условию """
        try:
            namespace = {**self.__modules, **self.__variables}
            condition = eval(ast.unparse(node.test), {"__builtins__": {}}, namespace)
            if condition:
                self.__tree.append(node.body)
                self.__node_ip_list.append(0)

            return True

        except Exception as e:
            print(e)
            return e

    def execute_While(self, node):
        """ Цикл While """
        self.counter_2 += 1
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
            return e

    def execute_For(self, node):
        """ Цикл For """
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
            return e

    def execute_Break(self, node):
        try:
            self.__tree.pop()
            self.__node_ip_list.pop()
            return True

        except Exception as e:
            print(e)
            return e

    def execute_Continue(self, node):
        try:
            self.__tree[-1] = [self.__tree[-1][-1]]
            self.__node_ip_list[-1] = 0
            return True

        except Exception as e:
            print(e)
            return e

    def __apply_aug_assign(self, target, op, value):
        """ Применяет операцию, вроде target += value, где операция op = "+=" """
        operator_type = type(op)
        if operator_type in self.__operators:
            return self.__operators[operator_type](target, value)
        else:
            raise TypeError(f"Неподдерживаемая операция: {operator_type}")

    def generic_visit(self, node):
        """ Обработчик нод, не добавленных в работу """
        print(f"Нода ::{node.__class__.__name__}:: не добавлена в обработку")
        return True