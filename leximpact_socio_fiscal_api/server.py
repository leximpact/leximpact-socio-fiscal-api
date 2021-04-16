import asyncio

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
from openfisca_core import periods
from openfisca_core.parameters import Bracket, Parameter, ParameterAtInstant, ParameterNode, Scale
from openfisca_core.simulation_builder import SimulationBuilder
from openfisca_france import FranceTaxBenefitSystem
from openfisca_web_api.loader.parameters import build_api_scale, build_source_url

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # Can't be True when allow_origins is set to ["*"].
    allow_methods=["*"],
    allow_headers=["*"],
    )

tax_benefit_system = FranceTaxBenefitSystem()
package_metadata = tax_benefit_system.get_package_metadata()


def export_parameter(parameter):
    export = {}
    if isinstance(parameter, Parameter):
        export["class"] = "Parameter"
        for key, value in parameter.__dict__.items():
            if key in ("description", "documentation"):
                if value is not None:
                    assert isinstance(value, str)
                    export[key] = value
            elif key == "file_path":
                if value is not None:
                    assert isinstance(value, str)
                    export["source"] = build_source_url(value, package_metadata)
            elif key == "metadata":
                metadata = export_parameter_metadata(parameter, value)
                if metadata is not None:
                    export.update(metadata)
            elif key == "name":
                assert isinstance(value, str)
                export[key] = value
            elif key == "reference":
                assert (
                    isinstance(value, str)
                    or isinstance(value, list) and all(
                        isinstance(item_value, str)
                        for item_value in value
                        )
                    or isinstance(value, dict) and all(
                        periods.INSTANT_PATTERN.match(item_key) and isinstance(item_value, str)
                        for item_key, item_value in value.items()
                        )
                    ), value
                export[key] = value
            elif key == "values_history":
                assert value == parameter
            elif key == "values_list":
                assert (
                    isinstance(value, list)
                    and all(isinstance(item_value, ParameterAtInstant) for item_value in value)
                    )
                export["values"] = [
                    export_parameter_at_instant(item_value)
                    for item_value in value
                    ]
            else:
                print("Parameter - Unhandled key:", key, "at:", parameter.file_path)
    elif isinstance(parameter, ParameterNode):
        export["class"] = "Node"
        for key, value in parameter.__dict__.items():
            if key == "children":
                assert isinstance(value, dict)
                export[key] = {
                    child_key: export_parameter(child_parameter)
                    for child_key, child_parameter in value.items()
                    }
            elif key in ("description", "documentation"):
                if value is not None:
                    assert isinstance(value, str)
                    export[key] = value
            elif key == "file_path":
                if value is not None:
                    assert isinstance(value, str)
                    export["source"] = build_source_url(value, package_metadata)
            elif key == "metadata":
                metadata = export_parameter_metadata(parameter, value)
                if metadata is not None:
                    export.update(metadata)
            elif key == "name":
                assert isinstance(value, str)
                export[key] = value
            elif key in parameter.children:
                continue
            else:
                print("ParameterNode - Unhandled key:", key, "at:", parameter.file_path)
    elif isinstance(parameter, Scale):
        export["class"] = "Scale"
        for key, value in parameter.__dict__.items():
            if key == "brackets":
                assert (
                    isinstance(value, list)
                    and len(value) > 0
                    and all(
                        isinstance(item_value, Bracket)
                        for item_value in value
                        )
                    ), value
                if "rate" in value[0].children:
                    scale = build_api_scale(parameter, "rate")
                    export["type"] = "marginal_rate"
                else:
                    assert "amount" in value[0].children
                    scale = build_api_scale(parameter, "amount")
                    export["type"] = "single_amount"
                assert (
                    isinstance(scale, dict)
                    and all(
                        periods.INSTANT_PATTERN.match(instant)
                        for instant in scale.keys()
                        )
                    and all(
                        item_value is None
                        or (
                            isinstance(item_value, dict)
                            and all(
                                isinstance(threshold, (float, int))
                                for threshold in item_value.keys()
                                )
                            and all(
                                scale_value is None or isinstance(scale_value, (float, int))
                                for scale_value in item_value.values()
                                )
                            )
                        for item_value in scale.values()
                        )
                    ), scale
                export[key] = scale
            elif key in ("description", "documentation"):
                if value is not None:
                    assert isinstance(value, str)
                    export[key] = value
            elif key == "file_path":
                if value is not None:
                    assert isinstance(value, str)
                    export["source"] = build_source_url(value, package_metadata)
            elif key == "metadata":
                metadata = export_parameter_metadata(parameter, value)
                if metadata is not None:
                    export.update(metadata)
            elif key == "name":
                assert isinstance(value, str)
                export[key] = value
            else:
                print("Scale - Unhandled key:", key, "at:", parameter.file_path)
    else:
        print("Unkwnown class of parameter:", parameter.__class__.__name__)
    return export


