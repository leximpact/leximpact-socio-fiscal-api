from fastapi import APIRouter
from typing import List
import pandas as pd
from openfisca_core.parameters import ParameterNode  # type: ignore
from openfisca_core import periods  # type: ignore
from openfisca_core.simulation_builder import SimulationBuilder
from openfisca_france import FranceTaxBenefitSystem  # type: ignore
from openfisca_france.model.base import Reform  # type: ignore
from leximpact_socio_fiscal_api.database.schemas import ReformCSG, CasType, TabCasType


tax_benefit_system = FranceTaxBenefitSystem()
router = APIRouter()


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


def TabloCasTypeToSituations(tct: List[CasType]):
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
            for i, d in enumerate(tct)
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
            for i, d in enumerate(tct)
        },
        "menages": {
            f"Menage {i}": {
                "personne_de_reference": [
                    f"Adulte {i}"
                ],
                "conjoint": [],
                "enfants": []
            }
            for i, d in enumerate(tct)
        }
    }


def compute_csg(tct, tax_benefit_system):
    print('debut')
    situation = TabloCasTypeToSituations(tct.castype)
    simulation_builder = SimulationBuilder()
    simulation = simulation_builder.build_from_entities(
        tax_benefit_system, situation)
    print('Simu ready_')
    value = simulation.calculate_add('csg', '2021')
    population = simulation.get_variable_population('csg')
    entity_count = simulation_builder.entity_counts[population.entity.plural]
    print(f"Calculated : {entity_count} {value}")
    return value


@router.post("/csg", tags=["castype"])
def csg(tct: TabCasType):
    value = compute_csg(tct, tax_benefit_system)
    return [{"csg": float(v)} for v in value]


def csv_to_list_castype(filename):
    data = pd.read_csv(filename)
    d = []
    for idfoy in set(data["idfoy"].values):
        revenu_salarie = sum(
            data[data["idfoy"] == idfoy]["salaire_de_base"].values)
        rev_retraite = sum(
            data[data["idfoy"] == idfoy]["retraite_brute"].values)
        rev_capital = sum(
            data[data["idfoy"] == idfoy]["f4ba"].values)
        rev_rempl = sum(
            data[data["idfoy"] == idfoy]["chomage_brut"].values)
        wprm = data[data["idfoy"] == idfoy]["wprm"].values[0]
        # print("Oui mon type est", type(revenu_salarie))
        mon_cas_type = CasType(
            revenu_activite=revenu_salarie, revenu_capital=rev_capital,
            revenu_remplacement=rev_rempl, revenu_retraite=rev_retraite,
            wprm=wprm)
        d += [mon_cas_type]
    return d


@router.get("/csg_pop", tags=["castype"])
def csg_pop():
    lct = csv_to_list_castype("./data/DCT.csv")
    mes_csg = compute_csg(TabCasType(castype=lct), tax_benefit_system)
    print("lct", lct)
    print("mes_csg", mes_csg)
    return sum(mes_csg[i] * lct[i].wprm for i in range(len(lct)))


class CSGReform(Reform):
    def __init__(self, tbs: FranceTaxBenefitSystem,
                 payload: ReformCSG, period: str) -> None:
        self.payload = payload
        self.instant = periods.instant(period)
        self.period = periods.period('year:1900:200')
        super().__init__(tbs)

    def modifier(self, parameters: ParameterNode) -> ParameterNode:
        parameters.prelevements_sociaux.contributions.csg.activite.imposable.taux.update(
            period=self.period, value=self.payload.csg_activite_imposable_taux)
        parameters.prelevements_sociaux.contributions.csg.activite.deductible.taux.update(
            period=self.period, value=self.payload.csg_activite_deductible_taux)
        return parameters

    def apply(self) -> None:
        self.modify_parameters(modifier_function=self.modifier)


@router.post("/reform_csg")
def reform_csg(reform: ReformCSG):
    """
    :reform: OpenFisca parameters to change.
    """

    tax_benefit_system = CSGReform(FranceTaxBenefitSystem(), reform, "2020")
    lct = csv_to_list_castype("./data/DCT.csv")
    mes_csg = compute_csg(TabCasType(castype=lct), tax_benefit_system)
    print("lct", lct[0])
    print("mes_csg", mes_csg)
    return sum(mes_csg[i] * lct[i].wprm for i in range(len(lct)))
