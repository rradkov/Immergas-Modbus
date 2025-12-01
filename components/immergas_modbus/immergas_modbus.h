#pragma once

#include "esphome.h"
#include <vector>
#include <string>

namespace esphome {
namespace immergas_modbus {

class IM_Device;

class ImmergasModbus : public PollingComponent {
 public:
  // Polling interval will be set by the integration code
  ImmergasModbus() : PollingComponent(15000), client_(nullptr) {}
  ImmergasModbus(IM_Client *client) : PollingComponent(15000), client_(client) {}

  void setup() override;
  void update() override;

  void set_debug_log_messages(bool v) { this->debug_logs_ = v; }
  void set_language(const std::string &lang) { this->language_ = lang; }
  void register_device(IM_Device *dev);

  // Low-level Modbus RTU read: read `count` holding registers at `reg_addr`
  // Returns true on success and fills `out` with register values.
  bool read_holding_registers(uint8_t slave_id, uint16_t reg_addr, uint16_t count, std::vector<uint16_t> &out);
  // Write multiple registers helper (function 0x10)
  bool write_multiple_registers(uint8_t slave_id, uint16_t reg_addr, const std::vector<uint16_t> &values);
  // Encode and write a PDU by pdu id, converting the float `value` according to the mapped type/scale
  bool write_pdu_by_value(uint8_t slave_id, uint16_t pdu, float value);

 private:
  bool debug_logs_{false};
  std::string language_{"en"};
  std::vector<IM_Device *> devices_;
  IM_Client *client_;
};

}  // namespace immergas_modbus
}  // namespace esphome
