"""
https://fastapi.tiangolo.com/tutorial/sql-databases/

To avoid confusion between the SQLAlchemy models and the Pydantic models,
 we will have the file models.py with the SQLAlchemy models,
  and the file schemas.py
  with the Pydantic models.

These Pydantic models define more or less a "schema" (a valid data shape).

So this will help us avoiding confusion while using both.
"""

from typing import List, Optional
from pydantic import BaseModel


class CasType(BaseModel):
    revenu_activite: float
    revenu_capital: float
    revenu_remplacement: float
    revenu_retraite: float
    wprm: Optional[float]

    class Config:
        schema_extra = {
            "example":
                {
                    "revenu_activite": 50000,
                    "revenu_capital": 0,
                    "revenu_remplacement": 0,
                    "revenu_retraite": 0,
                    "wprm": 10
                }
        }


class TabCasType(BaseModel):
    castype: List[CasType]

    class Config:
        schema_extra = {
            "example": {
                "castype":
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
        }


class ReformCSG(BaseModel):
    csg_activite_imposable_taux: float
    csg_activite_deductible_taux: float
