"""Entry-point manifest: concrete Extender classes this package exports to mloda discovery."""

from mloda.core.abstract_plugins.function_extender import Extender

from placeholder.extenders.my_plugin.my_extender import MyExtender

# Referenced by the "mloda.extenders" entry point in pyproject.toml.
EXTENDERS: list[type[Extender]] = [MyExtender]
