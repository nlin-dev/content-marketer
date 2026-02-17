from app.seed_data.claims import CLAIMS
from app.seed_data.isi import ISI_ASSET
from app.seed_data.assets import ASSETS as _ASSETS

ASSETS = _ASSETS + [ISI_ASSET]

__all__ = ["CLAIMS", "ASSETS"]
