#pragma once

#include "esphome.h"
#include "esphome/components/uart/uart.h"

namespace esphome {
namespace immergas_modbus {

class IM_Client : public uart::UARTDevice, public Component {
 public:
  IM_Client() : uart::UARTDevice(nullptr) {}
  void setup() override {}
  void loop() override {}

  void set_flow_control_pin(const gpio::GPIOPin &pin) { this->flow_control_pin_ = pin; }

 private:
  gpio::GPIOPin flow_control_pin_{};
};

}  // namespace immergas_modbus
}  // namespace esphome
