import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import binary_sensor
from ..immergas.const import IM_LABEL, IM_MESSAGE, IM_MODE
from ..immergas.labels_en import immergas_labels
from ..immergas.auto_entities import binary_sensors as auto_binary_map
from .. import (
    IM_CONTROLLER_ID,
    IM_DEVICE_ID,
    IM_BinarySensor,
)


AUTO_LOAD = ["immergas_modbus"]
DEPENDENCIES = ["immergas_modbus"]


def validate(config):
    if IM_MESSAGE in config:
        mapped = auto_binary_map.get(config[IM_MESSAGE]) if auto_binary_map is not None else None
        if mapped is not None:
            config[IM_LABEL] = mapped.get(IM_LABEL, immergas_labels.get(config[IM_MESSAGE], "IM_UNKNOWN_LABEL"))
            config[IM_MODE] = mapped.get(IM_MODE, "STATUS")
    return config


CONFIG_SCHEMA = cv.All(
    cv.Schema({cv.GenerateID(): cv.declare_id(IM_BinarySensor), cv.Required(IM_MESSAGE): cv.hex_int}, extra=cv.ALLOW_EXTRA),
    validate,
    binary_sensor.binary_sensor_schema(IM_BinarySensor)
    .extend({
        cv.GenerateID(): cv.declare_id(IM_BinarySensor),
        cv.Required(IM_MESSAGE): cv.hex_int,
    })
    .extend({cv.GenerateID(IM_CONTROLLER_ID): cv.use_id, cv.GenerateID(IM_DEVICE_ID): cv.use_id})
)


async def to_code(config):
    device = await cg.get_variable(config[IM_DEVICE_ID])
    controller = await cg.get_variable(config[IM_CONTROLLER_ID])
    var_bin = await binary_sensor.new_binary_sensor(
        config,
        config[IM_LABEL],
        config[IM_MESSAGE],
        config.get(IM_MODE, "STATUS"),
        device,
    )
    cg.add(var_bin.set_parent(controller))
    cg.add(controller.register_device(var_bin))
