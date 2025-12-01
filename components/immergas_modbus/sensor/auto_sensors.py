"""Auto-generated sensor definitions (helper list).

This file is generated from `immergas_registers.json` and exposes a simple
`AUTO_SENSORS` list suitable for quick inspection or templating into YAML.
"""
from ..immergas.auto_entities import sensors as AUTO_SENSORS_MAP

AUTO_SENSORS = []
for pid, meta in AUTO_SENSORS_MAP.items():
    AUTO_SENSORS.append({
        'pdu': pid,
        'label': meta.get('im_label'),
        'mode': meta.get('mode', 'STATUS'),
        'defaults': meta.get('defaults', {}),
    })
