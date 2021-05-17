---

# Pour consulter la dernière version du projet, merci de vous rendre sur https://git.leximpact.dev/leximpact/leximpact-socio-fiscal-api/

---
![](changement-depot-github-gitlab-illustration-small.png)
---

# LexImpact Socio-Fiscal API

_HTTP + WebSocket API for OpenFisca_

Used by [LexImpact Socio-Fiscal UI](https://github.com/leximpact/leximpact-socio-fiscal-ui), a simulator of the French tax-benefit system.

## Installation

```bash
git clone https://github.com/leximpact/leximpact-socio-fiscal-api.git
cd leximpact-socio-fiscal-api/
poetry install

poetry shell
# Install an OpenFisca country package (for example OpenFisca-France).
pip install OpenFisca-France
# Create environment configuration file and then edit it to reference country package et its JSON output.
cp example.env .env
```

## Usage

Start web API server:

```bash
poetry shell
uvicorn --reload leximpact_socio_fiscal_api.main:app
```
