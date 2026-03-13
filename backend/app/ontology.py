import os

_SITE_BASE = os.getenv("VALOR_SITE_BASE_URL", "https://valor-ecosystem.nl/")
_BASE = os.getenv("VALOR_ONTOLOGY_BASE_URL", f"{_SITE_BASE}ontology/")

VALOR_SITE_BASE = _SITE_BASE
VALOR_NS = _BASE
GUFO_NS = f"{_BASE}gufo-core#"
UFOC_NS = f"{_BASE}ufo-c#"
