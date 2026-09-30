# config/app_config.py
from packages.Windows.View2D.View2D import View2DClass
from packages.Windows.Spectrometer.Spectrometer import SpectrometerWindowClass
from packages.Windows.ODMR_Spectrometer.ODMR_Spectrometer import ODMRSpectrometerWindowClass
from packages.Windows.Gcode.gcode import GcodeWindowClass

WINDOWS = [View2DClass, SpectrometerWindowClass,
           ODMRSpectrometerWindowClass, GcodeWindowClass]

from packages.Controllers.GalvoScaner.GalvoScaner import GalvoControlClass
from packages.Controllers.PhotonCounter.Photon_counter import PhotonCounterControlClass
from packages.Controllers.Piezo.Piezo import PiezoControlClass
from packages.Controllers.StepperMotor.StepperMotor import StepperMotorControlClass
from packages.Controllers.LMX2820.LMX2820 import LMX2820ControlClass
from packages.core.config.device_schema import *

#DEVICE_CONFIG = ["Galvo", "PhotonCounter", "Piezo", "StepperMotor"]
DEVICE_CONFIG = [DeviceGroup.BEAM_STEERERS, DeviceGroup.DETECTORS, DeviceGroup.POSITIONERS,
                 DeviceGroup.SPECTRAL_TUNERS, DeviceGroup.MODULATORS]

CONTROLLERS = [GalvoControlClass, PiezoControlClass, PhotonCounterControlClass,
               StepperMotorControlClass, LMX2820ControlClass]

from packages.Floating_window.node_editor.NodeEditor import NodeEditorClass
FLOATING_WINDOWS = [NodeEditorClass]
