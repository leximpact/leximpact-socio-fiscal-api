import asyncio
import numpy as np
import pandas as pd
from fastapi import FastAPI, WebSocket
from openfisca_core.simulation_builder import SimulationBuilder
from openfisca_france import FranceTaxBenefitSystem
from pydantic import BaseModel
from typing import List, Optional


app = FastAPI()


"""
from openfisca_core.parameters import ParameterNode  # type: ignore
from openfisca_core import periods  # type: ignore
from openfisca_france import FranceTaxBenefitSystem  # type: ignore
from openfisca_france.model.base import Reform  # type: ignore

from Simulation_engine.reform_nbptr import generate_nbptr_class


#T = TypeVar("T", bound="ParametricReform")

class CSGReform(Reform):
    def __init__(self, tbs: FranceTaxBenefitSystem, payload: dict, period: str) -> None:
        #self.payload = payload.get("csg", {}) #Pas utilisé  for now
        self.instant = periods.instant(period)
        self.period = periods.period("year:1900:200")
        super().__init__(tbs)

    def modifier(self, parameters: ParameterNode) -> ParameterNode:
        print(parameters)
        parameter =getattr(parameters, "prelevements_sociaux.contributions.csg.activite.imposable")
        #parameters..update(period = self.period, value = 0)
        return parameter

    def apply(self) -> None:
        self.modify_parameters(modifier_function=self.modifier)"""




tax_benefit_system = FranceTaxBenefitSystem()
#tax_benefit_system = CSGReform(FranceTaxBenefitSystem(), None, "2020")


def walDecompositionLeafs(node):
    children = node.get("children")
    if children:
        for child in children:
            yield from walDecompositionLeafs(child)
        # Note: Ignore nodes that are the total of their children.
    else:
        yield node


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
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

        if not calculate:
            continue
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

class CasType(BaseModel):
    revenu_activite: float
    revenu_capital: float
    revenu_remplacement: float
    revenu_retraite: float
    wprm: Optional[float]

class TabCasType(BaseModel):
    castype: List[CasType]
    class Config:
        schema_extra = {
            "example": 
                [
                    {
                        "revenu_activite": 50000,
                        "revenu_capital": 0,
                        "revenu_remplacement": 0,
                        "revenu_retraite": 0
                    },
                        {
                        "revenu_activite": 0,
                        "revenu_capital": 50000,
                        "revenu_remplacement": 0,
                        "revenu_retraite": 0
                    },
                        {
                        "revenu_activite": 0,
                        "revenu_capital": 0,
                        "revenu_remplacement": 50000,
                        "revenu_retraite": 0
                    },
                        {
                        "revenu_activite": 0,
                        "revenu_capital": 0,
                        "revenu_remplacement": 0,
                        "revenu_retraite": 50000
                    }
                    ]
                }

def CasTypeToSituation(ct):
    return {
        "familles": {
            "Famille 1": {
                "parents": [
                    "Adulte 1"
                ],
                "enfants": []
            }
        },
        "foyers_fiscaux": {
            "Foyer fiscal 1": {
                "declarants": [
                    "Adulte 1"
                ],
                "personnes_a_charge": [],
                "assiette_csg_revenus_capital": {
                    "2021": ct.revenu_capital
                },
            }
        },
        "individus": {
            "Adulte 1": {
                "salaire_de_base": {
                    "2021": ct.revenu_activite
                },
                "chomage_brut": {
                    "2021": ct.revenu_remplacement
                },
                "retraite_brute": {
                    "2021": ct.revenu_retraite
                }
            }
        },
        "menages": {
            "Menage 1": {
                "personne_de_reference": [
                    "Adulte 1"
                ],
                "conjoint": [],
                "enfants": []
            }
        }
    }



def TabloCasTypeToSituations(tct : List[CasType]):
    return {
        "familles": {
            f"Famille {i}": {
                "parents": [
                    f"Adulte {i}"
                ],
                "enfants": []
            }
            for i in range(len(tct))
        },
        "foyers_fiscaux": {
            f"Foyer fiscal {i}": {
                "declarants": [
                    f"Adulte {i}"
                ],
                "personnes_a_charge": [],
                "assiette_csg_revenus_capital": {
                    "2021": d.revenu_capital
                },
            }
            for i,d in enumerate(tct)
        },
        "individus": {
            f"Adulte {i}": {
                "salaire_de_base": {
                    "2021": d.revenu_activite
                },
                "chomage_brut": {
                    "2021": d.revenu_remplacement
                },
                "retraite_brute": {
                    "2021": d.revenu_retraite
                }
            }
            for i,d in enumerate(tct)
        },
        "menages": {
            f"Menage {i}": {
                "personne_de_reference": [
                    f"Adulte {i}"
                ],
                "conjoint": [],
                "enfants": []
            }
            for i,d in enumerate(tct)
        }
    }


@app.post("/csg", tags=["castype"])
def csg(tct: TabCasType):
    situation = TabloCasTypeToSituations(tct)
    simulation_builder = SimulationBuilder()
    simulation = simulation_builder.build_from_entities(tax_benefit_system, situation)
    value = simulation.calculate_add('csg', '2021')
    population = simulation.get_variable_population('csg')
    entity_count = simulation_builder.entity_counts[population.entity.plural]
    print(f"Calculated : {entity_count} {value}")            
    return [{"csg": float(v)} for v in value]
    

def csv_to_list_castype(filename):
    data=pd.read_csv(filename)
    d=[]
    for idfoy in set(data["idfoy"].values):
        revenu_salarie = sum(data[data["idfoy"] == idfoy]["salaire_de_base"].values)
        rev_retraite = sum(data[data["idfoy"] == idfoy]["retraite_brute"].values)
        rev_capital = sum(data[data["idfoy"] == idfoy]["f4ba"].values)
        rev_rempl = sum(data[data["idfoy"] == idfoy]["chomage_brut"].values)
        wprm=data[data["idfoy"] == idfoy]["wprm"].values[0]
        # print("Oui mon type est", type(revenu_salarie))
        mon_cas_type = CasType(revenu_activite=revenu_salarie, revenu_capital=rev_capital, revenu_remplacement=rev_rempl, revenu_retraite = rev_retraite, wprm= wprm)
        d+=[mon_cas_type]
    return d 


@app.get("/csg_pop", tags=["castype"])
def csg_pop():
    lct= csv_to_list_castype("./data/DCT.csv")
    mes_csg= csg(lct)
    return sum(mes_csg[i]["csg"]*lct[i].wprm for i in range(len(lct)))


