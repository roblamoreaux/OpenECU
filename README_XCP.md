# OpenECU: XCP over UDP & CAN (Kvaser/neoVI) + ID Scanner

This patch adds XCP transports using `pyxcp`:
- XCP over **Ethernet UDP** (and TCP if desired)
- XCP over **CAN** via `python-can` with backends: Kvaser (`kvaser`), Intrepid neoVI (`neovi`), Vector, PCAN, IXXAT, SocketCAN.
- Configurable **CTO/DTO** IDs and an optional **identifier scanner**.

## Files
- `requirements.txt`: dependencies.
- `ECUSettings.py`: protocol & transport properties (UDP/TCP, CAN backend, CTO/DTO, scanner).
- `XCPDut.py`: new DUT implementing pyxcp master with UDP/TCP & CAN.
- `ECUDut.py`: minimal router (CCP via `CANDut` if present; XCP via `XCPDut`).

## Setup
1. Install deps:
   ```bash
   pip install -r requirements.txt
   # neoVI users:
   pip install "python-can[neovi]" && pip install python_ics
   ```
2. In OpenTap, set **Protocol**:
   - `XCP_ETH` and `EthProtocol = UDP` for Ethernet/UDP.
   - `XCP_CAN` for CAN; choose `CanInterface` `kvaser` or `neovi`, set `CanChannel`, `CanBitrate`.
3. If you know CTO/DTO IDs, set them; else keep **EnableIdScanner** = true.

## Notes
- pyxcp ETH supports both **TCP and UDP**; select via `EthProtocol`.
- python-can provides backends for **Kvaser** and **neoVI**.
- The provided `ECUDut.py` uses address-based read/write in XCP path; add symbol helpers if needed.
