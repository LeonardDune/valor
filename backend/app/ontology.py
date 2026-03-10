import os

_BASE = os.getenv("VALOR_ONTOLOGY_BASE_URL", "https://valor-ecosystem.nl/ontology/")

VALOR_NS = f"{_BASE}valor#"
GUFO_NS = f"{_BASE}gufo-core#"
UFOC_NS = f"{_BASE}ufo-c#"
