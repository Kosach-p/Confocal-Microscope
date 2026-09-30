import queue as queue_module
import time
from multiprocessing import Process, Queue
import pprint

DEVELOPER_MODE = False


def ppprint(*args):
    if DEVELOPER_MODE:
        print(f"[{time.strftime('%H:%M:%S')}]", *args)


def CommunicationProcess(input_q: Queue, l_p_input_q: Queue, output_q: Queue):
    on = True
    interface_controller = None
    current_id = -1

    stats = {
        'commands': 0,
        'send_receive': 0,
        'total_time': 0
    }

    ppprint(f"🔵 CommunicationProcess [ID={current_id}] запущен")

    while on:
        cmd = None
        start_cycle = time.time()

        try:
            cmd = l_p_input_q.get_nowait()
            if DEVELOPER_MODE and stats['commands'] % 100 == 0:
                ppprint(f"⚡ HIGH-PRIORITY команда: {cmd.get('command')} [ID={current_id}]")
        except queue_module.Empty:
            try:
                cmd = input_q.get_nowait()
                if DEVELOPER_MODE and stats['commands'] % 100 == 0:
                    ppprint(f"📨 Обычная команда: {cmd.get('command')} [ID={current_id}]")
            except queue_module.Empty:
                time.sleep(0.0005)
                continue

        if cmd is not None:
            cmd_start = time.time()
            stats['commands'] += 1

            try:
                command = cmd.get("command")
                params = cmd.get("params")
                cmd_id = int(cmd.get("id", -1))

                if command == "stop":
                    ppprint(f"⏹ STOP получен [ID={current_id}]")
                    if interface_controller and hasattr(interface_controller, 'disconnect'):
                        try:
                            interface_controller.disconnect()
                        except:
                            pass
                    on = False
                    output_q.put({
                        'command': 'stop',
                        'id': current_id,
                        'params': True,
                        'queue': input_q.qsize() + l_p_input_q.qsize()
                    })
                    break

                elif command == "set_id":
                    current_id = params
                    ppprint(f"🏷 ID установлен: {current_id}")

                elif command == "connect":
                    settings = params.get('settings', {})
                    iface_class = params.get('interface')

                    if interface_controller and hasattr(interface_controller, 'is_connected'):
                        if interface_controller.is_connected():
                            interface_controller.disconnect()

                    if iface_class:
                        interface_controller = iface_class()
                        if hasattr(interface_controller, 'connect'):
                            interface_controller.connect(settings)
                            ppprint(f"🔗 Подключен [ID={current_id}]")
                    else:
                        ppprint(f"❌ Ошибка: не передан класс интерфейса [ID={current_id}]")

                elif command == "disconnect":
                    if interface_controller and hasattr(interface_controller, 'disconnect'):
                        interface_controller.disconnect()
                        output_q.put({
                            'command': 'disconnect',
                            'id': current_id,
                            'params': True,
                            'queue': input_q.qsize() + l_p_input_q.qsize()
                        })
                        ppprint(f"🔌 Отключен [ID={current_id}]")

                elif command == "get_info":
                    info = {}
                    if interface_controller and hasattr(interface_controller, 'get_info'):
                        info = interface_controller.get_info()
                    else:
                        info = {"error": "Интерфейс не создан или нет метода get_info"}

                    output_q.put({
                        'command': 'get_info',
                        'id': current_id,
                        'params': info,
                        'queue': input_q.qsize() + l_p_input_q.qsize()
                    })
                    ppprint(f"ℹ️ GET_INFO отправлен [ID={current_id}]")

                elif command == "send_receive":
                    stats['send_receive'] += 1
                    sr_start = time.time()

                    if interface_controller and hasattr(interface_controller, 'send_receive'):
                        try:
                            response = interface_controller.send_receive(**params)
                            elapsed = (time.time() - sr_start) * 1000
                            output_q.put({
                                'command': 'send_receive',
                                'cmd_name': cmd.get("params").get("cmd_name"),
                                'id': current_id,
                                'params': response,
                                'receive_param_names': cmd.get("receive_param_names"),
                                'queue': input_q.qsize() + l_p_input_q.qsize(),
                                'time': time.time(),
                                'execution_time_ms': elapsed
                            })

                            if elapsed > 10:
                                ppprint(f"⚠️ SEND_RECEIVE выполнен за {elapsed:.2f} мс [ID={current_id}]")
                            elif DEVELOPER_MODE and stats['send_receive'] % 50 == 0:
                                ppprint(f"✅ SEND_RECEIVE выполнен за {elapsed:.2f} мс [ID={current_id}]")

                        except Exception as e:
                            ppprint(f"❌ Ошибка в send_receive [ID={current_id}]: {e}")
                            output_q.put({
                                'command': 'send_receive',
                                'id': current_id,
                                'params': {"error": str(e)},
                                'queue': input_q.qsize() + l_p_input_q.qsize(),
                                'time': time.time()
                            })
                    else:
                        ppprint(f"❌ Интерфейс не создан для send_receive [ID={current_id}]")
                        output_q.put({
                            'command': 'send_receive',
                            'id': current_id,
                            'params': {"error": "Интерфейс не создан"},
                            'queue': input_q.qsize() + l_p_input_q.qsize(),
                            'time': time.time()
                        })

                else:
                    ppprint(f"⚠️ Неизвестная команда: {command} [ID={current_id}]")

                cmd_elapsed = (time.time() - cmd_start) * 1000
                if cmd_elapsed > 50:
                    ppprint(f"⚠️ Команда {command} обрабатывалась {cmd_elapsed:.2f} мс [ID={current_id}]")

            except Exception as e:
                ppprint(f"❌ Ошибка обработки команды {cmd.get('command')} [ID={current_id}]: {e}")
                if DEVELOPER_MODE:
                    import traceback
                    traceback.print_exc()

    ppprint(f"🔴 CommunicationProcess [ID={current_id}] завершён. Статистика: {stats}")