def export_parameter_at_instant(parameter_at_instant):
    assert isinstance(parameter_at_instant, ParameterAtInstant)
    export = {}
    for key, value in parameter_at_instant.__dict__.items():
        if key == "file_path":
            if value is not None:
                assert isinstance(value, str)
                export["source"] = build_source_url(value, package_metadata)
        elif key == "instant_str":
            assert isinstance(value, str)
            export["instant"] = value
        elif key == "metadata":
            metadata = export_parameter_metadata(parameter_at_instant, value)
            if metadata is not None:
                export.update(metadata)
        elif key == "name":
            assert isinstance(value, str)
            export[key] = value
        elif key == "value":
            assert (
                value is None
                or isinstance(value, (float, int, str))
                or isinstance(value, list) and all(
                    isinstance(item_value, str)
                    for item_value in value
                    )
                ), value
            export[key] = value
        else:
            print("ParameterAtInstant - Unhandled key:", key, "at:", parameter_at_instant.file_path)
    return export


def export_parameter_metadata(parameter, metadata):
    assert isinstance(metadata, dict)
    if len(metadata) == 0:
        return None
    export = {}
    for key, value in metadata.items():
        if key == "documentation":
            if value is not None:
                assert isinstance(value, str)
                export[key] = value
        elif key == "rate_unit":
            assert parameter.__class__.__name__ == "Scale", parameter.__class__.__name__
            assert value in ("/1"), value
            export[key] = value
        elif key == "reference":
            assert (
                isinstance(value, str)
                or isinstance(value, list) and all(
                    isinstance(item_value, str)
                    for item_value in value
                    )
                or isinstance(value, dict) and all(
                    periods.INSTANT_PATTERN.match(item_key) and isinstance(item_value, str)
                    for item_key, item_value in value.items()
                    )
                ), value
            export[key] = value
        elif key == "threshold_unit":
            assert parameter.__class__.__name__ == "Scale", parameter.__class__.__name__
            assert value in ("currency"), value
            export[key] = value
        elif key == "type":
            assert parameter.__class__.__name__ == "Scale", parameter.__class__.__name__
            assert value in ("marginal_rate", "single_amount"), value
            # Ignore type, because it is set by bracket:
            # export[key] = value
        elif key == "unit":
            assert isinstance(value, str)
            assert value in ("/1", "currency", "ISO 3166-1 alpha-2", "year"), value
            export[key] = value
        else:
            print("Metadata - Unhandled key:", key, "=", value)
    return export


def walDecompositionLeafs(node):
    children = node.get("children")
    if children:
        for child in children:
            yield from walDecompositionLeafs(child)
        # Note: Ignore nodes that are the total of their children.
    else:
        yield node


@app.websocket("/calculate")
async def calculate(websocket: WebSocket):
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
                print(f"Calculated {node["code"]}: {value}")
                await websocket.send_json(dict(code=node["code"], value=value.tolist()))
                await asyncio.sleep(0)


@app.get("/parameters")
async def list_parameters():
    return export_parameter(tax_benefit_system.parameters)
