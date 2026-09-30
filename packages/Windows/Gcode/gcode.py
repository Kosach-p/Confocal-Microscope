from PyQt6.QtWidgets import QFileDialog
from PyQt6.uic import loadUi

from packages.Windows.Gcode.Gcode_GalvoUI import GcodeGalvoUI
from packages.Windows.Gcode.Gcode_Processor import GcodeProcessorClass
from packages.Windows.Gcode.Gcode_ScanManageUI import GcodeScanManageUI
from packages.Windows.Gcode.Gcode_Editor import GcodeEditorClass
from packages.Windows.ParentWindow import ParentWindow

from packages.Controllers.ParentController import ControllerRegistry
from packages.core.config.path import ui


class GcodeWindowClass(ParentWindow):
    name = "GcodeWindowClass"

    def _post_init(self):
        loadUi(ui("Gcode_window.ui"), self)

        self.__Engraving_flag = False
        self.__event_bus = self.parent.event_bus

        self.MenuBar_open = self.parent.MenuBar_File_Open_Gcode

        self.Galvo_control = ControllerRegistry.get("GalvoControlClass")
        self.__galvoUI = GcodeGalvoUI(self.galvo_frame, self.Galvo_control, self.__event_bus)
        self.__ScanManageUI = GcodeScanManageUI(self.galvo_frame, self.Galvo_control, self.__event_bus)
        self.__GcodeProcessor = GcodeProcessorClass(self.chart_frame, self.Tools_frame, self.Statistic_frame, self.F_listWidget, self.__event_bus, self.Galvo_control)
        self.__GcodeEditor = GcodeEditorClass(self.QScintilla)

        self.__connection_init()

    def window_selected(self):
        """ Действия, при выборе окна как активного """
        self.__galvoUI.update()

    def __connection_init(self):
        self.MenuBar_open.triggered.connect(self.openFile)
        
        self.__event_bus.GalvoControl.connect(self.__event_process)
        self.__event_bus.GcodeUI.connect(self.__event_process)
    
    def __event_process(self, transmitter, receiver, command, data):
        """ Обработка emit на линии event_bus """
        if transmitter == self.name:
            return

        if receiver == self.name or receiver == "All":
            if transmitter == "GalvoControlClass":
                params = data[0]
                if self.__Engraving_flag:
                    if (command == "send_gcode_G00" or command == "send_gcode_F" or command == "send_gcode_G01"
                        or command == "send_gcode_G04" or command == "send_gcode_M03" or command == "send_gcode_M05"
                        or command == "send_gcode_S" or command == "send_gcode_M112"):
                        self.__next_line_Engraving(params)
            
            elif transmitter == "GcodeScanManageUI":
                if command == "pause":
                    self.__pause_Engraving()
                elif command == "stop":
                    self.__stop_Engraving()
                elif command == "start":
                    if not self.__event_bus.ProgramBusy:
                        self.__start_Engraving()
    
    def __openFile(self, file_path):
        """ Метод для реализации загрузки файла """
        try:
            l = self.__GcodeProcessor.load_gcode_file(file_path)
            self.__GcodeEditor.editor.setText(''.join(l))
            self.__event_bus.StatusBar.emit("Файл успешно загружен ✅", 3, "success")
        except FileNotFoundError:
            self.__event_bus.StatusBar.emit("Файл или директория не найдены ❌", 3, "error")
        except PermissionError:
            self.__event_bus.StatusBar.emit("Нет прав доступа к файлу ❌", 3, "error")
        except Exception as e:
            print("ERROR::GcodeWindowClass::__openFile::", e)
            self.__event_bus.StatusBar.emit("Не удалось загрузить файл ❌", 3, "error")

    def openFile(self):
        """ Публичный метод для открытия файла по указанному пути  """
        file_path, selected_filter = QFileDialog.getOpenFileName(self, "Открыть", "",
                                                    "G-code файлы (*.gcode *.nc *.g *.cnc *.tap *.ngc *.gc *.txt);;"
                                                    "SVG файлы (*.svg);;""Все файлы (*.*)")

        if not file_path:
            return

        self.__openFile(file_path=file_path)

    def __send_gcode(self, data):
        print("__send_gcode, отправляем эту строку", data)
        command = data[0]
        param = data[1:]

        if command in ('G00', 'G0'):
            self.Galvo_control.G00(x=int(param[0]), y=int(param[1]), receive_marker=self.name)
        elif command in ('G01', 'G1'):
            self.Galvo_control.G01(x=int(param[0]), y=int(param[1]), receive_marker=self.name)
        elif command in ('M03', 'M3'):
            self.Galvo_control.M03(receive_marker=self.name)
        elif command in ('M05', 'M5'):
            self.Galvo_control.M05(receive_marker=self.name)
        elif command == 'F':
            self.Galvo_control.F(F=int(param[0]), receive_marker=self.name)
        elif command == 'S':
            self.Galvo_control.S(S=int(param[0]), receive_marker=self.name)
        else:
            print("Неизвестная команда", command)
            self.__next_line_Engraving([1])

    def __start_Engraving(self):
        if not self.__GcodeProcessor.isReady:
            return

        line = self.__GcodeProcessor.first_line
        
        if line is not None:
            self.__event_bus.ProgramBusy = True
            self.__Engraving_flag = True
            self.__GcodeProcessor.enable_paramUI(False)
            self.__ScanManageUI.progressBar_setValue(0)
            self.__send_gcode(line)
        else:
            print("Gcode отсутствует")

    def __stop_Engraving(self):
        if self.__Engraving_flag:
            self.__event_bus.ProgramBusy = False
            self.__Engraving_flag = False
            self.__GcodeProcessor.enable_paramUI(True)
            self.__galvoUI.stop_scan()
            self.__ScanManageUI.progressBar_setValue(100)
            self.__ScanManageUI.laser_checkBox_set(False)

        self.__send_gcode(data=['M5'])

    def __pause_Engraving(self):
        self.__Engraving_flag = False

    def __next_line_Engraving(self, data):
        """ После получения ответа от Гальвосканера, решаем, что дальше отправлять """

        if int(self.__GcodeProcessor.progress) != self.__ScanManageUI.progressBar_Value():
            self.__ScanManageUI.progressBar_setValue(self.__GcodeProcessor.progress)

        if data is None:        # Гальвосканер не подтвердил получение команды
            line = self.__GcodeProcessor.last_used_line
        elif data['status'] == 1:      # Гальвосканер записал последнюю команду
            line = self.__GcodeProcessor.next_line
        else:                   # Гальвосканер не смог записать последнюю команду
            line = self.__GcodeProcessor.last_used_line
        
        if line is not None:
            self.__send_gcode(line)
        else:
            self.__Gcode_completed()

    def __Gcode_completed(self):
        if self.__ScanManageUI.is_looped():
            self.__start_Engraving()
        else:
            self.__stop_Engraving()
