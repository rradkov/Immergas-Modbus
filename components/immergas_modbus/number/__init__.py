import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import number
from esphome.const import CONF_MAX_VALUE, CONF_MIN_VALUE, CONF_STEP
from ..immergas.const import IM_LABEL, IM_MESSAGE, IM_MODE
from ..immergas.labels_en import immergas_labels
from ..immergas.auto_entities import numbers as auto_numbers_map
from .. import (
    IM_CONTROLLER_ID,
    IM_DEVICE_ID,
    IM_Number,
)


AUTO_LOAD = ["immergas_modbus"]
DEPENDENCIES = ["immergas_modbus"]


def validate(config):
    if IM_MESSAGE in config:
        mapped = auto_numbers_map.get(config[IM_MESSAGE]) if auto_numbers_map is not None else None
        if mapped is not None:
            config[IM_LABEL] = mapped.get(IM_LABEL, immergas_labels.get(config[IM_MESSAGE], "IM_UNKNOWN_LABEL"))
            config[IM_MODE] = mapped.get(IM_MODE, "CONTROL")
            defaults = mapped.get('defaults', {})
            if defaults.get('min') is not None:
                config[CONF_MIN_VALUE] = defaults.get('min')
            if defaults.get('max') is not None:
                config[CONF_MAX_VALUE] = defaults.get('max')
            if defaults.get('step') is not None:
                config[CONF_STEP] = defaults.get('step')
        else:
            config[IM_LABEL] = immergas_labels.get(config[IM_MESSAGE], "IM_UNKNOWN_LABEL")
    return config


CONFIG_SCHEMA = cv.All(
    cv.Schema({cv.GenerateID(): cv.declare_id(IM_Number), cv.Required(IM_MESSAGE): cv.hex_int}, extra=cv.ALLOW_EXTRA),
    validate,
    number.number_schema(IM_Number)
    .extend({
        cv.GenerateID(): cv.declare_id(IM_Number),
        cv.Required(IM_MESSAGE): cv.hex_int,
        cv.Required(CONF_MIN_VALUE): cv.float_,
        cv.Required(CONF_MAX_VALUE): cv.float_,
        cv.Required(CONF_STEP): cv.positive_float,
    })
    .extend({cv.GenerateID(IM_CONTROLLER_ID): cv.use_id, cv.GenerateID(IM_DEVICE_ID): cv.use_id})
)


async def to_code(config):
    device = await cg.get_variable(config[IM_DEVICE_ID])
    controller = await cg.get_variable(config[IM_CONTROLLER_ID])
    var_number = await number.new_number(
        config,
        config[IM_LABEL],
        config[IM_MESSAGE],
        config.get(IM_MODE, "CONTROL"),
        device,
        min_value=config[CONF_MIN_VALUE],
        max_value=config[CONF_MAX_VALUE],
        step=config[CONF_STEP]
    )
    cg.add(var_number.set_pdu(config[IM_MESSAGE]))
    cg.add(var_number.set_parent(controller))
    cg.add(controller.register_device(var_number))
