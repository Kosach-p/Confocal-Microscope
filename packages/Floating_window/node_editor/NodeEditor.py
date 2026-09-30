from PyQt6.QtGui import QAction
import os
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMdiArea, QMessageBox, QFileDialog
from PyQt6.QtCore import Qt

from nodeeditor.utils import loadStylesheets
from nodeeditor.node_editor_window import NodeEditorWindow
from packages.Floating_window.node_editor.calc_sub_window import CalculatorSubWindow

from nodeeditor.utils import dumpException, pp
# Enabling edge validators
from nodeeditor.node_edge import Edge
from nodeeditor.node_edge_validators import (
    edge_validator_debug,
    edge_cannot_connect_two_outputs_or_two_inputs,
    edge_cannot_connect_input_and_output_of_same_node
)
from packages.Floating_window.node_editor.calc_conf import *

Edge.registerEdgeValidator(edge_validator_debug)
Edge.registerEdgeValidator(edge_cannot_connect_two_outputs_or_two_inputs)
Edge.registerEdgeValidator(edge_cannot_connect_input_and_output_of_same_node)


DEBUG = False


class NodeEditorClass(NodeEditorWindow):
    name = "NodeEditorClass"

    def initUI(self):
        register_all_nodes()

        self.empty_icon = QIcon(".")
        self.mdiArea = QMdiArea()
        self.mdiArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.mdiArea.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.mdiArea.setViewMode(QMdiArea.ViewMode.TabbedView)
        self.mdiArea.setDocumentMode(True)
        self.mdiArea.setTabsClosable(True)
        self.mdiArea.setTabsMovable(True)
        self.setCentralWidget(self.mdiArea)

        self.mdiArea.subWindowActivated.connect(self.updateMenus)
        self.createActions()
        self.createMenus()
        self.createStatusBar()
        self.updateMenus()

        self.readSettings()

        self.setWindowTitle("Редактор Нод")
        self.onFileNew()

    def closeEvent(self, event):
        self.mdiArea.closeAllSubWindows()
        if self.mdiArea.currentSubWindow():
            event.ignore()
        else:
            self.writeSettings()
            event.accept()

    def getCurrentNodeEditorWidget(self):
        """ we're returning NodeEditorWidget here... """
        activeSubWindow = self.mdiArea.activeSubWindow()
        if activeSubWindow:
            return activeSubWindow.widget()
        return None

    def onFileNew(self):
        try:
            subwnd = self.createMdiChild()
            subwnd.widget().fileNew()
            subwnd.show()
        except Exception as e:
            dumpException(e)

    def onFileOpen(self):
        fnames, filter = QFileDialog.getOpenFileNames(self, 'Open graph from file', self.getFileDialogDirectory(),
                                                      self.getFileDialogFilter())

        try:
            for fname in fnames:
                if fname:
                    existing = self.findMdiChild(fname)
                    if existing:
                        self.mdiArea.setActiveSubWindow(existing)
                    else:
                        # we need to create new subWindow and open the file
                        self.nodeeditor = CalculatorSubWindow()
                        if self.nodeeditor.fileLoad(fname):
                            self.statusBar().showMessage("File %s loaded" % fname, 5000)
                            self.nodeeditor.setTitle()
                            subwnd = self.createMdiChild(self.nodeeditor)
                            subwnd.show()
                        else:
                            self.nodeeditor.close()
        except Exception as e:
            dumpException(e)

    def createMenus(self):
        super().createMenus()

    def updateMenus(self):
        # print("update Menus")
        active = self.getCurrentNodeEditorWidget()
        hasMdiChild = (active is not None)

        self.actSave.setEnabled(hasMdiChild)
        self.actSaveAs.setEnabled(hasMdiChild)

        self.updateEditMenu()

    def updateEditMenu(self):
        try:
            # print("update Edit Menu")
            active = self.getCurrentNodeEditorWidget()
            hasMdiChild = (active is not None)

            self.actPaste.setEnabled(hasMdiChild)

            self.actCut.setEnabled(hasMdiChild and active.hasSelectedItems())
            self.actCopy.setEnabled(hasMdiChild and active.hasSelectedItems())
            self.actDelete.setEnabled(hasMdiChild and active.hasSelectedItems())

            self.actUndo.setEnabled(hasMdiChild and active.canUndo())
            self.actRedo.setEnabled(hasMdiChild and active.canRedo())
        except Exception as e:
            dumpException(e)

    def post_init(self):
        """ Ничего """

    def createStatusBar(self):
        self.statusBar().showMessage("Ready")

    def createMdiChild(self, child_widget=None):
        self.nodeeditor = child_widget if child_widget is not None else CalculatorSubWindow()
        subwnd = self.mdiArea.addSubWindow(self.nodeeditor)
        subwnd.setWindowIcon(self.empty_icon)
        # self.nodeeditor.scene.addItemSelectedListener(self.updateEditMenu)
        # self.nodeeditor.scene.addItemsDeselectedListener(self.updateEditMenu)
        self.nodeeditor.scene.history.addHistoryModifiedListener(self.updateEditMenu)
        self.nodeeditor.addCloseEventListener(self.onSubWndClose)
        return subwnd

    def onSubWndClose(self, widget, event):
        existing = self.findMdiChild(widget.filename)
        self.mdiArea.setActiveSubWindow(existing)

        if self.maybeSave():
            event.accept()
        else:
            event.ignore()

    def findMdiChild(self, filename):
        for window in self.mdiArea.subWindowList():
            if window.widget().filename == filename:
                return window
        return None


