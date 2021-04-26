from fastapi import APIRouter, Depends

from ..parameters import get_parameter_with_ancestors, get_parameters


router = APIRouter(
    prefix="/parameters",
    tags=["parameters"],
    )


@router.get("/")
async def list_parameters(parameters = Depends(get_parameters)):
    return parameters


@router.get("/{name}")
async def get_parameter(name: str, parameters = Depends(get_parameters)):
    parameter, ancestors = get_parameter_with_ancestors(name)
    if parameter is None:
        # TODO: Return not found.
        return None

    # Remove children from ancestors, because we don't want to send the full tree.
    ancestors = [
        ancestor.copy()
        for ancestor in ancestors
        ]
    for ancestor in ancestors:
        ancestor.pop("children", None)

    return dict(ancestors = ancestors, parameter = parameter)
