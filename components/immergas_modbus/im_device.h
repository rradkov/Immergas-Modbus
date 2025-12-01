#pragma once

#include "esphome.h"

namespace esphome {
namespace immergas_modbus {

class IM_Device : public Component {
 public:
  IM_Device(const std::string &address) : address_(address) {}
  virtual ~IM_Device() = default;

  virtual void setup() override {}
  virtual void loop() override {}

  // Called by the controller when a PDU value is available. Implementations
  // should publish the value to their underlying entity (sensor/number/etc).
  virtual void handle_immergas_update(uint16_t pdu, float value) {}

  const std::string &get_address() const { return this->address_; }

  void set_pdu(uint16_t pdu) { this->pdu_ = pdu; }
  uint16_t get_pdu() const { return this->pdu_; }

  // Controller pointer (set by the controller on registration)
  void set_controller(class ImmergasModbus *ctrl) { this->controller_ = ctrl; }
  class ImmergasModbus *get_controller() const { return this->controller_; }

  // Controller pointer (set by the controller on registration)
  void set_controller(class ImmergasModbus *ctrl) { this->controller_ = ctrl; }
  class ImmergasModbus *get_controller() const { return this->controller_; }

 protected:
  std::string address_;
  uint16_t pdu_{0};
  class ImmergasModbus *controller_{nullptr};
};

}  // namespace immergas_modbus
}  // namespace esphome
