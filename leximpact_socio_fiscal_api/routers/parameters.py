import json
import os

from fastapi import APIRouter, Depends

from .. import config


parameters = None
router = APIRouter(
    prefix="/parameters",
    tags=["parameters"],
    )


def get_parameters(settings: config.Settings = Depends(config.get_settings)):
    global parameters
    if parameters is None:
        with open(os.path.join(settings.country_json_dir, "parameters.json"), encoding="utf-8") as parameters_file:
            parameters = json.load(parameters_file)
    return parameters


@router.get("/")
async def list_parameters(parameters = Depends(get_parameters)):
    return parameters
