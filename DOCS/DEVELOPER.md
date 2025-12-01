Developer Notes — Immergas-Modbus
================================

Purpose and goals
------------------
- Provide an ESPHome custom component that exposes Immergas device PDUs (Modbus registers) as ESPHome sensors, numbers, switches, selects and climate entities.
- Centralize the mapping of PDUs and labels in a single `immergas_registers.json` artifact and generate a C++ header for runtime decoding.
- Offer a lightweight Modbus RTU implementation (frame CRC, basic read/write) and safe wiring for entity write operations.
- Provide tools and a small test harness to validate Modbus framing and parsing without hardware.

Repository layout (important files)
----------------------------------
- `immergas_registers.json` — canonical PDU map used to generate the C++ header.
- `components/immergas_modbus/` — Python glue + C++ component and device classes.
- `tools/generate_pdus_header.py` — generator that reads `immergas_registers.json` and emits `components/immergas_modbus/immergas_pdus.h`.
- `tools/modbus_loopback.cpp` — small C++ program to simulate Modbus RTU request/response frames and validate CRC/parsing.
- `archive/` — (optional) archived helper scripts such as original extractors.

How it works — high level
-------------------------
1. The generator reads `immergas_registers.json` and produces a header `immergas_pdus.h` containing an array of `ImmergasPduEntry` structures. Each entry contains:
   - `pdu`: canonical PDU id
   - `reg_addr`: Modbus register address (currently set to PDU number)
   - `count`: number of consecutive registers
   - `type`: enum describing data type (u16, s16, temp, u32, float32, etc.)
   - `scale`: multiplicative scale (e.g., temp decimal -> 0.1)
   - `writable`: whether the PDU supports write
   - `label`: textual label (currently empty or generated if available)

2. At runtime, the `ImmergasModbus` controller polls devices registered in YAML. Devices declare a string `address` (e.g. `"20.00.00"`) and may be assigned PDUs via the Python glue.

3. Polling is batched: contiguous register ranges from the header are merged into a single read to reduce Modbus traffic.

4. Decoding supports basic types and applies scales. For 32-bit values the code assumes big-endian register order (high word first).

5. Writing: `write_pdu_by_value` encodes a float according to the PDU mapping and sends a Modbus 0x10 (Write Multiple Registers) request. Platform entities (Number/Switch/Select) call this helper in safe mode.

Developer workflow
------------------
1) Update or regenerate `immergas_registers.json` (if you have the original JSONs and extractor):

```powershell
cd Z:\GitHub\Immergas-Modbus
node extract_registers.js
# or
python extract_registers.py
```

2) Regenerate the C++ header:

```powershell
python .\tools\generate_pdus_header.py
```

3) Build and test locally (test harness):

```powershell
cd Z:\GitHub\Immergas-Modbus\tools
g++ modbus_loopback.cpp -o modbus_loopback
.\modbus_loopback
```

4) Build the ESPHome firmware containing `components/immergas_modbus` (use `example.yaml` as a starting point):

```powershell
esphome compile example.yaml
esphome run example.yaml
```

Notes about assumptions and how to validate
-----------------------------------------
- Register mapping: this project currently uses PDU number == Modbus register address. Confirm using the device manual. If addresses differ, update `generate_pdus_header.py` to map correctly.
- Endianness: 32-bit types assume high-word first. If values appear swapped, try swapping words or bytes in the generator and recompile.
- Signed values: s16/s32 are decoded using native signed casts.
- Test on a single safe read-only PDU first (outdoor temp, water temp) before enabling writes.

Where to change behavior
------------------------
- `tools/generate_pdus_header.py`: adjust type detection, scale heuristics, or emit extra fields (endianness, comments).
- `components/immergas_modbus/immergas_modbus.cpp`: decoding logic and write implementation — add retries, backoff, or timeouts here.
- `components/immergas_modbus/*/__init__.py`: Python glue for each platform — adjust schema/defaults and how the PDU id is passed to the C++ device.

Archival
--------
Some helper scripts have been moved to `archive/` to keep the main tree focused. If you need the original extractors or earlier tools, check `archive/` before re-creating them.

Next recommended improvements
---------------------------
- Add an automated mock `IM_Client` unit test inside `components/immergas_modbus/test/` to run component-level tests without hardware.
- Improve header generator to include human-readable labels pulled from the label JSON and to emit `endianness` hints.
- Implement write batching and command queueing with retries and exponential backoff to make writes robust for flaky RS-485 links.

Contact / ownership
-------------------
This scaffold was created to consolidate an Immergas register mapping and a corresponding ESPHome custom component. If you want me to implement any of the "Next recommended improvements", tell me which item to prioritize.
