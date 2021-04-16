from fastapi import APIRouter, Depends

from ..parameters import get_parameter as get_parameter_func, get_parameters


router = APIRouter(
    prefix="/parameters",
    tags=["parameters"],
    )


@router.get("/")
async def list_parameters(parameters = Depends(get_parameters)):
    return parameters


@router.get("/{name}")
async def get_parameter(name: str, parameters = Depends(get_parameters)):
    parameter = get_parameter_func(name)
    if parameter is None:
        return None
    return parameter
