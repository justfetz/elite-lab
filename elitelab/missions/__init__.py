"""Mission registry. Add a mission by dropping a module here that exposes MISSION."""
import importlib
import pkgutil

from .base import Mission


def load_missions():
    missions = {}
    for info in pkgutil.iter_modules(__path__):
        if info.name in ("base",):
            continue
        mod = importlib.import_module(f"{__name__}.{info.name}")
        found = getattr(mod, "MISSIONS", None) or [getattr(mod, "MISSION", None)]
        for m in found:
            if isinstance(m, Mission):
                missions[m.id] = m
    # sort by layer label then id
    return dict(sorted(missions.items(), key=lambda kv: (kv[1].layer, kv[1].id)))
