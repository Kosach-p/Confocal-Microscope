from multiprocessing import Process, Queue
from PyQt6.QtCore import QTimer
import time
import queue as queue_module

DEVELOPER_MODE = False


def ppprint(*args):
    if DEVELOPER_MODE:
        print(f"[{time.strftime('%H:%M:%S')}]", *args)


def ProcessController(cmd_queue: Queue, output_q: Queue):
    """Рабочий процесс с гарантированным завершением"""
    import gc
    import os

    on = True
    while on:
        try:
            cmd = cmd_queue.get(timeout=0.1)
            if cmd["command"] == "do":
                try:
                    result = cmd["func"](*cmd["args"], **cmd.get("kwargs", {}))
                    output_q.put({"result": result, "error": None})
                    result = None
                    gc.collect()

                except Exception as e:
                    output_q.put({"result": None, "error": str(e)})

            elif cmd["command"] == "stop":
                ppprint(f"💀 Процесс {os.getpid()} принудительно завершается")

                # Очистка
                result = None
                gc.collect()

                # Жёсткое завершение без дальнейшей очистки
                os._exit(0)

        except queue_module.Empty:
            continue


def ProcessCollector(cmd_queue: Queue, output_q: Queue, max_process_num: int):
    hang_time = 2

    process_list = []
    to_worker_list = []
    from_worker_list = []
    start_time_list = []
    busy_list = []
    task_num_list = []

    parent_alive = True

    stats = {
        'tasks_created': 0,
        'tasks_completed': 0,
        'hanged_processes': 0,
        'last_health_check': time.time()
    }

    ppprint(f"🟢 ProcessCollector запущен с {max_process_num} процессами")
    ppprint(f"  ├─ hang_time: {hang_time}с")
    ppprint(f"  ├─ cmd_queue: {cmd_queue}")
    ppprint(f"  └─ output_q: {output_q}")

    # Инициализация процессов
    ppprint("🔧 Инициализация процессов...")
    for i in range(max_process_num):
        try:
            to_worker = Queue()
            from_worker = Queue()
            process = Process(target=ProcessController, args=(to_worker, from_worker), daemon=True)
            process.start()
            process_list.append(process)
            to_worker_list.append(to_worker)
            from_worker_list.append(from_worker)
            start_time_list.append(None)
            busy_list.append(False)
            task_num_list.append(None)
            ppprint(f"  ├─ Процесс {i} запущен [PID={process.pid}]")
        except Exception as e:
            ppprint(f"  ❌ Ошибка запуска процесса {i}: {e}")

    ppprint(f"✅ Инициализация завершена: {len(process_list)} процессов запущено")

    on = True
    iteration_count = 0

    while on:
        iteration_count += 1

        # Периодический вывод статуса каждые 1000 итераций
        if iteration_count % 10000 == 0:
            ppprint(
                f"🔄 Итерация {iteration_count}: busy={busy_list}, tasks_created={stats['tasks_created']}, tasks_completed={stats['tasks_completed']}")

        # Обработка входящих команд (без активного ожидания)
        cmd = None

        try:
            cmd = cmd_queue.get_nowait()
            if cmd is not None:
                ppprint(f"📥 Получена команда: {cmd.get('command', 'unknown')}" +
                        (f" [task_num={cmd.get('task_num')}]" if 'task_num' in cmd else ""))

        except queue_module.Empty:
            pass

        if cmd is not None:
            parent_alive = True
            if cmd["command"] == "create":
                func = cmd["func"]
                args = cmd["args"]
                task_num = cmd["task_num"]
                kwargs = cmd.get("kwargs", {})

                ppprint(f"🔍 Обработка create для задачи {task_num}:")
                ppprint(f"  ├─ func: {func.__name__ if hasattr(func, '__name__') else func}")
                ppprint(f"  ├─ args: {args}")
                ppprint(f"  └─ kwargs: {kwargs}")

                # Поиск свободного процесса
                assigned = False
                for i in range(len(process_list)):
                    # Проверка на зависшие процессы
                    if busy_list[i] and start_time_list[i] is not None:
                        elapsed = time.time() - start_time_list[i]
                        if elapsed > hang_time:
                            ppprint(
                                f"⚠️ Процесс {i} завис на задаче {task_num_list[i]} (прошло {elapsed:.2f}с), перезапуск...")
                            try:
                                process_list[i].terminate()
                                process_list[i].join(timeout=1)
                                ppprint(f"  ├─ Старый процесс {i} остановлен")
                            except Exception as e:
                                ppprint(f"  ├─ Ошибка остановки процесса {i}: {e}")

                            # Пересоздание процесса
                            new_to_worker = Queue()
                            new_from_worker = Queue()
                            new_process = Process(target=ProcessController,
                                                  args=(new_to_worker, new_from_worker),
                                                  daemon=True)
                            new_process.start()
                            ppprint(f"  ├─ Новый процесс {i} запущен [PID={new_process.pid}]")

                            # Очистка старых очередей
                            cleared_to = 0
                            cleared_from = 0
                            while not to_worker_list[i].empty():
                                try:
                                    to_worker_list[i].get_nowait()
                                    cleared_to += 1
                                except:
                                    break
                            while not from_worker_list[i].empty():
                                try:
                                    from_worker_list[i].get_nowait()
                                    cleared_from += 1
                                except:
                                    break
                            ppprint(f"  ├─ Очищено из очередей: to_worker={cleared_to}, from_worker={cleared_from}")

                            process_list[i] = new_process
                            to_worker_list[i] = new_to_worker
                            from_worker_list[i] = new_from_worker
                            busy_list[i] = False
                            start_time_list[i] = None
                            stats['hanged_processes'] += 1
                            ppprint(f"  └─ Процесс {i} перезапущен (всего зависших: {stats['hanged_processes']})")

                    # Назначение задачи свободному процессу
                    if not busy_list[i]:
                        try:
                            to_worker_list[i].put({
                                "command": "do",
                                "func": func,
                                "args": args,
                                "kwargs": kwargs
                            })
                            busy_list[i] = True
                            task_num_list[i] = task_num
                            start_time_list[i] = time.time()
                            stats['tasks_created'] += 1
                            assigned = True
                            ppprint(f"📤 Задача {task_num} → процесс {i} [создано задач: {stats['tasks_created']}]")
                            break
                        except Exception as e:
                            ppprint(f"❌ Ошибка отправки задачи {task_num} процессу {i}: {e}")

                if not assigned:
                    ppprint(f"⚠️ Нет свободных процессов для задачи {task_num}")
                    ppprint(f"  ├─ busy_list: {busy_list}")
                    ppprint(f"  └─ start_time_list: {start_time_list}")
                    try:
                        to_worker = Queue()
                        from_worker = Queue()
                        process = Process(target=ProcessController, args=(to_worker, from_worker), daemon=True)
                        process.start()
                        process_list.append(process)
                        to_worker_list.append(to_worker)
                        from_worker_list.append(from_worker)
                        start_time_list.append(None)
                        busy_list.append(False)
                        task_num_list.append(None)
                        ppprint(f"  ├─ Процесс {len(process_list) - 1} запущен [PID={process.pid}]")

                        try:
                            to_worker_list[len(process_list) - 1].put({
                                "command": "do",
                                "func": func,
                                "args": args,
                                "kwargs": kwargs
                            })
                            busy_list[len(process_list) - 1] = True
                            task_num_list[len(process_list) - 1] = task_num
                            start_time_list[len(process_list) - 1] = time.time()
                            stats['tasks_created'] += 1
                            ppprint(f"📤 Задача {task_num} → процесс {len(process_list) - 1} [создано задач: {stats['tasks_created']}]")

                        except Exception as e:
                            ppprint(f"❌ Ошибка отправки задачи {task_num} процессу {len(process_list) - 1}: {e}")

                    except Exception as e:
                        ppprint(f"  ❌ Ошибка запуска процесса {i}: {e}")

            elif cmd["command"] == "stop":
                ppprint("⏹ Получена команда остановки...")
                ppprint("  ├─ Отправка stop всем процессам...")
                for i in range(len(process_list)):
                    try:
                        to_worker_list[i].put({"command": "stop"})
                        ppprint(f"  │  ├─ Процесс {i}: stop отправлен")
                    except Exception as e:
                        ppprint(f"  │  ├─ Процесс {i}: ошибка отправки stop: {e}")
                ppprint("  └─ Все stop команды отправлены")
                on = False
                break

            elif cmd["command"] == "boot":
                ppprint("⏹ Получена команда для первой загрузки...")
                ppprint("  ├─ Отправка загрузки всем процессам...")
                for i in range(len(process_list)):
                    try:
                        to_worker_list[i].put({"command": "boot"})
                        ppprint(f"  │  ├─ Процесс {i}: загрузка запущена")
                    except Exception as e:
                        ppprint(f"  │  ├─ Процесс {i}: загрузка не запущена: {e}")
                ppprint("  └─ Все boot команды отправлены")
                on = True

        # Сбор результатов
        for i in range(len(process_list)):
            try:
                while True:
                    try:
                        result = from_worker_list[i].get_nowait()
                        ppprint(f"📨 Получен результат из процесса {i}:")
                        ppprint(f"  ├─ task_num: {task_num_list[i]}")
                        ppprint(f"  ├─ result: {result.get('result') if result else 'None'}")
                        ppprint(f"  └─ error: {result.get('error') if result else 'None'}")

                        if busy_list[i]:
                            output_q.put({
                                "task_num": task_num_list[i],
                                "result": result.get("result"),
                                "error": result.get("error")
                            })
                            busy_list[i] = False
                            start_time_list[i] = None
                            stats['tasks_completed'] += 1
                            ppprint(
                                f"✅ Задача {task_num_list[i]} завершена [процесс {i}] [всего завершено: {stats['tasks_completed']}]")

                            exec_time = (time.time() - start_time_list[i]) * 1000 if start_time_list[i] else 0
                            if exec_time > 100:
                                ppprint(f"⚠️ Задача {task_num_list[i]} выполнена за {exec_time:.0f}мс [Процесс {i}]")
                    except queue_module.Empty:
                        break
            except Exception as e:
                ppprint(f"❌ Ошибка при сборе из процесса {i}: {e}")

        i = 0
        while len(process_list) > max_process_num and i + 1 < len(process_list) - 1:
            i += 1
            if busy_list[i] is False:
                to_worker_list[i].put({"command": "stop"})
                del process_list[i]
                del to_worker_list[i]
                del from_worker_list[i]
                del start_time_list[i]
                del busy_list[i]
                del task_num_list[i]
                ppprint(f"  │  ├─ Процесс {i}: Закрыт, осталось {len(process_list)} процессов")


        current_time = time.time()
        if current_time - stats['last_health_check'] >= 10:
            if not parent_alive:
                ppprint("⏹ Получена команда остановки...")
                ppprint("  ├─ Отправка stop всем процессам...")
                for i in range(len(process_list)):
                    try:
                        to_worker_list[i].put({"command": "stop"})
                        ppprint(f"  │  ├─ Процесс {i}: stop отправлен")
                    except Exception as e:
                        ppprint(f"  │  ├─ Процесс {i}: ошибка отправки stop: {e}")
                ppprint("  └─ Все stop команды отправлены")
                on = False
                break
            else:
                parent_alive = False
            stats['last_health_check'] = current_time
            ppprint("🏥 Health check...")

            dead_processes = []
            for i, proc in enumerate(process_list):
                if not proc.is_alive():
                    dead_processes.append(i)
                    ppprint(f"  ├─ 💀 Процесс {i} мёртв!")

            if not dead_processes:
                ppprint(f"  └─ ✅ Все {len(process_list)} процессов живы")
            else:
                for i in dead_processes:
                    ppprint(f"🔄 Перезапуск мёртвого процесса {i}...")
                    try:
                        new_to_worker = Queue()
                        new_from_worker = Queue()
                        new_process = Process(target=ProcessController,
                                              args=(new_to_worker, new_from_worker),
                                              daemon=True)
                        new_process.start()
                        process_list[i] = new_process
                        to_worker_list[i] = new_to_worker
                        from_worker_list[i] = new_from_worker
                        busy_list[i] = False
                        start_time_list[i] = None
                        ppprint(f"  └─ Процесс {i} перезапущен [PID={new_process.pid}]")
                    except Exception as e:
                        ppprint(f"  └─ ❌ Ошибка перезапуска процесса {i}: {e}")

        # Легкий sleep для снижения нагрузки на CPU
        time.sleep(0.0001)

    # Завершение всех процессов
    ppprint("🔧 Завершение всех процессов...")
    for i, proc in enumerate(process_list):
        try:
            if proc.is_alive():
                ppprint(f"  ├─ Ожидание завершения процесса {i}...")
                proc.join(timeout=1)
                if proc.is_alive():
                    ppprint(f"  │  ├─ Процесс {i} не завершился, принудительная остановка...")
                    proc.terminate()
                    ppprint(f"  │  └─ Процесс {i} остановлен")
                else:
                    ppprint(f"  │  └─ Процесс {i} завершён")
            else:
                ppprint(f"  ├─ Процесс {i} уже завершён")
        except Exception as e:
            ppprint(f"  ├─ ❌ Ошибка завершения процесса {i}: {e}")

    ppprint(f"🔴 ProcessCollector завершён. Статистика:")
    ppprint(f"  ├─ tasks_created: {stats['tasks_created']}")
    ppprint(f"  ├─ tasks_completed: {stats['tasks_completed']}")
    ppprint(f"  ├─ hanged_processes: {stats['hanged_processes']}")
    ppprint(f"  ├─ last_health_check: {stats['last_health_check']}")
    ppprint(f"  └─ Всего итераций цикла: {iteration_count}")


