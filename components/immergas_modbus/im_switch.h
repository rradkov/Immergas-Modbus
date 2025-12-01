#pragma once
#include "esphome.h"
#include "im_device.h"

namespace esphome {
namespace immergas_modbus {

class IM_Switch : public switch_::Switch, public IM_Device {
 public:
  IM_Switch(const std::string &address) : IM_Device(address) {}
  void setup() override {}
  void loop() override {}
  void write_state(bool state) override {
    auto ctrl = this->get_controller();
    if (!ctrl) {
      ESP_LOGW("immergas_modbus", "IM_Switch: controller not set for device %s", this->get_address().c_str());
      return;
    }
    uint16_t pdu = this->get_pdu();
    if (pdu == 0) {
      ESP_LOGW("immergas_modbus", "IM_Switch: no PDU configured for device %s", this->get_address().c_str());
      return;
    }
    uint16_t slave = 0;
    try {
      std::string addr = this->get_address();
      size_t pos = addr.find('.');
      if (pos != std::string::npos) slave = static_cast<uint16_t>(std::stoi(addr.substr(0, pos)));
      else slave = static_cast<uint16_t>(std::stoi(addr));
    } catch (...) { slave = 0; }
    if (slave == 0) {
      ESP_LOGW("immergas_modbus", "IM_Switch: invalid slave address '%s'", this->get_address().c_str());
      return;
    }
    float v = state ? 1.0f : 0.0f;
    bool ok = ctrl->write_pdu_by_value(static_cast<uint8_t>(slave), pdu, v);
    if (!ok) ESP_LOGW("immergas_modbus", "IM_Switch: write failed for slave %d pdu %d", slave, pdu);
  }
  void handle_immergas_update(uint16_t pdu, float value) override { this->publish_state(value >= 1.0f); }
};

}  // namespace immergas_modbus
}  // namespace esphome
