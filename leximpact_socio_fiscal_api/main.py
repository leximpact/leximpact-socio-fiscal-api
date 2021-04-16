from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import parameters, simulations, variables


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_credentials = False,  # Can't be True when allow_origins is set to ["*"].
    allow_methods = ["*"],
    allow_headers = ["*"],
    )
app.include_router(parameters.router)
app.include_router(simulations.router)
app.include_router(variables.router)