class ProcessManager:
    def __init__(self, max_process_num=4):
        self.max_process_num = max_process_num
        self.to_worker = Queue()
        self.from_worker = Queue()
        self.worker_process = None

        self.start()

        self.Timer = QTimer()
        self.Timer.timeout.connect(self.check_callback)
        self.Timer.start(10)

        self.callbacks = {}
        self.task_counter = 0

        self.TIM = QTimer()
        self.TIM.timeout.connect(lambda: self.to_worker.put({"command": "pulse"}))
        self.TIM.start(1000)

    def start(self):
        self.worker_process = Process(
            target=ProcessCollector,
            args=(self.to_worker, self.from_worker, self.max_process_num),
        )
        self.worker_process.start()

    def stop(self):
        self.to_worker.put({"command": "stop"})
        self.worker_process.join(timeout=2)
        if self.worker_process.is_alive():
            self.worker_process.terminate()

    def run_process(self, func, args, callback, kwargs=None):
        self.callbacks[self.task_counter] = callback
        self.to_worker.put({
            "command": "create",
            "func": func,
            "args": args,
            "kwargs": kwargs or {},
            "task_num": self.task_counter
        })
        self.task_counter += 1

    def kill(self, obj=None, event=None):
        self.to_worker.put({"command": "stop"})

    def check_callback(self):
        while not self.from_worker.empty():
            cmd = self.from_worker.get()
            callback = self.callbacks.pop(cmd["task_num"], None)
            if callback:
                if cmd.get("error"):
                    callback({"error": cmd["error"], "result": cmd.get("result")})
                else:
                    callback(cmd["result"])