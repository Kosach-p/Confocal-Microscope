import queue


def send_receive(cmd_queue: queue.PriorityQueue, interface_id, **kwargs) -> None:
    cmd_queue.put({
        'command': "send_receive",
        'id': interface_id,
        'params': kwargs
    })


class BaseModbusDevice:
    """Базовый класс для всех Modbus устройств"""

    def __init__(self, cmd_queue: queue.PriorityQueue):
        self.cmd_queue = cmd_queue
        self.interface_id = None
        self.state = False
        self.check_ECHO = True

    def simple_send(self, data, fmt, use_slave_id, use_CRC, receive_marker):
        """
            Отправляет просто данные, без добавления команды (command = None)
            Может добавить slave_id в начале (если установлен флаг)
            Может добавить CRC в начале (если установлен флаг)
        """
        try:
            send_receive(
                cmd_queue=self.cmd_queue,
                slave_id=self.slave_id,
                command=None,
                data=data,
                format=fmt,
                expected_send_size=[use_slave_id, True, use_CRC],
                expected_receive_size=[],
                send_alignment=["little"],
                send_sign=[False],
                receive_alignment=["little"],
                receive_sign=[False],
                receive_marker=receive_marker,
                receive_param_names=None
            )
            return True
        except Exception as e:
            print("ERROR::BaseModbusDevice::simple_send::", e)
            return False
