#pragma once
#include "esphome.h"
#include "im_device.h"

namespace esphome {
namespace immergas_modbus {

class IM_Select : public select::Select, public IM_Device {
 public:
  IM_Select(const std::string &address) : IM_Device(address) {}
  void setup() override {}
  void loop() override {}
  void control(select::SelectOptions value) override {
    auto ctrl = this->get_controller();
    if (!ctrl) {
      ESP_LOGW("immergas_modbus", "IM_Select: controller not set for device %s", this->get_address().c_str());
      return;
    }
    uint16_t pdu = this->get_pdu();
    if (pdu == 0) {
      ESP_LOGW("immergas_modbus", "IM_Select: no PDU configured for device %s", this->get_address().c_str());
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
      ESP_LOGW("immergas_modbus", "IM_Select: invalid slave address '%s'", this->get_address().c_str());
      return;
    }
    // Convert selection options to integer index (best-effort)
    float v = static_cast<float>(this->get_index_of_option(value));
    bool ok = ctrl->write_pdu_by_value(static_cast<uint8_t>(slave), pdu, v);
    if (!ok) ESP_LOGW("immergas_modbus", "IM_Select: write failed for slave %d pdu %d", slave, pdu);
  }
  void handle_immergas_update(uint16_t pdu, float value) override {}
};

}  // namespace immergas_modbus
}  // namespace esphome
