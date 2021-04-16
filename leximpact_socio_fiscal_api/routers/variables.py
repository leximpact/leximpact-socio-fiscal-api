import json
import os

from fastapi import APIRouter, Depends

from .. import config


router = APIRouter(
    prefix="/variables",
    tags=["variables"],
    )
variables = None


def get_variables(settings: config.Settings = Depends(config.get_settings)):
    global variables
    if variables is None:
        with open(os.path.join(settings.country_json_dir, "variables.json"), encoding="utf-8") as variables_file:
            variables = json.load(variables_file)
    return variables


@router.get("/")
async def list_variables(variables = Depends(get_variables)):
    return variables
# async def list_variables(settings: config.Settings = Depends(config.get_settings)):
#     with open(os.path.join(settings.country_json_dir, "variables.json"), encoding="utf-8") as variables_file:
#         return json.load(variables_file)
