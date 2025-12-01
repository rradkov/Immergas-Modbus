#pragma once
#include "esphome.h"
#include "im_device.h"

namespace esphome {
namespace immergas_modbus {

class IM_Climate : public climate::Climate, public IM_Device {
 public:
  IM_Climate(const std::string &address) : IM_Device(address) {}
  void setup() override {}
  void loop() override {}
  void control(const climate::ClimateCall &call) override {}
  void handle_immergas_update(uint16_t pdu, float value) override { this->publish_state(value); }
};

}  // namespace immergas_modbus
}  // namespace esphome
