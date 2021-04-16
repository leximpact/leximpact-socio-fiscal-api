import asyncio

from fastapi import APIRouter, Depends, WebSocket
import numpy as np
from openfisca_core.scripts import build_tax_benefit_system
from openfisca_core.simulation_builder import SimulationBuilder
from openfisca_core.taxbenefitsystems import TaxBenefitSystem

from .. import config


router = APIRouter(
    prefix="/simulations",
    tags=["simulations"],
    )
tax_benefit_system = None


def get_tax_benefit_system(settings: config.Settings = Depends(config.get_settings)):
    global tax_benefit_system
    if tax_benefit_system is None:
        tax_benefit_system = build_tax_benefit_system(
            settings.country_package,
            None,  # settings.extension,
            None,  # settings.reform,
            )
    return tax_benefit_system


# Note: Router prefix is not used for websocket‽
@router.websocket("/simulations/calculate")
async def calculate(websocket: WebSocket, tax_benefit_system: TaxBenefitSystem = Depends(get_tax_benefit_system)):
    await websocket.accept()
    decomposition = None
    period = None
    simulation = None
    situation = None
    while True:
        data = await websocket.receive_json()
        calculate = False
        for key, value in data.items():
            if key == "calculate":
                calculate = True
            if key == "decomposition":
                print("Received decomposition.")
                decomposition = value
                continue
            if key == "period":
                print("Received period.")
                period = value
                continue
            if key == "situation":
                print("Received situation.")
                situation = value
                simulation_builder = SimulationBuilder()
                simulation = simulation_builder.build_from_entities(tax_benefit_system, situation)
                continue

        if calculate:
            print("Calculating…")

            errors = {}
            if decomposition is None:
                errors["decomposition"] = "Missing value"
            if period is None:
                errors["period"] = "Missing value"
            if situation is None or simulation is None:
                errors["situation"] = "Missing value"
            if len(errors) > 0:
                await websocket.send_json(dict(errors=errors))
                continue

            for node in walDecompositionLeafs(decomposition):
                value = simulation.calculate_add(node["code"], period)
                population = simulation.get_variable_population(node["code"])
                entity_count = simulation_builder.entity_counts[population.entity.plural]
                if entity_count > 1:
                    value = np.sum(np.split(value, simulation.get_variable_population(node["code"]).count // entity_count), 1)
                print(f"Calculated {node['code']}: {value}")
                await websocket.send_json(dict(code=node["code"], value=value.tolist()))
                await asyncio.sleep(0)


def walDecompositionLeafs(node):
    children = node.get("children")
    if children:
        for child in children:
            yield from walDecompositionLeafs(child)
        # Note: Ignore nodes that are the total of their children.
    else:
        yield node
