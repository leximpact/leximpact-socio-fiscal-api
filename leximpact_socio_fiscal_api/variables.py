import json
import os

from fastapi import Depends

from . import config
from .parameters import get_parameter


variables = None


def get_variables(settings: config.Settings = Depends(config.get_settings)):
    global variables
    if variables is None:
        with open(os.path.join(settings.country_json_dir, "variables.json"), encoding="utf-8") as variables_file:
            variables = json.load(variables_file)
    return variables


def iter_variable_input_variables(variable, date, encountered_variables_name = None):
    if encountered_variables_name is None:
        encountered_variables_name = set()

    name = variable["name"]
    if name in encountered_variables_name:
        return
    encountered_variables_name.add(name)

    formulas = variable.get("formulas")
    if formulas is None:
        # Variable is an input variable.
        yield variable
        return
    dates = sorted(formulas.keys(), reverse = True)
    for best_date in dates:
        if best_date <= date:
            break
    else:
        # No candidate date less than or equal to date found.
        return
    formula = formulas[best_date]
    if formula is None:
        return
    referred_variables_name = formula.get("variables")
    if referred_variables_name is None:
        return
    for referred_variable_name in referred_variables_name:
        referred_variable = variables[referred_variable_name]
        yield from iter_variable_input_variables(referred_variable, date, encountered_variables_name)


def iter_variable_parameters(variable, date, encountered_parameters_name = None, encountered_variables_name = None):
    if encountered_parameters_name is None:
        encountered_parameters_name = set()
    if encountered_variables_name is None:
        encountered_variables_name = set()

    name = variable["name"]
    if name in encountered_variables_name:
        return
    encountered_variables_name.add(name)

    formulas = variable.get("formulas")
    if formulas is None:
        return
    dates = sorted(formulas.keys(), reverse = True)
    for best_date in dates:
        if best_date <= date:
            break
    else:
        # No candidate date less than or equal to date found.
        return
    formula = formulas[best_date]
    if formula is None:
        return

    referred_variables_name = formula.get("variables")
    if referred_variables_name is not None:
        for referred_variable_name in referred_variables_name:
            referred_variable = variables[referred_variable_name]
            yield from iter_variable_parameters(referred_variable, date, encountered_parameters_name, encountered_variables_name)

    referred_parameters_name = formula.get("parameters")
    if referred_parameters_name is not None:
        for referred_parameter_name in referred_parameters_name:
            if referred_parameter_name in encountered_parameters_name:
                continue
            encountered_parameters_name.add(referred_parameter_name)
            referred_parameter = get_parameter(referred_parameter_name)
            if referred_parameter is None:
                continue
            yield referred_parameter
