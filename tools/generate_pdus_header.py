#!/usr/bin/env python3
"""Generate C++ header mapping PDUs from immergas_registers.json.

Output: components/immergas_modbus/immergas_pdus.h
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JSON_P = ROOT / "immergas_registers.json"
OUT_P = ROOT / "components" / "immergas_modbus" / "immergas_pdus.h"

TYPE_UNKNOWN = 0
TYPE_U16 = 1
TYPE_S16 = 2
TYPE_U8 = 3
TYPE_TEMP = 4
TYPE_LB_FLAG8 = 5

def detect_type(view):
    ret = view.get("return")
    if not ret:
        return TYPE_UNKNOWN, 1, 1.0
    if isinstance(ret, list):
        t0 = ret[0]
        if t0 == "u16":
            return TYPE_U16, 1, 1.0
        if t0 == "s16":
            return TYPE_S16, 1, 1.0
        if t0 == "u8":
            return TYPE_U8, 1, 1.0
        if t0 == "temp":
            # check decimal
            dec = view.get("decimal", None)
            scale = 1.0
            if isinstance(dec, int) and dec > 0:
                scale = 10 ** (-dec)
            return TYPE_TEMP, 1, scale
        if t0 == "LB":
            # LB flag types are usually byte flags
            return TYPE_LB_FLAG8, 1, 1.0
    # fallback
    return TYPE_UNKNOWN, 1, 1.0

def main():
    data = json.loads(JSON_P.read_text())
    pdus = data.get("pdus", [])

    entries = []
    for p in pdus:
        pdu = p.get("pdu")
        views = p.get("views", [])
        # choose first view that has a return
        found = None
        for v in views:
            if v.get("return"):
                found = v
                break
        if found is None and views:
            found = views[0]
        if found is None:
            # still include as unknown
            t, cnt, scale = TYPE_UNKNOWN, 1, 1.0
        else:
            t, cnt, scale = detect_type(found)

        messages = p.get("messages", [])
        writable = any(m.get("action") == "write" for m in messages)

        entries.append({
            "pdu": int(pdu),
            "reg": int(pdu),
            "count": int(cnt),
            "type": int(t),
            "scale": float(scale),
            "writable": bool(writable),
        })

    # sort by reg
    entries.sort(key=lambda x: x["reg"])

    header = []
    header.append("#pragma once")
    header.append("#include <cstdint>")
    header.append("namespace esphome { namespace immergas_modbus {")
    header.append("enum ImmergasPduType : uint8_t { IM_PDU_UNKNOWN=0, IM_PDU_U16=1, IM_PDU_S16=2, IM_PDU_U8=3, IM_PDU_TEMP=4, IM_PDU_LB_FLAG8=5, IM_PDU_U32=6, IM_PDU_S32=7, IM_PDU_FLOAT32=8 };\n")
    header.append("struct ImmergasPduEntry { uint16_t pdu; uint16_t reg_addr; uint8_t count; uint8_t type; float scale; bool writable; const char *label; };\n")

    header.append(f"static const ImmergasPduEntry immergas_pdu_map[] = {{")
    for e in entries:
        # try to include a label if available in the source (we have no label here, use empty)
        label = '""'
        header.append("    { %d, %d, %d, %d, %ff, %s, %s }," % (e["pdu"], e["reg"], e["count"], e["type"], e["scale"], "true" if e["writable"] else "false", label))
    header.append("};")
    header.append(f"static const size_t immergas_pdu_map_len = sizeof(immergas_pdu_map)/sizeof(immergas_pdu_map[0]);")
    header.append("}} // namespace esphome::immergas_modbus")

    OUT_P.parent.mkdir(parents=True, exist_ok=True)
    OUT_P.write_text("\n".join(header))
    print(f"Wrote {OUT_P}")

if __name__ == '__main__':
    main()
