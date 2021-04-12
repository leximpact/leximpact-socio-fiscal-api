# LexImpact Socio-Fiscal API

_HTTP + WebSocket API for OpenFisca_

Used by [LexImpact Socio-Fiscal UI](https://github.com/leximpact/leximpact-socio-fiscal-ui), a simulator of the French tax-benefit system.

## Installation

```bash
git clone https://github.com/leximpact/leximpact-socio-fiscal-api.git
cd leximpact-socio-fiscal-api/
poetry install
```

## Usage

```bash
poetry shell
uvicorn --reload leximpact_socio_fiscal_api.server:app
```
