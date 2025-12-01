Auto-generated entity helpers
=============================

Files under the `sensor/`, `number/`, `switch/`, `select/`, `binary_sensor/`, and
`climate/` directories with names starting with `auto_` are generated from
`immergas_registers.json` and expose simple Python lists/dicts that describe
the discovered PDUs and suggested labels/defaults.

How to use
----------
- Inspect `components/immergas_modbus/sensor/auto_sensors.py` for suggested
  sensors and copy the relevant blocks into your `example.yaml`.
- The generator also exposes `components/immergas_modbus/immergas/auto_entities.py`
  which programmatically builds the mappings at import-time; custom component
  platform modules can import these maps to provide auto-configuration defaults.

Notes
-----
- These helper files are intended to speed up wiring PDUs to ESPHome entities.
- They do not replace the platform glue required by ESPHome to register
  components at build time; however, `sensor/__init__.py` has been updated to
  read the auto-entities map when available and apply labels/defaults.
