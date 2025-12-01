Immergas-Modbus
================

This folder contains helper tools and the initial scaffold for an ESPHome component that will read Immergas heat-pump registers over Modbus.

Files
- `extract_registers.js`: Node.js script that parses the `dominus` project JSONs and emits `immergas_registers.json` with discovered PDUs and basic metadata.

How to run (PowerShell)

```powershell
cd z:\GitHub\Immergas-Modbus
node extract_registers.js
```

Next steps
- Review `immergas_registers.json` output and mark which PDUs should become sensors/switches in the ESPHome component.
- I can scaffold `components/immergas_modbus` (C++/Python) matching the structure of `components/samsung_nasa` and generate basic sensors from the register map.
