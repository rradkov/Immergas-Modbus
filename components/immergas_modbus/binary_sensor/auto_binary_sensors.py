"""Auto-generated binary_sensor definitions (helper list)."""
from ..immergas.auto_entities import binary_sensors as AUTO_BINARY_MAP

AUTO_BINARY_SENSORS = []
for pid, meta in AUTO_BINARY_MAP.items():
    AUTO_BINARY_SENSORS.append({
        'pdu': pid,
        'label': meta.get('im_label'),
        'mode': meta.get('mode', 'STATUS'),
        'defaults': meta.get('defaults', {}),
    })
