"""Auto-generated switches definitions (helper list)."""
from ..immergas.auto_entities import switches as AUTO_SWITCHES_MAP

AUTO_SWITCHES = []
for pid, meta in AUTO_SWITCHES_MAP.items():
    AUTO_SWITCHES.append({
        'pdu': pid,
        'label': meta.get('im_label'),
        'mode': meta.get('mode', 'CONTROL'),
        'defaults': meta.get('defaults', {}),
    })
