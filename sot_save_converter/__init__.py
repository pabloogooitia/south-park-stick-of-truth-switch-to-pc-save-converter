"""South Park: The Stick of Truth (La Vara de la Verdad) - Switch to PC save converter."""

__version__ = "1.0.0"

from .convert import convert_save, convert_state, pc_name_for
from .formats import PcSave, SaveFormatError, SwitchSave, detect_platform

__all__ = ["convert_save", "convert_state", "pc_name_for", "PcSave", "SwitchSave",
           "SaveFormatError", "detect_platform", "__version__"]
