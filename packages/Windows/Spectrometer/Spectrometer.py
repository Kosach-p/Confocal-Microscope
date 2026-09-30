import numpy as np
from PyQt6.QtWidgets import QFileDialog
from PyQt6.uic import loadUi
import os

from packages.Windows.Spectrometer.Spectrometer_StepperMotorUI import SpectrometerStepperMotorUI
from packages.Windows.Spectrometer.Spectrometer_SpectrumUI import SpectrometerSpectrumUI
from packages.Windows.Spectrometer.Spectrometer_FSM import SpectrumControllerClass
from packages.core.widgets.PhotonCounterWidget import PhotonCounterWidget
from packages.core.services.save_service.DataSave_service import SpectrumSaver

from packages.Windows.ParentWindow import ParentWindow
from packages.Controllers.ParentController import ControllerRegistry

from packages.core.widgets.TreeModuleWidget import TreeModule
from packages.core.units.UnitManager import *
from packages.core.config.path import ui


class SpectrometerWindowClass(ParentWindow):
    name = "SpectrometerWindowClass"

    def _post_init(self):
        loadUi(ui("Spectrometer_window.ui"), self)

        for label in self.findChildren(QLabel):
            if "UnitLabel" in label.objectName():
                label = UnitLabel(label)

        self.event_bus = self.parent.event_bus
        self.MenuBar_save = self.parent.MenuBar_File_Save_Spectrum
        self.MenuBar_open = self.parent.MenuBar_File_Open_Spectrum

        self.StepperMotor_control = ControllerRegistry.get("StepperMotorControlClass")
        self.PhotonCounter_control = ControllerRegistry.get("PhotonCounterControlClass")

        self.photonCounterUI = PhotonCounterWidget(self.PhotonCounter_GroupBox, self.event_bus)
        self.StepperMotorUI = SpectrometerStepperMotorUI(self.Stepper_motor_panel, self.StepperMotor_control, self.event_bus)
        self.SpectrumUI = SpectrometerSpectrumUI(self.Stepper_motor_panel, self.event_bus)
        self.ScanFSM = SpectrumControllerClass(self.spectrum_chart_frame)
        self.FileManager = SpectrumSaver()
        self.Tree = TreeModule(self.Tree_frame, self.FileManager, self.event_bus.SpectrometerUI, tmp_save=False)

        self.removingSpectrum = False
        self.preparationRemovingSpectrum = False
        self.__fast_mode = True

        self.window_selected()
        self.__connection_init()

        self.__initialized = True

        self.event_bus.StatusBar.emit("Окно спектрометра инициализировано", True, "success")

    def window_selected(self):
        """ Действия при выборе окна, как активного """
        print("SpectrometerWindowClass::window_selected::Функционал метода не прописан")

    def __connection_init(self):
        """ Инициализация подключений """
        self.event_bus.SpectrometerUI.connect(self.__event_process)
        self.event_bus.PhotonCounterControl.connect(self.__event_process)
        self.event_bus.StepperMotorControl.connect(self.__event_process)

        self.MenuBar_save.triggered.connect(self.saveFile)
        self.MenuBar_open.triggered.connect(self.openFile)

    def __event_process(self, transmitter, receiver, command, data):
        """ Обработчик emit в выбранном канале """
        if transmitter == self.name:
            return
        if receiver == self.name or receiver == "All":
            if transmitter == "PhotonCounterControlClass":
                if command == "StartGetCounting":
                    if self.removingSpectrum:
                        self.__new_point_in_spectrum(data)

            elif transmitter == "StepperMotorControlClass":
                if command == "movement_completed":
                    if self.preparationRemovingSpectrum:
                        self.preparationRemovingSpectrum = False
                        self.removingSpectrum = True
                        speed = self.ScanFSM.step / (self.ScanFSM.accum_time / 1000)
                        self.StepperMotor_control.set_speed_nm(speed)

                    if self.removingSpectrum:
                        self.PhotonCounter_control.StartGetCounting(self.name)

            elif transmitter == "SpectrometerSpectrumUI":
                if command == "start_button":
                    if data[0] and not self.event_bus.ProgramBusy:
                        if self.StepperMotor_control.is_ready:
                            #if self.PhotonCounter_control.is_ready:
                            if True:
                                self.__start_spectrum()
                            else:
                                self.event_bus.StatusBar.emit(f"Детектор не готов к работе ❗", 3, "warning")
                        else:
                            self.event_bus.StatusBar.emit(f"Шаговый мотор не готов к работе ❗", 3, "warning")
                    if not data[0]:
                        self.__stop_spectrum()

            elif transmitter == "TreeModule":
                if command == "show_data":
                    dataset = data[0]['data']
                    reason = data[0]['reason']
                    self.ScanFSM.show_data_Tree(dataset, reason)
                if command == "save_data":
                    self.saveFile("save")

    def __start_spectrum(self):
        """ Начало снятие спектра """
        if self.__fast_mode:
            self.preparationRemovingSpectrum = True
            self.removingSpectrum = False
        else:
            self.preparationRemovingSpectrum = False
            self.removingSpectrum = True

        self.event_bus.ProgramBusy = True

        self.SpectrumUI.start_removing()
        self.__fast_mode = self.SpectrumUI.fast_mode_CheckBox_state

        self.ScanFSM.fast_mode = self.__fast_mode
        current_wavelength = self.StepperMotor_control.get_cord()
        self.ScanFSM.load_scan_parameters(self.SpectrumUI.get_scan_param(), current_wavelength)

        self.PhotonCounter_control.set_accum_time_ms(self.ScanFSM.accum_time)
        self.StepperMotor_control.go_to(self.ScanFSM.get_first_cord())

    def __stop_spectrum(self):
        """ Завершение снятия спектра """
        self.removingSpectrum = False
        self.preparationRemovingSpectrum = False
        self.event_bus.ProgramBusy = False
        self.StepperMotor_control.smooth_stop()

        self.SpectrumUI.stop_removing()
        self.PhotonCounter_control.set_normal_accum_time_ms()
        self.StepperMotor_control.set_normal_speed()

    def __spectrum_recording_completed(self):
        """ Завершили снимать один проход спектра """
        data = self.ScanFSM.dat_file()
        inf = self.ScanFSM.inf_file()

        self.Tree.Add_branch(inf, data)

        if self.ScanFSM.repetition_completed:
            self.__continue_record_spectrum()
        else:
            self.__stop_spectrum()

    def __continue_record_spectrum(self):
        """ Продолжаем снимать проход спектра """
        current_wavelength = self.StepperMotor_control.get_cord()
        self.ScanFSM.generate_Matrices(current_wavelength)

        self.StepperMotor_control.go_to(self.ScanFSM.get_first_cord())

    def __new_point_in_spectrum(self, data):
        """ Добавляет новую точку в спектр и перемещает шаговый мотор на новую точку """
        current_wavelength = self.StepperMotor_control.get_cord()
        point_number = self.ScanFSM.append_point(data[1], current_wavelength)
        self.SpectrumUI.progressBar_setValue(self.ScanFSM.calculatePercentage())

        target_wavelength = self.ScanFSM.get_next_cord(current_wavelength)

        if self.__fast_mode:
            if point_number == 0:
                self.StepperMotor_control.go_to(target_wavelength)

            if current_wavelength == self.ScanFSM.end:
                self.__spectrum_recording_completed()
                return
            else:
                self.PhotonCounter_control.StartGetCounting(self.name)
        else:
            if target_wavelength is None:
                self.__spectrum_recording_completed()
                return
            else:
                self.StepperMotor_control.go_to(target_wavelength)
