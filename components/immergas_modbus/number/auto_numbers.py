"""Auto-generated number definitions (helper list).

Expose `AUTO_NUMBERS` derived from the extractor mapping.
"""
from ..immergas.auto_entities import numbers as AUTO_NUMBERS_MAP

AUTO_NUMBERS = []
for pid, meta in AUTO_NUMBERS_MAP.items():
    AUTO_NUMBERS.append({
        'pdu': pid,
        'label': meta.get('im_label'),
        'mode': meta.get('mode', 'CONTROL'),
        'defaults': meta.get('defaults', {}),
    })
