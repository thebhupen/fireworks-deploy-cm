"""Make the Bharat apps loadable by ARE's own scenario importer, without changing ARE.

ARE's importer builds apps from `are.simulation.apps.ALL_APPS` (unknown classes are skipped
silently), and replayed actions look classes up as attributes of `are.simulation.apps`. Both are
plain module-level objects, so registering at import time is enough.
"""

from __future__ import annotations

import are.simulation.apps as are_apps


def register_with_are(app_classes: tuple[type, ...]) -> None:
    """Add the classes to ARE's app registry and module namespace. Safe to call more than once."""
    for app_class in app_classes:
        if app_class not in are_apps.ALL_APPS:
            are_apps.ALL_APPS.append(app_class)
        setattr(are_apps, app_class.__name__, app_class)
