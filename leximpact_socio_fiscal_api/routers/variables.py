from fastapi import APIRouter, Depends

from ..parameters import get_parameters
from ..variables import get_variables, iter_variable_input_variables, iter_variable_parameters


router = APIRouter(
    prefix="/variables",
    tags=["variables"],
    )


@router.get("/")
async def list_variables(variables = Depends(get_variables)):
    return variables


@router.get("/{name}")
async def get_variable(name: str, variables = Depends(get_variables)):
    return variables.get(name)


@router.get("/{name}/inputs/{date}")
async def get_input_variables(name: str, date: str, variables = Depends(get_variables)):
    variable = variables.get(name)
    if variable is None:
        return None
    return [
        input_variable
        for input_variable in iter_variable_input_variables(variable, date)
        ]


@router.get("/{name}/parameters/{date}")
async def get_parameters(name: str, date: str, parameters = Depends(get_parameters), variables = Depends(get_variables)):
    variable = variables.get(name)
    if variable is None:
        return None
    return [
        parameter
        for parameter in iter_variable_parameters(variable, date)
        ]
