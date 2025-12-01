import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import sensor
from esphome.const import CONF_DEFAULTS, CONF_FILTERS
from ..immergas.const import IM_LABEL, IM_MESSAGE, IM_MODE
from ..immergas.labels_en import immergas_labels
try:
    from ..immergas.auto_entities import sensors as auto_sensors_map
except Exception:
    auto_sensors_map = None
from .. import (
    IM_CONTROLLER_ID,
    IM_DEVICE_ID,
)


AUTO_LOAD = ["immergas_modbus"]
DEPENDENCIES = ["immergas_modbus"]


def validate(config):
    if IM_MESSAGE in config:
        # If a generated sensors map exists, prefer its defaults (label, mode, defaults)
        if auto_sensors_map and (mapped := auto_sensors_map.get(config[IM_MESSAGE])) is not None:
            config[IM_LABEL] = mapped.get(IM_LABEL, immergas_labels.get(config[IM_MESSAGE], "IM_UNKNOWN_LABEL"))
            if mapped.get(IM_MODE) is not None:
                config[IM_MODE] = mapped.get(IM_MODE)
            # apply any default keys provided by the mapper
            for key, value in mapped.get("defaults", {}).items():
                config.setdefault(key, value)
            cv._LOGGER.log(cv.logging.INFO, f"Auto configured Immergas message {config[IM_MESSAGE]} from auto_entities map")
        else:
            label = immergas_labels.get(config[IM_MESSAGE], "IM_UNKNOWN_LABEL")
            config[IM_LABEL] = label
            cv._LOGGER.log(cv.logging.INFO, f"Auto configured Immergas message {config[IM_MESSAGE]} as sensor")
    return config


n_schema = cv.All(
    cv.Schema({cv.Required(IM_MESSAGE): cv.hex_int}, extra=cv.ALLOW_EXTRA),
    validate,
)

CONFIG_SCHEMA = cv.All(
    n_schema,
    sensor.sensor_schema(cg.Component)
    .extend({
        cv.GenerateID(): cv.declare_id(cg.Component),
        cv.Required(IM_MESSAGE): cv.hex_int,
        cv.Optional(CONF_FILTERS): sensor.validate_filters,
    })
    .extend({cv.GenerateID(IM_CONTROLLER_ID): cv.use_id}),
)


async def to_code(config):
    controller = await cg.get_variable(config[IM_CONTROLLER_ID])
    var = await sensor.new_sensor(config, config[IM_LABEL], config[IM_MESSAGE], config.get(IM_MODE, "STATUS"), controller)
    cg.add(var.set_parent(controller))
    cg.add(controller.register_component(var))
