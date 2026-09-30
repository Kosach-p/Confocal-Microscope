import time

from PyQt6.QtWidgets import QFileDialog
from PyQt6.uic import loadUi
import os

from packages.Windows.ParentWindow import ParentWindow

from packages.core.widgets.PhotonCounterWidget import PhotonCounterWidget
from packages.core.widgets.TreeModuleWidget import TreeModule
from packages.Windows.ODMR_Spectrometer.ODMR_FSM import ODMRSpectrumControllerClass
from packages.Windows.ODMR_Spectrometer.ODMR_SpectrumUI import ODMRSpectrometerSpectrumUI
from packages.Windows.ODMR_Spectrometer.ODMR_GeneratorUI import ODMRSpectrometerGeneratorUI
from packages.Controllers.ParentController import ControllerRegistry

from packages.core.services.save_service.DataSave_service import SpectrumSaver
from packages.core.config.path import ui


class ODMRSpectrometerWindowClass(ParentWindow):
    name = "ODMRSpectrometerWindowClass"

    def _post_init(self):
        loadUi(ui("ODMR_Spectrometer_window.ui"), self)
        self.__event_bus = self.parent.event_bus

        self.PhotonCounter_control = ControllerRegistry.get("PhotonCounterControlClass")
        self.LMX2820_control = ControllerRegistry.get("LMX2820ControlClass")

        self.photonCounterUI = PhotonCounterWidget(self.PhotonCounter_GroupBox, self.__event_bus)
        self.ODMR_SpectrumUI = ODMRSpectrometerSpectrumUI(self.ODMR_spectrum_frame, self.__event_bus)
        self.ScanFSM = ODMRSpectrumControllerClass(self.spectrum_chart_frame)
        self.generatorUI = ODMRSpectrometerGeneratorUI(self.ODMR_spectrum_frame, self.LMX2820_control, self.__event_bus)
        self.FileManager = SpectrumSaver()

        self.Tree = TreeModule(self.Tree_frame, file_manager=self.FileManager, event_bus=self.__event_bus.ODMRSpectrometerUI, tmp_save=True)

        self.removingSpectrum = False
        self.preparationRemovingSpectrum = False
        self.__random_scan = False
        self.__ref_point = False
        
        self.window_selected()
        self.__connection_init()

        self.__initialized = True

        self.__event_bus.StatusBar.emit("Окно ОДМР спектрометра инициализировано", True, "success")

    def window_selected(self):
        """ Действия при выборе окна, как активного """
        print("ODMRSpectrometerWindowClass::window_selected::Функционал метода не прописан")

    def __connection_init(self):
        """ Инициализация подключений """
        self.__event_bus.ODMRSpectrometerUI.connect(self.__event_process)
        self.__event_bus.PhotonCounterControl.connect(self.__event_process)
        self.__event_bus.StepperMotorControl.connect(self.__event_process)
        self.__event_bus.LMX2820Control.connect(self.__event_process)

    def __event_process(self, transmitter, receiver, command, data):
        """ Обработчик emit в выбранном канале """
        if transmitter == self.name:
            return
        if receiver == self.name or receiver == "All":
            if transmitter == "PhotonCounterControlClass":
                if command == "StartGetCounting":
                    if self.removingSpectrum:
                        result = data[0]
                        self.__new_point_in_spectrum(result)

            elif transmitter == "ODMRSpectrometerSpectrumUI":
                if command == "start_button":
                    if data[0] and not self.__event_bus.ProgramBusy:
                        if self.LMX2820_control.is_ready:
                            if self.PhotonCounter_control.is_ready:
                                self.__start_spectrum()

                            else:
                                self.__event_bus.StatusBar.emit(f"Детектор не готов к работе ❗", 3, "warning")
                        else:
                            self.__event_bus.StatusBar.emit(f"Генератор не подключен ❗", 3, "warning")
                    if not data[0]:
                        self.__stop_spectrum()

            elif transmitter == "TreeModule":
                if command == "show_data":
                    dataset = data[0]['data']
                    reason = data[0]['reason']
                    self.ScanFSM.show_data_Tree(dataset, reason)

                if command == "save_data":
                    self.saveFile()

            elif transmitter == "LMX2820ControlClass":
                if command == "set_frq_MHZ":
                    if data[0]:
                        self.PhotonCounter_control.StartGetCounting(self.name)
                    else:
                        self.__event_bus.StatusBar.emit(f"Ошибка при снятии спектра, генератор не отвечает ❌ ", 3, "error")
                        self.LMX2820_control.connect_std_device()
                        self.LMX2820_control.update_frq()

    def __start_spectrum(self):
        """ Начало снятие спектра """
        self.__event_bus.ProgramBusy = True
        self.removingSpectrum = True

        self.ODMR_SpectrumUI.start_removing()
        self.__random_scan = self.ODMR_SpectrumUI.random_scan

        self.ScanFSM.random_scan = self.__random_scan
        self.ScanFSM.load_scan_parameters(self.ODMR_SpectrumUI.get_scan_param())

        self.PhotonCounter_control.set_accum_time_ms(self.ScanFSM.accum_time)
        if self.LMX2820_control.set_frq_1_MHZ(self.ScanFSM.get_first_cord()):
            self.PhotonCounter_control.StartGetCounting(self.name)
        else:
            self.__event_bus.StatusBar.emit(f"Ошибка при снятии спектра, генератор не отвечает ❌ ", 3, "error")
            self.__stop_spectrum()
        
    def __stop_spectrum(self):
        """ Завершение снятия спектра """
        self.removingSpectrum = False
        self.preparationRemovingSpectrum = False
        self.__event_bus.ProgramBusy = False

        self.ODMR_SpectrumUI.stop_removing()
        self.PhotonCounter_control.set_normal_accum_time_ms()

    def __spectrum_recording_completed(self):
        """ Завершили снимать один проход спектра """
        data = self.ScanFSM.dat_file()
        inf = self.ScanFSM.inf_file()

        self.Tree.Add_branch(inf, data)
        self.Tree.save_tmp()

        if self.ScanFSM.repetition_completed:
            self.__continue_record_spectrum()
        else:
            self.__stop_spectrum()

    def __continue_record_spectrum(self):
        """ Продолжаем снимать проход спектра """
        self.ScanFSM.generate_Matrices()
        if self.LMX2820_control.set_frq_1_MHZ(self.ScanFSM.get_first_cord()):
            self.PhotonCounter_control.StartGetCounting(self.name)
        else:
            self.__event_bus.StatusBar.emit(f"Ошибка при снятии спектра, генератор не отвечает ❌ ", 3, "error")
            self.__stop_spectrum()

    def __new_point_in_spectrum(self, data):
        """ Добавляет новую точку в спектр и перемещает шаговый мотор на новую точку """
        current_wavelength = self.LMX2820_control.frq_1_MHZ

        self.ScanFSM.append_point(data, current_wavelength)

        self.ODMR_SpectrumUI.progressBar_setValue(self.ScanFSM.calculatePercentage())

        target_frq = self.ScanFSM.get_next_cord(current_wavelength)
        if target_frq is None:
            self.__spectrum_recording_completed()
            return
        else:
            if self.LMX2820_control.set_frq_1_MHZ(target_frq):
                self.PhotonCounter_control.StartGetCounting(self.name)
            else:
                self.__event_bus.StatusBar.emit(f"Ошибка при снятии спектра, генератор не отвечает ❌ ", 3, "error")
                self.__stop_spectrum()

