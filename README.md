Immergas-Modbus
===============

Immergas-Modbus
===============

Minimal project overview
------------------------
This repository provides a scaffold and tools for an ESPHome custom component that reads Immergas device registers over Modbus RTU (UART / RS-485). The integration exposes device PDUs as ESPHome sensors, numbers, switches, selects and climate entities.

Project goals
-------------
- Centralize PDU/register metadata in `immergas_registers.json`.
- Generate a C++ header from that mapping to drive decoding/reads at runtime.
- Implement a simple Modbus RTU client (CRC, read/write) and safe wiring for entity writes.

See `DOCS/DEVELOPER.md` for detailed developer instructions, goals, assumptions, and the test harness usage.

Quick start
-----------
- Regenerate the header after updating `immergas_registers.json`:

```powershell
python .\tools\generate_pdus_header.py
```

- Build with ESPHome (using `example.yaml` as a starting point):

```powershell
esphome compile example.yaml
esphome run example.yaml
```

Notes
-----
- The detailed developer instructions and test-harness steps were moved to `DOCS/DEVELOPER.md` to keep this `README.md` concise.
- If you need archived helper scripts, see the `archive/` directory.
