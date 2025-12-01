#pragma once
#include "esphome.h"
#include "im_device.h"

namespace esphome {
namespace immergas_modbus {

class IM_Number : public number::Number, public IM_Device {
 public:
  IM_Number(const std::string &address) : IM_Device(address) {}
  void setup() override {}
  void loop() override {}
  void control(float value) override {
    auto ctrl = this->get_controller();
    if (!ctrl) {
      ESP_LOGW("immergas_modbus", "IM_Number: controller not set for device %s", this->get_address().c_str());
      return;
    }
    uint16_t pdu = this->get_pdu();
    if (pdu == 0) {
      ESP_LOGW("immergas_modbus", "IM_Number: no PDU configured for device %s", this->get_address().c_str());
      return;
    }
    uint16_t slave = this->parse_slave();
    if (slave == 0) {
      ESP_LOGW("immergas_modbus", "IM_Number: invalid slave address '%s'", this->get_address().c_str());
      return;
    }
    bool ok = ctrl->write_pdu_by_value(static_cast<uint8_t>(slave), pdu, value);
    if (!ok) ESP_LOGW("immergas_modbus", "IM_Number: write failed for slave %d pdu %d", slave, pdu);
    this->publish_state(value);
  }
  void handle_immergas_update(uint16_t pdu, float value) override { this->publish_state(value); }
};

}  // namespace immergas_modbus
}  // namespace esphome
