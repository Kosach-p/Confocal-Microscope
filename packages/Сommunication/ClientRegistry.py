class ClientRegistry:
    """ Словарь всех добавленных контроллеров """
    __registry = {}

    @classmethod
    def register(cls, controller):
        """ Добавляем ссылку на Клиент в общий словарь """
        cls.__registry[controller.group] = controller

    @classmethod
    def get(cls, name):
        """ Возвращаем ссылку на клиент с name """
        controller = cls.__registry.get(name)
        return controller

    @classmethod
    def get_by_id(cls, id):
        """ Возвращаем ссылку на клиент с name """
        _, controller_list = cls.get_all()
        for controller in controller_list:
            print(controller.client.device_id, id)
            if controller.client.device_id == id:
                return controller

    @classmethod
    def get_all(cls):
        """ Возвращаем список всех name, которые были добавлены """
        name_list = list()
        controller_list = list()
        for name, controller in cls.__registry.items():
            name_list.append(name)
            controller_list.append(controller)

        return name_list, controller_list