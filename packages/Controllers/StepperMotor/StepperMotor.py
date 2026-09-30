from packages.Controllers.ParentController import ParentController
from packages.Controllers.ParentController import ControllerSettings



from PyQt6.QtCore import QTimer

import numpy as np


class StepperMotorSettings(ControllerSettings):
    # Класс для хранения и управления настройками шаговым мотором

    def _post_init(self):
        self._parameters = {'ID': 103, 'steps_in_nm': 8000.0, 'MAX_speed': 2.0, 'MIN_speed': 0.01, 'accel_per_sec': 2.0,
                        'I_HOLD': 12, 'I_RUN': 16, 'I_HOLD_DELAY': 16, 'threshold': 255, 'current_wave_length': 800.0}
        self._load_settings()

    def get_current_settings(self):
        """ Возвращает все настроки, касающиеся контроля тока драйвера """
        return [self.I_HOLD, self.I_RUN, self.I_HOLD_DELAY]

    def get_StallGuard_settings(self):
        """ Возвращает все настроки, касающиеся контроля ограничения по току """
        return self.threshold

    def get_acceleration_settings(self):
        """ Возвращает все настроки, касающиеся контроля ускорения (с переводом в шаги из нанометров) """
        MAX_speed = int(self.MAX_speed * self.steps_in_nm)
        MIN_speed = int(self.MIN_speed * self.steps_in_nm)
        accel_per_sec = int(self.accel_per_sec * self.steps_in_nm)
        return [MAX_speed, MIN_speed, accel_per_sec]

    def braking_distance(self):
        """ Возвращает тормозной пусть шагового мотора, с учётом настроек макс скорости и ускорения """
        return int((self.MAX_speed / self.accel_per_sec) * self.steps_in_nm)