def register_all_nodes():
    """Импортировать все модули с нодами"""
    # ======================== DATA_IO ========================
    from packages.Floating_window.node_editor.nodes.DATA_IO.Import.Internal.input import INintNode
    from packages.Floating_window.node_editor.nodes.DATA_IO.Export.Internal.output import OutputNode
    from packages.Floating_window.node_editor.nodes.DATA_IO.Import.matrix_psf_gen import PSFGeneratorNode
    from packages.Floating_window.node_editor.nodes.DATA_IO.Import.matrix_noise_gen import NoiseGeneratorNode
    from packages.Floating_window.node_editor.nodes.DATA_IO.Import.matrix_gen import FormulaGeneratorNode

    register_node(OP_NODE_INPUT_INT)(INintNode)
    register_node(OP_NODE_EXPORT_INT)(OutputNode)
    register_node(OP_NODE_PSF_GENERATOR)(PSFGeneratorNode)
    register_node(OP_NODE_NOISE_GENERATOR)(NoiseGeneratorNode)
    register_node(OP_NODE_FORMULA_GENERATOR)(FormulaGeneratorNode)

    # ======================== MATH ========================
    from packages.Floating_window.node_editor.nodes.MATH.Unary_Operations import UnaryNode
    from packages.Floating_window.node_editor.nodes.MATH.Normalization import NormalizeNode
    from packages.Floating_window.node_editor.nodes.MATH.Statistics import StatisticsNode
    from packages.Floating_window.node_editor.nodes.MATH.Interpolation import InterpolationNode
    from packages.Floating_window.node_editor.nodes.MATH.Products import ProductsNode

    register_node(OP_NODE_UNARY)(UnaryNode)
    register_node(OP_NODE_NORMALIZE)(NormalizeNode)
    register_node(OP_NODE_STATISTICS)(StatisticsNode)
    register_node(OP_NODE_INTERPOLATION)(InterpolationNode)
    register_node(OP_NODE_PRODUCTS)(ProductsNode)

    # ======================== FILTERS ========================
    from packages.Floating_window.node_editor.nodes.FILTERS.Smoothing import SmoothingNode
    from packages.Floating_window.node_editor.nodes.FILTERS.Denoising import DenoisingNode
    from packages.Floating_window.node_editor.nodes.FILTERS.Edge_Detection import EdgeNode
    from packages.Floating_window.node_editor.nodes.FILTERS.Morphological import MorphologyNode
    from packages.Floating_window.node_editor.nodes.FILTERS.Frequency import FrequencyNode
    from packages.Floating_window.node_editor.nodes.FILTERS.Convolution import ConvolutionNode

    register_node(OP_NODE_SMOOTHING)(SmoothingNode)
    register_node(OP_NODE_DENOISING)(DenoisingNode)
    register_node(OP_NODE_EDGE)(EdgeNode)
    register_node(OP_NODE_MORPHOLOGY)(MorphologyNode)
    register_node(OP_NODE_FREQUENCY)(FrequencyNode)
    register_node(OP_NODE_CONVOLUTION)(ConvolutionNode)

    # ======================== TRANSFORMS ========================
    from packages.Floating_window.node_editor.nodes.TRANSFORMS.Geometric import GeometricNode
    from packages.Floating_window.node_editor.nodes.TRANSFORMS.Selection import SelectionNode
    from packages.Floating_window.node_editor.nodes.TRANSFORMS.Signal import SignalNode
    from packages.Floating_window.node_editor.nodes.TRANSFORMS.matrix_cropping import MatrixCropNode
    from packages.Floating_window.node_editor.nodes.TRANSFORMS.Spectrum_cropping import SpectrumCropNode

    register_node(OP_NODE_GEOMETRIC)(GeometricNode)
    register_node(OP_NODE_SELECTION)(SelectionNode)
    register_node(OP_NODE_SIGNAL)(SignalNode)
    register_node(OP_NODE_MATRIX_CROP)(MatrixCropNode)
    register_node(OP_NODE_SPECTRUM_CROP)(SpectrumCropNode)

    # ======================== AVERAGING ========================
    from packages.Floating_window.node_editor.nodes.AVERAGING.Simple import AvgSimpleNode
    from packages.Floating_window.node_editor.nodes.AVERAGING.Advanced import AvgAdvancedNode

    register_node(OP_NODE_AVG_SIMPLE)(AvgSimpleNode)
    register_node(OP_NODE_AVG_ADVANCED)(AvgAdvancedNode)

    # ======================== SEGMENTATION ========================
    from packages.Floating_window.node_editor.nodes.SEGMENTATION.Threshold import ThresholdNode
    from packages.Floating_window.node_editor.nodes.SEGMENTATION.Connected_Components import ConnectedNode
    from packages.Floating_window.node_editor.nodes.SEGMENTATION.Clustering import ClusteringNode

    register_node(OP_NODE_THRESHOLD)(ThresholdNode)
    register_node(OP_NODE_CONNECTED)(ConnectedNode)
    register_node(OP_NODE_CLUSTERING)(ClusteringNode)

    # ======================== VISUALIZATION ========================
    from packages.Floating_window.node_editor.nodes.VISUALIZATION.matrix import \
        VisualizationLineNode as MatrixVisualizationNode
    from packages.Floating_window.node_editor.nodes.VISUALIZATION.spectrum import \
        VisualizationLineNode as SpectrumVisualizationNode
    from packages.Floating_window.node_editor.nodes.VISUALIZATION.line import \
        VisualizationLineNode as LineVisualizationNode

    register_node(OP_NODE_IMAGEVIEW)(MatrixVisualizationNode)
    register_node(OP_NODE_SPECTRUM)(SpectrumVisualizationNode)
    register_node(OP_NODE_LINE)(LineVisualizationNode)

    from packages.Floating_window.node_editor.nodes.SPECIAL_SPECTRA.NV_ODMR import \
        NV_ODMR_Node

    register_node(OP_NODE_NV_ODMR)(NV_ODMR_Node)

    return CALC_NODES
