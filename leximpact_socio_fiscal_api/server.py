from fastapi import FastAPI
from leximpact_socio_fiscal_api.routers import csg, waterfall


app = FastAPI()
app.include_router(csg.router)
app.include_router(waterfall.router)


@app.get("/", tags=["root"])
def root():
    return {"message": "please go to /docs"}


@app.get("/status", tags=["root"])
def status():
    return {"status": "OK"}
