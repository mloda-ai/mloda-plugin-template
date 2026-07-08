"""The installed package must expose its plugins to mloda via entry points, with no manual import.

Rename-safe: these assertions never name the ``placeholder`` package, so they keep passing after
``bin/customize.sh`` renames it (exercised end-to-end by scaffold-test.yml).
"""

import importlib.metadata

from mloda.core.abstract_plugins.plugin_registry.plugin_registry import PluginRegistry
from mloda.user import PluginLoader

# group -> the manifest attribute its entry point must resolve to (value suffix survives rename)
EXPECTED_ENTRY_POINTS = {
    "mloda.feature_groups": "manifest:FEATURE_GROUPS",
    "mloda.compute_frameworks": "manifest:COMPUTE_FRAMEWORKS",
    "mloda.extenders": "manifest:EXTENDERS",
}


def test_entry_points_declared() -> None:
    """Each mloda group exposes a manifest entry point in the installed distribution metadata."""
    for group, suffix in EXPECTED_ENTRY_POINTS.items():
        values = [ep.value for ep in importlib.metadata.entry_points(group=group)]
        assert any(v.endswith(suffix) for v in values), f"{group}: no entry point ending in {suffix}; got {values}"


def test_plugin_loader_discovers_example_classes() -> None:
    """PluginLoader.all() registers the example classes via entry points, without importing the package."""
    PluginLoader.all(force_reload=True)
    registered = {cls.__name__ for cls in PluginRegistry.default().registered_classes()}
    assert {"MyFeatureGroup", "MyComputeFramework", "MyExtender"} <= registered