class StepperMotorControlClass(ParentController):
    """ Основной класс для управления шаговым мотором """
    name = "StepperMotorControlClass"
    device_name = 'StepperMotor'
    group = 'spectral_tuners'

    def __init__(self, parent=None):
        self.settings = StepperMotorSettings(self.name)
        super().__init__(parent.event_bus, parent.event_bus.StepperMotorControl, self.settings, self.device_name)
        self.emit_settings()

        # Переменные для управления шаговым мотором
        self.__target_wave_length = self.settings.current_wave_length
        self.__remaining_shift_step = 0
        self.deferred_go_to = 0
        self.deferred_shift = 0
        self.__stepper_motor_running = False
        self.__shift_step = 0
        self.__shift = 0

        # Инициализация класса
        self.__widget_init()
        self.__TIM_Init()

        # Флаги готовности
        self.settings_updated = False

    def event_process(self, transmitter, receiver, command, data):
        """ Обработка emit на линии event_bus """
        if transmitter == self.name:
            return

        if receiver == self.name or receiver == "All":
            if transmitter == "SpectrometerStepperMotorUI":
                if command == "waveLength_changed":
                    self.set_cord(data[0])
                if command == "go_to":
                    self.go_to(data[0])
                if command == "shift":

                    self.shift(data[0])
                if command == "smooth_stop":
                    self.smooth_stop()
                if command == "hold_StepperMotor":
                    self.hold_StepperMotor(data[0])
                if command == "get_current_wave_length":
                    self.event_bus.StepperMotorControl.emit(self.name, "All", "current_wave_length",
                                                              [self.settings.current_wave_length])
            elif transmitter == "DialUpService":
                self.event_bus.StatusBar.emit("Настройки шагового мотора обновлены ✅", True, "success")
                self.settings_updated = True

            else:
                if command == "update_settings":
                    self.update_settings(data[0])

                elif command == "get_settings":
                    self.emit_settings()

    def __TIM_Init(self):
        """ Инициализация таймер """
        self.TIM_STEPPER = QTimer()
        self.TIM_STEPPER.timeout.connect(lambda: self.__TIM_Interruption("TIM_STEPPER"))

    def __TIM_Interruption(self, TIMx):
        """ Обработка прерываний по таймеру """
        if TIMx == "TIM_STEPPER":
            self.client.get_stepper_status(receive_marker=self.name)

    def __widget_init(self):
        """ Инициализация виджетов в окне настроек """
        lines_edit_value = self.settings.load_settings()

        self.event_bus.StepperMotorControl.emit(self.name, "All", "current_wave_length", [self.settings.current_wave_length])

    def __update_client_settings(self):
        self.settings_updated = False
        client_method = [
            self.client.stepper_motor_current_settings,
            self.client.stepper_motor_StallGuard_settings,
            self.client.stepper_motor_acceleration_settings
        ]

        commands = ['stepper_motor_current_settings', 'stepper_motor_StallGuard_settings', 'stepper_motor_acceleration_settings']

        I_HOLD, I_RUN, I_HOLD_DELAY = self.settings.get_current_settings()
        threshold = self.settings.get_StallGuard_settings()
        MAX_speed, MIN_speed, accel = self.settings.get_acceleration_settings()

        data = [
            {"I_HOLD": I_HOLD, "I_RUN": I_RUN, "I_HOLD_DELAY": I_HOLD_DELAY},
            {"threshold": threshold},
            {"MAX_speed": MAX_speed, "MIN_speed": MIN_speed, "accel": accel}
        ]

        self.event_bus.DialUp.emit(
            self.name,
            "DialUpService",
            "DualUp",
            [self.client.device_id, client_method, commands, data, True]
        )

    def __shift_in_step(self, shift):
        """ Смещение координаты длинны волны на shift шагов шагового мотора """
        self.shift(shift / self.settings.steps_in_nm)

    # Публичные методы, для работы с координатами
    @property
    def is_ready(self):
        """ Возвращает состояние готовности к работе """
        return self.settings_updated * self.client.state

    def set_cord(self, wave_length: float, receive_marker=None):
        """ Установка координаты """
        self.settings.current_wave_length = wave_length
        self.__target_wave_length = self.settings.current_wave_length

    def get_cord(self):
        """ Возвращает текущие координаты """
        return self.settings.current_wave_length

    def set_speed_nm(self, speed):
        """ Устанавливает скорость вращения шпинделя в нм/сек """
        _, MIN_speed, accel_per_sec = self.settings.get_acceleration_settings()
        speed = int(speed * self.settings.steps_in_nm)
        self.client.stepper_motor_acceleration_settings(MAX_speed=speed, MIN_speed=MIN_speed, accel=accel_per_sec,
                                                          receive_marker=self.name)

    def set_normal_speed(self):
        """ Устанавливает скорость вращения шпинделя в нм/сек из настроек """
        self.__update_client_settings()

    def get_speed(self):
        """ Возвращает скорость вращения шпинделя из настроек """
        return self.settings.MAX_speed

    def go_to(self, wave_length: float):
        """ Перемещение на координату """
        if self.__stepper_motor_running:
            self.smooth_stop()
            self.deferred_go_to = wave_length
        else:
            shift_nm = wave_length - self.settings.current_wave_length
            self.shift(shift_nm)
            return shift_nm

    def shift(self, shift: float):
        """ Смещение координаты длинны волны на shift """
        # Если запрошенное направление движения противоположно текущему движению, то осуществляем плавное торможение
        if np.sign(self.__remaining_shift_step * shift) < 0:
            self.smooth_stop()
            self.deferred_shift = shift
            return

        self.__shift = shift
        self.__shift_step = int(shift * self.settings.steps_in_nm)

        self.TIM_STEPPER.start(150)

        self.client.stepper_motor_go(travel=self.__shift_step, receive_marker=self.name)

        self.__stepper_motor_running = True
        self.event_bus.StepperMotorControl.emit(self.name, "All", "current_wave_length", [self.settings.current_wave_length])

    def smooth_stop(self):
        """ Плавная остановка шагового мотора """
        self.deferred_go_to = 0
        self.deferred_shift = 0
        braking_distance = self.settings.braking_distance()
        if abs(self.__remaining_shift_step) > braking_distance:
            self.__shift_in_step(int(braking_distance * np.sign(self.__remaining_shift_step)))

    def hold_StepperMotor(self, state):
        """ Блокирует или разблокирует удержание мотороа (HOLD_Reset = True->Удержания нет, поэтому делаем инверсию) """
        self.client.stepper_motor_hold(HOLD_Reset=not state, receive_marker=self.name)

    def update_settings(self, dict):
        self.__update_client_settings()
        self.emit_settings()

    def emit_settings(self):
        self.event_bus_controller.emit(self.name, "All", "set_settings", [self.settings.load_settings_dict()])

    def Process_ModBus_Packet(self, cmd_name, data) -> bool:
        """ Обработка пакетов данных, адресованных данному пользователю """
        if cmd_name == 'get_stepper_status' or cmd_name == 'stepper_motor_go':
            self.__process_movement_packet(cmd_name, data)
        return True

    def __process_movement_packet(self, command, data):
        """ Обработка прихода данных о пройденных шагах шаговым мотором """
        """ оставшееся число шагов|направление|первый концевик|второй концевик|защита по току """
        if command == 'get_stepper_status':
            status, num_steps, direction, end_cap1, end_cap2, sg1_event = data.values()
        elif command == 'stepper_motor_go':
            direction, num_steps = data.values()
        else:
            return

        self.__remaining_shift_step = num_steps * (1 - 2 * direction)
        remaining_shift_nm = self.__remaining_shift_step / self.settings.steps_in_nm

        if command == 'get_stepper_status':
            if self.__remaining_shift_step == 0:
                if self.__stepper_motor_running:
                    self.__stepper_motor_running = False
                    self.settings.current_wave_length = round(self.__target_wave_length, 2)

                    if self.deferred_go_to != 0:
                        self.go_to(self.deferred_go_to)
                        self.deferred_go_to = 0
                    elif self.deferred_shift != 0:
                        self.shift(self.deferred_shift)
                        self.deferred_shift = 0
                    else:
                        self.event_bus.StepperMotorControl.emit(self.name, "All", "movement_completed",
                                                                  [self.settings.current_wave_length])
                        self.TIM_STEPPER.stop()
            else:
                self.__stepper_motor_running = True
                self.settings.current_wave_length = round(self.__target_wave_length - remaining_shift_nm, 2)
                self.event_bus.StepperMotorControl.emit(self.name, "All", "current_wave_length",
                                                          [self.settings.current_wave_length])
        # Команда 0x06 - ответ на запрос перемещения
        elif command == 'stepper_motor_go':
            self.settings.current_wave_length = round(self.__target_wave_length - remaining_shift_nm, 2)
            self.__target_wave_length = self.settings.current_wave_length + self.__shift

        else:
            return

