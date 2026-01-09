from System import String, Int32, Boolean
from opentap import *
import OpenTap

@attribute(OpenTap.Display("ECU Settings", "Connection and protocol selection", "Resources"))
class ECUSettings:
    Protocol = property(String, "CCP") \
        .add_attribute(OpenTap.Display("Protocol", "Choose CCP, XCP_CAN, or XCP_ETH", "Transport", 0)) \
        .add_attribute(OpenTap.AvailableValues(["CCP", "XCP_CAN", "XCP_ETH"]))

    A2LFile = property(String, "") \
        .add_attribute(OpenTap.Display("A2L File", "ASAP2 file for symbol/units", "Transport", 1))

    # -------- XCP over CAN --------
    CanInterface = property(String, "kvaser") \
        .add_attribute(OpenTap.Display("CAN Interface",
            "python-can backend: kvaser/vector/pcan/ixxat/socketcan/neovi",
            "XCP CAN", 0))
    CanChannel = property(String, "0") \
        .add_attribute(OpenTap.Display("CAN Channel", "e.g., 0, can0, PCAN_USBBUS1", "XCP CAN", 1))
    CanBitrate = property(Int32, 500000) \
        .add_attribute(OpenTap.Display("Bitrate", "bit/s", "XCP CAN", 2))
    VectorAppName = property(String, "") \
        .add_attribute(OpenTap.Display("Vector App", "If using 'vector', set app name (e.g., CANalyzer)", "XCP CAN", 3))

    XcpCtoId = property(Int32, 0x7E0) \
        .add_attribute(OpenTap.Display("CTO ID", "CAN arb ID for XCP commands", "XCP CAN", 4))
    XcpDtoId = property(Int32, 0x7E8) \
        .add_attribute(OpenTap.Display("DTO ID", "CAN arb ID for XCP data", "XCP CAN", 5))

    EnableIdScanner = property(Boolean, True) \
        .add_attribute(OpenTap.Display("Enable Identifier Scanner", "Try to auto-detect CTO/DTO IDs", "XCP CAN", 6))

    ScannerMode = property(String, "PassiveThenActive") \
        .add_attribute(OpenTap.Display("Scanner Mode", "PassiveThenActive / PassiveOnly / ActiveSweep", "XCP CAN", 7)) \
        .add_attribute(OpenTap.AvailableValues(["PassiveThenActive", "PassiveOnly", "ActiveSweep"]))

    # -------- XCP over Ethernet --------
    EthHost = property(String, "127.0.0.1") \
        .add_attribute(OpenTap.Display("Host", "ECU IP/host", "XCP ETH", 0))
    EthPort = property(Int32, 5555) \
        .add_attribute(OpenTap.Display("Port", "TCP/UDP port", "XCP ETH", 1))
    EthProtocol = property(String, "UDP") \
        .add_attribute(OpenTap.Display("Protocol", "TCP or UDP", "XCP ETH", 2)) \
        .add_attribute(OpenTap.AvailableValues(["TCP", "UDP"]))