def CommunicationProcessCollector(input_q: Queue, l_p_input_q: Queue, output_q: Queue):
    parent_alive = True

    on = True
    process_dict = {}
    to_worker_dict = {}
    from_worker_dict = {}
    l_p_to_worker_dict = {}

    stats = {
        'commands_received': 0,
        'commands_forwarded': 0,
        'responses_collected': 0,
        'processes_created': 0,
        'processes_closed': 0,
        'last_health_check': time.time()
    }

    ppprint("🟢 CommunicationProcessCollector запущен")

    while on:
        cmd = None
        cycle_start = time.time()

        try:
            cmd = input_q.get_nowait()
        except queue_module.Empty:
            try:
                cmd = l_p_input_q.get_nowait()
            except queue_module.Empty:
                pass

        if cmd is not None:
            parent_alive = True
            stats['commands_received'] += 1

            try:
                command = cmd.get("command")
                cmd_id = int(cmd.get("id", -1))

                if command == "open":
                    id = cmd_id

                    if id not in process_dict:
                        to_worker = Queue()
                        l_p_to_worker = Queue()
                        from_worker = Queue()

                        process = Process(
                            target=CommunicationProcess,
                            args=(to_worker, l_p_to_worker, from_worker),
                            daemon=True
                        )
                        process.start()

                        process_dict[id] = process
                        to_worker_dict[id] = to_worker
                        l_p_to_worker_dict[id] = l_p_to_worker
                        from_worker_dict[id] = from_worker
                        stats['processes_created'] += 1

                        to_worker.put({'command': 'set_id', 'id': id, 'params': id})

                        output_q.put({
                            'command': 'open',
                            'id': id,
                            'params': True,
                            'queue': input_q.qsize() + l_p_input_q.qsize()
                        })

                        ppprint(f"✅ Процесс создан: ID={id}, PID={process.pid}")
                    else:
                        output_q.put({
                            'command': 'open',
                            'id': id,
                            'params': False,
                            'queue': input_q.qsize() + l_p_input_q.qsize()
                        })
                        ppprint(f"⚠️ Процесс с ID={id} уже существует")

                elif command == "close":
                    id = cmd_id

                    if id in process_dict:
                        to_worker_dict[id].put({'command': 'stop', 'id': id, 'params': True})
                        ppprint(f"⏹ Отправлен STOP процессу ID={id}")
                    else:
                        output_q.put({
                            'command': 'close',
                            'id': id,
                            'params': False,
                            'queue': input_q.qsize() + l_p_input_q.qsize()
                        })
                        ppprint(f"⚠️ Процесс с ID={id} не найден")

                elif command == "stop":
                    ppprint("⏹ Остановка всех процессов...")
                    for wid, queue in to_worker_dict.items():
                        try:
                            queue.put({"command": "stop"})
                        except:
                            pass

                    on = False
                    output_q.put({
                        'command': 'stop',
                        'id': -1,
                        'params': True,
                        'queue': input_q.qsize() + l_p_input_q.qsize()
                    })
                    ppprint("🟢 Collector завершён")
                    break

                elif command == "get_info":
                    for wid, queue in to_worker_dict.items():
                        queue.put({"command": "get_info", 'id': wid, 'params': None})

                    output_q.put({
                        'command': 'get_info',
                        'id': -1,
                        'params': True,
                        'queue': input_q.qsize() + l_p_input_q.qsize()
                    })
                    ppprint(f"ℹ️ GET_INFO отправлен всем {len(to_worker_dict)} процессам")

                else:
                    if cmd_id in process_dict:
                        target_queue = None
                        if command == "send_receive":
                            target_queue = l_p_to_worker_dict.get(cmd_id)
                        else:
                            target_queue = to_worker_dict.get(cmd_id)
                        if target_queue:
                            target_queue.put(cmd)
                            stats['commands_forwarded'] += 1
                        else:
                            ppprint(f"❌ Очередь не найдена для ID={cmd_id}")
                    else:
                        ppprint(f"❌ Процесс с ID={cmd_id} не найден")

            except Exception as e:
                ppprint(f"❌ Ошибка в Collector при обработке команды: {e}")
                if DEVELOPER_MODE:
                    import traceback
                    traceback.print_exc()

        for wid, from_worker in list(from_worker_dict.items()):
            try:
                while True:
                    try:
                        result = from_worker.get_nowait()
                        stats['responses_collected'] += 1

                        if result.get('command') == 'send_receive':
                            exec_time = result.get('execution_time_ms', 0)
                            if exec_time > 10:
                                ppprint(f"📦 SEND_RECEIVE ответ [ID={wid}]: {exec_time:.2f} мс")

                        if result.get('command') == 'stop':
                            res_id = result.get('id')
                            if res_id in process_dict:
                                del process_dict[res_id]
                                del from_worker_dict[res_id]
                                del to_worker_dict[res_id]
                                if res_id in l_p_to_worker_dict:
                                    del l_p_to_worker_dict[res_id]
                                stats['processes_closed'] += 1
                                ppprint(f"🗑️ Процесс ID={res_id} удалён")

                        output_q.put(result)

                    except queue_module.Empty:
                        break

            except Exception as e:
                ppprint(f"❌ Ошибка при сборе ответов от ID={wid}: {e}")

        current_time = time.time()
        if current_time - stats['last_health_check'] >= 5 and process_dict:
            if not parent_alive:
                ppprint("⏹ Остановка всех процессов...")
                for wid, queue in to_worker_dict.items():
                    try:
                        queue.put({"command": "stop"})
                    except:
                        pass

                on = False
                output_q.put({
                    'command': 'stop',
                    'id': -1,
                    'params': True,
                    'queue': input_q.qsize() + l_p_input_q.qsize()
                })
                ppprint("🟢 Collector завершён")
                break
            else:
                parent_alive = False

            stats['last_health_check'] = current_time
            dead_processes = []
            for wid, proc in process_dict.items():
                if not proc.is_alive():
                    dead_processes.append(wid)

            for wid in dead_processes:
                ppprint(f"⚠️ Процесс ID={wid} мёртв! Удаляем...")
                if wid in process_dict:
                    del process_dict[wid]
                if wid in from_worker_dict:
                    del from_worker_dict[wid]
                if wid in to_worker_dict:
                    del to_worker_dict[wid]
                if wid in l_p_to_worker_dict:
                    del l_p_to_worker_dict[wid]

        if stats['commands_received'] > 0 and stats['commands_received'] % 1000 == 0:
            ppprint(f"📊 Статистика Collector: "
                    f"команд={stats['commands_received']}, "
                    f"отправлено={stats['commands_forwarded']}, "
                    f"ответов={stats['responses_collected']}, "
                    f"процессов={len(process_dict)}")

        time.sleep(0.0001)

    ppprint(f"🔴 Collector завершён. Итоговая статистика: {stats}")