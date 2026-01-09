from opentap import *
import OpenTap
from OpenTap import Log

from .ECUSettings import ECUSettings
from .XCPDut import XCPDut
try:
    from .CANDut import CANDut  # existing CCP path (adjust if different)
except Exception:
    CANDut = None

@attribute(OpenTap.Display("ECU DUT", "Device Under Test", "Resources"))
class ECUDut(object):
    def __init__(self):
        self.Settings = ECUSettings()
        self._backend = None
        self._a2l = None  # hook your existing A2L loader here

    def _ensure_backend(self):
        if self.Settings.Protocol == "CCP":
            if CANDut is None:
                raise RuntimeError("CCP backend CANDut not available.")
            if self._backend is None or not isinstance(self._backend, CANDut):
                self._backend = CANDut(self.Settings)
        elif self.Settings.Protocol in ("XCP_CAN", "XCP_ETH"):
            if self._backend is None or not isinstance(self._backend, XCPDut):
                self._backend = XCPDut(self.Settings, a2l_db=self._a2l)
        else:
            raise RuntimeError("Unknown Protocol selection.")

    def connect(self):
        self._ensure_backend()
        self._backend.connect()

    def disconnect(self):
        if self._backend:
            self._backend.disconnect()

    # Calibration access; for XCP this uses upload/download by address unless you add symbol helpers
    def read_calibration(self, name_or_addr, length=None):
        if isinstance(name_or_addr, str):
            # If you add symbol helpers to XCPDut, call them here; otherwise expect addr/len
            raise NotImplementedError("Symbol-based read not implemented in XCP path.")
        return self._backend.read_by_addr(int(name_or_addr), int(length))

    def write_calibration(self, name_or_addr, value_or_bytes, length=None):
        if isinstance(name_or_addr, str):
            raise NotImplementedError("Symbol-based write not implemented in XCP path.")
        return self._backend.write_by_addr(int(name_or_addr), bytes(value_or_bytes))
