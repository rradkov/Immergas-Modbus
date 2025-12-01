#pragma once
#include "esphome.h"
#include "im_device.h"

namespace esphome {
namespace immergas_modbus {

class IM_BinarySensor : public binary_sensor::BinarySensor, public IM_Device {
 public:
  IM_BinarySensor(const std::string &address) : IM_Device(address) {}
  void setup() override {}
  void loop() override {}
  void handle_immergas_update(uint16_t pdu, float value) override { this->publish_state(value >= 1.0f); }
};

}  // namespace immergas_modbus
}  // namespace esphome
