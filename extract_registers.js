const fs = require('fs');
const path = require('path');

const cfgPath = path.resolve(__dirname, '..', 'dominus', 'CFG-WFC01_IM_MBUS.json');
const lblPath = path.resolve(__dirname, '..', 'dominus', 'LBL-WFC01_IM_MBUS.json');

function safeReadJson(p) {
  try {
    return JSON.parse(fs.readFileSync(p, 'utf8'));
  } catch (e) {
    console.error('Failed to read/parse', p, e.message);
    process.exit(1);
  }
}

const cfg = safeReadJson(cfgPath);
const lbl = safeReadJson(lblPath);

const pdus = new Map();

function addPdu(pdu, entry) {
  if (!pdu && pdu !== 0) return;
  if (!pdus.has(pdu)) pdus.set(pdu, { pdu: pdu, views: [], commands: [], messages: [] });
  const rec = pdus.get(pdu);
  if (entry.view) rec.views.push(entry.view);
  if (entry.command) rec.commands.push(entry.command);
  if (entry.message) rec.messages.push(entry.message);
}

function scanObject(obj) {
  if (!obj || typeof obj !== 'object') return;
  if (Array.isArray(obj)) return obj.forEach(scanObject);
  // Recognize common structures
  if ('pdu' in obj) {
    const p = obj.pdu;
    if (obj.view) addPdu(p, { view: obj.view });
    if (obj.action && obj.action === 'write' && obj.view) addPdu(p, { command: obj.view });
    if (obj.item && obj.data) addPdu(p, { command: { item: obj.item, data: obj.data } });
    if (obj.action && (obj.action === 'read' || obj.action === 'write')) addPdu(p, { message: { action: obj.action } });
  }
  // Recurse
  Object.keys(obj).forEach(k => scanObject(obj[k]));
}

scanObject(cfg);

// Basic flattening + derive return types from view entries
const out = [];
for (const [k, v] of pdus.entries()) {
  const entry = { pdu: k, views: [], commands: [], messages: [] };
  v.views.forEach(viewA => {
    if (Array.isArray(viewA)) viewA.forEach(vv => entry.views.push(vv));
    else entry.views.push(viewA);
  });
  v.commands.forEach(ca => {
    if (Array.isArray(ca)) ca.forEach(cc => entry.commands.push(cc));
    else entry.commands.push(ca);
  });
  v.messages.forEach(m => entry.messages.push(m));
  // dedupe arrays
  entry.views = entry.views.filter((x, i, a) => i === a.findIndex(y => JSON.stringify(y) === JSON.stringify(x)));
  entry.commands = entry.commands.filter((x, i, a) => i === a.findIndex(y => JSON.stringify(y) === JSON.stringify(x)));
  entry.messages = entry.messages.filter((x, i, a) => i === a.findIndex(y => JSON.stringify(y) === JSON.stringify(x)));
  out.push(entry);
}

// Also include labels (a subset) to help mapping later
const result = {
  generated_at: (new Date()).toISOString(),
  source_cfg: cfgPath,
  source_lbl: lblPath,
  pdus: out,
  lbl_summary: {
    anomalies_count: Array.isArray(lbl.anomalies) ? lbl.anomalies.length : 0
  }
};

const outPath = path.resolve(__dirname, 'immergas_registers.json');
fs.writeFileSync(outPath, JSON.stringify(result, null, 2), 'utf8');
console.log('Wrote', outPath, ' - PDUs found:', out.pdu ? out.pdu.length : out.length);
