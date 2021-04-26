import json
import os

from fastapi import Depends

from . import config


parameters = None


def get_parameter(name: str):
    parameter = parameters
    for id in name.split("."):
        children = parameter.get("children")
        if children is None:
            return None
        parameter = children.get(id)
        if parameter is None:
            return None
    return parameter


def get_parameter_with_ancestors(name: str):
    ancestors = []
    parameter = parameters
    for id in name.split("."):
        if parameter["name"]:
            ancestors.append(parameter)
        children = parameter.get("children")
        if children is None:
            return None, ancestors
        parameter = children.get(id)
        if parameter is None:
            return None, ancestors
    return parameter, ancestors


def get_parameters(settings: config.Settings = Depends(config.get_settings)):
    global parameters
    if parameters is None:
        with open(os.path.join(settings.country_json_dir, "parameters.json"), encoding="utf-8") as parameters_file:
            parameters = json.load(parameters_file)
    return parameters
