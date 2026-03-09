"""
Integratietest: alle schrijfroutes (POST/PATCH/DELETE) moeten een
get_current_user dependency hebben. Voeg een route toe aan EXEMPT_PATHS
alleen als ze bewust publiek zijn.
"""
import pytest
from fastapi.routing import APIRoute
from app.auth import get_current_user


EXEMPT_PATHS = {
    ("POST", "/chat"),  # publieke AI-chat endpoint
}

WRITE_METHODS = {"POST", "PATCH", "DELETE"}


def get_mutation_routes():
    from app.main import app

    routes = []
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        for method in route.methods or []:
            if method in WRITE_METHODS:
                routes.append((method, route.path, route))
    return routes


@pytest.mark.parametrize("method,path,route", get_mutation_routes())
def test_schrijfroute_heeft_auth(method, path, route):
    if (method, path) in EXEMPT_PATHS:
        pytest.skip(f"{method} {path} is bewust publiek")

    dependency_callables = [d.dependency for d in route.dependencies]

    # Controleer ook dependencies op de handler zelf via __wrapped__ / dependant
    try:
        from fastapi.dependencies.utils import get_dependant
        dependant = get_dependant(path=path, call=route.endpoint)
        all_deps = [d.call for d in dependant.dependencies]
    except Exception:
        all_deps = dependency_callables

    assert get_current_user in all_deps, (
        f"{method} {path} mist get_current_user dependency — "
        "voeg Depends(get_current_user) toe of voeg toe aan EXEMPT_PATHS."
    )
