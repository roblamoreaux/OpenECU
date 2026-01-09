import time
import can
from pyxcp.cmdline import ArgumentParser
from OpenTap import Log

class XCPDut(object):
    def __init__(self, settings, a2l_db=None):
        self.s = settings
        self.a2l = a2l_db
        self._ap = None
        self._ctx = None
        self._x = None

    # ---------- CAN setup ----------
    def _build_can_bus(self):
        kw = {}
        if self.s.CanInterface == "vector" and self.s.VectorAppName:
            kw["app_name"] = self.s.VectorAppName
        return can.interface.Bus(
            bustype=self.s.CanInterface,  # kvaser / vector / neovi / socketcan / pcan / ixxat
            channel=self.s.CanChannel,
            bitrate=int(self.s.CanBitrate),
            **kw
        )

    # ---------- Connect ----------
    def connect(self):
        self._ap = ArgumentParser(description="OpenECU XCP")
        if self.s.Protocol == "XCP_CAN":
            can_if = self._build_can_bus()
            self._ctx = self._ap.run(transport_layer_interface=can_if)
            self._x = self._ctx.__enter__()

            # Set explicit identifiers if provided
            self._set_can_ids(self.s.XcpCtoId, self.s.XcpDtoId)

            # Optional identifier scanner
            if self.s.EnableIdScanner:
                self._maybe_scan_identifiers()

        elif self.s.Protocol == "XCP_ETH":
            # ETH over TCP/UDP
            self._ap.set_defaults(transport="eth",
                                  host=self.s.EthHost,
                                  port=int(self.s.EthPort),
                                  protocol=self.s.EthProtocol)   # "TCP" or "UDP"
            self._ctx = self._ap.run()
            self._x = self._ctx.__enter__()
        else:
            raise RuntimeError("XCPDut: Protocol must be XCP_CAN or XCP_ETH")

        self._x.connect()
        Log.Info(f"XCPDut connected ({self.s.Protocol}).")

    def disconnect(self):
        if self._x:
            try:
                self._x.disconnect()
            finally:
                self._ctx.__exit__(None, None, None)
                self._x = None
                self._ctx = None
                Log.Info("XCPDut disconnected.")

    # ---------- CAN IDs ----------
    def _set_can_ids(self, cto, dto):
        try:
            tl = getattr(self._x, "transportLayer", None)
            if tl and hasattr(tl, "setIdentifiers"):
                tl.setIdentifiers(int(cto), int(dto))
                Log.Info(f"XCP CAN IDs set CTO=0x{cto:X}, DTO=0x{dto:X}")
        except Exception as e:
            Log.Warning(f"Could not set CAN IDs explicitly: {e}")

    # ---------- Identifier scanner ----------
    def _maybe_scan_identifiers(self):
        mode = (self.s.ScannerMode or "PassiveThenActive").lower()
        if mode in ("passiveonly", "passivethenactive"):
            if self._passive_learn_ids(timeout_s=1.0):
                return
        if mode in ("activesweep", "passivethenactive"):
            self._active_sweep_ids()

    def _passive_learn_ids(self, timeout_s=1.0):
        """
        Listen for CAN traffic and detect likely XCP CTO/DTO IDs.
        """
        bus = self._x.transportLayer.canif  # python-can Bus
        end = time.time() + timeout_s
        seen = set()
        while time.time() < end:
            msg = bus.recv(timeout=0.05)
            if not msg:
                continue
            # Heuristic: XCP packets often start with 0xFF CONNECT, 0xFE DISCONNECT etc.
            if len(msg.data) >= 1 and msg.data[0] in (0xFF, 0xFE, 0xFD, 0xFC):
                seen.add(msg.arbitration_id)
        if len(seen) >= 2:
            cto, dto = sorted(seen)[:2]
            self._set_can_ids(cto, dto)
            Log.Info(f"Passive learned XCP IDs CTO=0x{cto:X}, DTO=0x{dto:X}")
            return True
        return False

    def _active_sweep_ids(self):
        """
        Try common CTO/DTO pairs and attempt CONNECT; stop on success.
        """
        candidates = [
            (0x7E0, 0x7E8), (0x7E1, 0x7E9),
            (0x6F1, 0x611), (0x650, 0x650),
        ]
        for cto, dto in candidates:
            try:
                self._set_can_ids(cto, dto)
                self._x.connect()
                Log.Info(f"Identifier sweep succeeded CTO=0x{cto:X}, DTO=0x{dto:X}")
                return
            except Exception:
                try:
                    self._x.disconnect()
                except Exception:
                    pass
                self._ctx.__exit__(None, None, None)
                self._ctx = self._ap.run(transport_layer_interface=self._x.transportLayer.canif)
                self._x = self._ctx.__enter__()
        Log.Warning("Active sweep: no valid XCP IDs found; using configured CTO/DTO.")

    # ---------- Polling APIs ----------
    def read_by_addr(self, address, length):
        try:
            if length <= 8:
                data = self._x.shortUpload(address, length)
            else:
                data = self._x.upload(address, length)
            return bytes(data)
        except Exception as e:
            Log.Error(f"XCP read failed @0x{address:X} len={length}: {e}")
            raise

    def write_by_addr(self, address, data_bytes):
        try:
            if len(data_bytes) <= 8:
                self._x.shortDownload(address, data_bytes)
            else:
                self._x.download(address, data_bytes)
        except Exception as e:
            Log.Error(f"XCP write failed @0x{address:X}: {e}")
            raise
