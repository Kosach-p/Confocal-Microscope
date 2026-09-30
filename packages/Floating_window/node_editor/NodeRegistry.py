class NodeRegistry:
    """ Словарь всех добавленных входных и выходных нод виджетов """
    __registry_input = {}
    __registry_output = {}
    __registry_type = {}
    __callbacks = []

    @classmethod
    def register_input(cls, func, name):
        """ Добавляем ссылку на функцию ноды в словарь входных """
        cls.__registry_input[name] = func

    @classmethod
    def get_input_func(cls, name):
        """ Возвращает функцию входной ноды по имени name """
        func = cls.__registry_input.get(name)
        return func

    @classmethod
    def get_all_input_name(cls):
        """ Возвращаем список всех name, которые были добавлены """
        return list(cls.__registry_input.keys())

    @classmethod
    def get_all_input_func(cls):
        """ Возвращаем dict всех func, которые были добавлены """
        return cls.__registry_input

    @classmethod
    def register_output(cls, func, name):
        """ Добавляем ссылку на функцию ноды в словарь выходных """
        cls.__registry_output[name] = func

    @classmethod
    def get_output_func(cls, name):
        """ Возвращает функцию выходной ноды по имени name """
        func = cls.__registry_output.get(name)
        return func

    @classmethod
    def get_all_output_name(cls):
        """ Возвращаем список всех name, которые были добавлены """
        return list(cls.__registry_output.keys())

    @classmethod
    def get_all_output_func(cls):
        """ Возвращаем список всех func, которые были добавлены """
        return cls.__registry_output

    @classmethod
    def register_type(cls, type, name):
        """ Добавляем ссылку на функцию ноды в словарь выходных """
        cls.__registry_type[name] = type

    @classmethod
    def get_type(cls, name):
        """ Возвращает функцию входной ноды по имени name """
        type = cls.__registry_type.get(name)
        return type

    @classmethod
    def send_signal(cls, name):
        for cb in cls.__callbacks:
            if callable(cb):
                cb(name)
            else:
                print(f"ERROR::NodeRegistry::send_signal:: Переданная переменная не вызываемая", cb)

    @classmethod
    def register_callback(cls, callback):
        cls.__callbacks.append(callback)

    @classmethod
    def unregister_callback(cls, callback):
        cls.__callbacks.remove(callback)
