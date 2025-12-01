"""Auto-generated selects definitions (helper list)."""
from ..immergas.auto_entities import selects as AUTO_SELECTS_MAP

AUTO_SELECTS = []
for pid, meta in AUTO_SELECTS_MAP.items():
    AUTO_SELECTS.append({
        'pdu': pid,
        'label': meta.get('im_label'),
        'mode': meta.get('mode', 'CONTROL'),
        'defaults': meta.get('defaults', {}),
    })
