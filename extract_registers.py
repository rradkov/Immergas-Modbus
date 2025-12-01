#!/usr/bin/env python3
"""
Convert Dominus CFG/LBL files into a compact Immergas register mapping
and generate per-language label modules for the ESPHome custom component.

Writes:
- `components/immergas_modbus/immergas/labels_<lang>.py` for each language
- `immergas_registers.json` (compact PDU list)

Run from the `Immergas-Modbus` directory:
    python extract_registers.py
"""
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent
CFG_PATH = (ROOT.parent / 'dominus' / 'CFG-WFC01_IM_MBUS.json').resolve()
LBL_PATH = (ROOT.parent / 'dominus' / 'LBL-WFC01_IM_MBUS.json').resolve()
OUT_PATH = ROOT / 'immergas_registers.json'
LABELS_DIR = ROOT / 'components' / 'immergas_modbus' / 'immergas'


def safe_read_json(p: Path):
    try:
        return json.loads(p.read_text(encoding='utf8'))
    except Exception as e:
        print(f'Failed to read/parse {p}: {e}', file=sys.stderr)
        sys.exit(1)


def scan_object(obj, pdus: dict):
    if obj is None:
        return
    if isinstance(obj, list):
        for v in obj:
            scan_object(v, pdus)
        return
    if not isinstance(obj, dict):
        return

    if 'pdu' in obj:
        p = obj.get('pdu')
        if p is None and p != 0:
            pass
        else:
            rec = pdus.setdefault(p, {'pdu': p, 'views': [], 'commands': [], 'messages': []})
            if 'view' in obj:
                rec['views'].append(obj['view'])
            if obj.get('action') == 'write' and 'view' in obj:
                rec['commands'].append(obj['view'])
            if 'item' in obj and 'data' in obj:
                rec['commands'].append({'item': obj['item'], 'data': obj['data']})
            if obj.get('action') in ('read', 'write'):
                rec['messages'].append({'action': obj.get('action')})

    for k, v in obj.items():
        scan_object(v, pdus)


def dedupe_list(lst):
    out = []
    seen = set()
    for x in lst:
        js = json.dumps(x, sort_keys=True)
        if js not in seen:
            seen.add(js)
            out.append(x)
    return out


def generate_label_modules(lbl_json: dict):
    # detect languages from keys like 'text1-en', 'action-it', 'comment-fr'
    langs = set()
    for entry in lbl_json.get('anomalies', []):
        for k in entry.keys():
            m = re.match(r'.+-(?P<lang>[a-z]{2})$', k)
            if m:
                langs.add(m.group('lang'))
    if not langs:
        print('No language keys found in label file')
        return []

    LABELS_DIR.mkdir(parents=True, exist_ok=True)
    generated = []
    for lang in sorted(langs):
        mapping = {}
        for entry in lbl_json.get('anomalies', []):
            code = entry.get('fault-code')
            if code is None:
                continue
            text1 = entry.get(f'text1-{lang}') or entry.get('text1-en')
            text2 = entry.get(f'text2-{lang}') or entry.get('text2-en')
            action = entry.get(f'action-{lang}') or entry.get('action-en')
            comment = entry.get(f'comment-{lang}') or entry.get('comment-en')
            mapping[code] = {
                'text1': text1,
                'text2': text2,
                'action': action,
                'comment': comment,
            }

        # write python module
        mod_path = LABELS_DIR / f'labels_{lang}.py'
        with mod_path.open('w', encoding='utf8') as f:
            f.write('"""Generated Immergas labels (language: %s)"""\n' % lang)
            f.write('\n')
            f.write('immergas_labels = {\n')
            for code, d in mapping.items():
                # ensure code is a valid literal (int or string)
                key = repr(code)
                text1 = repr(d['text1'])
                text2 = repr(d['text2'])
                action = repr(d['action'])
                comment = repr(d['comment'])
                f.write(f'    {key}: {{"text1": {text1}, "text2": {text2}, "action": {action}, "comment": {comment}}},\n')
            f.write('}\n')
        generated.append(str(mod_path))
    return generated


def main():
    cfg = safe_read_json(CFG_PATH)
    lbl = safe_read_json(LBL_PATH)

    pdus = {}
    scan_object(cfg, pdus)

    out = []
    for k, v in pdus.items():
        entry = {'pdu': k, 'views': [], 'commands': [], 'messages': []}
        for va in v.get('views', []):
            if isinstance(va, list):
                entry['views'].extend(va)
            else:
                entry['views'].append(va)
        for ca in v.get('commands', []):
            if isinstance(ca, list):
                entry['commands'].extend(ca)
            else:
                entry['commands'].append(ca)
        for m in v.get('messages', []):
            entry['messages'].append(m)
        entry['views'] = dedupe_list(entry['views'])
        entry['commands'] = dedupe_list(entry['commands'])
        entry['messages'] = dedupe_list(entry['messages'])
        out.append(entry)

    result = {
        'generated_at': __import__('datetime').datetime.utcnow().isoformat() + 'Z',
        'source_cfg': str(CFG_PATH),
        'source_lbl': str(LBL_PATH),
        'pdus': out,
        'lbl_summary': {
            'anomalies_count': len(lbl.get('anomalies', []))
        }
    }

    with OUT_PATH.open('w', encoding='utf8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print('Wrote', OUT_PATH, '- PDUs found:', len(out))

    generated = generate_label_modules(lbl)
    if generated:
        print('Generated label modules:')
        for p in generated:
            print(' -', p)


if __name__ == '__main__':
    main()
