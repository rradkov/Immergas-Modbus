"""
ESPHome integration for the Immergas Modbus custom component.

This module mirrors the structure used in `esphome-samsung-nasa`:
- provides a controller/client schema
- exposes a `language` option (e.g. `en`, `it`) which can be used
  to select label translations for sensors and other entities
- registers declared devices

Notes:
- Label mapping files for each language live under
  `components/immergas_modbus/immergas/labels_<lang>.py`. A minimal
  English and Italian file are included; the full mapping should be
  generated from the Dominus label JSON and placed here for production.
"""

import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import uart
from esphome import pins
from esphome.cpp_helpers import gpio_pin_expression
from esphome.const import CONF_ID, CONF_FLOW_CONTROL_PIN
from esphome.components import number, select, sensor as esph_sensor, binary_sensor as esph_binary, switch as esph_switch, climate as esph_climate

MULTI_CONF = False
CODEOWNERS = ["You"]
DEPENDENCIES = ["uart"]


immergas_ns = cg.esphome_ns.namespace("immergas_modbus")

# Controller / client / device classes (C++ implementations live under
# the `immergas_modbus` C++ namespace and match these names)
IM_Controller = immergas_ns.class_("ImmergasModbus", cg.PollingComponent)
IM_Client = immergas_ns.class_("IM_Client")
IM_Device = immergas_ns.class_("IM_Device")

# Platform-specific device classes (C++ side should implement these)
IM_Number = immergas_ns.class_("IM_Number", number.Number, IM_Device)
IM_Select = immergas_ns.class_("IM_Select", select.Select, IM_Device)
IM_Sensor = immergas_ns.class_("IM_Sensor", esph_sensor.Sensor, IM_Device)
IM_BinarySensor = immergas_ns.class_("IM_BinarySensor", esph_binary.BinarySensor, IM_Device)
IM_Switch = immergas_ns.class_("IM_Switch", esph_switch.Switch, IM_Device)
IM_Climate = immergas_ns.class_("IM_Climate", esph_climate.Climate, cg.Component)

IM_CONTROLLER_ID = "im_controller_id"
IM_CLIENT_ID = "im_client_id"
IM_DEVICES = "devices"
IM_DEVICE_ID = "im_device_id"
IM_DEVICE_ADDRESS = "address"
IM_DEBUG_LOG_MESSAGES = "debug_log_messages"
IM_LANGUAGE = "language"


def device_validator(config):
	# For now accept any string address; future: validate Modbus address
	if IM_DEVICE_ADDRESS not in config:
		raise cv.Invalid("Device must declare an 'address' string")
	return config


device_schema = cv.All(
	cv.Schema({cv.GenerateID(): cv.declare_id(IM_Device), cv.Required(IM_DEVICE_ADDRESS): cv.string_strict}),
	device_validator,
)

client_schema = cv.Schema(
	{
		cv.GenerateID(IM_CLIENT_ID): cv.declare_id(IM_Client),
		cv.Optional(CONF_FLOW_CONTROL_PIN): pins.gpio_output_pin_schema,
	}
)


CONFIG_SCHEMA = cv.Schema(
	{
		cv.GenerateID(IM_CONTROLLER_ID): cv.declare_id(IM_Controller),
		cv.Required("client"): client_schema,
		cv.Optional(IM_DEBUG_LOG_MESSAGES, default=False): cv.boolean,
		cv.Optional(IM_LANGUAGE, default="en"): cv.one_of("en", "it", "fr", "de", "es"),
		cv.Required(IM_DEVICES): cv.ensure_list(device_schema),
	}
).extend(uart.UART_DEVICE_SCHEMA).extend(cv.polling_component_schema("30s"))


async def to_code(config):
	conf_client = config["client"]
	client_var = cg.new_Pvariable(conf_client[IM_CLIENT_ID])
	if (conf_pin := conf_client.get(CONF_FLOW_CONTROL_PIN)) is not None:
		pin = await gpio_pin_expression(conf_pin)
		cg.add(client_var.set_flow_control_pin(pin))

	controller = cg.new_Pvariable(config[IM_CONTROLLER_ID], client_var)
	cg.add(controller.set_debug_log_messages(config[IM_DEBUG_LOG_MESSAGES]))
	# pass selected language to C++ component (no-op if not used yet)
	cg.add(controller.set_language(config[IM_LANGUAGE]))

	for device in config[IM_DEVICES]:
		var_device = cg.new_Pvariable(device[CONF_ID], device[IM_DEVICE_ADDRESS])
		cg.add(controller.register_device(var_device))

	await cg.register_component(controller, config)
	await cg.register_component(client_var, conf_client)
	await uart.register_uart_device(client_var, config)
