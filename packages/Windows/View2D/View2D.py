# Встроенные библиотеки
import time

Time = time.time()
import os
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = ""  # Отключает ненужные Qt-плагины

from PyQt6.uic import loadUi

from PyQt6.QtWidgets import QStackedWidget
# Визуализация
from packages.Windows.View2D.Scan_FSM import ScanFSM
from packages.Windows.ParentWindow import ParentWindow
from packages.Windows.View2D.View2D_GalvoUI import View2DGalvoUI
from packages.Windows.View2D.View2D_PiezoUI import View2DPiezoUI
from packages.core.widgets.PhotonCounterWidget import PhotonCounterWidget
from packages.core.services.save_service.DataSave_service import ArraySaver

from packages.Controllers.ParentController import ControllerRegistry
from packages.core.widgets.TreeModuleWidget import TreeModule
from packages.core.widgets.ImageView import ImageView
import numpy as np
from packages.core.config.path import ui

from packages.Windows.View3D.View3D_Render import View3DRenderClass

from packages.core.widgets.QColorMapDialog import ColormapDialog, ColormapButton
from PyQt6.QtWidgets import QDialog


class View2DClass(ParentWindow):
    name = "View2DClass"

    def _post_init(self):
        loadUi(ui("view_2D.ui"), self)
        self.event_bus = self.parent.event_bus

        self.ScanFSM = ScanFSM()
        self.view_3d = View3DRenderClass(self.view_3d_widget, user_name="3D вид", event_bus=self.event_bus)

        self.ImageView = ImageView(self.ImageView_frame, user_name="2D вид", event_bus=self.event_bus)
        self.ImageView.imshow(np.loadtxt("service_files/Init_image.txt"))
        self.ImageView.callback = self.__on_roi_changed

        self.color_map_btn = ColormapButton("magma", parent=self.color_map_btn_2d)
        self.color_map_btn.setFixedSize(20, 20)
        self.color_map_btn.setProperty("color", "magma")
        self.color_map_btn.clicked.connect(self.pick_color_map)

        self.__connection_init()

        self.Galvo_control = ControllerRegistry.get("GalvoControlClass")
        self.Piezo_control = ControllerRegistry.get("PiezoControlClass")
        self.PhotonCounter_control = ControllerRegistry.get("PhotonCounterControlClass")

        self.__scan_state = 0
        self.last_opened_dir = ""

        self.index_of_pixel = 0

        self.galvoUI = View2DGalvoUI(self.galvo_frame, self.Galvo_control, self.event_bus)
        self.piezoUI = View2DPiezoUI(self.piezo_frame, self.Piezo_control, self.event_bus)
        self.photonCounterUI = PhotonCounterWidget(self.PhotonCounter_GroupBox, self.event_bus)

        self.FileManager = ArraySaver()
        self.Tree = TreeModule(self.Tree_frame, file_manager=self.FileManager, event_bus=self.event_bus.View2DUI, tmp_save=False)

        self.window_selected()
        self.view_tabWidget.setCurrentIndex(0)

    def pick_color_map(self):
        """Открытие диалога выбора цветовой карты"""
        dialog = ColormapDialog()
        if dialog.exec() == QDialog.DialogCode.Accepted:
            cmap_name = dialog.get_selected_cmap()
            self.color_map_btn.setProperty("color", cmap_name)
            self.color_map_btn.cmap_name = cmap_name
            self.ImageView.set_colormap(cmap_name)

    def window_selected(self):
        """ Действия, при выборе окна как активного """
        self.galvoUI.update()
        self.piezoUI.update()
        self.photonCounterUI.update()

    def __connection_init(self):
        self.event_bus.View2DUI.connect(self.__event_process)
        self.event_bus.View3DUI.connect(self.__event_process)
        self.event_bus.PhotonCounterControl.connect(self.__event_process)
        self.event_bus.GalvoControl.connect(self.__event_process)

    def __event_process(self, transmitter, receiver, command, data):
        """ Обработчик emit в выбранном канале """
        if transmitter == self.name:
            return

        if receiver == self.name or receiver == "All":
            if transmitter == "View2DGalvoUI":
                if command == "scan_start":
                    if self.Galvo_control.is_ready:
                        if self.PhotonCounter_control.is_ready:
                            self.galvo_start_scan()
                        else:
                            self.event_bus.StatusBar.emit(f"Детектор не готов к работе ❗", 3, "warning")
                            self.galvo_stop_scan()
                    else:
                        self.event_bus.StatusBar.emit(f"Гальвосканер не готов к работе ❗", 3, "warning")
                        self.galvo_stop_scan()

                elif command == "scan_stop":
                    self.galvo_stop_scan()

            elif transmitter == "TreeModule":
                if command == "show_data":
                    dataset = data[0]['data']
                    reason = data[0]['reason']
                    self.ImageView.imshow_TreeData(dataset, reason)
                    self.view_3d.matrixshow_TreeData(dataset, reason)

                if command == "save_data":
                    self.saveFile()

            elif transmitter == "PhotonCounterControlClass":
                if command == "StartGetCounting":
                    if self.__scan_state:
                        self.__new_point_in_scan(data[-1])

            elif transmitter == "GalvoControlClass":
                if command == "movement_completed":
                    if self.__scan_state:
                        self.PhotonCounter_control.StartGetCounting(receive_marker=self.name)


    def __on_roi_changed(self, x1, y1, x2, y2):
        """ Прерывание при изменении размеров области выделения на ImageView """
        scan_parameters = [[x1, x2, None], [y1, y2, None], [None, None, None], None]
        self.galvoUI.set_scan_param(scan_parameters)

    def galvo_start_scan(self):
        self.event_bus.ProgramBusy = True
        self.__scan_state = 1
        self.ScanFSM.load_scan_parameters(self.galvoUI.get_scan_param())
        self.galvoUI.start_scan()

        x_origin, y_origin, z_origin = self.ScanFSM.get_first_cord()

        self.Galvo_control.set_cord(x_origin, y_origin, receive_marker=self.name)
        self.Piezo_control.set_cord(0, 0, z_origin, receive_marker=self.name)
        self.PhotonCounter_control.set_accum_time_ms(accum_time=self.ScanFSM.accum_time)
        self.event_bus.StatusBar.emit("... 2D сканирование ...", 0, "Status")
        self.PhotonCounter_control.StartGetCounting(receive_marker=self.name)

    def __new_point_in_scan(self, data):
        self.ScanFSM.append_point(data)
        z, x, y = self.ScanFSM.get_next_cord()
        if (x is None) or (y is None) or (z is None):
            self.galvo_stop_scan()
            return
        self.Galvo_control.set_cord(x, y, receive_marker=self.name)
        self.galvoUI.progressBar_setValue(self.ScanFSM.percentage)
        if self.ScanFSM.time_to_show is True:
            print(1)
            self.ImageView.imshow(self.ScanFSM.DataMatrix[0], scale_x=self.ScanFSM.step_x, scale_y=self.ScanFSM.step_y,
                                  offset_x=self.ScanFSM.x1, offset_y=self.ScanFSM.y1)

    def galvo_stop_scan(self):
        self.event_bus.ProgramBusy = False
        self.__scan_state = 0
        self.PhotonCounter_control.set_normal_accum_time_ms()
        self.Tree.Add_branch(self.ScanFSM.inf_file, self.ScanFSM.DataMatrix)
        print(2)
        self.ImageView.imshow(self.ScanFSM.DataMatrix[0], scale_x=self.ScanFSM.step_x, scale_y=self.ScanFSM.step_y,
                              offset_x=self.ScanFSM.x1, offset_y=self.ScanFSM.y1)

        self.galvoUI.stop_scan()
        self.photonCounterUI.reset()

    def piezo_start_scan(self):
        self.event_bus.ProgramBusy = True
        ...

    def piezo_stop_scan(self):
        self.event_bus.ProgramBusy = False
        ...
