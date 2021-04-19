from fastapi import APIRouter
from typing import List
import pandas as pd
from openfisca_core.parameters import ParameterNode  # type: ignore
from openfisca_core import periods  # type: ignore
from openfisca_core.simulation_builder import SimulationBuilder
from openfisca_france import FranceTaxBenefitSystem  # type: ignore
from openfisca_france.model.base import Reform  # type: ignore
from leximpact_socio_fiscal_api.database.schemas import ReformCSG, CasType, TabCasType

# For profiling
import timeit
from memory_profiler import profile

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
    # print('debut')
    situation = TabloCasTypeToSituations(tct.castype)
    print("\tSituation - Nombre de foyers : ", len(situation['foyers_fiscaux']))
    print("\tSituation - Nombre d'individus' : ", len(situation['individus']))
    simulation_builder = SimulationBuilder()
    simulation = simulation_builder.build_from_entities(
        tax_benefit_system, situation)
    # print('Simu ready_')
    value = simulation.calculate_add('csg', '2021')
    # population = simulation.get_variable_population('csg')
    # entity_count = simulation_builder.entity_counts[population.entity.plural]
    # print(f"Calculated : {entity_count} {value}")
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
        mon_cas_type = CasType(
            revenu_activite=revenu_salarie, revenu_capital=rev_capital,
            revenu_remplacement=rev_rempl, revenu_retraite=rev_retraite,
            wprm=wprm)
        d += [mon_cas_type]
    # print("Nombre de foyer de cas type : ", len(d))
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


@profile
def compute_reform(reform: ReformCSG):
    """
    :reform: OpenFisca parameters to change.
    """

    # Monitor CPU and RAM
    # timeit.timeit('"-".join(str(n) for n in range(100))', number=10000)
    debut = timeit.default_timer()
    tax_benefit_system = CSGReform(FranceTaxBenefitSystem(), reform, "2020")
    print(f"Temps de création de la réforme : {timeit.default_timer() - debut} secondes")
    debut_load_csv = timeit.default_timer()
    lct = csv_to_list_castype("./data/DCT.csv")

    # for i in range(10):  # 10 -> 6 144 foyers
    #     lct += lct
    print(f"Temps de création des faux castypes : {timeit.default_timer() - debut_load_csv} secondes")
    print(f"Temps de traitement avant calcul : {timeit.default_timer() - debut} secondes")
    debut_compute = timeit.default_timer()
    mes_csg = compute_csg(TabCasType(castype=lct), tax_benefit_system)
    print(f"Temps de calcul sur la population : {timeit.default_timer() - debut_compute} secondes")
    montant_total = sum(mes_csg[i] * lct[i].wprm for i in range(len(lct)))
    print(f"Temps de traitement total pour {len(lct)} foyers : {timeit.default_timer() - debut} secondes")
    # print("lct", lct[0])
    # print("mes_csg", mes_csg)
    return montant_total


@router.post("/reform_csg")
def reform_csg(reform: ReformCSG):
    return compute_reform(reform)
