#include "immergas_modbus.h"
#include "im_device.h"
#include "im_number.h"
#include "im_binary_sensor.h"
#include "im_switch.h"
#include "im_select.h"

#include "im_climate.h"
#include "im_client.h"
#include <cmath>
#include <vector>
#include <cstring>
#include "immergas_pdus.h"

namespace esphome {
namespace immergas_modbus {

void ImmergasModbus::setup() {
	// TODO: initialise Modbus client / registers
	if (this->debug_logs_) {
		ESP_LOGD("immergas_modbus", "Setup called (language=%s)", this->language_.c_str());
	}
}

void ImmergasModbus::register_device(IM_Device *dev) {
	if (dev == nullptr) return;
	this->devices_.push_back(dev);
	dev->set_controller(this);
}


static bool crc16_calc(const uint8_t *buf, size_t len, uint16_t &out_crc) {
	uint16_t crc = 0xFFFF;
	for (size_t pos = 0; pos < len; pos++) {
		crc ^= (uint16_t)buf[pos];
		for (int i = 8; i != 0; i--) {
			if ((crc & 0x0001) != 0) {
				crc >>= 1;
				crc ^= 0xA001;
			} else
				crc >>= 1;
		}
	}
	out_crc = crc;
	return true;
}

static uint16_t parse_slave_from_address(const std::string &addr) {
	size_t pos = addr.find('.');
	try {
		if (pos != std::string::npos) {
			return static_cast<uint16_t>(std::stoi(addr.substr(0, pos)));
		}
		return static_cast<uint16_t>(std::stoi(addr));
	} catch (...) {
		return 0;
	}
}

bool ImmergasModbus::read_holding_registers(uint8_t slave_id, uint16_t reg_addr, uint16_t count, std::vector<uint16_t> &out) {
	if (this->client_ == nullptr) return false;
	uint8_t req[8];
	req[0] = slave_id;
	req[1] = 0x03;
	req[2] = (reg_addr >> 8) & 0xFF;
	req[3] = reg_addr & 0xFF;
	req[4] = (count >> 8) & 0xFF;
	req[5] = count & 0xFF;
	uint16_t crc;
	crc16_calc(req, 6, crc);
	req[6] = crc & 0xFF;
	req[7] = (crc >> 8) & 0xFF;

	this->client_->write_array(req, 8);
	this->client_->flush();

	const uint32_t timeout_ms = 300;
	uint32_t start = millis();
	std::vector<uint8_t> buf;
	while (millis() - start < timeout_ms) {
		int avail = this->client_->available();
		if (avail > 0) {
			for (int i = 0; i < avail; i++) {
				int b = this->client_->read();
				if (b >= 0) buf.push_back(static_cast<uint8_t>(b));
			}
			if (buf.size() >= static_cast<size_t>(5 + 2 * count)) break;
		}
		delay(5);
	}

	if (buf.size() < 5) return false;
	uint16_t resp_crc;
	crc16_calc(buf.data(), buf.size() - 2, resp_crc);
	uint16_t resp_crc_in = buf[buf.size() - 2] | (buf[buf.size() - 1] << 8);
	if (resp_crc != resp_crc_in) return false;
	uint8_t func = buf[1];
	if (func & 0x80) return false;
	uint8_t bytecount = buf[2];
	if (bytecount != 2 * count) return false;

	out.clear();
	for (size_t i = 0; i < count; i++) {
		size_t idx = 3 + i * 2;
		uint16_t val = (buf[idx] << 8) | buf[idx + 1];
		out.push_back(val);
	}
	return true;
}

bool ImmergasModbus::write_multiple_registers(uint8_t slave_id, uint16_t reg_addr, const std::vector<uint16_t> &values) {
	if (this->client_ == nullptr) return false;
	// function 0x10: Write Multiple Registers
	uint16_t count = static_cast<uint16_t>(values.size());
	// build header: slave, func, addr_hi, addr_lo, count_hi, count_lo, bytecount
	std::vector<uint8_t> pkt;
	pkt.push_back(slave_id);
	pkt.push_back(0x10);
	pkt.push_back((reg_addr >> 8) & 0xFF);
	pkt.push_back(reg_addr & 0xFF);
	pkt.push_back((count >> 8) & 0xFF);
	pkt.push_back(count & 0xFF);
	pkt.push_back(static_cast<uint8_t>(count * 2));
	for (uint16_t v : values) {
		pkt.push_back((v >> 8) & 0xFF);
		pkt.push_back(v & 0xFF);
	}
	uint16_t crc;
	crc16_calc(pkt.data(), pkt.size(), crc);
	pkt.push_back(crc & 0xFF);
	pkt.push_back((crc >> 8) & 0xFF);

	this->client_->write_array(pkt.data(), pkt.size());
	this->client_->flush();

	const uint32_t timeout_ms = 500;
	uint32_t start = millis();
	std::vector<uint8_t> buf;
	while (millis() - start < timeout_ms) {
		int avail = this->client_->available();
		if (avail > 0) {
			for (int i = 0; i < avail; i++) {
				int b = this->client_->read();
				if (b >= 0) buf.push_back(static_cast<uint8_t>(b));
			}
			// expected response length: 8 bytes (slave, func, addr_hi, addr_lo, count_hi, count_lo, crc_lo, crc_hi)
			if (buf.size() >= 8) break;
		}
		delay(5);
	}
	if (buf.size() < 8) return false;
	uint16_t resp_crc;
	crc16_calc(buf.data(), buf.size() - 2, resp_crc);
	uint16_t resp_crc_in = buf[buf.size() - 2] | (buf[buf.size() - 1] << 8);
	if (resp_crc != resp_crc_in) return false;
	uint8_t func = buf[1];
	if (func & 0x80) return false;
	// success if echo of addr/count
	uint16_t resp_addr = (buf[2] << 8) | buf[3];
	uint16_t resp_count = (buf[4] << 8) | buf[5];
	return resp_addr == reg_addr && resp_count == count;
}

bool ImmergasModbus::write_pdu_by_value(uint8_t slave_id, uint16_t pdu, float value) {
	// find PDU entry
	const ImmergasPduEntry *entry = nullptr;
	for (size_t i = 0; i < immergas_pdu_map_len; ++i) {
		if (immergas_pdu_map[i].pdu == pdu) { entry = &immergas_pdu_map[i]; break; }
	}
	if (entry == nullptr) return false;
	std::vector<uint16_t> vals;
	switch (entry->type) {
		case IM_PDU_TEMP: {
			// inverse scale
			float inv = (entry->scale != 0.0f) ? (1.0f / entry->scale) : 1.0f;
			int32_t iv = static_cast<int32_t>(roundf(value * inv));
			vals.push_back(static_cast<uint16_t>(iv & 0xFFFF));
			break;
		}
		case IM_PDU_U16: {
			uint16_t v = static_cast<uint16_t>(roundf(value)); vals.push_back(v); break;
		}
		case IM_PDU_S16: {
			int16_t sv = static_cast<int16_t>(roundf(value)); vals.push_back(static_cast<uint16_t>(sv)); break;
		}
		case IM_PDU_U8:
		case IM_PDU_LB_FLAG8: {
			uint16_t v = static_cast<uint16_t>(static_cast<int>(roundf(value)) & 0xFF); vals.push_back(v); break;
		}
		case IM_PDU_FLOAT32: {
			// encode IEEE754 into two registers (big-endian: high reg first)
			uint32_t u; memcpy(&u, &value, sizeof(float));
			uint16_t hi = static_cast<uint16_t>((u >> 16) & 0xFFFF);
			uint16_t lo = static_cast<uint16_t>(u & 0xFFFF);
			vals.push_back(hi); vals.push_back(lo);
			break;
		}
		case IM_PDU_U32:
		case IM_PDU_S32: {
			uint32_t u = static_cast<uint32_t>(roundf(value));
			uint16_t hi = static_cast<uint16_t>((u >> 16) & 0xFFFF);
			uint16_t lo = static_cast<uint16_t>(u & 0xFFFF);
			vals.push_back(hi); vals.push_back(lo);
			break;
		}
		default:
			// fallback to single register
			vals.push_back(static_cast<uint16_t>(roundf(value)));
	}
	return this->write_multiple_registers(slave_id, entry->reg_addr, vals);
}

// Helper to read contiguous ranges using the pdu map, batching consecutive registers
void ImmergasModbus::poll_device(uint16_t slave, IM_Device *dev) {
	size_t i = 0;
	while (i < immergas_pdu_map_len) {
		const ImmergasPduEntry &start_e = immergas_pdu_map[i];
		uint16_t batch_start = start_e.reg_addr;
		uint16_t batch_count = start_e.count;
		size_t j = i + 1;
		// merge contiguous entries
		while (j < immergas_pdu_map_len) {
			const ImmergasPduEntry &next_e = immergas_pdu_map[j];
			if (next_e.reg_addr == batch_start + batch_count) {
				batch_count += next_e.count;
				++j;
			} else break;
		}
		std::vector<uint16_t> regs;
		if (!this->read_holding_registers(static_cast<uint8_t>(slave), batch_start, batch_count, regs)) {
			if (this->debug_logs_) ESP_LOGD("immergas_modbus", "No response from slave %d for batch %d..%d", slave, batch_start, batch_start + batch_count - 1);
			i = j;
			continue;
		}
		// dispatch values back to individual PDUs
		size_t offset = 0;
		for (size_t k = i; k < j; ++k) {
			const ImmergasPduEntry &e = immergas_pdu_map[k];
			// collect registers for this entry
			std::vector<uint16_t> sub;
			for (size_t x = 0; x < e.count && (offset + x) < regs.size(); ++x) sub.push_back(regs[offset + x]);
			offset += e.count;
			float value = 0.0f;
			switch (e.type) {
				case IM_PDU_TEMP:
					if (!sub.empty()) value = static_cast<float>(sub[0]) * e.scale;
					break;
				case IM_PDU_U16:
					if (!sub.empty()) value = static_cast<float>(sub[0]);
					break;
				case IM_PDU_S16:
					if (!sub.empty()) {
						int16_t sv = static_cast<int16_t>(sub[0]);
						value = static_cast<float>(sv);
					}
					break;
				case IM_PDU_U8:
				case IM_PDU_LB_FLAG8:
					if (!sub.empty()) value = static_cast<float>(sub[0] & 0xFF);
					break;
				case IM_PDU_U32:
				case IM_PDU_S32:
				case IM_PDU_FLOAT32:
					if (sub.size() >= 2) {
						// combine registers: assume big-endian register order (reg N = high 16 bits)
						uint32_t hi = sub[0];
						uint32_t lo = sub[1];
						uint32_t comb = (hi << 16) | lo;
						if (e.type == IM_PDU_FLOAT32) {
							float f; memcpy(&f, &comb, sizeof(float)); value = f * e.scale;
						} else if (e.type == IM_PDU_S32) {
							int32_t si = static_cast<int32_t>(comb); value = static_cast<float>(si) * e.scale;
						} else {
							value = static_cast<float>(comb) * e.scale;
						}
					}
					break;
				default:
					if (!sub.empty()) value = static_cast<float>(sub[0]);
			}
			dev->handle_immergas_update(e.pdu, value);
		}
		i = j;
	}
}

void ImmergasModbus::update() {
	if (this->debug_logs_) {
		ESP_LOGD("immergas_modbus", "Update called (polling) devices=%d", this->devices_.size());
	}
	// For each registered device, iterate the generated PDU map and read each entry.
	for (auto dev : this->devices_) {
		uint16_t slave = parse_slave_from_address(dev->get_address());
		if (slave == 0) continue;
		this->poll_device(slave, dev);
	}
}

}  // namespace immergas_modbus
}  // namespace esphome

